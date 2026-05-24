"""Pivot high / pivot low indicator calculation.

This module consumes already-provided candle data and emits confirmed local
swing-point events. It does not fetch market data, read secrets, call exchange
APIs, place orders, or make trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

REQUIRED_PIVOT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "open",
    "high",
    "low",
    "close",
)

PIVOT_OUTPUT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "pivot_timestamp",
    "confirmed_timestamp",
    "pivot_index",
    "confirmed_index",
    "pivot_type",
    "price",
    "high_price",
    "low_price",
    "strength",
    "high_strength",
    "low_strength",
    "left_window",
    "right_window",
    "is_confirmed",
)


class PivotType(Enum):
    """Supported pivot classifications."""

    PIVOT_HIGH = "PIVOT_HIGH"
    PIVOT_LOW = "PIVOT_LOW"
    BOTH = "BOTH"
    NONE = "NONE"
    INVALID = "INVALID"
    UNCONFIRMED = "UNCONFIRMED"


@dataclass(frozen=True)
class PivotConfig:
    """Configuration for deterministic pivot detection."""

    left_window: int = 3
    right_window: int = 3
    allow_equal_high_low: bool = False
    minimum_distance_between_pivots: int = 3
    use_atr_filter: bool = False
    minimum_pivot_strength_atr: float = 0.5
    require_full_window: bool = True

    def __post_init__(self) -> None:
        if self.left_window < 1:
            raise ValueError("left_window must be at least 1")
        if self.right_window < 1:
            raise ValueError("right_window must be at least 1")
        if self.minimum_distance_between_pivots < 1:
            raise ValueError("minimum_distance_between_pivots must be at least 1")
        if self.minimum_pivot_strength_atr < 0:
            raise ValueError("minimum_pivot_strength_atr must be non-negative")


def detect_pivots(
    candles: pd.DataFrame, config: PivotConfig | None = None
) -> pd.DataFrame:
    """Return confirmed pivot events for standard OHLC candle data.

    The result contains one row per detected pivot event. Warm-up candles without
    enough left neighbors are omitted. With the default ``require_full_window``
    setting, cool-down candles without enough right neighbors are also omitted
    so returned pivot events are confirmed and safe for backtesting consumers.

    Args:
        candles: Candle data containing symbol, timestamp, open, high, low, and
            close columns. Optional ``atr`` is required only when the ATR filter
            is enabled.
        config: Pivot detection configuration. Defaults to ``PivotConfig()``.

    Raises:
        ValueError: If required columns are missing, numeric values are invalid,
            or ATR filtering is requested without valid ATR values.
    """

    pivot_config = config or PivotConfig()
    _validate_candles(candles, pivot_config)

    if candles.empty:
        return _empty_pivot_frame()

    high = pd.to_numeric(candles["high"], errors="raise")
    low = pd.to_numeric(candles["low"], errors="raise")
    atr = (
        pd.to_numeric(candles["atr"], errors="raise")
        if pivot_config.use_atr_filter
        else None
    )

    pivots: list[dict[str, Any]] = []
    candle_count = len(candles)

    for pivot_index in range(candle_count):
        if pivot_index < pivot_config.left_window:
            continue

        confirmed_index = pivot_index + pivot_config.right_window
        has_full_right_window = confirmed_index < candle_count
        if not has_full_right_window:
            if pivot_config.require_full_window:
                continue
            pivots.append(
                _unconfirmed_pivot(candles, pivot_config, pivot_index, candle_count)
            )
            continue

        left_slice = slice(pivot_index - pivot_config.left_window, pivot_index)
        right_slice = slice(pivot_index + 1, confirmed_index + 1)
        current_high = high.iloc[pivot_index]
        current_low = low.iloc[pivot_index]

        left_high = high.iloc[left_slice]
        right_high = high.iloc[right_slice]
        left_low = low.iloc[left_slice]
        right_low = low.iloc[right_slice]

        left_max_high = left_high.max()
        right_max_high = right_high.max()
        left_min_low = left_low.min()
        right_min_low = right_low.min()

        if pivot_config.allow_equal_high_low:
            is_pivot_high = current_high >= left_max_high and current_high >= right_max_high
            is_pivot_low = current_low <= left_min_low and current_low <= right_min_low
        else:
            is_pivot_high = current_high > left_max_high and current_high > right_max_high
            is_pivot_low = current_low < left_min_low and current_low < right_min_low

        high_strength = None
        low_strength = None

        if is_pivot_high:
            high_strength = float(current_high - max(left_max_high, right_max_high))
            if not _passes_atr_filter(high_strength, atr, pivot_config, pivot_index):
                is_pivot_high = False
                high_strength = None

        if is_pivot_low:
            low_strength = float(min(left_min_low, right_min_low) - current_low)
            if not _passes_atr_filter(low_strength, atr, pivot_config, pivot_index):
                is_pivot_low = False
                low_strength = None

        if not is_pivot_high and not is_pivot_low:
            continue

        pivots.append(
            _pivot_event(
                candles=candles,
                pivot_config=pivot_config,
                pivot_index=pivot_index,
                confirmed_index=confirmed_index,
                is_pivot_high=is_pivot_high,
                is_pivot_low=is_pivot_low,
                high_strength=high_strength,
                low_strength=low_strength,
            )
        )

    filtered = remove_close_duplicate_pivots(pivots, pivot_config)
    if not filtered:
        return _empty_pivot_frame()
    return pd.DataFrame(filtered, columns=PIVOT_OUTPUT_COLUMNS)


def pivot_timing_metadata(config: PivotConfig | None = None) -> dict[str, Any]:
    """Return Pivot indicator timing semantics without changing output columns."""

    pivot_config = config or PivotConfig()
    return {
        "schema_version": "indicator_timing_metadata_v1",
        "indicator": "PIVOT",
        "current_candle_included": False,
        "requires_closed_candle": True,
        "warmup_period": int(pivot_config.left_window + pivot_config.right_window + 1),
        "confirmation_delay": int(pivot_config.right_window),
        "baseline_mode": "CONFIRMED_AFTER_RIGHT_WINDOW",
        "use_atr_filter": bool(pivot_config.use_atr_filter),
        "minimum_pivot_strength_atr": float(pivot_config.minimum_pivot_strength_atr),
        "safe_usage": "confirmed_pivot_only_after_right_window_closes",
    }


def pivot_strength_diagnostics(
    pivots: pd.DataFrame | list[dict[str, Any]] | tuple[dict[str, Any], ...],
    config: PivotConfig | None = None,
    *,
    current_index: int | None = None,
    candle_count: int | None = None,
) -> dict[str, Any]:
    """Return pivot strength, density, and confirmation metadata."""

    pivot_config = config or PivotConfig()
    frame = pivots.copy(deep=True) if isinstance(pivots, pd.DataFrame) else pd.DataFrame(list(pivots))
    if frame.empty:
        strengths: list[float] = []
        confirmed_indices: list[int] = []
        confirmed_count = 0
    else:
        strengths = _numeric_column_values(frame, "strength")
        confirmed_count = (
            int(frame["is_confirmed"].fillna(False).astype(bool).sum())
            if "is_confirmed" in frame.columns
            else len(frame)
        )
        confirmed_indices = [
            int(value) for value in _numeric_column_values(frame, "confirmed_index")
        ]
    total_count = len(frame)
    max_confirmed_index = max(confirmed_indices) if confirmed_indices else None
    no_lookahead_confirmed = (
        True
        if current_index is None or max_confirmed_index is None
        else max_confirmed_index <= current_index
    )
    density = (
        None
        if not candle_count or candle_count <= 0
        else total_count / float(candle_count) * 100.0
    )
    return {
        "schema_version": "pivot_strength_diagnostics_v1",
        "left_window": int(pivot_config.left_window),
        "right_window": int(pivot_config.right_window),
        "confirmation_delay": int(pivot_config.right_window),
        "use_atr_filter": bool(pivot_config.use_atr_filter),
        "minimum_pivot_strength_atr": float(pivot_config.minimum_pivot_strength_atr),
        "pivot_count": total_count,
        "confirmed_pivot_count": confirmed_count,
        "pivot_density_per_100_candles": density,
        "average_strength": None if not strengths else sum(strengths) / len(strengths),
        "max_strength": None if not strengths else max(strengths),
        "min_strength": None if not strengths else min(strengths),
        "max_confirmed_index": max_confirmed_index,
        "current_index": current_index,
        "no_lookahead_confirmed": no_lookahead_confirmed,
        "higher_timeframe_context": {
            "enabled": False,
            "mode": "metadata_only_not_configured",
        },
    }


def _numeric_column_values(frame: pd.DataFrame, column: str) -> list[float]:
    if column not in frame.columns:
        return []
    return [
        float(value)
        for value in pd.to_numeric(frame[column], errors="coerce").dropna().tolist()
    ]


def remove_close_duplicate_pivots(
    pivots: list[dict[str, Any]], config: PivotConfig
) -> list[dict[str, Any]]:
    """Remove same-type pivots that occur closer than the configured distance."""

    filtered: list[dict[str, Any]] = []
    for pivot in pivots:
        if not filtered:
            filtered.append(pivot)
            continue

        previous = filtered[-1]
        same_type = previous["pivot_type"] == pivot["pivot_type"]
        too_close = (
            pivot["pivot_index"] - previous["pivot_index"]
            < config.minimum_distance_between_pivots
        )

        if same_type and too_close and pivot["pivot_type"] != PivotType.UNCONFIRMED.value:
            if _is_stronger_duplicate(pivot, previous):
                filtered[-1] = pivot
        else:
            filtered.append(pivot)

    return filtered


def _validate_candles(candles: pd.DataFrame, config: PivotConfig) -> None:
    missing_columns = [
        column for column in REQUIRED_PIVOT_COLUMNS if column not in candles.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Candle data is missing required columns: {missing}")

    if config.use_atr_filter and "atr" not in candles.columns:
        raise ValueError("Candle data is missing required ATR column: atr")

    for column in ("open", "high", "low", "close"):
        try:
            pd.to_numeric(candles[column], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError(f"Candle data contains non-numeric {column} values") from error

    if candles["high"].isna().any() or candles["low"].isna().any():
        raise ValueError("Candle data contains missing high or low values")

    if config.use_atr_filter:
        try:
            atr = pd.to_numeric(candles["atr"], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError("Candle data contains non-numeric ATR values") from error
        if atr.isna().any():
            raise ValueError("Candle data contains missing ATR values")


def _passes_atr_filter(
    strength: float,
    atr: pd.Series | None,
    config: PivotConfig,
    pivot_index: int,
) -> bool:
    if not config.use_atr_filter:
        return True
    if atr is None:
        return False
    required_strength = config.minimum_pivot_strength_atr * float(atr.iloc[pivot_index])
    return strength >= required_strength


def _pivot_event(
    candles: pd.DataFrame,
    pivot_config: PivotConfig,
    pivot_index: int,
    confirmed_index: int,
    is_pivot_high: bool,
    is_pivot_low: bool,
    high_strength: float | None,
    low_strength: float | None,
) -> dict[str, Any]:
    current = candles.iloc[pivot_index]
    confirmed = candles.iloc[confirmed_index]

    if is_pivot_high and is_pivot_low:
        pivot_type = PivotType.BOTH.value
    elif is_pivot_high:
        pivot_type = PivotType.PIVOT_HIGH.value
    else:
        pivot_type = PivotType.PIVOT_LOW.value

    event: dict[str, Any] = {
        "symbol": current["symbol"],
        "pivot_timestamp": current["timestamp"],
        "confirmed_timestamp": confirmed["timestamp"],
        "pivot_index": pivot_index,
        "confirmed_index": confirmed_index,
        "pivot_type": pivot_type,
        "price": pd.NA,
        "high_price": pd.NA,
        "low_price": pd.NA,
        "strength": pd.NA,
        "high_strength": pd.NA,
        "low_strength": pd.NA,
        "left_window": pivot_config.left_window,
        "right_window": pivot_config.right_window,
        "is_confirmed": True,
    }

    if pivot_type == PivotType.PIVOT_HIGH.value:
        event["price"] = float(current["high"])
        event["strength"] = high_strength
    elif pivot_type == PivotType.PIVOT_LOW.value:
        event["price"] = float(current["low"])
        event["strength"] = low_strength
    else:
        event["high_price"] = float(current["high"])
        event["low_price"] = float(current["low"])
        event["high_strength"] = high_strength
        event["low_strength"] = low_strength

    return event


def _unconfirmed_pivot(
    candles: pd.DataFrame,
    pivot_config: PivotConfig,
    pivot_index: int,
    candle_count: int,
) -> dict[str, Any]:
    current = candles.iloc[pivot_index]
    return {
        "symbol": current["symbol"],
        "pivot_timestamp": current["timestamp"],
        "confirmed_timestamp": pd.NA,
        "pivot_index": pivot_index,
        "confirmed_index": min(pivot_index + pivot_config.right_window, candle_count - 1),
        "pivot_type": PivotType.UNCONFIRMED.value,
        "price": pd.NA,
        "high_price": pd.NA,
        "low_price": pd.NA,
        "strength": pd.NA,
        "high_strength": pd.NA,
        "low_strength": pd.NA,
        "left_window": pivot_config.left_window,
        "right_window": pivot_config.right_window,
        "is_confirmed": False,
    }


def _is_stronger_duplicate(
    pivot: dict[str, Any], previous: dict[str, Any]
) -> bool:
    pivot_type = pivot["pivot_type"]
    if pivot_type == PivotType.PIVOT_HIGH.value:
        return float(pivot["price"]) > float(previous["price"])
    if pivot_type == PivotType.PIVOT_LOW.value:
        return float(pivot["price"]) < float(previous["price"])
    if pivot_type == PivotType.BOTH.value:
        pivot_strength = float(pivot["high_strength"]) + float(pivot["low_strength"])
        previous_strength = float(previous["high_strength"]) + float(
            previous["low_strength"]
        )
        return pivot_strength > previous_strength
    return False


def _empty_pivot_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=PIVOT_OUTPUT_COLUMNS)
