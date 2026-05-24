"""Trendline Break risk/exit planning.

This module consumes already-detected ``TrendlineBreakEvent`` records plus
optional caller-supplied candle/retest context and returns deterministic
risk/exit plan data. It does not detect patterns, fetch market data, call
exchange APIs, place orders, or simulate exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.risk import (
    BreakEvenSettings,
    PartialExitSettings,
    RiskExitConfig,
    RiskExitDirection,
    RiskExitPlan,
    TimeStopSettings,
    TrailingStopSettings,
    create_risk_exit_plan,
)
from quant_bitcoin.patterns.trendline_break import (
    TrendlineBreakDirection,
    TrendlineBreakEvent,
)

TRENDLINE_BREAK_ATR_BUFFER_MIN = 0.2
TRENDLINE_BREAK_ATR_BUFFER_MAX = 0.4


@dataclass(frozen=True)
class TrendlineBreakSoftInvalidation:
    """Future-simulator metadata for re-entering the broken trendline side."""

    enabled: bool
    rule: str
    trendline_value: float
    invalidates_when: str


@dataclass(frozen=True)
class TrendlineBreakRiskExitConfig:
    """Configuration for Trendline Break risk/exit planning."""

    atr_buffer_multiplier: float = 0.2
    r_multiples: tuple[float, ...] = (1.0, 2.0, 3.0)
    minimum_first_target_r: float = 0.8
    follow_through_bars: int = 5
    follow_through_required_r: float = 1.0
    break_even: BreakEvenSettings = field(default_factory=BreakEvenSettings)
    trailing_stop: TrailingStopSettings = field(default_factory=TrailingStopSettings)
    partial_exits: tuple[PartialExitSettings, ...] = field(
        default_factory=lambda: (
            PartialExitSettings(1.0, 0.33),
            PartialExitSettings(2.0, 0.33),
            PartialExitSettings(3.0, 0.34),
        )
    )

    def __post_init__(self) -> None:
        if not (
            TRENDLINE_BREAK_ATR_BUFFER_MIN
            <= self.atr_buffer_multiplier
            <= TRENDLINE_BREAK_ATR_BUFFER_MAX
        ):
            raise ValueError("atr_buffer_multiplier must be between 0.2 and 0.4")
        if self.follow_through_bars < 1:
            raise ValueError("follow_through_bars must be at least 1")
        if self.follow_through_required_r < 0:
            raise ValueError("follow_through_required_r must be non-negative")

    def to_risk_exit_config(self) -> RiskExitConfig:
        """Convert to the shared risk/exit contract config."""

        return RiskExitConfig(
            atr_buffer_multiplier=self.atr_buffer_multiplier,
            r_multiples=self.r_multiples,
            minimum_first_target_r=self.minimum_first_target_r,
            time_stop=TimeStopSettings(
                max_bars_in_trade=self.follow_through_bars,
                required_r_multiple=self.follow_through_required_r,
            ),
            break_even=self.break_even,
            trailing_stop=self.trailing_stop,
            partial_exits=self.partial_exits,
        )


@dataclass(frozen=True)
class TrendlineBreakRiskExitPlan:
    """Trendline Break-specific wrapper around the shared risk/exit plan."""

    event_id: str
    risk_plan: RiskExitPlan
    structural_stop_source: str
    breakout_reference: float | None
    retest_pivot_reference: float | None
    structural_targets: tuple[float, ...]
    soft_invalidation: TrendlineBreakSoftInvalidation


def create_trendline_break_risk_exit_plan(
    event: TrendlineBreakEvent,
    *,
    candles: pd.DataFrame | Iterable[dict[str, Any]] | None = None,
    retest_pivot_price: float | int | None = None,
    prior_swing_targets: Iterable[float | int] | None = None,
    config: TrendlineBreakRiskExitConfig | None = None,
) -> TrendlineBreakRiskExitPlan:
    """Create a Trendline Break risk/exit plan from a detected event.

    Retest detection is intentionally not implemented here. If a caller has a
    deterministic retest pivot, it may pass ``retest_pivot_price``; otherwise
    the planner falls back to the breakout candle low/high when candles are
    supplied, then the event ``stop_reference``.
    """

    planner_config = config or TrendlineBreakRiskExitConfig()
    direction = _risk_direction(event.direction)
    breakout_reference = _breakout_candle_reference(event, candles, direction)
    structural_stop, structural_stop_source = _structural_stop(
        direction=direction,
        breakout_reference=breakout_reference,
        retest_pivot_price=_optional_float(retest_pivot_price),
        event_stop_reference=_optional_float(event.stop_reference),
    )
    targets = _structural_targets(
        direction=direction,
        entry_price=float(event.entry_reference),
        event_target_reference=_optional_float(event.target_reference),
        prior_swing_targets=prior_swing_targets,
    )

    risk_plan = create_risk_exit_plan(
        direction=direction,
        entry_price=event.entry_reference,
        structural_stop=structural_stop,
        atr=event.atr,
        config=planner_config.to_risk_exit_config(),
        structural_targets=targets,
        detector_target_reference=event.target_reference,
        atr_metadata=getattr(event, "atr_metadata", {}),
    )

    return TrendlineBreakRiskExitPlan(
        event_id=event.event_id,
        risk_plan=risk_plan,
        structural_stop_source=structural_stop_source,
        breakout_reference=breakout_reference,
        retest_pivot_reference=_optional_float(retest_pivot_price),
        structural_targets=targets,
        soft_invalidation=_soft_invalidation(event, direction),
    )


def _risk_direction(direction: str) -> RiskExitDirection:
    if direction == TrendlineBreakDirection.BULLISH.value:
        return RiskExitDirection.LONG
    if direction == TrendlineBreakDirection.BEARISH.value:
        return RiskExitDirection.SHORT
    raise ValueError("Trendline Break direction must be BULLISH or BEARISH")


def _breakout_candle_reference(
    event: TrendlineBreakEvent,
    candles: pd.DataFrame | Iterable[dict[str, Any]] | None,
    direction: RiskExitDirection,
) -> float | None:
    if candles is None:
        return None
    frame = candles if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    if event.end_index < 0 or event.end_index >= len(frame):
        raise ValueError("event end_index is outside supplied candles")
    column = "low" if direction == RiskExitDirection.LONG else "high"
    if column not in frame.columns:
        raise ValueError(f"candles must include {column} for Trendline Break risk planning")
    return _optional_float(frame.iloc[event.end_index][column])


def _structural_stop(
    *,
    direction: RiskExitDirection,
    breakout_reference: float | None,
    retest_pivot_price: float | None,
    event_stop_reference: float | None,
) -> tuple[float | None, str]:
    references: list[tuple[str, float]] = []
    if breakout_reference is not None:
        references.append(("breakout_candle", breakout_reference))
    if retest_pivot_price is not None:
        references.append(("retest_pivot", retest_pivot_price))

    if references:
        if direction == RiskExitDirection.LONG:
            source, value = min(references, key=lambda item: item[1])
        else:
            source, value = max(references, key=lambda item: item[1])
        if len(references) == 2:
            source = "breakout_candle_and_retest_pivot"
        return value, source

    return event_stop_reference, "event_stop_reference"


def _structural_targets(
    *,
    direction: RiskExitDirection,
    entry_price: float,
    event_target_reference: float | None,
    prior_swing_targets: Iterable[float | int] | None,
) -> tuple[float, ...]:
    candidates: list[float] = []
    if prior_swing_targets is not None:
        for target in prior_swing_targets:
            target_price = _optional_float(target)
            if target_price is not None:
                candidates.append(target_price)
    if event_target_reference is not None:
        candidates.append(event_target_reference)

    actionable: list[float] = []
    for candidate in candidates:
        if direction == RiskExitDirection.LONG and candidate > entry_price:
            actionable.append(candidate)
        if direction == RiskExitDirection.SHORT and candidate < entry_price:
            actionable.append(candidate)
    return tuple(actionable)


def _soft_invalidation(
    event: TrendlineBreakEvent,
    direction: RiskExitDirection,
) -> TrendlineBreakSoftInvalidation:
    if direction == RiskExitDirection.LONG:
        condition = "close <= trendline_value"
    else:
        condition = "close >= trendline_value"
    return TrendlineBreakSoftInvalidation(
        enabled=True,
        rule="close_reenters_broken_trendline_side",
        trendline_value=float(event.trendline_value),
        invalidates_when=condition,
    )


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
