"""Diamond Pattern risk/exit planning.

This module consumes already-detected ``DiamondEvent`` records plus optional
caller-supplied candle context and returns deterministic risk/exit plan data. It
does not detect patterns, fetch market data, call exchange APIs, place orders,
or simulate exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.patterns.diamond import DiamondDirection, DiamondEvent
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

DIAMOND_ATR_BUFFER_MIN = 0.2
DIAMOND_ATR_BUFFER_MAX = 0.5


@dataclass(frozen=True)
class DiamondSoftInvalidation:
    """Future-simulator metadata for close back inside the diamond range."""

    enabled: bool
    upper_boundary_value: float
    lower_boundary_value: float
    invalidates_when: str
    rule: str = "diamond_close_back_inside_range"


@dataclass(frozen=True)
class DiamondRiskExitConfig:
    """Configuration for Diamond risk/exit planning."""

    atr_buffer_multiplier: float = 0.2
    r_multiples: tuple[float, ...] = (1.0, 2.0, 3.0)
    minimum_first_target_r: float = 0.8
    time_stop_bars: int = 5
    time_stop_required_r: float = 1.0
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
        if not DIAMOND_ATR_BUFFER_MIN <= self.atr_buffer_multiplier <= DIAMOND_ATR_BUFFER_MAX:
            raise ValueError("atr_buffer_multiplier must be between 0.2 and 0.5")
        if self.time_stop_bars < 1:
            raise ValueError("time_stop_bars must be at least 1")
        if self.time_stop_required_r < 0:
            raise ValueError("time_stop_required_r must be non-negative")

    def to_risk_exit_config(self) -> RiskExitConfig:
        """Convert to the shared risk/exit contract config."""

        return RiskExitConfig(
            atr_buffer_multiplier=self.atr_buffer_multiplier,
            r_multiples=self.r_multiples,
            minimum_first_target_r=self.minimum_first_target_r,
            time_stop=TimeStopSettings(
                max_bars_in_trade=self.time_stop_bars,
                required_r_multiple=self.time_stop_required_r,
            ),
            break_even=self.break_even,
            trailing_stop=self.trailing_stop,
            partial_exits=self.partial_exits,
        )


@dataclass(frozen=True)
class DiamondRiskExitPlan:
    """Diamond-specific wrapper around the shared risk/exit plan."""

    event_id: str
    risk_plan: RiskExitPlan
    structural_stop_source: str
    internal_pivot_reference: float | None
    measured_target: float
    soft_invalidation: DiamondSoftInvalidation


def create_diamond_risk_exit_plan(
    event: DiamondEvent,
    *,
    candles: pd.DataFrame | Iterable[dict[str, Any]] | None = None,
    config: DiamondRiskExitConfig | None = None,
) -> DiamondRiskExitPlan:
    """Create a Diamond risk/exit plan from a detected event.

    When candles are supplied, the planner reconstructs the last internal pivot
    low/high reference from ``source_pivot_indices``. Without candles it falls
    back to the detector's existing ``stop_reference`` to avoid guessing hidden
    pivot prices.
    """

    planner_config = config or DiamondRiskExitConfig()
    direction = _risk_direction(event.direction)
    internal_pivot = _internal_pivot_reference(event, candles, direction)
    structural_stop = internal_pivot if internal_pivot is not None else float(event.stop_reference)
    structural_stop_source = (
        "last_internal_pivot_low"
        if direction == RiskExitDirection.LONG and internal_pivot is not None
        else "last_internal_pivot_high"
        if direction == RiskExitDirection.SHORT and internal_pivot is not None
        else "event_stop_reference"
    )
    measured_target = _measured_target(event, direction)

    risk_plan = create_risk_exit_plan(
        direction=direction,
        entry_price=event.entry_reference,
        structural_stop=structural_stop,
        atr=event.atr,
        config=planner_config.to_risk_exit_config(),
        measured_targets=(measured_target,),
        detector_target_reference=event.target_reference,
        atr_metadata=getattr(event, "atr_metadata", {}),
    )

    return DiamondRiskExitPlan(
        event_id=event.event_id,
        risk_plan=risk_plan,
        structural_stop_source=structural_stop_source,
        internal_pivot_reference=internal_pivot,
        measured_target=measured_target,
        soft_invalidation=_soft_invalidation(event, direction),
    )


def _risk_direction(direction: str) -> RiskExitDirection:
    if direction == DiamondDirection.BULLISH.value:
        return RiskExitDirection.LONG
    if direction == DiamondDirection.BEARISH.value:
        return RiskExitDirection.SHORT
    raise ValueError("Diamond direction must be BULLISH or BEARISH")


def _internal_pivot_reference(
    event: DiamondEvent,
    candles: pd.DataFrame | Iterable[dict[str, Any]] | None,
    direction: RiskExitDirection,
) -> float | None:
    if candles is None:
        return None
    frame = candles if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    internal_indices = tuple(
        index for index in event.source_pivot_indices if index < event.breakout_index
    )
    if not internal_indices:
        return None
    pivot_index = max(internal_indices)
    if pivot_index < 0 or pivot_index >= len(frame):
        raise ValueError("source pivot index is outside supplied candles")
    column = "low" if direction == RiskExitDirection.LONG else "high"
    if column not in frame.columns:
        raise ValueError(f"candles must include {column} for Diamond risk planning")
    return float(frame.iloc[pivot_index][column])


def _measured_target(event: DiamondEvent, direction: RiskExitDirection) -> float:
    if direction == RiskExitDirection.LONG:
        return float(event.breakout_price) + float(event.pattern_height)
    return float(event.breakout_price) - float(event.pattern_height)


def _soft_invalidation(event: DiamondEvent, direction: RiskExitDirection) -> DiamondSoftInvalidation:
    if direction == RiskExitDirection.LONG:
        condition = "close <= upper_boundary_value"
    else:
        condition = "close >= lower_boundary_value"
    return DiamondSoftInvalidation(
        enabled=True,
        upper_boundary_value=float(event.upper_boundary_value),
        lower_boundary_value=float(event.lower_boundary_value),
        invalidates_when=condition,
    )
