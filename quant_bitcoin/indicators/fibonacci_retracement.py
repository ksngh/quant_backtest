"""Fibonacci retracement confluence helpers for completed-candle research."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FibonacciDirection(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class FibonacciOverlapMode(Enum):
    MIDPOINT = "MIDPOINT"
    ANY_ZONE_OVERLAP = "ANY_ZONE_OVERLAP"
    FULL_ZONE_CONTAINED = "FULL_ZONE_CONTAINED"


@dataclass(frozen=True)
class FibonacciRetracementConfig:
    min_level: float = 0.382
    max_level: float = 0.618
    tolerance_atr_multiplier: float = 0.0
    overlap_mode: FibonacciOverlapMode | str = FibonacciOverlapMode.MIDPOINT

    def __post_init__(self) -> None:
        if not 0 <= self.min_level <= 1:
            raise ValueError("min_level must be between 0 and 1")
        if not 0 <= self.max_level <= 1:
            raise ValueError("max_level must be between 0 and 1")
        if self.min_level > self.max_level:
            raise ValueError("min_level must be less than or equal to max_level")
        if self.tolerance_atr_multiplier < 0:
            raise ValueError("tolerance_atr_multiplier must be non-negative")
        _coerce_overlap_mode(self.overlap_mode)


def evaluate_fibonacci_retracement_confluence(
    *,
    direction: FibonacciDirection | str,
    anchor_low: float,
    anchor_high: float,
    zone_low: float,
    zone_high: float,
    atr: float | None = None,
    config: FibonacciRetracementConfig | None = None,
) -> dict[str, Any]:
    """Return direction-aware retracement confluence metadata."""

    cfg = config or FibonacciRetracementConfig()
    mode = _coerce_overlap_mode(cfg.overlap_mode)
    direction_value = _coerce_direction(direction).value
    low = float(anchor_low)
    high = float(anchor_high)
    zone_min = float(min(zone_low, zone_high))
    zone_max = float(max(zone_low, zone_high))
    if high <= low:
        return _invalid_result(direction_value, "INVALID_ANCHOR_RANGE", cfg, mode)
    if zone_max < zone_min:
        return _invalid_result(direction_value, "INVALID_ZONE_RANGE", cfg, mode)

    anchor_range = high - low
    if direction_value == FibonacciDirection.BULLISH.value:
        band_a = high - cfg.min_level * anchor_range
        band_b = high - cfg.max_level * anchor_range
        midpoint_level = (high - ((zone_min + zone_max) / 2.0)) / anchor_range
    else:
        band_a = low + cfg.min_level * anchor_range
        band_b = low + cfg.max_level * anchor_range
        midpoint_level = (((zone_min + zone_max) / 2.0) - low) / anchor_range

    tolerance = _tolerance(atr, cfg)
    band_low = min(band_a, band_b) - tolerance
    band_high = max(band_a, band_b) + tolerance
    overlaps = _overlaps(zone_min, zone_max, band_low, band_high, mode)
    reason = "FIBONACCI_CONFLUENCE_PASS" if overlaps else "FIBONACCI_CONFLUENCE_FAIL"
    return {
        "schema_version": "fibonacci_retracement_confluence_v1",
        "feature_available": True,
        "source": "observed_displacement_candle_range",
        "direction": direction_value,
        "anchor_low": low,
        "anchor_high": high,
        "anchor_range": anchor_range,
        "zone_low": zone_min,
        "zone_high": zone_max,
        "zone_mid": (zone_min + zone_max) / 2.0,
        "retracement_level_at_zone_mid": midpoint_level,
        "band_min_level": cfg.min_level,
        "band_max_level": cfg.max_level,
        "band_low": band_low,
        "band_high": band_high,
        "tolerance": tolerance,
        "overlap_mode": mode.value,
        "confluence_pass": bool(overlaps),
        "reason": reason,
        "score": 1.0 if overlaps else 0.0,
        "limitations": [
            "Fibonacci confluence is deterministic research metadata, not an optimized profitability claim.",
            "Displacement candle anchors use only candles available at FVG confirmation time.",
        ],
    }


def _invalid_result(
    direction: str,
    reason: str,
    config: FibonacciRetracementConfig,
    mode: FibonacciOverlapMode,
) -> dict[str, Any]:
    return {
        "schema_version": "fibonacci_retracement_confluence_v1",
        "feature_available": False,
        "source": "missing_context",
        "direction": direction,
        "confluence_pass": False,
        "reason": reason,
        "band_min_level": config.min_level,
        "band_max_level": config.max_level,
        "overlap_mode": mode.value,
        "score": 0.0,
        "limitations": [
            "Fibonacci confluence is unavailable because a valid no-lookahead anchor was not supplied."
        ],
    }


def _overlaps(
    zone_low: float,
    zone_high: float,
    band_low: float,
    band_high: float,
    mode: FibonacciOverlapMode,
) -> bool:
    if mode == FibonacciOverlapMode.MIDPOINT:
        midpoint = (zone_low + zone_high) / 2.0
        return band_low <= midpoint <= band_high
    if mode == FibonacciOverlapMode.ANY_ZONE_OVERLAP:
        return max(zone_low, band_low) <= min(zone_high, band_high)
    return zone_low >= band_low and zone_high <= band_high


def _tolerance(atr: float | None, config: FibonacciRetracementConfig) -> float:
    if atr is None:
        return 0.0
    return max(0.0, float(atr) * config.tolerance_atr_multiplier)


def _coerce_direction(direction: FibonacciDirection | str) -> FibonacciDirection:
    if isinstance(direction, FibonacciDirection):
        return direction
    return FibonacciDirection(str(direction).upper())


def _coerce_overlap_mode(mode: FibonacciOverlapMode | str) -> FibonacciOverlapMode:
    if isinstance(mode, FibonacciOverlapMode):
        return mode
    return FibonacciOverlapMode(str(mode).upper())
