"""Fair Value Gap risk/exit planning.

This module consumes already-detected ``PatternEvent`` Fair Value Gap records
plus optional caller-supplied structure/liquidity targets and returns
deterministic risk/exit plan data. It does not detect patterns, fetch market
data, call exchange APIs, place orders, or simulate exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.patterns.fair_value_gap import PatternDirection, PatternEvent
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

FVG_ATR_BUFFER_MIN = 0.1
FVG_ATR_BUFFER_MAX = 0.3


@dataclass(frozen=True)
class FairValueGapReactionFailureRule:
    """Future-simulator metadata for missing a midpoint reaction after FVG entry."""

    enabled: bool
    max_bars_after_entry: int
    midpoint_price: float
    favorable_close_condition: str
    rule: str = "fvg_midpoint_reaction_failure"
    action: str = "SOFT_INVALIDATION_EXIT"


class FairValueGapStopMode(Enum):
    FVG_BOUNDARY_ATR_BUFFER = "FVG_BOUNDARY_ATR_BUFFER"
    SWING_PIVOT = "SWING_PIVOT"
    WIDER_OF_FVG_AND_SWING = "WIDER_OF_FVG_AND_SWING"


@dataclass(frozen=True)
class FairValueGapRiskExitConfig:
    """Configuration for Fair Value Gap risk/exit planning."""

    atr_buffer_multiplier: float = 0.2
    r_multiples: tuple[float, ...] = (1.0, 2.0, 3.0)
    minimum_first_target_r: float = 0.8
    reaction_failure_bars: int = 5
    break_even: BreakEvenSettings = field(default_factory=BreakEvenSettings)
    trailing_stop: TrailingStopSettings = field(default_factory=TrailingStopSettings)
    partial_exits: tuple[PartialExitSettings, ...] = field(
        default_factory=lambda: (
            PartialExitSettings(1.0, 0.33),
            PartialExitSettings(2.0, 0.33),
            PartialExitSettings(3.0, 0.34),
        )
    )
    use_liquidity_targets: bool = False
    require_liquidity_target: bool = False
    minimum_liquidity_target_r: float = 0.0
    stop_mode: FairValueGapStopMode | str = FairValueGapStopMode.FVG_BOUNDARY_ATR_BUFFER

    def __post_init__(self) -> None:
        if not FVG_ATR_BUFFER_MIN <= self.atr_buffer_multiplier <= FVG_ATR_BUFFER_MAX:
            raise ValueError("atr_buffer_multiplier must be between 0.1 and 0.3")
        if self.reaction_failure_bars < 1:
            raise ValueError("reaction_failure_bars must be at least 1")
        if self.minimum_liquidity_target_r < 0:
            raise ValueError("minimum_liquidity_target_r must be non-negative")
        _coerce_stop_mode(self.stop_mode)

    def to_risk_exit_config(self) -> RiskExitConfig:
        """Convert to the shared risk/exit contract config."""

        return RiskExitConfig(
            atr_buffer_multiplier=self.atr_buffer_multiplier,
            r_multiples=self.r_multiples,
            minimum_first_target_r=self.minimum_first_target_r,
            time_stop=TimeStopSettings(max_bars_in_trade=self.reaction_failure_bars),
            break_even=self.break_even,
            trailing_stop=self.trailing_stop,
            partial_exits=self.partial_exits,
        )


@dataclass(frozen=True)
class FairValueGapRiskExitPlan:
    """Fair Value Gap-specific wrapper around the shared risk/exit plan."""

    event_id: str
    risk_plan: RiskExitPlan
    structural_stop_source: str
    fvg_boundary_target: float
    structural_targets: tuple[float, ...]
    reaction_failure: FairValueGapReactionFailureRule
    liquidity_target_metadata: dict[str, Any] = field(default_factory=dict)
    stop_mode: str = FairValueGapStopMode.FVG_BOUNDARY_ATR_BUFFER.value
    stop_metadata: dict[str, Any] = field(default_factory=dict)


def create_fair_value_gap_risk_exit_plan(
    event: PatternEvent,
    *,
    structural_targets: Iterable[float | int] | None = None,
    liquidity_target_metadata: dict[str, Any] | None = None,
    swing_stop: float | int | None = None,
    config: FairValueGapRiskExitConfig | None = None,
) -> FairValueGapRiskExitPlan:
    """Create a Fair Value Gap risk/exit plan from a detected event.

    The hard stop structural reference is the unbuffered FVG boundary. The
    shared Task 047 contract applies the configured ATR buffer. Liquidity and
    swing targets are optional caller inputs and are not fabricated when absent.
    """

    planner_config = config or FairValueGapRiskExitConfig()
    direction = _risk_direction(event.direction)
    atr = _event_atr(event)
    structural_stop, structural_stop_source, stop_metadata = _structural_stop(
        event,
        direction,
        planner_config,
        swing_stop=swing_stop,
    )
    fvg_boundary_target = _fvg_boundary_target(event, direction)
    targets = _structural_targets(
        direction=direction,
        entry_price=float(event.entry_reference),
        fvg_boundary_target=fvg_boundary_target,
        event_target_reference=_optional_float(event.target_reference),
        structural_targets=structural_targets,
    )
    if planner_config.require_liquidity_target and not tuple(structural_targets or ()):
        targets = ()

    risk_plan = create_risk_exit_plan(
        direction=direction,
        entry_price=event.entry_reference,
        structural_stop=structural_stop,
        atr=atr,
        config=planner_config.to_risk_exit_config(),
        structural_targets=targets,
        detector_target_reference=event.target_reference,
        atr_metadata={
            **getattr(event, "atr_metadata", {}),
            "fvg_stop_mode": stop_metadata,
        },
    )

    return FairValueGapRiskExitPlan(
        event_id=event.event_id,
        risk_plan=risk_plan,
        structural_stop_source=structural_stop_source,
        fvg_boundary_target=fvg_boundary_target,
        structural_targets=targets,
        reaction_failure=_reaction_failure_rule(event, direction, planner_config),
        liquidity_target_metadata=dict(liquidity_target_metadata or {}),
        stop_mode=_coerce_stop_mode(planner_config.stop_mode).value,
        stop_metadata=stop_metadata,
    )


def _risk_direction(direction: str) -> RiskExitDirection:
    if direction == PatternDirection.BULLISH.value:
        return RiskExitDirection.LONG
    if direction == PatternDirection.BEARISH.value:
        return RiskExitDirection.SHORT
    raise ValueError("Fair Value Gap direction must be BULLISH or BEARISH")


def _event_atr(event: PatternEvent) -> float | None:
    gap_size = _optional_float(event.gap_size)
    gap_size_atr = _optional_float(event.gap_size_atr)
    if gap_size is None or gap_size_atr is None or gap_size_atr <= 0:
        return None
    return gap_size / gap_size_atr


def _structural_stop(
    event: PatternEvent,
    direction: RiskExitDirection,
    config: FairValueGapRiskExitConfig,
    *,
    swing_stop: float | int | None,
) -> tuple[float | None, str, dict[str, Any]]:
    stop_mode = _coerce_stop_mode(config.stop_mode)
    if direction == RiskExitDirection.LONG:
        fvg_stop = float(event.zone_low)
        fvg_source = "fvg_zone_low"
    else:
        fvg_stop = float(event.zone_high)
        fvg_source = "fvg_zone_high"
    swing = _optional_float(swing_stop)
    if stop_mode == FairValueGapStopMode.FVG_BOUNDARY_ATR_BUFFER:
        selected = fvg_stop
        source = fvg_source
    elif swing is None:
        selected = None
        source = "missing_swing_pivot_stop"
    elif stop_mode == FairValueGapStopMode.SWING_PIVOT:
        selected = swing
        source = "confirmed_swing_pivot"
    else:
        selected = min(fvg_stop, swing) if direction == RiskExitDirection.LONG else max(fvg_stop, swing)
        source = "wider_of_fvg_boundary_and_swing"
    return selected, source, {
        "schema_version": "fvg_stop_mode_v1",
        "stop_mode": stop_mode.value,
        "fvg_boundary_stop": fvg_stop,
        "swing_stop": swing,
        "selected_stop": selected,
        "source": source,
        "direction": direction.value,
        "no_lookahead": True,
    }


def _fvg_boundary_target(event: PatternEvent, direction: RiskExitDirection) -> float:
    if direction == RiskExitDirection.LONG:
        return float(event.zone_high)
    return float(event.zone_low)


def _structural_targets(
    *,
    direction: RiskExitDirection,
    entry_price: float,
    fvg_boundary_target: float,
    event_target_reference: float | None,
    structural_targets: Iterable[float | int] | None,
) -> tuple[float, ...]:
    candidates: list[float] = [fvg_boundary_target]
    if structural_targets is not None:
        for target in structural_targets:
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


def _reaction_failure_rule(
    event: PatternEvent,
    direction: RiskExitDirection,
    config: FairValueGapRiskExitConfig,
) -> FairValueGapReactionFailureRule:
    if direction == RiskExitDirection.LONG:
        condition = "close > fvg_midpoint"
    else:
        condition = "close < fvg_midpoint"
    return FairValueGapReactionFailureRule(
        enabled=True,
        max_bars_after_entry=config.reaction_failure_bars,
        midpoint_price=float(event.zone_mid),
        favorable_close_condition=condition,
    )


def _coerce_stop_mode(stop_mode: FairValueGapStopMode | str) -> FairValueGapStopMode:
    if isinstance(stop_mode, FairValueGapStopMode):
        return stop_mode
    return FairValueGapStopMode(str(stop_mode).upper())


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
