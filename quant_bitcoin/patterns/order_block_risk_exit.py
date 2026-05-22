"""Order Block risk/exit planning.

This module consumes already-detected ``OrderBlockEvent`` records plus optional
caller-supplied structure targets and returns deterministic risk/exit plan data.
It does not detect patterns, fetch market data, call exchange APIs, place orders,
or simulate exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.patterns.order_block import OrderBlockDirection, OrderBlockEvent
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


class OrderBlockEntryMode(Enum):
    """Supported deterministic Order Block entry references."""

    ZONE_MID = "ZONE_MID"
    ZONE_618 = "ZONE_618"
    EVENT_ENTRY_REFERENCE = "EVENT_ENTRY_REFERENCE"


@dataclass(frozen=True)
class OrderBlockNoReactionStop:
    """Future-simulator metadata for no reaction after entering the OB zone."""

    enabled: bool
    max_bars_after_entry: int
    required_reaction_r: float
    rule: str = "no_reaction_after_order_block_entry"


@dataclass(frozen=True)
class OrderBlockRiskExitConfig:
    """Configuration for Order Block risk/exit planning."""

    atr_buffer_multiplier: float = 0.2
    entry_mode: OrderBlockEntryMode | str = OrderBlockEntryMode.ZONE_MID
    r_multiples: tuple[float, ...] = (1.0, 2.0, 3.0)
    minimum_first_target_r: float = 0.8
    no_reaction_bars: int = 5
    no_reaction_required_r: float = 0.0
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
        if self.atr_buffer_multiplier < 0:
            raise ValueError("atr_buffer_multiplier must be non-negative")
        _coerce_entry_mode(self.entry_mode)
        if self.no_reaction_bars < 1:
            raise ValueError("no_reaction_bars must be at least 1")
        if self.no_reaction_required_r < 0:
            raise ValueError("no_reaction_required_r must be non-negative")

    def to_risk_exit_config(self) -> RiskExitConfig:
        """Convert to the shared risk/exit contract config."""

        return RiskExitConfig(
            atr_buffer_multiplier=self.atr_buffer_multiplier,
            r_multiples=self.r_multiples,
            minimum_first_target_r=self.minimum_first_target_r,
            time_stop=TimeStopSettings(
                max_bars_in_trade=self.no_reaction_bars,
                required_r_multiple=self.no_reaction_required_r,
            ),
            break_even=self.break_even,
            trailing_stop=self.trailing_stop,
            partial_exits=self.partial_exits,
        )


@dataclass(frozen=True)
class OrderBlockRiskExitPlan:
    """Order Block-specific wrapper around the shared risk/exit plan."""

    event_id: str
    risk_plan: RiskExitPlan
    entry_mode: OrderBlockEntryMode
    entry_reference: float
    structural_stop_source: str
    structural_targets: tuple[float, ...]
    no_reaction_stop: OrderBlockNoReactionStop


def create_order_block_risk_exit_plan(
    event: OrderBlockEvent,
    *,
    structural_targets: Iterable[float | int] | None = None,
    config: OrderBlockRiskExitConfig | None = None,
) -> OrderBlockRiskExitPlan:
    """Create an Order Block risk/exit plan from a detected event.

    The hard stop structural reference is the unbuffered zone boundary; the
    shared Task 047 contract applies the configured ATR buffer. Previous
    liquidity or market-structure targets may be supplied by callers through
    ``structural_targets`` and the existing event ``target_reference`` is also
    considered when actionable.
    """

    planner_config = config or OrderBlockRiskExitConfig()
    direction = _risk_direction(event.direction)
    atr = _event_atr(event)
    entry_mode = _coerce_entry_mode(planner_config.entry_mode)
    entry_reference = _entry_reference(event, direction, entry_mode)
    structural_stop, structural_stop_source = _structural_stop(event, direction)
    targets = _structural_targets(
        direction=direction,
        entry_price=entry_reference,
        event_target_reference=_optional_float(event.target_reference),
        structural_targets=structural_targets,
    )

    risk_plan = create_risk_exit_plan(
        direction=direction,
        entry_price=entry_reference,
        structural_stop=structural_stop,
        atr=atr,
        config=planner_config.to_risk_exit_config(),
        structural_targets=targets,
    )

    return OrderBlockRiskExitPlan(
        event_id=event.event_id,
        risk_plan=risk_plan,
        entry_mode=entry_mode,
        entry_reference=entry_reference,
        structural_stop_source=structural_stop_source,
        structural_targets=targets,
        no_reaction_stop=OrderBlockNoReactionStop(
            enabled=True,
            max_bars_after_entry=planner_config.no_reaction_bars,
            required_reaction_r=planner_config.no_reaction_required_r,
        ),
    )


def _risk_direction(direction: str) -> RiskExitDirection:
    if direction == OrderBlockDirection.BULLISH.value:
        return RiskExitDirection.LONG
    if direction == OrderBlockDirection.BEARISH.value:
        return RiskExitDirection.SHORT
    raise ValueError("Order Block direction must be BULLISH or BEARISH")


def _event_atr(event: OrderBlockEvent) -> float | None:
    zone_size = _optional_float(event.zone_size)
    zone_size_atr = _optional_float(event.zone_size_atr)
    if zone_size is None or zone_size_atr is None or zone_size_atr <= 0:
        return None
    return zone_size / zone_size_atr


def _entry_reference(
    event: OrderBlockEvent,
    direction: RiskExitDirection,
    entry_mode: OrderBlockEntryMode,
) -> float:
    zone_low = float(event.zone_low)
    zone_high = float(event.zone_high)
    zone_size = zone_high - zone_low
    if entry_mode == OrderBlockEntryMode.ZONE_MID:
        return float(event.zone_mid)
    if entry_mode == OrderBlockEntryMode.EVENT_ENTRY_REFERENCE:
        return float(event.entry_reference)
    if direction == RiskExitDirection.LONG:
        return zone_high - zone_size * 0.618
    return zone_low + zone_size * 0.618


def _structural_stop(
    event: OrderBlockEvent,
    direction: RiskExitDirection,
) -> tuple[float, str]:
    if direction == RiskExitDirection.LONG:
        return float(event.zone_low), "order_block_zone_low"
    return float(event.zone_high), "order_block_zone_high"


def _structural_targets(
    *,
    direction: RiskExitDirection,
    entry_price: float,
    event_target_reference: float | None,
    structural_targets: Iterable[float | int] | None,
) -> tuple[float, ...]:
    candidates: list[float] = []
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


def _coerce_entry_mode(entry_mode: OrderBlockEntryMode | str) -> OrderBlockEntryMode:
    if isinstance(entry_mode, OrderBlockEntryMode):
        return entry_mode
    try:
        return OrderBlockEntryMode(str(entry_mode).upper())
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in OrderBlockEntryMode)
        raise ValueError(f"entry_mode must be one of: {allowed}") from exc


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)
