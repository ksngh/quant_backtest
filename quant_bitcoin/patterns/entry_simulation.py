"""Deterministic pattern entry simulation contract.

This module defines reusable pure helpers for simulating historical entry fills
from completed candle data. It does not fetch market data, call exchange APIs,
place orders, persist records, or mutate caller input data.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

import pandas as pd


class PatternEntryMode(Enum):
    """Supported historical entry simulation modes."""

    MARKET_ON_CONFIRMATION_CLOSE = "MARKET_ON_CONFIRMATION_CLOSE"
    MARKET_ON_NEXT_OPEN = "MARKET_ON_NEXT_OPEN"
    LIMIT_AT_ENTRY_REFERENCE = "LIMIT_AT_ENTRY_REFERENCE"
    LIMIT_AT_PATTERN_MIDPOINT = "LIMIT_AT_PATTERN_MIDPOINT"
    LIMIT_AT_PATTERN_BOUNDARY = "LIMIT_AT_PATTERN_BOUNDARY"
    LIMIT_AT_PATTERN_NEAR_BOUNDARY = "LIMIT_AT_PATTERN_NEAR_BOUNDARY"
    LIMIT_AT_PATTERN_FAR_BOUNDARY = "LIMIT_AT_PATTERN_FAR_BOUNDARY"
    LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT = "LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT"
    LIMIT_AT_TRENDLINE_RETEST = "LIMIT_AT_TRENDLINE_RETEST"
    LIMIT_AT_NECKLINE_RETEST = "LIMIT_AT_NECKLINE_RETEST"
    LIMIT_AT_CUSTOM_PRICE = "LIMIT_AT_CUSTOM_PRICE"


class PatternEntryStatus(Enum):
    """Deterministic entry simulation outcomes."""

    FILLED = "FILLED"
    NOT_FILLED = "NOT_FILLED"
    CANCELLED = "CANCELLED"
    INVALID = "INVALID"


class PatternEntryTrigger(Enum):
    """Supported historical limit-entry trigger requirements."""

    TOUCH = "TOUCH"
    TOUCH_AND_REACTION_CLOSE = "TOUCH_AND_REACTION_CLOSE"
    TOUCH_AND_RECLAIM_MIDPOINT = "TOUCH_AND_RECLAIM_MIDPOINT"


@dataclass(frozen=True)
class PatternEntryConfig:
    """Configuration for deterministic no-fill behavior."""

    max_wait_bars: int | None = None
    expire_status: PatternEntryStatus = PatternEntryStatus.NOT_FILLED
    entry_trigger: PatternEntryTrigger | str = PatternEntryTrigger.TOUCH

    def __post_init__(self) -> None:
        if self.max_wait_bars is not None and self.max_wait_bars < 1:
            raise ValueError("max_wait_bars must be at least 1 when supplied")
        if self.expire_status not in (PatternEntryStatus.NOT_FILLED, PatternEntryStatus.CANCELLED):
            raise ValueError("expire_status must be NOT_FILLED or CANCELLED")
        _coerce_trigger(self.entry_trigger)


@dataclass(frozen=True)
class PatternEntryPlan:
    mode: PatternEntryMode
    direction: str
    limit_price: float | None
    config: PatternEntryConfig
    event_id: str | None = None
    pattern_type: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class PatternEntrySimulationResult:
    status: PatternEntryStatus
    fill_price: float | None
    fill_timestamp: Any | None
    fill_candle_index: int | None
    bars_waited: int
    plan: PatternEntryPlan
    reason: str | None = None
    entry_trigger: str = PatternEntryTrigger.TOUCH.value
    touch_timestamp: Any | None = None
    touch_candle_index: int | None = None
    reaction_timestamp: Any | None = None
    reaction_candle_index: int | None = None


def fair_value_gap_retest_entry_preset(
    *,
    entry_trigger: PatternEntryTrigger | str = PatternEntryTrigger.TOUCH,
    max_wait_bars: int = 5,
    expire_status: PatternEntryStatus = PatternEntryStatus.NOT_FILLED,
) -> PatternEntryConfig:
    """Return the opt-in FVG retest preset entry configuration."""

    return PatternEntryConfig(
        max_wait_bars=max_wait_bars,
        expire_status=expire_status,
        entry_trigger=entry_trigger,
    )


def create_entry_plan_from_event(
    event: Any,
    mode: PatternEntryMode | str,
    direction: str,
    custom_price: float | None = None,
    max_wait_bars: int | None = None,
) -> PatternEntryPlan:
    """Create a reusable entry plan from a compatible pattern event."""

    entry_mode = _coerce_mode(mode)
    normalized_direction = _coerce_direction(direction)
    entry_config = PatternEntryConfig(max_wait_bars=max_wait_bars)
    event_id = _event_field(event, "event_id")
    pattern_type = _event_field(event, "pattern_type")

    try:
        if entry_mode == PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE:
            limit_price = None
        elif entry_mode == PatternEntryMode.MARKET_ON_NEXT_OPEN:
            limit_price = None
        elif entry_mode == PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE:
            limit_price = _required_numeric_field(event, "entry_reference")
        elif entry_mode == PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT:
            limit_price = _required_numeric_field(event, "zone_mid")
        elif entry_mode == PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY:
            limit_price = _boundary_price(event, normalized_direction, variant="far")
        elif entry_mode == PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY:
            limit_price = _boundary_price(event, normalized_direction, variant="near")
        elif entry_mode == PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY:
            limit_price = _boundary_price(event, normalized_direction, variant="far")
        elif entry_mode == PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT:
            limit_price = _order_block_618_price(event, normalized_direction)
        elif entry_mode == PatternEntryMode.LIMIT_AT_TRENDLINE_RETEST:
            limit_price = _required_numeric_field(event, "trendline_value")
        elif entry_mode == PatternEntryMode.LIMIT_AT_NECKLINE_RETEST:
            limit_price = _required_numeric_field(event, "neckline")
        else:
            if custom_price is None:
                raise ValueError("custom_price is required for LIMIT_AT_CUSTOM_PRICE mode")
            limit_price = _positive_float(custom_price, "custom_price")
    except ValueError as exc:
        return PatternEntryPlan(
            mode=entry_mode,
            direction=normalized_direction,
            limit_price=None,
            config=entry_config,
            event_id=_optional_str(event_id),
            pattern_type=_optional_str(pattern_type),
            metadata={"invalid_reason": str(exc)},
        )

    return PatternEntryPlan(
        mode=entry_mode,
        direction=normalized_direction,
        limit_price=limit_price,
        config=entry_config,
        event_id=_optional_str(event_id),
        pattern_type=_optional_str(pattern_type),
    )


def simulate_pattern_entry(
    plan: PatternEntryPlan,
    confirmation_candle: dict[str, Any] | pd.Series,
    future_candles: pd.DataFrame | Iterable[dict[str, Any]],
) -> PatternEntrySimulationResult:
    """Simulate deterministic entry fill behavior from completed candles.

    Required columns:
    - confirmation candle: ``timestamp``, ``open``, ``high``, ``low``, ``close``
    - future candles: ``timestamp``, ``open``, ``high``, ``low``, ``close``
    """

    if plan.metadata and "invalid_reason" in plan.metadata:
        return PatternEntrySimulationResult(
            status=PatternEntryStatus.INVALID,
            fill_price=None,
            fill_timestamp=None,
            fill_candle_index=None,
            bars_waited=0,
            plan=plan,
            reason=str(plan.metadata["invalid_reason"]),
        )

    confirmation = _normalize_one_candle(confirmation_candle, candle_name="confirmation_candle")
    frame = _normalize_candles(future_candles)

    if plan.mode == PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE:
        return PatternEntrySimulationResult(
            status=PatternEntryStatus.FILLED,
            fill_price=float(confirmation["close"]),
            fill_timestamp=confirmation["timestamp"],
            fill_candle_index=0,
            bars_waited=0,
            plan=plan,
        )

    if plan.mode == PatternEntryMode.MARKET_ON_NEXT_OPEN:
        if frame.empty:
            return PatternEntrySimulationResult(
                status=plan.config.expire_status,
                fill_price=None,
                fill_timestamp=None,
                fill_candle_index=None,
                bars_waited=0,
                plan=plan,
                reason="next candle is required for MARKET_ON_NEXT_OPEN",
            )
        first = frame.iloc[0]
        return PatternEntrySimulationResult(
            status=PatternEntryStatus.FILLED,
            fill_price=float(first["open"]),
            fill_timestamp=first["timestamp"],
            fill_candle_index=0,
            bars_waited=1,
            plan=plan,
        )

    assert plan.limit_price is not None
    trigger = _coerce_trigger(plan.config.entry_trigger)
    max_rows = len(frame) if plan.config.max_wait_bars is None else min(len(frame), plan.config.max_wait_bars)
    touch_timestamp = None
    touch_index = None
    for index in range(max_rows):
        candle = frame.iloc[index]
        if float(candle["low"]) <= plan.limit_price <= float(candle["high"]):
            touch_timestamp = candle["timestamp"]
            touch_index = index
            if trigger != PatternEntryTrigger.TOUCH:
                break
            return PatternEntrySimulationResult(
                status=PatternEntryStatus.FILLED,
                fill_price=float(plan.limit_price),
                fill_timestamp=candle["timestamp"],
                fill_candle_index=index,
                bars_waited=index + 1,
                plan=plan,
                entry_trigger=trigger.value,
                touch_timestamp=candle["timestamp"],
                touch_candle_index=index,
            )

    if touch_index is not None and trigger != PatternEntryTrigger.TOUCH:
        for index in range(touch_index, max_rows):
            candle = frame.iloc[index]
            if _reaction_confirmed(candle, plan.direction, plan.limit_price, trigger):
                return PatternEntrySimulationResult(
                    status=PatternEntryStatus.FILLED,
                    fill_price=float(candle["close"]),
                    fill_timestamp=candle["timestamp"],
                    fill_candle_index=index,
                    bars_waited=index + 1,
                    plan=plan,
                    entry_trigger=trigger.value,
                    touch_timestamp=touch_timestamp,
                    touch_candle_index=touch_index,
                    reaction_timestamp=candle["timestamp"],
                    reaction_candle_index=index,
                )
        return PatternEntrySimulationResult(
            status=plan.config.expire_status,
            fill_price=None,
            fill_timestamp=None,
            fill_candle_index=None,
            bars_waited=max_rows,
            plan=plan,
            reason="limit price touched but reaction trigger was not confirmed within evaluated candles",
            entry_trigger=trigger.value,
            touch_timestamp=touch_timestamp,
            touch_candle_index=touch_index,
        )

    return PatternEntrySimulationResult(
        status=plan.config.expire_status,
        fill_price=None,
        fill_timestamp=None,
        fill_candle_index=None,
        bars_waited=max_rows,
        plan=plan,
        reason="limit price not touched within evaluated candles",
        entry_trigger=trigger.value,
    )


def _coerce_mode(mode: PatternEntryMode | str) -> PatternEntryMode:
    if isinstance(mode, PatternEntryMode):
        return mode
    return PatternEntryMode(str(mode).upper())


def _coerce_direction(direction: str) -> str:
    normalized = str(direction).upper()
    if normalized not in ("LONG", "SHORT"):
        raise ValueError("direction must be LONG or SHORT")
    return normalized


def _coerce_trigger(trigger: PatternEntryTrigger | str) -> PatternEntryTrigger:
    if isinstance(trigger, PatternEntryTrigger):
        return trigger
    return PatternEntryTrigger(str(trigger).upper())


def _reaction_confirmed(
    candle: pd.Series,
    direction: str,
    limit_price: float,
    trigger: PatternEntryTrigger,
) -> bool:
    close = float(candle["close"])
    open_price = float(candle["open"])
    if trigger == PatternEntryTrigger.TOUCH_AND_REACTION_CLOSE:
        return close > open_price if direction == "LONG" else close < open_price
    if direction == "LONG":
        return close >= limit_price
    return close <= limit_price


def _event_field(event: Any, name: str) -> Any:
    if isinstance(event, dict):
        return event.get(name)
    return getattr(event, name, None)


def _required_numeric_field(event: Any, name: str) -> float:
    value = _event_field(event, name)
    if value is None:
        raise ValueError(f"event is missing required field for entry mode: {name}")
    return _positive_float(value, name)


def _boundary_price(event: Any, direction: str, *, variant: str) -> float:
    zone_low = _event_field(event, "zone_low")
    if zone_low is None:
        zone_low = _event_field(event, "lower_boundary_value")
    zone_high = _event_field(event, "zone_high")
    if zone_high is None:
        zone_high = _event_field(event, "upper_boundary_value")
    zone_low = _positive_float(zone_low, "zone_low")
    zone_high = _positive_float(zone_high, "zone_high")
    if variant == "near":
        if direction == "LONG":
            return zone_high
        return zone_low
    if direction == "LONG":
        return zone_low
    return zone_high


def _order_block_618_price(event: Any, direction: str) -> float:
    zone_low = _positive_float(_event_field(event, "zone_low"), "zone_low")
    zone_high = _positive_float(_event_field(event, "zone_high"), "zone_high")
    if zone_high <= zone_low:
        raise ValueError("zone_high must be greater than zone_low")
    zone_size = zone_high - zone_low
    if direction == "LONG":
        return zone_high - zone_size * 0.618
    return zone_low + zone_size * 0.618


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _positive_float(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if number <= 0:
        raise ValueError(f"{name} must be positive")
    return number


def _normalize_one_candle(candle: dict[str, Any] | pd.Series, *, candle_name: str) -> pd.Series:
    row = candle.copy(deep=True) if isinstance(candle, pd.Series) else dict(candle)
    frame = pd.DataFrame([row])
    normalized = _normalize_candles(frame, candle_name=candle_name)
    return normalized.iloc[0]


def _normalize_candles(
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    candle_name: str = "future_candles",
) -> pd.DataFrame:
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    required_columns = ("timestamp", "open", "high", "low", "close")
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required {candle_name} columns: {', '.join(missing)}")
    if not frame.empty and not frame["timestamp"].is_monotonic_increasing:
        raise ValueError(f"{candle_name} must be sorted ascending by timestamp")
    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if frame[column].isna().any():
            raise ValueError(f"{candle_name} column contains missing values: {column}")
    return frame.reset_index(drop=True)
