"""Adam and Eve risk/exit planning.

This module consumes already-detected ``AdamAndEveEvent`` records plus optional
caller-supplied structure targets and returns deterministic risk/exit plan data.
It does not detect patterns, fetch market data, call exchange APIs, place orders,
or simulate exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from quant_bitcoin.patterns.adam_and_eve import AdamAndEveDirection, AdamAndEveEvent
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

ADAM_AND_EVE_ATR_BUFFER_MIN = 0.3
ADAM_AND_EVE_ATR_BUFFER_MAX = 0.6


class AdamAndEveStopMode(Enum):
    """Supported Adam and Eve structural stop modes."""

    EVE_LOW = "EVE_LOW"
    WIDER_ADAM_EVE_LOW = "WIDER_ADAM_EVE_LOW"


@dataclass(frozen=True)
class AdamAndEveNecklineSoftExit:
    """Future-simulator metadata for neckline re-entry invalidation."""

    enabled: bool
    neckline: float
    invalidates_when: str = "close < neckline_after_breakout"
    rule: str = "adam_and_eve_neckline_reentry"


@dataclass(frozen=True)
class AdamAndEveRiskExitConfig:
    """Configuration for Adam and Eve risk/exit planning."""

    atr_buffer_multiplier: float = 0.3
    stop_mode: AdamAndEveStopMode | str = AdamAndEveStopMode.EVE_LOW
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
            ADAM_AND_EVE_ATR_BUFFER_MIN
            <= self.atr_buffer_multiplier
            <= ADAM_AND_EVE_ATR_BUFFER_MAX
        ):
            raise ValueError("atr_buffer_multiplier must be between 0.3 and 0.6")
        _coerce_stop_mode(self.stop_mode)
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
class AdamAndEveRiskExitPlan:
    """Adam and Eve-specific wrapper around the shared risk/exit plan."""

    event_id: str
    risk_plan: RiskExitPlan
    stop_mode: AdamAndEveStopMode
    structural_stop_source: str
    measured_target: float
    structural_targets: tuple[float, ...]
    neckline_soft_exit: AdamAndEveNecklineSoftExit


def create_adam_and_eve_risk_exit_plan(
    event: AdamAndEveEvent,
    *,
    structural_targets: Iterable[float | int] | None = None,
    config: AdamAndEveRiskExitConfig | None = None,
) -> AdamAndEveRiskExitPlan:
    """Create an Adam and Eve risk/exit plan from a detected bullish event.

    The current detector emits bullish Adam and Eve events only. Inverse or
    bearish directions are explicitly rejected instead of fabricated.
    """

    planner_config = config or AdamAndEveRiskExitConfig()
    direction = _risk_direction(event.direction)
    stop_mode = _coerce_stop_mode(planner_config.stop_mode)
    structural_stop, structural_stop_source = _structural_stop(event, stop_mode)
    measured_target = _measured_target(event)
    structure_targets = _structural_targets(
        entry_price=float(event.entry_reference),
        structural_targets=structural_targets,
    )

    risk_plan = create_risk_exit_plan(
        direction=direction,
        entry_price=event.entry_reference,
        structural_stop=structural_stop,
        atr=event.atr,
        config=planner_config.to_risk_exit_config(),
        structural_targets=structure_targets,
        measured_targets=(measured_target,),
    )

    return AdamAndEveRiskExitPlan(
        event_id=event.event_id,
        risk_plan=risk_plan,
        stop_mode=stop_mode,
        structural_stop_source=structural_stop_source,
        measured_target=measured_target,
        structural_targets=structure_targets,
        neckline_soft_exit=AdamAndEveNecklineSoftExit(
            enabled=True,
            neckline=float(event.neckline),
        ),
    )


def _risk_direction(direction: str) -> RiskExitDirection:
    if direction == AdamAndEveDirection.BULLISH.value:
        return RiskExitDirection.LONG
    raise ValueError("Adam and Eve risk planning supports only BULLISH events")


def _structural_stop(
    event: AdamAndEveEvent,
    stop_mode: AdamAndEveStopMode,
) -> tuple[float, str]:
    if stop_mode == AdamAndEveStopMode.WIDER_ADAM_EVE_LOW:
        return min(float(event.adam_low_price), float(event.eve_low_price)), "min_adam_eve_low"
    return float(event.eve_low_price), "eve_low_price"


def _measured_target(event: AdamAndEveEvent) -> float:
    return float(event.neckline) + float(event.pattern_height)


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


def _coerce_stop_mode(stop_mode: AdamAndEveStopMode | str) -> AdamAndEveStopMode:
    if isinstance(stop_mode, AdamAndEveStopMode):
        return stop_mode
    try:
        return AdamAndEveStopMode(str(stop_mode).upper())
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in AdamAndEveStopMode)
        raise ValueError(f"stop_mode must be one of: {allowed}") from exc
