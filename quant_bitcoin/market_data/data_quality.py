"""Deterministic quality audit for standard candle data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable

import pandas as pd

REQUIRED_CANDLE_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


class CandleDataQualitySeverity(str, Enum):
    """Severity levels for candle data quality issues."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class CandleDataQualityIssue:
    """One detected candle data quality issue."""

    severity: CandleDataQualitySeverity
    code: str
    message: str
    row_indices: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class CandleDataQualityConfig:
    """Runtime configuration for candle data quality checks."""

    expected_interval: str = "1m"
    expected_start_time: datetime | str | None = None
    expected_end_time: datetime | str | None = None
    treat_zero_volume_as_error: bool = False
    allow_empty: bool = False


@dataclass(frozen=True)
class CandleDataQualityReport:
    """Summary and issue list from a candle data quality audit."""

    candle_count: int
    issue_count: int
    has_errors: bool
    has_warnings: bool
    first_timestamp: pd.Timestamp | None
    last_timestamp: pd.Timestamp | None
    duplicate_timestamp_count: int
    missing_interval_count: int
    zero_volume_count: int
    zero_volume_ratio: float
    issues: list[CandleDataQualityIssue] = field(default_factory=list)


def _to_dataframe(candles: Any) -> pd.DataFrame:
    if isinstance(candles, pd.DataFrame):
        return candles.copy(deep=True)
    if candles is None:
        return pd.DataFrame()
    return pd.DataFrame(list(candles))


def _parse_optional_timestamp(value: datetime | str | None, field_name: str, issues: list[CandleDataQualityIssue]) -> pd.Timestamp | None:
    if value is None:
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.ERROR,
                code="INVALID_EXPECTED_BOUNDARY",
                message=f"{field_name} could not be parsed as a timestamp.",
            )
        )
        return None
    return pd.Timestamp(parsed)


def audit_standard_candles(candles: Any, config: CandleDataQualityConfig | None = None) -> CandleDataQualityReport:
    """Audit standard candle rows and return a deterministic quality report."""

    cfg = config or CandleDataQualityConfig()
    issues: list[CandleDataQualityIssue] = []
    frame = _to_dataframe(candles)

    if frame.empty:
        if cfg.allow_empty:
            issues.append(
                CandleDataQualityIssue(
                    severity=CandleDataQualitySeverity.INFO,
                    code="EMPTY_INPUT",
                    message="No candles provided; empty input allowed by configuration.",
                )
            )
        else:
            issues.append(
                CandleDataQualityIssue(
                    severity=CandleDataQualitySeverity.ERROR,
                    code="EMPTY_INPUT",
                    message="No candles provided.",
                )
            )
        return CandleDataQualityReport(
            candle_count=0,
            issue_count=len(issues),
            has_errors=any(issue.severity == CandleDataQualitySeverity.ERROR for issue in issues),
            has_warnings=any(issue.severity == CandleDataQualitySeverity.WARNING for issue in issues),
            first_timestamp=None,
            last_timestamp=None,
            duplicate_timestamp_count=0,
            missing_interval_count=0,
            zero_volume_count=0,
            zero_volume_ratio=0.0,
            issues=issues,
        )

    missing_columns = [column for column in REQUIRED_CANDLE_COLUMNS if column not in frame.columns]
    if missing_columns:
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.ERROR,
                code="MISSING_REQUIRED_COLUMNS",
                message=f"Missing required columns: {', '.join(missing_columns)}.",
            )
        )
        return CandleDataQualityReport(
            candle_count=len(frame),
            issue_count=len(issues),
            has_errors=True,
            has_warnings=False,
            first_timestamp=None,
            last_timestamp=None,
            duplicate_timestamp_count=0,
            missing_interval_count=0,
            zero_volume_count=0,
            zero_volume_ratio=0.0,
            issues=issues,
        )

    frame = frame.loc[:, list(REQUIRED_CANDLE_COLUMNS)].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    invalid_timestamp_rows = frame.index[frame["timestamp"].isna()].tolist()
    if invalid_timestamp_rows:
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.ERROR,
                code="INVALID_TIMESTAMP",
                message="One or more timestamps could not be parsed.",
                row_indices=invalid_timestamp_rows,
            )
        )

    expected_delta = pd.to_timedelta(cfg.expected_interval)

    for column in ("open", "high", "low", "close", "volume"):
        numeric_series = pd.to_numeric(frame[column], errors="coerce")
        invalid_rows = frame.index[numeric_series.isna()].tolist()
        frame[column] = numeric_series
        if invalid_rows:
            issues.append(
                CandleDataQualityIssue(
                    severity=CandleDataQualitySeverity.ERROR,
                    code="INVALID_NUMERIC_VALUE",
                    message=f"Column '{column}' contains non-numeric values.",
                    row_indices=invalid_rows,
                )
            )

    valid_ts_frame = frame[frame["timestamp"].notna()].copy()
    duplicate_timestamp_count = int(valid_ts_frame["timestamp"].duplicated(keep=False).sum())
    if duplicate_timestamp_count:
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.WARNING,
                code="DUPLICATE_TIMESTAMPS",
                message="Duplicate timestamps detected.",
            )
        )

    if not valid_ts_frame["timestamp"].is_monotonic_increasing:
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.ERROR,
                code="NON_ASCENDING_TIMESTAMPS",
                message="Timestamps are not sorted in ascending order.",
            )
        )

    missing_interval_count = 0
    if len(valid_ts_frame) > 1:
        deltas = valid_ts_frame["timestamp"].diff().iloc[1:]
        gaps = deltas[deltas > expected_delta]
        if not gaps.empty:
            missing_interval_count = int(((gaps / expected_delta) - 1).sum())
            issues.append(
                CandleDataQualityIssue(
                    severity=CandleDataQualitySeverity.WARNING,
                    code="MISSING_INTERVAL_GAPS",
                    message="Missing expected candle intervals detected.",
                )
            )

    expected_start = _parse_optional_timestamp(cfg.expected_start_time, "expected_start_time", issues)
    expected_end = _parse_optional_timestamp(cfg.expected_end_time, "expected_end_time", issues)

    first_timestamp = pd.Timestamp(valid_ts_frame["timestamp"].iloc[0]) if not valid_ts_frame.empty else None
    last_timestamp = pd.Timestamp(valid_ts_frame["timestamp"].iloc[-1]) if not valid_ts_frame.empty else None

    if expected_start is not None and first_timestamp is not None and first_timestamp > expected_start:
        missing_interval_count += int(((first_timestamp - expected_start) / expected_delta))
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.WARNING,
                code="EXPECTED_START_GAP",
                message="First candle is later than expected_start_time.",
            )
        )

    if expected_end is not None and last_timestamp is not None and last_timestamp < expected_end:
        missing_interval_count += int(((expected_end - last_timestamp) / expected_delta))
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.WARNING,
                code="EXPECTED_END_GAP",
                message="Last candle is earlier than expected_end_time.",
            )
        )

    invalid_high_low_rows = frame.index[(frame["high"] < frame["low"])].tolist()
    if invalid_high_low_rows:
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.ERROR,
                code="HIGH_BELOW_LOW",
                message="One or more candles have high < low.",
                row_indices=invalid_high_low_rows,
            )
        )

    invalid_open_close_rows = frame.index[
        (frame["open"] < frame["low"]) | (frame["open"] > frame["high"]) | (frame["close"] < frame["low"]) | (frame["close"] > frame["high"])
    ].tolist()
    if invalid_open_close_rows:
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.ERROR,
                code="OPEN_CLOSE_OUTSIDE_RANGE",
                message="Open/close is outside candle high-low range.",
                row_indices=invalid_open_close_rows,
            )
        )

    negative_volume_rows = frame.index[frame["volume"] < 0].tolist()
    if negative_volume_rows:
        issues.append(
            CandleDataQualityIssue(
                severity=CandleDataQualitySeverity.ERROR,
                code="NEGATIVE_VOLUME",
                message="Negative volume detected.",
                row_indices=negative_volume_rows,
            )
        )

    zero_volume_count = int((frame["volume"] == 0).sum())
    zero_volume_ratio = float(zero_volume_count / len(frame)) if len(frame) else 0.0
    if zero_volume_count:
        issues.append(
            CandleDataQualityIssue(
                severity=(CandleDataQualitySeverity.ERROR if cfg.treat_zero_volume_as_error else CandleDataQualitySeverity.WARNING),
                code="ZERO_VOLUME",
                message="Zero-volume candles detected.",
            )
        )

    has_errors = any(issue.severity == CandleDataQualitySeverity.ERROR for issue in issues)
    has_warnings = any(issue.severity == CandleDataQualitySeverity.WARNING for issue in issues)

    return CandleDataQualityReport(
        candle_count=len(frame),
        issue_count=len(issues),
        has_errors=has_errors,
        has_warnings=has_warnings,
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
        duplicate_timestamp_count=duplicate_timestamp_count,
        missing_interval_count=missing_interval_count,
        zero_volume_count=zero_volume_count,
        zero_volume_ratio=zero_volume_ratio,
        issues=issues,
    )
