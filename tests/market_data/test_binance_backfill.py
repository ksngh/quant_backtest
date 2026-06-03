from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pytest

from quant_bitcoin.market_data.binance_backfill import (
    RETRYABLE_HTTP_STATUS_CODES,
    BinanceHistoricalBackfiller,
    MultiIntervalBackfillError,
    MultiIntervalBinanceBackfillRunner,
    RetryableBinanceError,
    _interval_milliseconds,
    map_binance_kline_to_persisted_candle,
    parse_interval_list,
)
from quant_bitcoin.persistence import HISTORICAL_BACKFILL_MODE, SOURCE_BINANCE_SPOT


def sample_kline(open_time_ms: int, interval_ms: int = 60_000) -> list[object]:
    return [
        open_time_ms,
        "42000.00",
        "42100.00",
        "41900.00",
        "42050.00",
        "12.50000000",
        open_time_ms + interval_ms - 1,
        "525625.00000000",
        123,
        "6.10000000",
        "256405.00000000",
        "0",
    ]


class InMemoryCandleRepository:
    def __init__(self) -> None:
        self.rows = {}
        self.checkpoints = []
        self.latest = None

    def latest_open_time(self, source: str, symbol: str, interval: str):
        assert source == SOURCE_BINANCE_SPOT
        assert symbol == "BTCUSDT"
        return self.latest

    def upsert_candles(self, candles):
        for candle in candles:
            key = (candle.source, candle.symbol, candle.interval, candle.open_time)
            self.rows[key] = candle
            self.latest = candle.open_time
        return len(candles)

    def save_checkpoint(self, checkpoint):
        self.checkpoints.append(checkpoint)


def fixed_now() -> datetime:
    return datetime(2024, 1, 1, 0, 3, 30, tzinfo=timezone.utc)


def test_maps_binance_kline_payload_to_persistence_row():
    candle = map_binance_kline_to_persisted_candle(
        sample_kline(1_704_067_200_000),
        symbol=" btcusdt ",
        interval="1m",
        now=datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc),
    )

    assert candle.source == SOURCE_BINANCE_SPOT
    assert candle.symbol == "BTCUSDT"
    assert candle.interval == "1m"
    assert candle.open_time == datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert candle.close_time == datetime(
        2024, 1, 1, 0, 0, 59, 999000, tzinfo=timezone.utc
    )
    assert candle.open == Decimal("42000.00")
    assert candle.high == Decimal("42100.00")
    assert candle.low == Decimal("41900.00")
    assert candle.close == Decimal("42050.00")
    assert candle.volume == Decimal("12.50000000")
    assert candle.quote_asset_volume == Decimal("525625.00000000")
    assert candle.number_of_trades == 123
    assert candle.taker_buy_base_asset_volume == Decimal("6.10000000")
    assert candle.taker_buy_quote_asset_volume == Decimal("256405.00000000")
    assert candle.is_closed is True
    assert candle.raw_payload == sample_kline(1_704_067_200_000)


def test_open_in_progress_kline_is_not_persisted_as_closed():
    candle = map_binance_kline_to_persisted_candle(
        sample_kline(1_704_067_380_000),
        symbol="BTCUSDT",
        interval="1m",
        now=fixed_now(),
    )

    assert candle.is_closed is False


def test_backfill_paginates_from_earliest_start_and_persists_closed_candles():
    repository = InMemoryCandleRepository()
    requested_urls = []
    pages = [
        [sample_kline(1_704_067_200_000), sample_kline(1_704_067_260_000)],
        [sample_kline(1_704_067_320_000)],
    ]

    def fake_http_get(url: str, timeout: float):
        requested_urls.append(url)
        assert timeout == 2.0
        assert "/api/v3/klines" in url
        assert "/order" not in url.lower()
        return pages.pop(0)

    result = BinanceHistoricalBackfiller(
        repository,
        timeout=2.0,
        http_get=fake_http_get,
        now=fixed_now,
    ).run(start_time=1_704_067_200_000, end_time=1_704_067_320_000, limit=2)

    assert result.stored_candles == 3
    assert result.pages_fetched == 2
    assert len(repository.rows) == 3
    first_query = parse_qs(urlparse(requested_urls[0]).query)
    second_query = parse_qs(urlparse(requested_urls[1]).query)
    assert first_query["startTime"] == ["1704067200000"]
    assert first_query["endTime"] == ["1704067320000"]
    assert first_query["limit"] == ["2"]
    assert second_query["startTime"] == ["1704067320000"]
    assert repository.checkpoints[-1].status == "completed"
    assert repository.checkpoints[-1].mode == HISTORICAL_BACKFILL_MODE


def test_backfill_resumes_after_latest_stored_candle():
    repository = InMemoryCandleRepository()
    repository.latest = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    requested_urls = []

    def fake_http_get(url: str, timeout: float):
        requested_urls.append(url)
        return [sample_kline(1_704_067_260_000)]

    result = BinanceHistoricalBackfiller(
        repository, http_get=fake_http_get, now=fixed_now
    ).run(end_time=1_704_067_260_000, limit=1000)

    assert result.stored_candles == 1
    query = parse_qs(urlparse(requested_urls[0]).query)
    assert query["startTime"] == ["1704067260000"]


def test_backfill_filters_open_candles_before_upsert():
    repository = InMemoryCandleRepository()

    def fake_http_get(url: str, timeout: float):
        return [sample_kline(1_704_067_320_000), sample_kline(1_704_067_380_000)]

    result = BinanceHistoricalBackfiller(
        repository, http_get=fake_http_get, now=fixed_now
    ).run(start_time=1_704_067_320_000, end_time=1_704_067_380_000, limit=2)

    assert result.stored_candles == 1
    assert len(repository.rows) == 1
    stored = next(iter(repository.rows.values()))
    assert stored.open_time == datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc)


def test_backfill_retries_rate_limited_market_data_response():
    repository = InMemoryCandleRepository()
    attempts = []
    sleeps = []

    def fake_http_get(url: str, timeout: float):
        attempts.append(url)
        if len(attempts) == 1:
            raise RetryableBinanceError("rate limited")
        return [sample_kline(1_704_067_200_000)]

    result = BinanceHistoricalBackfiller(
        repository,
        http_get=fake_http_get,
        sleep=sleeps.append,
        now=fixed_now,
        max_retries=1,
    ).run(start_time=1_704_067_200_000, end_time=1_704_067_200_000)

    assert result.stored_candles == 1
    assert len(attempts) == 2
    assert sleeps == [1]


def test_backfill_retries_rate_limit_payload_from_market_data_response():
    repository = InMemoryCandleRepository()
    attempts = []
    sleeps = []

    def fake_http_get(url: str, timeout: float):
        attempts.append(url)
        if len(attempts) == 1:
            return {"status": "429", "msg": "rate limit"}
        return [sample_kline(1_704_067_200_000)]

    result = BinanceHistoricalBackfiller(
        repository,
        http_get=fake_http_get,
        sleep=sleeps.append,
        now=fixed_now,
        max_retries=1,
    ).run(start_time=1_704_067_200_000, end_time=1_704_067_200_000)

    assert result.stored_candles == 1
    assert len(attempts) == 2
    assert sleeps == [1]


def test_http_retry_statuses_include_binance_rate_limit_and_ip_ban_responses():
    assert 418 in RETRYABLE_HTTP_STATUS_CODES
    assert 429 in RETRYABLE_HTTP_STATUS_CODES


def test_backfill_uses_public_market_data_endpoint_without_signed_request_data():
    repository = InMemoryCandleRepository()

    def fake_http_get(url: str, timeout: float):
        parsed = urlparse(url)
        assert parsed.path == "/api/v3/klines"
        assert "order" not in parsed.path.lower()
        assert "apiKey" not in url
        assert "signature" not in url
        assert "X-MBX-APIKEY" not in url
        return []

    result = BinanceHistoricalBackfiller(
        repository, http_get=fake_http_get, now=fixed_now
    ).run(start_time=1_704_067_200_000, end_time=1_704_067_200_000)

    assert result.stored_candles == 0


@pytest.mark.parametrize(
    ("interval", "interval_ms"),
    [("1h", 3_600_000), ("4h", 14_400_000), ("1d", 86_400_000)],
)
def test_backfill_accepts_higher_timeframe_intervals_for_public_kline_requests(
    interval: str, interval_ms: int
):
    repository = InMemoryCandleRepository()
    open_time_ms = 1_704_067_200_000
    requested_urls = []

    def fake_http_get(url: str, timeout: float):
        requested_urls.append(url)
        return [sample_kline(open_time_ms, interval_ms=interval_ms)]

    result = BinanceHistoricalBackfiller(
        repository,
        http_get=fake_http_get,
        now=lambda: datetime(2024, 1, 3, tzinfo=timezone.utc),
    ).run(
        interval=interval,
        start_time=open_time_ms,
        end_time=open_time_ms,
    )

    query = parse_qs(urlparse(requested_urls[0]).query)
    assert query["interval"] == [interval]
    assert result.interval == interval
    assert result.stored_candles == 1
    assert next(iter(repository.rows.values())).interval == interval


@pytest.mark.parametrize(
    ("interval", "expected_ms"),
    [("1h", 3_600_000), ("4h", 14_400_000), ("1d", 86_400_000)],
)
def test_interval_milliseconds_maps_higher_timeframe_intervals(
    interval: str, expected_ms: int
):
    assert _interval_milliseconds(interval) == expected_ms


def test_interval_list_parser_trims_deduplicates_and_preserves_order():
    assert parse_interval_list("1m, 1h,4h,1d,1h,5m") == (
        "1m",
        "1h",
        "4h",
        "1d",
        "5m",
    )


def test_interval_list_parser_rejects_unsupported_interval():
    with pytest.raises(ValueError, match="supported Binance kline interval"):
        parse_interval_list("1m,2h")


def test_multi_interval_runner_calls_backfiller_once_per_interval():
    calls = []

    class FakeBackfiller:
        def run(self, **kwargs):
            calls.append(kwargs)
            return type(
                "Result",
                (),
                {
                    "symbol": kwargs["symbol"],
                    "interval": kwargs["interval"],
                    "requested_start_time": kwargs["start_time"],
                    "requested_end_time": kwargs["end_time"],
                    "stored_candles": 1,
                    "pages_fetched": 1,
                },
            )()

    result = MultiIntervalBinanceBackfillRunner(FakeBackfiller()).run(
        symbol="btcusdt",
        intervals=("1m", "1h", "4h", "1d"),
        start_time=1,
        end_time=2,
        limit=100,
    )

    assert result.symbol == "BTCUSDT"
    assert result.intervals == ("1m", "1h", "4h", "1d")
    assert [call["interval"] for call in calls] == ["1m", "1h", "4h", "1d"]
    assert all(call["symbol"] == "BTCUSDT" for call in calls)


def test_multi_interval_runner_reports_failing_interval():
    class FailingBackfiller:
        def run(self, **kwargs):
            if kwargs["interval"] == "5m":
                raise RuntimeError("network down")
            return object()

    with pytest.raises(MultiIntervalBackfillError) as error:
        MultiIntervalBinanceBackfillRunner(FailingBackfiller()).run(
            intervals=("1m", "5m", "15m")
        )

    assert error.value.interval == "5m"
    assert "5m" in str(error.value)


def test_persisted_candle_identity_separates_same_open_time_by_interval():
    repository = InMemoryCandleRepository()
    one_minute = map_binance_kline_to_persisted_candle(
        sample_kline(1_704_067_200_000),
        symbol="BTCUSDT",
        interval="1m",
        now=fixed_now(),
    )
    five_minute = map_binance_kline_to_persisted_candle(
        sample_kline(1_704_067_200_000),
        symbol="BTCUSDT",
        interval="5m",
        now=fixed_now(),
    )

    assert repository.upsert_candles([one_minute, five_minute]) == 2
    assert len(repository.rows) == 2


@pytest.mark.parametrize(
    ("raw_kline", "message"),
    [
        ("not-a-row", "must be a sequence"),
        ([1, "42000"], "at least 11 fields"),
        (
            sample_kline(1_704_067_200_000)[:1]
            + ["bad"]
            + sample_kline(1_704_067_200_000)[2:],
            "must be numeric",
        ),
    ],
)
def test_kline_mapping_rejects_invalid_payloads(raw_kline, message):
    with pytest.raises(ValueError, match=message):
        map_binance_kline_to_persisted_candle(
            raw_kline, symbol="BTCUSDT", interval="1m", now=fixed_now()
        )
