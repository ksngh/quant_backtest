"""Strict validation for standard candle data used by backtests."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import pandas as pd

STANDARD_CANDLE_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
)

NUMERIC_CANDLE_COLUMNS: tuple[str, ...] = (
    "open",
    "high",
    "low",
    "close",
    "volume",
)

PRICE_CANDLE_COLUMNS: tuple[str, ...] = ("open", "high", "low", "close")

SUPPORTED_INTERVAL_DELTAS: dict[str, pd.Timedelta] = {
    "1m": pd.Timedelta(minutes=1),
    "3m": pd.Timedelta(minutes=3),
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "30m": pd.Timedelta(minutes=30),
    "1h": pd.Timedelta(hours=1),
    "4h": pd.Timedelta(hours=4),
    "1d": pd.Timedelta(days=1),
}


@dataclass(frozen=True)
class CandleValidationConfig:
    """Configuration for strict standard candle validation."""

    interval: str | None = None
    enforce_continuity: bool = False
    allow_empty: bool = True
    context: str = "Candle data"


def validate_standard_candles(
    candles: pd.DataFrame,
    config: CandleValidationConfig | None = None,
) -> None:
    """Raise ``ValueError`` if standard candle rows violate backtest invariants.

    The validator inspects a defensive copy of the relevant columns and never
    mutates caller-owned data.
    """

    cfg = config or CandleValidationConfig()
    if not isinstance(candles, pd.DataFrame):
        raise ValueError(f"{cfg.context} must be a pandas DataFrame")

    missing = [column for column in STANDARD_CANDLE_COLUMNS if column not in candles.columns]
    if missing:
        raise ValueError(f"{cfg.context} is missing required columns: {', '.join(missing)}")
    if candles.empty:
        if cfg.allow_empty:
            return
        raise ValueError(f"{cfg.context} must not be empty")

    frame = candles.loc[:, STANDARD_CANDLE_COLUMNS].copy()
    timestamps = _parse_timestamps(frame["timestamp"], cfg.context)
    frame["timestamp"] = timestamps

    duplicate_mask = timestamps.duplicated(keep=False)
    if bool(duplicate_mask.any()):
        duplicate_ts = timestamps[duplicate_mask].iloc[0]
        raise ValueError(f"{cfg.context} contains duplicate timestamp: {_format_timestamp(duplicate_ts)}")

    if not timestamps.is_monotonic_increasing:
        raise ValueError(f"{cfg.context} must be sorted ascending by timestamp")

    for column in NUMERIC_CANDLE_COLUMNS:
        numeric = _parse_numeric(frame[column], column, cfg.context)
        invalid_rows = [idx for idx, value in numeric.items() if not isfinite(float(value))]
        if invalid_rows:
            raise ValueError(f"{cfg.context} contains non-finite values in column: {column}")
        frame[column] = numeric

    _validate_prices(frame, cfg.context)
    _validate_volume(frame, cfg.context)
    if cfg.enforce_continuity:
        _validate_continuity(timestamps, cfg.interval, cfg.context)


def normalize_timestamp_series(
    values: pd.Series,
    *,
    context: str = "Candle data",
) -> pd.Series:
    """Parse timestamps with deterministic UTC normalization."""

    return _parse_timestamps(values, context)


def _parse_timestamps(values: pd.Series, context: str) -> pd.Series:
    try:
        parsed = pd.to_datetime(values, errors="raise", utc=True, format="mixed")
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context} contains invalid timestamp values") from error
    if parsed.isna().any():
        raise ValueError(f"{context} contains invalid timestamp values")
    return pd.Series(parsed, index=values.index)


def _parse_numeric(values: pd.Series, column: str, context: str) -> pd.Series:
    try:
        numeric = pd.to_numeric(values, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context} contains non-numeric values in column: {column}") from error
    return numeric


def _validate_prices(frame: pd.DataFrame, context: str) -> None:
    for column in PRICE_CANDLE_COLUMNS:
        invalid = frame.index[frame[column] <= 0]
        if len(invalid):
            raise ValueError(
                f"{context} contains non-positive price in column: {column} at timestamp {_row_timestamp(frame, invalid[0])}"
            )

    high_below_low = frame.index[frame["high"] < frame["low"]]
    if len(high_below_low):
        raise ValueError(f"{context} has high < low at timestamp {_row_timestamp(frame, high_below_low[0])}")

    high_below_open_close = frame.index[
        (frame["high"] < frame[["open", "close"]].max(axis=1))
    ]
    if len(high_below_open_close):
        raise ValueError(
            f"{context} has high below open/close at timestamp {_row_timestamp(frame, high_below_open_close[0])}"
        )

    low_above_open_close = frame.index[
        (frame["low"] > frame[["open", "close"]].min(axis=1))
    ]
    if len(low_above_open_close):
        raise ValueError(
            f"{context} has low above open/close at timestamp {_row_timestamp(frame, low_above_open_close[0])}"
        )


def _validate_volume(frame: pd.DataFrame, context: str) -> None:
    invalid = frame.index[frame["volume"] < 0]
    if len(invalid):
        raise ValueError(f"{context} contains negative volume at timestamp {_row_timestamp(frame, invalid[0])}")


def _validate_continuity(timestamps: pd.Series, interval: str | None, context: str) -> None:
    if interval is None:
        raise ValueError(f"{context} continuity validation requires an interval")
    expected_delta = SUPPORTED_INTERVAL_DELTAS.get(str(interval))
    if expected_delta is None:
        raise ValueError(f"{context} continuity validation does not support interval: {interval}")
    if len(timestamps) <= 1:
        return

    deltas = timestamps.diff().iloc[1:]
    gap_mask = deltas != expected_delta
    if bool(gap_mask.any()):
        gap_index = gap_mask[gap_mask].index[0]
        previous_ts = timestamps.loc[timestamps.index[timestamps.index.get_loc(gap_index) - 1]]
        current_ts = timestamps.loc[gap_index]
        raise ValueError(
            f"{context} has interval gap for {interval}: expected {expected_delta} between "
            f"{_format_timestamp(previous_ts)} and {_format_timestamp(current_ts)}"
        )


def _row_timestamp(frame: pd.DataFrame, row_index: Any) -> str:
    return _format_timestamp(frame.loc[row_index, "timestamp"])


def _format_timestamp(value: Any) -> str:
    return str(pd.Timestamp(value))
