"""Average True Range (ATR) indicator calculation.

This module consumes already-provided candle data and emits deterministic ATR
values. It does not fetch market data, read secrets, call exchange APIs, place
orders, or make trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

REQUIRED_ATR_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "high",
    "low",
    "close",
)

ATR_OUTPUT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "period",
    "true_range",
    "atr",
    "close",
    "normalized_atr",
    "normalized_atr_percent",
    "smoothing_method",
    "volatility_status",
    "is_valid",
)


class AtrSmoothingMethod(Enum):
    """Supported ATR smoothing methods."""

    SMA = "SMA"
    EMA = "EMA"
    RMA = "RMA"


class VolatilityStatus(Enum):
    """Normalized ATR volatility classifications."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class AtrConfig:
    """Configuration for deterministic ATR calculation."""

    period: int = 14
    smoothing_method: AtrSmoothingMethod | str = AtrSmoothingMethod.RMA
    require_full_window: bool = True
    reject_missing_price: bool = True
    low_volatility_threshold_percent: float = 1.0
    high_volatility_threshold_percent: float = 4.0

    def __post_init__(self) -> None:
        if self.period < 1:
            raise ValueError("period must be at least 1")
        if self.low_volatility_threshold_percent < 0:
            raise ValueError("low_volatility_threshold_percent must be non-negative")
        if self.high_volatility_threshold_percent < 0:
            raise ValueError("high_volatility_threshold_percent must be non-negative")
        if (
            self.low_volatility_threshold_percent
            > self.high_volatility_threshold_percent
        ):
            raise ValueError(
                "low_volatility_threshold_percent must be less than or equal to "
                "high_volatility_threshold_percent"
            )
        _coerce_smoothing_method(self.smoothing_method)


def calculate_atr(candles: pd.DataFrame, config: AtrConfig | None = None) -> pd.DataFrame:
    """Return ATR rows for already-provided OHLC candle data.

    The returned frame has one row per input candle and includes true range, ATR,
    normalized ATR, volatility status, and validity. With the default
    ``require_full_window`` setting, rows before the configured warm-up period
    are returned as invalid ATR rows with ``volatility_status`` set to
    ``UNKNOWN``.

    Args:
        candles: Candle data containing symbol, timestamp, high, low, and close
            columns.
        config: ATR calculation configuration. Defaults to ``AtrConfig()``.

    Raises:
        ValueError: If required columns are missing, numeric values are
            non-numeric, or configuration values are invalid.
    """

    atr_config = config or AtrConfig()
    _validate_candles(candles)

    if candles.empty:
        return _empty_atr_frame()

    high = pd.to_numeric(candles["high"], errors="raise")
    low = pd.to_numeric(candles["low"], errors="raise")
    close = pd.to_numeric(candles["close"], errors="raise")

    true_ranges, true_range_validity = _calculate_true_ranges(high, low, close)
    atr_values = _calculate_atr_values(
        true_ranges,
        atr_config.period,
        _coerce_smoothing_method(atr_config.smoothing_method),
    )

    rows: list[dict[str, Any]] = []
    smoothing_method = _coerce_smoothing_method(atr_config.smoothing_method).value

    for index, candle in candles.iterrows():
        current_close = _optional_float(close.loc[index])
        true_range = true_ranges[len(rows)]
        atr = atr_values[len(rows)]
        has_full_window = len(rows) + 1 >= atr_config.period
        prices_are_valid = true_range_validity[len(rows)] and current_close is not None
        atr_is_ready = atr is not None
        is_valid = prices_are_valid and atr_is_ready

        if atr_config.require_full_window and not has_full_window:
            is_valid = False

        normalized_atr = None
        normalized_atr_percent = None
        if atr is not None and current_close is not None and current_close > 0:
            normalized_atr = atr / current_close
            normalized_atr_percent = normalized_atr * 100

        volatility_status = classify_volatility(
            normalized_atr_percent if is_valid else None,
            atr_config,
        )

        rows.append(
            {
                "symbol": candle["symbol"],
                "timestamp": candle["timestamp"],
                "period": atr_config.period,
                "true_range": true_range,
                "atr": atr if is_valid else None,
                "close": current_close,
                "normalized_atr": normalized_atr if is_valid else None,
                "normalized_atr_percent": (
                    normalized_atr_percent if is_valid else None
                ),
                "smoothing_method": smoothing_method,
                "volatility_status": volatility_status,
                "is_valid": bool(is_valid),
            }
        )

    return pd.DataFrame(rows, columns=ATR_OUTPUT_COLUMNS)


def calculate_true_range(
    high: float | int | None,
    low: float | int | None,
    previous_close: float | int | None,
) -> float | None:
    """Calculate true range for one candle and its previous close."""

    current_high = _optional_float(high)
    current_low = _optional_float(low)
    previous_close_value = _optional_float(previous_close)

    if current_high is None or current_low is None:
        return None
    if current_high < current_low:
        return None
    if previous_close_value is None:
        return current_high - current_low

    return max(
        current_high - current_low,
        abs(current_high - previous_close_value),
        abs(current_low - previous_close_value),
    )


def classify_volatility(
    normalized_atr_percent: float | None,
    config: AtrConfig | None = None,
) -> str:
    """Classify normalized ATR percentage into LOW, NORMAL, HIGH, or UNKNOWN."""

    atr_config = config or AtrConfig()
    if normalized_atr_percent is None:
        return VolatilityStatus.UNKNOWN.value
    if normalized_atr_percent >= atr_config.high_volatility_threshold_percent:
        return VolatilityStatus.HIGH.value
    if normalized_atr_percent <= atr_config.low_volatility_threshold_percent:
        return VolatilityStatus.LOW.value
    return VolatilityStatus.NORMAL.value


def calculate_atr_snapshot(
    candles: pd.DataFrame,
    config: AtrConfig | None = None,
    *,
    include_timing_metadata: bool = False,
) -> dict[str, Any]:
    """Return the latest ATR output row as a dictionary."""

    atr_config = config or AtrConfig()
    atr_rows = calculate_atr(candles, config)
    if atr_rows.empty:
        snapshot = {column: None for column in ATR_OUTPUT_COLUMNS}
    else:
        snapshot = atr_rows.iloc[-1].to_dict()
    if include_timing_metadata:
        snapshot["timing"] = atr_timing_metadata(atr_config)
    return snapshot


def atr_timing_metadata(config: AtrConfig | None = None) -> dict[str, Any]:
    """Return ATR timing semantics without changing the output frame schema."""

    atr_config = config or AtrConfig()
    smoothing_method = _coerce_smoothing_method(atr_config.smoothing_method).value
    return {
        "schema_version": "indicator_timing_metadata_v1",
        "indicator": "ATR",
        "period": int(atr_config.period),
        "smoothing_method": smoothing_method,
        "current_candle_included": True,
        "requires_closed_candle": True,
        "warmup_period": int(atr_config.period),
        "first_valid_index": int(atr_config.period - 1),
        "confirmation_delay": 0,
        "baseline_mode": "CURRENT_INCLUSIVE",
        "safe_usage": "after_close_completed_candle_signal",
    }


def _calculate_true_ranges(
    high: pd.Series, low: pd.Series, close: pd.Series
) -> tuple[list[float | None], list[bool]]:
    true_ranges: list[float | None] = []
    validity: list[bool] = []

    for position in range(len(high)):
        previous_close = close.iloc[position - 1] if position > 0 else None
        if position > 0 and _optional_float(previous_close) is None:
            true_ranges.append(None)
            validity.append(False)
            continue

        current_close = _optional_float(close.iloc[position])
        true_range = calculate_true_range(
            high.iloc[position],
            low.iloc[position],
            previous_close,
        )
        is_valid = true_range is not None and true_range >= 0 and current_close is not None
        true_ranges.append(true_range)
        validity.append(is_valid)

    return true_ranges, validity


def _calculate_atr_values(
    true_ranges: list[float | None],
    period: int,
    smoothing_method: AtrSmoothingMethod,
) -> list[float | None]:
    if smoothing_method == AtrSmoothingMethod.SMA:
        return _calculate_sma_atr(true_ranges, period)
    if smoothing_method == AtrSmoothingMethod.EMA:
        return _calculate_ema_atr(true_ranges, period)
    return _calculate_rma_atr(true_ranges, period)


def _calculate_sma_atr(
    true_ranges: list[float | None], period: int
) -> list[float | None]:
    atr_values: list[float | None] = [None] * len(true_ranges)
    for index in range(period - 1, len(true_ranges)):
        window = true_ranges[index - period + 1 : index + 1]
        if all(value is not None for value in window):
            atr_values[index] = sum(value for value in window if value is not None) / period
    return atr_values


def _calculate_ema_atr(
    true_ranges: list[float | None], period: int
) -> list[float | None]:
    atr_values: list[float | None] = [None] * len(true_ranges)
    multiplier = 2 / (period + 1)
    for index in range(period - 1, len(true_ranges)):
        current_true_range = true_ranges[index]
        if current_true_range is None:
            continue

        previous_atr = atr_values[index - 1] if index > 0 else None
        if previous_atr is None:
            window = true_ranges[index - period + 1 : index + 1]
            if all(value is not None for value in window):
                atr_values[index] = (
                    sum(value for value in window if value is not None) / period
                )
            continue

        atr_values[index] = current_true_range * multiplier + previous_atr * (
            1 - multiplier
        )
    return atr_values


def _calculate_rma_atr(
    true_ranges: list[float | None], period: int
) -> list[float | None]:
    atr_values: list[float | None] = [None] * len(true_ranges)
    for index in range(period - 1, len(true_ranges)):
        current_true_range = true_ranges[index]
        if current_true_range is None:
            continue

        previous_atr = atr_values[index - 1] if index > 0 else None
        if previous_atr is None:
            window = true_ranges[index - period + 1 : index + 1]
            if all(value is not None for value in window):
                atr_values[index] = (
                    sum(value for value in window if value is not None) / period
                )
            continue

        atr_values[index] = (previous_atr * (period - 1) + current_true_range) / period
    return atr_values


def _validate_candles(candles: pd.DataFrame) -> None:
    missing_columns = [
        column for column in REQUIRED_ATR_COLUMNS if column not in candles.columns
    ]
    if missing_columns:
        raise ValueError(f"missing required ATR columns: {', '.join(missing_columns)}")


def _empty_atr_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=ATR_OUTPUT_COLUMNS)


def _coerce_smoothing_method(
    smoothing_method: AtrSmoothingMethod | str,
) -> AtrSmoothingMethod:
    if isinstance(smoothing_method, AtrSmoothingMethod):
        return smoothing_method
    try:
        return AtrSmoothingMethod[str(smoothing_method).upper()]
    except KeyError as exc:
        raise ValueError("smoothing_method must be one of: SMA, EMA, RMA") from exc


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)
