"""Cup and Handle risk/exit planning.

This module consumes already-detected ``CupAndHandleEvent`` records plus optional
caller-supplied structure targets and returns deterministic risk/exit plan data.
It does not detect patterns, fetch market data, call exchange APIs, place orders,
or simulate exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from quant_bitcoin.patterns.cup_and_handle import (
    CupAndHandleDirection,
    CupAndHandleEvent,
)
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

CUP_AND_HANDLE_ATR_BUFFER_MIN = 0.3
CUP_AND_HANDLE_ATR_BUFFER_MAX = 0.6


@dataclass(frozen=True)
class CupAndHandleNecklineSoftExit:
    """Future-simulator metadata for fast neckline re-entry invalidation."""

    enabled: bool
    neckline: float
    invalidates_when: str = "close < neckline_after_breakout"
    rule: str = "cup_and_handle_neckline_reentry"


@dataclass(frozen=True)
class CupAndHandleHardStopRule:
    """Metadata describing the wider handle-low hard stop rule."""

    structural_stop: float
    atr_buffer_multiplier: float
    rule: str = "handle_low_minus_atr_buffer"


@dataclass(frozen=True)
class CupAndHandleRiskExitConfig:
    """Configuration for Cup and Handle risk/exit planning."""

    atr_buffer_multiplier: float = 0.3
    r_multiples: tuple[float, ...] = (1.0, 2.0, 3.0)
    minimum_first_target_r: float = 0.8
    breakout_follow_through_bars: int = 5
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
            CUP_AND_HANDLE_ATR_BUFFER_MIN
            <= self.atr_buffer_multiplier
            <= CUP_AND_HANDLE_ATR_BUFFER_MAX
        ):
            raise ValueError("atr_buffer_multiplier must be between 0.3 and 0.6")
        if self.breakout_follow_through_bars < 1:
            raise ValueError("breakout_follow_through_bars must be at least 1")

    def to_risk_exit_config(self) -> RiskExitConfig:
        """Convert to the shared risk/exit contract config."""

        return RiskExitConfig(
            atr_buffer_multiplier=self.atr_buffer_multiplier,
            r_multiples=self.r_multiples,
            minimum_first_target_r=self.minimum_first_target_r,
            time_stop=TimeStopSettings(max_bars_in_trade=self.breakout_follow_through_bars),
            break_even=self.break_even,
            trailing_stop=self.trailing_stop,
            partial_exits=self.partial_exits,
        )


@dataclass(frozen=True)
class CupAndHandleRiskExitPlan:
    """Cup and Handle-specific wrapper around the shared risk/exit plan."""

    event_id: str
    risk_plan: RiskExitPlan
    structural_stop_source: str
    measured_target: float
    structural_targets: tuple[float, ...]
    neckline_soft_exit: CupAndHandleNecklineSoftExit
    hard_stop: CupAndHandleHardStopRule


def create_cup_and_handle_risk_exit_plan(
    event: CupAndHandleEvent,
    *,
    structural_targets: Iterable[float | int] | None = None,
    config: CupAndHandleRiskExitConfig | None = None,
) -> CupAndHandleRiskExitPlan:
    """Create a Cup and Handle risk/exit plan from a detected bullish event.

    The current detector emits bullish Cup and Handle events only. Inverse or
    bearish directions are explicitly rejected instead of fabricated.
    """

    planner_config = config or CupAndHandleRiskExitConfig()
    direction = _risk_direction(event.direction)
    measured_target = _measured_target(event)
    structure_targets = _structural_targets(
        entry_price=float(event.entry_reference),
        structural_targets=structural_targets,
    )

    risk_plan = create_risk_exit_plan(
        direction=direction,
        entry_price=event.entry_reference,
        structural_stop=event.handle_low_price,
        atr=event.atr,
        config=planner_config.to_risk_exit_config(),
        structural_targets=structure_targets,
        measured_targets=(measured_target,),
    )

    return CupAndHandleRiskExitPlan(
        event_id=event.event_id,
        risk_plan=risk_plan,
        structural_stop_source="handle_low_price",
        measured_target=measured_target,
        structural_targets=structure_targets,
        neckline_soft_exit=CupAndHandleNecklineSoftExit(
            enabled=True,
            neckline=float(event.neckline),
        ),
        hard_stop=CupAndHandleHardStopRule(
            structural_stop=float(event.handle_low_price),
            atr_buffer_multiplier=planner_config.atr_buffer_multiplier,
        ),
    )


def _risk_direction(direction: str) -> RiskExitDirection:
    if direction == CupAndHandleDirection.BULLISH.value:
        return RiskExitDirection.LONG
    raise ValueError("Cup and Handle risk planning supports only BULLISH events")


def _measured_target(event: CupAndHandleEvent) -> float:
    return float(event.neckline) + float(event.cup_depth)


def _structural_targets(
    *,
    entry_price: float,
    structural_targets: Iterable[float | int] | None,
) -> tuple[float, ...]:
    if structural_targets is None:
        return ()
    actionable: list[float] = []
    for target in structural_targets:
        target_price = float(target)
        if target_price > entry_price:
            actionable.append(target_price)
    return tuple(actionable)
