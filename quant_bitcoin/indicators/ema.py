"""EMA trend features for completed-candle research.

This module consumes already-provided candle rows and does not fetch market
data, read secrets, call exchange APIs, place orders, or make trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


EMA_OUTPUT_COLUMNS: tuple[str, ...] = (
    "symbol",
    "timestamp",
    "close",
    "fast_period",
    "slow_period",
    "ema_fast",
    "ema_slow",
    "ema_fast_slope",
    "ema_slow_slope",
    "close_vs_ema_slow",
    "fast_vs_slow",
    "is_valid",
    "reason",
)


@dataclass(frozen=True)
class EmaTrendConfig:
    """Configuration for deterministic EMA trend features."""

    fast_period: int = 9
    slow_period: int = 21
    slope_lookback: int = 3
    include_slow_slope: bool = True
    require_full_window: bool = True

    def __post_init__(self) -> None:
        if self.fast_period < 1:
            raise ValueError("fast_period must be at least 1")
        if self.slow_period < 1:
            raise ValueError("slow_period must be at least 1")
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be less than slow_period")
        if self.slope_lookback < 1:
            raise ValueError("slope_lookback must be at least 1")

    @property
    def warmup_period(self) -> int:
        return max(self.slow_period, self.slope_lookback + 1)


def calculate_ema_trend_features(
    candles: pd.DataFrame,
    config: EmaTrendConfig | None = None,
) -> pd.DataFrame:
    """Return EMA fast/slow and slope features for one completed timeframe."""

    cfg = config or EmaTrendConfig()
    _validate_ema_input(candles)
    if candles.empty:
        return pd.DataFrame(columns=EMA_OUTPUT_COLUMNS)

    frame = candles.copy().reset_index(drop=True)
    timestamps = pd.to_datetime(frame["timestamp"], errors="raise", utc=True, format="mixed")
    close = pd.to_numeric(frame["close"], errors="raise")
    ema_fast = close.ewm(span=cfg.fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=cfg.slow_period, adjust=False).mean()
    fast_slope = ema_fast - ema_fast.shift(cfg.slope_lookback)
    slow_slope = ema_slow - ema_slow.shift(cfg.slope_lookback)

    rows: list[dict[str, Any]] = []
    for index, row in frame.iterrows():
        has_warmup = index + 1 >= cfg.warmup_period
        slopes_ready = pd.notna(fast_slope.iloc[index]) and (
            not cfg.include_slow_slope or pd.notna(slow_slope.iloc[index])
        )
        is_valid = bool(slopes_ready and (has_warmup or not cfg.require_full_window))
        reason = None if is_valid else "WARMUP"
        current_close = float(close.iloc[index])
        rows.append(
            {
                "symbol": row["symbol"] if "symbol" in frame.columns else None,
                "timestamp": timestamps.iloc[index],
                "close": current_close,
                "fast_period": cfg.fast_period,
                "slow_period": cfg.slow_period,
                "ema_fast": float(ema_fast.iloc[index]),
                "ema_slow": float(ema_slow.iloc[index]),
                "ema_fast_slope": _optional_float(fast_slope.iloc[index]),
                "ema_slow_slope": _optional_float(slow_slope.iloc[index]),
                "close_vs_ema_slow": current_close - float(ema_slow.iloc[index]),
                "fast_vs_slow": float(ema_fast.iloc[index]) - float(ema_slow.iloc[index]),
                "is_valid": is_valid,
                "reason": reason,
            }
        )
    return pd.DataFrame(rows, columns=EMA_OUTPUT_COLUMNS)


def ema_timing_metadata(config: EmaTrendConfig | None = None) -> dict[str, Any]:
    """Return timing metadata for EMA trend features."""

    cfg = config or EmaTrendConfig()
    return {
        "schema_version": "indicator_timing_metadata_v1",
        "indicator": "ema_trend",
        "current_candle_included": True,
        "requires_closed_candle": True,
        "warmup_period": cfg.warmup_period,
        "confirmation_delay": 0,
        "baseline_mode": "current completed candle close is included in EMA updates",
        "safe_usage": "safe after the evaluated candle has closed; not an intrabar signal",
        "fast_period": cfg.fast_period,
        "slow_period": cfg.slow_period,
        "slope_lookback": cfg.slope_lookback,
    }


def _validate_ema_input(candles: pd.DataFrame) -> None:
    if not isinstance(candles, pd.DataFrame):
        raise ValueError("EMA candles must be a pandas DataFrame")
    missing = [column for column in ("timestamp", "close") if column not in candles.columns]
    if missing:
        raise ValueError(f"EMA candles missing required columns: {', '.join(missing)}")
    if candles.empty:
        return
    timestamps = pd.to_datetime(candles["timestamp"], errors="raise", utc=True, format="mixed")
    if timestamps.duplicated().any():
        raise ValueError("EMA candles contain duplicate timestamp")
    if not pd.Series(timestamps).is_monotonic_increasing:
        raise ValueError("EMA candles must be sorted ascending by timestamp")
    pd.to_numeric(candles["close"], errors="raise")


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)
