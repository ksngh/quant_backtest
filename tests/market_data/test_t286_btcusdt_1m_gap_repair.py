from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pandas as pd

from quant_bitcoin.market_data.t286_btcusdt_1m_gap_repair import (
    CoverageAudit,
    TimeRange,
    audit_candle_frame,
    find_missing_ranges,
    plan_binance_request_ranges,
    repair_btcusdt_1m_gaps,
)
from quant_bitcoin.persistence import SOURCE_BINANCE_SPOT


def ts(minute: int) -> datetime:
    return datetime(2026, 4, 20, 0, minute, tzinfo=timezone.utc)


def sample_kline(open_time: datetime) -> list[object]:
    open_time_ms = int(open_time.timestamp() * 1000)
    return [
        open_time_ms,
        "42000.00",
        "42100.00",
        "41900.00",
        "42050.00",
        "12.50000000",
        open_time_ms + 59_999,
        "525625.00000000",
        123,
        "6.10000000",
        "256405.00000000",
        "0",
    ]


def candle_row(timestamp: datetime, close: str = "42050.00") -> dict[str, object]:
    close_decimal = Decimal(close)
    return {
        "timestamp": timestamp,
        "open": close_decimal - Decimal("50"),
        "high": close_decimal + Decimal("50"),
        "low": close_decimal - Decimal("150"),
        "close": close_decimal,
        "volume": Decimal("12.5"),
    }


class InMemoryRepository:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = {
            row["timestamp"]: dict(row)
            for row in rows
        }
        self.initialized = False
        self.checkpoints = []

    def initialize_schema(self) -> None:
        self.initialized = True

    def latest_open_time(self, source: str, symbol: str, interval: str):
        if not self.rows:
            return None
        return max(self.rows)

    def load_standard_candles(self, **kwargs):
        start_time = kwargs["start_time"]
        end_time = kwargs["end_time"]
        return [
            dict(row)
            for timestamp, row in sorted(self.rows.items())
            if start_time <= timestamp <= end_time
        ]

    def upsert_candles(self, candles):
        count = 0
        for candle in candles:
            self.rows[candle.open_time] = {
                "timestamp": candle.open_time,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
            }
            count += 1
        return count

    def save_checkpoint(self, checkpoint):
        self.checkpoints.append(checkpoint)


def test_find_missing_ranges_detects_leading_internal_and_trailing_gaps():
    target = TimeRange(ts(0), ts(9))

    missing = find_missing_ranges([ts(2), ts(3), ts(6), ts(7)], target_range=target)

    assert missing == (
        TimeRange(ts(0), ts(1)),
        TimeRange(ts(4), ts(5)),
        TimeRange(ts(8), ts(9)),
    )


def test_plan_binance_request_ranges_splits_by_limit():
    target = TimeRange(ts(0), ts(5))

    pages = plan_binance_request_ranges(target, limit=2)

    assert pages == (
        TimeRange(ts(0), ts(1)),
        TimeRange(ts(2), ts(3)),
        TimeRange(ts(4), ts(5)),
    )


def test_audit_candle_frame_reports_known_gap_and_utc_metadata():
    target = TimeRange(ts(0), ts(4))
    candles = pd.DataFrame([candle_row(ts(0)), candle_row(ts(1)), candle_row(ts(4))])

    audit = audit_candle_frame(
        candles,
        symbol="BTCUSDT",
        interval="1m",
        target_range=target,
    )

    assert isinstance(audit, CoverageAudit)
    assert audit.expected_candle_count == 5
    assert audit.actual_candle_count == 3
    assert audit.min_open_time == ts(0)
    assert audit.max_open_time == ts(4)
    assert audit.missing_ranges == (TimeRange(ts(2), ts(3)),)
    assert audit.validation_errors == ()


def test_repair_runner_fills_missing_rows_with_public_kline_endpoint(tmp_path):
    repository = InMemoryRepository([candle_row(ts(0)), candle_row(ts(2))])
    requested_urls = []

    def fake_http_get(url: str, timeout: float):
        requested_urls.append(url)
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        assert parsed.path == "/api/v3/klines"
        assert "order" not in parsed.path.lower()
        assert "apiKey" not in url
        assert "signature" not in url
        assert query["startTime"] == [str(int(ts(1).timestamp() * 1000))]
        assert query["endTime"] == [str(int(ts(1).timestamp() * 1000))]
        return [sample_kline(ts(1))]

    result = repair_btcusdt_1m_gaps(
        repository,
        target_start=ts(0),
        target_end=ts(2),
        http_get=fake_http_get,
        report_path=tmp_path / "task286.md",
        sleep=lambda _: None,
    )

    assert result.status == "COMPLETED"
    assert repository.initialized is True
    assert result.before.missing_ranges == (TimeRange(ts(1), ts(1)),)
    assert result.after.missing_ranges == ()
    assert result.repair_results[0].fetched_closed_candles == 1
    assert result.repair_results[0].estimated_new_candles == 1
    assert result.repair_results[0].duplicate_candles == 0
    assert len(requested_urls) == 1
    assert (tmp_path / "task286.md").read_text(encoding="utf-8").startswith(
        "# Task 286 BTCUSDT 1m Data Backfill And Gap Repair"
    )


def test_repair_runner_skips_network_when_no_missing_ranges(tmp_path):
    repository = InMemoryRepository([candle_row(ts(0)), candle_row(ts(1))])

    def unexpected_http_get(url: str, timeout: float):
        raise AssertionError("network should not be used when there are no gaps")

    result = repair_btcusdt_1m_gaps(
        repository,
        target_start=ts(0),
        target_end=ts(1),
        http_get=unexpected_http_get,
        report_path=tmp_path / "task286.md",
    )

    assert result.status == "COMPLETED"
    assert result.repair_results == ()
    assert result.before.missing_ranges == ()
    assert result.after.missing_ranges == ()


def test_repair_runner_reports_incomplete_when_gap_remains(tmp_path):
    repository = InMemoryRepository([candle_row(ts(0)), candle_row(ts(2))])

    def empty_http_get(url: str, timeout: float):
        return []

    result = repair_btcusdt_1m_gaps(
        repository,
        target_start=ts(0),
        target_end=ts(2),
        http_get=empty_http_get,
        report_path=tmp_path / "task286.md",
        sleep=lambda _: None,
    )

    assert result.status == "INCOMPLETE"
    assert result.before.missing_ranges == (TimeRange(ts(1), ts(1)),)
    assert result.after.missing_ranges == (TimeRange(ts(1), ts(1)),)
    assert "INCOMPLETE" in (tmp_path / "task286.md").read_text(encoding="utf-8")


def test_repair_runner_uses_binance_spot_source_by_default(tmp_path):
    repository = InMemoryRepository([candle_row(ts(0))])
    seen = {}
    original_load = repository.load_standard_candles

    def fake_load_standard_candles(**kwargs):
        seen.update(kwargs)
        return original_load(**kwargs)

    repository.load_standard_candles = fake_load_standard_candles  # type: ignore[method-assign]

    repair_btcusdt_1m_gaps(
        repository,
        target_start=ts(0),
        target_end=ts(0),
        report_path=tmp_path / "task286.md",
    )

    assert seen["source"] == SOURCE_BINANCE_SPOT
