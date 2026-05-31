"""Task 286 BTCUSDT 1m data backfill and continuity repair.

This module is intentionally market-data-only. It audits persisted public candle
coverage, repairs missing closed BTCUSDT 1m candles through the existing Binance
historical backfiller, and writes a before/after report. It does not import
strategy code, place orders, sign requests, or use account/private endpoints.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from quant_bitcoin.market_data.binance_backfill import (
    BINANCE_MAX_KLINE_LIMIT,
    BinanceHistoricalBackfiller,
)
from quant_bitcoin.market_data.binance_backfill_cli import DEFAULT_DATABASE_URL
from quant_bitcoin.market_data.binance_downloader import DEFAULT_MARKET_DATA_BASE_URL
from quant_bitcoin.market_data.candle_validation import (
    CandleValidationConfig,
    validate_standard_candles,
)
from quant_bitcoin.persistence import PersistedCandle, PostgresCandleRepository
from quant_bitcoin.persistence.postgres import SOURCE_BINANCE_SPOT

TASK_ID = "TASK_286"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"
DEFAULT_SOURCE = SOURCE_BINANCE_SPOT
TASK_TARGET_START = datetime(2026, 4, 20, 0, 0, tzinfo=timezone.utc)
TASK_TARGET_END = datetime(2026, 5, 28, 8, 26, tzinfo=timezone.utc)
ONE_MINUTE = timedelta(minutes=1)
DEFAULT_REPORT_PATH = Path("reports/TASK_286_BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR.md")


class CandleRepository(Protocol):
    def initialize_schema(self) -> None: ...

    def latest_open_time(self, source: str, symbol: str, interval: str) -> datetime | None: ...

    def load_standard_candles(
        self,
        *,
        source: str,
        symbol: str,
        interval: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]: ...

    def upsert_candles(self, candles: Iterable[PersistedCandle]) -> int: ...

    def save_checkpoint(self, checkpoint: Any) -> None: ...


HttpGet = Callable[[str, float], object]
Sleep = Callable[[float], None]


@dataclass(frozen=True, order=True)
class TimeRange:
    """Inclusive open-time range."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("TimeRange timestamps must be timezone-aware")
        if self.start > self.end:
            raise ValueError("TimeRange start must be <= end")

    @property
    def candle_count(self) -> int:
        return int((self.end - self.start) / ONE_MINUTE) + 1


@dataclass(frozen=True)
class CoverageAudit:
    symbol: str
    interval: str
    start_time: datetime
    end_time: datetime
    expected_candle_count: int
    actual_candle_count: int
    min_open_time: datetime | None
    max_open_time: datetime | None
    duplicate_count: int
    duplicate_timestamps: tuple[datetime, ...]
    missing_ranges: tuple[TimeRange, ...]
    validation_errors: tuple[str, ...]


@dataclass(frozen=True)
class RepairRangeResult:
    requested_range: TimeRange
    planned_pages: int
    expected_missing_candles: int
    fetched_closed_candles: int
    estimated_new_candles: int
    duplicate_candles: int
    conflicting_duplicate_candles: int
    repository_upserted_candles: int
    pages_fetched: int


@dataclass(frozen=True)
class RepairRunResult:
    task_id: str
    status: str
    symbol: str
    interval: str
    source: str
    target_range: TimeRange
    before: CoverageAudit
    repair_results: tuple[RepairRangeResult, ...]
    after: CoverageAudit
    report_path: Path
    dry_run: bool


class CountingCandleRepository:
    """Count duplicate/new candles while delegating persistence to a repository."""

    def __init__(
        self,
        repository: CandleRepository,
        *,
        existing_by_open_time: dict[datetime, dict[str, Any]],
    ) -> None:
        self.repository = repository
        self.existing_by_open_time = dict(existing_by_open_time)
        self.seen_new_open_times: set[datetime] = set()
        self.fetched_closed_candles = 0
        self.estimated_new_candles = 0
        self.duplicate_candles = 0
        self.conflicting_duplicate_candles = 0
        self.repository_upserted_candles = 0

    def latest_open_time(self, source: str, symbol: str, interval: str) -> datetime | None:
        return self.repository.latest_open_time(source, symbol, interval)

    def save_checkpoint(self, checkpoint: Any) -> None:
        self.repository.save_checkpoint(checkpoint)

    def upsert_candles(self, candles: Iterable[PersistedCandle]) -> int:
        candle_list = list(candles)
        self.fetched_closed_candles += len(candle_list)
        for candle in candle_list:
            open_time = _as_utc(candle.open_time)
            existing = self.existing_by_open_time.get(open_time)
            if existing is not None or open_time in self.seen_new_open_times:
                self.duplicate_candles += 1
                if existing is not None and not _persisted_candle_matches_existing(candle, existing):
                    self.conflicting_duplicate_candles += 1
                continue
            self.estimated_new_candles += 1
            self.seen_new_open_times.add(open_time)

        upserted = self.repository.upsert_candles(candle_list)
        self.repository_upserted_candles += int(upserted)
        return upserted


def repair_btcusdt_1m_gaps(
    repository: CandleRepository,
    *,
    symbol: str = DEFAULT_SYMBOL,
    interval: str = DEFAULT_INTERVAL,
    source: str = DEFAULT_SOURCE,
    target_start: datetime = TASK_TARGET_START,
    target_end: datetime = TASK_TARGET_END,
    base_url: str = DEFAULT_MARKET_DATA_BASE_URL,
    timeout: float = 10.0,
    max_retries: int = 3,
    limit: int = BINANCE_MAX_KLINE_LIMIT,
    report_path: Path | str = DEFAULT_REPORT_PATH,
    initialize_schema: bool = True,
    dry_run: bool = False,
    http_get: HttpGet | None = None,
    sleep: Sleep | None = None,
) -> RepairRunResult:
    """Audit, repair, validate, and report BTCUSDT 1m candle coverage."""

    normalized_target = TimeRange(_as_utc(target_start), _as_utc(target_end))
    normalized_symbol = symbol.strip().upper()
    if interval != "1m":
        raise ValueError("Task 286 repairs only 1m candles")
    if initialize_schema:
        repository.initialize_schema()

    before = audit_repository_coverage(
        repository,
        source=source,
        symbol=normalized_symbol,
        interval=interval,
        target_range=normalized_target,
    )
    existing_by_open_time = _existing_candles_by_open_time(
        repository,
        source=source,
        symbol=normalized_symbol,
        interval=interval,
        target_range=normalized_target,
    )
    repair_ranges = before.missing_ranges
    repair_results: list[RepairRangeResult] = []
    if not dry_run:
        for missing_range in repair_ranges:
            counting_repository = CountingCandleRepository(
                repository,
                existing_by_open_time=existing_by_open_time,
            )
            backfiller_kwargs: dict[str, Any] = {
                "base_url": base_url,
                "timeout": timeout,
                "max_retries": max_retries,
            }
            if http_get is not None:
                backfiller_kwargs["http_get"] = http_get
            if sleep is not None:
                backfiller_kwargs["sleep"] = sleep
            backfiller = BinanceHistoricalBackfiller(
                counting_repository,
                **backfiller_kwargs,
            )
            result = backfiller.run(
                symbol=normalized_symbol,
                interval=interval,
                start_time=missing_range.start,
                end_time=missing_range.end,
                limit=limit,
            )
            repair_results.append(
                RepairRangeResult(
                    requested_range=missing_range,
                    planned_pages=len(plan_binance_request_ranges(missing_range, limit=limit)),
                    expected_missing_candles=missing_range.candle_count,
                    fetched_closed_candles=counting_repository.fetched_closed_candles,
                    estimated_new_candles=counting_repository.estimated_new_candles,
                    duplicate_candles=counting_repository.duplicate_candles,
                    conflicting_duplicate_candles=(
                        counting_repository.conflicting_duplicate_candles
                    ),
                    repository_upserted_candles=counting_repository.repository_upserted_candles,
                    pages_fetched=result.pages_fetched,
                )
            )
            for open_time in counting_repository.seen_new_open_times:
                existing_by_open_time[open_time] = {"timestamp": open_time}

    after = audit_repository_coverage(
        repository,
        source=source,
        symbol=normalized_symbol,
        interval=interval,
        target_range=normalized_target,
    )
    status = "DRY_RUN" if dry_run else _status_from_after_audit(after)
    output_path = Path(report_path)
    run_result = RepairRunResult(
        task_id=TASK_ID,
        status=status,
        symbol=normalized_symbol,
        interval=interval,
        source=source,
        target_range=normalized_target,
        before=before,
        repair_results=tuple(repair_results),
        after=after,
        report_path=output_path,
        dry_run=dry_run,
    )
    write_markdown_report(run_result, output_path)
    return run_result


def audit_repository_coverage(
    repository: CandleRepository,
    *,
    source: str,
    symbol: str,
    interval: str,
    target_range: TimeRange,
) -> CoverageAudit:
    rows = repository.load_standard_candles(
        source=source,
        symbol=symbol,
        interval=interval,
        start_time=target_range.start,
        end_time=target_range.end,
    )
    frame = pd.DataFrame(rows, columns=("timestamp", "open", "high", "low", "close", "volume"))
    return audit_candle_frame(
        frame,
        symbol=symbol,
        interval=interval,
        target_range=target_range,
    )


def audit_candle_frame(
    candles: pd.DataFrame,
    *,
    symbol: str,
    interval: str,
    target_range: TimeRange,
) -> CoverageAudit:
    expected_candle_count = target_range.candle_count
    if candles.empty:
        return CoverageAudit(
            symbol=symbol,
            interval=interval,
            start_time=target_range.start,
            end_time=target_range.end,
            expected_candle_count=expected_candle_count,
            actual_candle_count=0,
            min_open_time=None,
            max_open_time=None,
            duplicate_count=0,
            duplicate_timestamps=(),
            missing_ranges=(target_range,),
            validation_errors=(),
        )

    frame = candles.copy()
    validation_errors: list[str] = []
    try:
        validate_standard_candles(
            frame,
            CandleValidationConfig(
                interval=interval,
                enforce_continuity=False,
                allow_empty=True,
                context=f"{TASK_ID} {symbol} {interval} candle audit",
            ),
        )
    except ValueError as error:
        validation_errors.append(str(error))

    timestamps = pd.to_datetime(frame["timestamp"], errors="raise", utc=True)
    frame["timestamp"] = timestamps
    frame = frame[
        (frame["timestamp"] >= pd.Timestamp(target_range.start))
        & (frame["timestamp"] <= pd.Timestamp(target_range.end))
    ].sort_values("timestamp", kind="mergesort")
    duplicate_series = frame["timestamp"][frame["timestamp"].duplicated(keep=False)]
    duplicate_timestamps = tuple(
        _as_utc(ts.to_pydatetime()) for ts in duplicate_series.drop_duplicates().tolist()
    )
    unique_timestamps = tuple(
        _as_utc(ts.to_pydatetime())
        for ts in frame["timestamp"].drop_duplicates().sort_values().tolist()
    )
    missing_ranges = find_missing_ranges(
        unique_timestamps,
        target_range=target_range,
    )
    min_open_time = unique_timestamps[0] if unique_timestamps else None
    max_open_time = unique_timestamps[-1] if unique_timestamps else None
    return CoverageAudit(
        symbol=symbol,
        interval=interval,
        start_time=target_range.start,
        end_time=target_range.end,
        expected_candle_count=expected_candle_count,
        actual_candle_count=len(unique_timestamps),
        min_open_time=min_open_time,
        max_open_time=max_open_time,
        duplicate_count=int(len(duplicate_series)),
        duplicate_timestamps=duplicate_timestamps,
        missing_ranges=missing_ranges,
        validation_errors=tuple(validation_errors),
    )


def find_missing_ranges(
    timestamps: Sequence[datetime],
    *,
    target_range: TimeRange,
    interval_delta: timedelta = ONE_MINUTE,
) -> tuple[TimeRange, ...]:
    """Return inclusive missing open-time ranges inside a target range."""

    expected = target_range.start
    missing: list[TimeRange] = []
    normalized = sorted(
        {
            _as_utc(timestamp)
            for timestamp in timestamps
            if target_range.start <= _as_utc(timestamp) <= target_range.end
        }
    )
    for timestamp in normalized:
        if timestamp < expected:
            continue
        if timestamp > expected:
            missing.append(TimeRange(expected, timestamp - interval_delta))
        expected = timestamp + interval_delta
    if expected <= target_range.end:
        missing.append(TimeRange(expected, target_range.end))
    return tuple(missing)


def plan_binance_request_ranges(
    missing_range: TimeRange,
    *,
    limit: int = BINANCE_MAX_KLINE_LIMIT,
    interval_delta: timedelta = ONE_MINUTE,
) -> tuple[TimeRange, ...]:
    """Split an inclusive open-time range into Binance limit-sized requests."""

    if limit <= 0:
        raise ValueError("limit must be positive")
    ranges: list[TimeRange] = []
    current = missing_range.start
    while current <= missing_range.end:
        page_end = min(missing_range.end, current + (limit - 1) * interval_delta)
        ranges.append(TimeRange(current, page_end))
        current = page_end + interval_delta
    return tuple(ranges)


def write_markdown_report(result: RepairRunResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(result), encoding="utf-8")


def render_markdown_report(result: RepairRunResult) -> str:
    repair_table = _render_repair_table(result.repair_results)
    before = result.before
    after = result.after
    return "\n".join(
        [
            "# Task 286 BTCUSDT 1m Data Backfill And Gap Repair",
            "",
            f"- Status: `{result.status}`",
            f"- Symbol: `{result.symbol}`",
            f"- Interval: `{result.interval}`",
            f"- Source: `{result.source}`",
            f"- Target range: `{_iso_z(result.target_range.start)}` to `{_iso_z(result.target_range.end)}`",
            f"- Dry run: `{str(result.dry_run).lower()}`",
            "",
            "## Before Audit",
            "",
            _render_audit_summary(before),
            "",
            "## Repair Results",
            "",
            repair_table,
            "",
            "## After Audit",
            "",
            _render_audit_summary(after),
            "",
            "## Safety Boundary",
            "",
            "- Used Binance public market-data kline backfill path only.",
            "- No API keys, signed requests, account endpoints, order endpoints, strategy tuning, live trading, futures, or leverage were used.",
            "",
            "## Next Task",
            "",
            "- Create or execute a locked OOS/WFO validation task on the repaired complete BTCUSDT 1m range before any strategy promotion claim.",
            "",
        ]
    )


def _render_audit_summary(audit: CoverageAudit) -> str:
    lines = [
        f"- Expected candles: `{audit.expected_candle_count}`",
        f"- Actual unique candles: `{audit.actual_candle_count}`",
        f"- Min open time: `{_optional_iso_z(audit.min_open_time)}`",
        f"- Max open time: `{_optional_iso_z(audit.max_open_time)}`",
        f"- Duplicate row count: `{audit.duplicate_count}`",
        f"- Missing range count: `{len(audit.missing_ranges)}`",
        f"- Missing candle count: `{sum(item.candle_count for item in audit.missing_ranges)}`",
    ]
    if audit.missing_ranges:
        lines.append("- Missing ranges:")
        for item in audit.missing_ranges:
            lines.append(
                f"  - `{_iso_z(item.start)}` to `{_iso_z(item.end)}` (`{item.candle_count}` candles)"
            )
    if audit.validation_errors:
        lines.append("- Validation errors:")
        for error in audit.validation_errors:
            lines.append(f"  - `{error}`")
    return "\n".join(lines)


def _render_repair_table(results: Sequence[RepairRangeResult]) -> str:
    if not results:
        return "- No missing ranges were repaired."
    lines = [
        "| Range | Planned pages | Expected missing | Fetched closed | Estimated new | Duplicates | Conflicts | Repository upserts | Pages fetched |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in results:
        lines.append(
            "| "
            f"`{_iso_z(item.requested_range.start)}` to `{_iso_z(item.requested_range.end)}` "
            f"| {item.planned_pages} "
            f"| {item.expected_missing_candles} "
            f"| {item.fetched_closed_candles} "
            f"| {item.estimated_new_candles} "
            f"| {item.duplicate_candles} "
            f"| {item.conflicting_duplicate_candles} "
            f"| {item.repository_upserted_candles} "
            f"| {item.pages_fetched} |"
        )
    return "\n".join(lines)


def _status_from_after_audit(audit: CoverageAudit) -> str:
    if audit.validation_errors or audit.duplicate_count or audit.missing_ranges:
        return "INCOMPLETE"
    if audit.actual_candle_count != audit.expected_candle_count:
        return "INCOMPLETE"
    return "COMPLETED"


def _existing_candles_by_open_time(
    repository: CandleRepository,
    *,
    source: str,
    symbol: str,
    interval: str,
    target_range: TimeRange,
) -> dict[datetime, dict[str, Any]]:
    rows = repository.load_standard_candles(
        source=source,
        symbol=symbol,
        interval=interval,
        start_time=target_range.start,
        end_time=target_range.end,
    )
    existing: dict[datetime, dict[str, Any]] = {}
    for row in rows:
        timestamp = _as_utc(pd.Timestamp(row["timestamp"]).to_pydatetime())
        existing[timestamp] = row
    return existing


def _persisted_candle_matches_existing(
    candle: PersistedCandle, existing: dict[str, Any]
) -> bool:
    fields = ("open", "high", "low", "close", "volume")
    return all(str(getattr(candle, field)) == str(existing[field]) for field in fields)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso_z(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _optional_iso_z(value: datetime | None) -> str:
    return "None" if value is None else _iso_z(value)


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return _as_utc(parsed)


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return _iso_z(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, TimeRange):
        return {"start": _iso_z(value.start), "end": _iso_z(value.end), "candles": value.candle_count}
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m quant_bitcoin.market_data.t286_btcusdt_1m_gap_repair",
        description="Task 286 BTCUSDT 1m public candle gap repair.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="PostgreSQL connection URL for candle persistence",
    )
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--interval", default=DEFAULT_INTERVAL)
    parser.add_argument(
        "--target-start",
        type=_parse_timestamp,
        default=TASK_TARGET_START,
        help="inclusive UTC open-time start for the coverage audit",
    )
    parser.add_argument(
        "--target-end",
        type=_parse_timestamp,
        default=TASK_TARGET_END,
        help="inclusive UTC open-time end for the coverage audit",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BINANCE_MARKET_DATA_BASE_URL", DEFAULT_MARKET_DATA_BASE_URL),
        help="Binance public market-data REST base URL",
    )
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--limit", type=int, default=BINANCE_MAX_KLINE_LIMIT)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--initialize-schema",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = PostgresCandleRepository(args.database_url)
    result = repair_btcusdt_1m_gaps(
        repository,
        symbol=args.symbol,
        interval=args.interval,
        target_start=args.target_start,
        target_end=args.target_end,
        base_url=args.base_url,
        timeout=args.timeout_seconds,
        max_retries=args.max_retries,
        limit=args.limit,
        report_path=args.report_path,
        initialize_schema=args.initialize_schema,
        dry_run=args.dry_run,
    )
    print(
        json.dumps(
            {
                "task_id": result.task_id,
                "status": result.status,
                "report_path": result.report_path,
                "before_missing_ranges": result.before.missing_ranges,
                "after_missing_ranges": result.after.missing_ranges,
                "repair_ranges": [item.requested_range for item in result.repair_results],
                "estimated_new_candles": sum(
                    item.estimated_new_candles for item in result.repair_results
                ),
                "fetched_closed_candles": sum(
                    item.fetched_closed_candles for item in result.repair_results
                ),
            },
            default=_json_default,
            sort_keys=True,
        )
    )
    return 0 if result.status in {"COMPLETED", "DRY_RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
