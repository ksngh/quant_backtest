"""Liquidity sweep reversal risk/exit planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from quant_bitcoin.patterns.liquidity_sweep_reversal import (
    LiquiditySweepDirection,
    LiquiditySweepReversalEvent,
)
from quant_bitcoin.risk import (
    BreakEvenSettings,
    RiskExitConfig,
    RiskExitDirection,
    RiskExitPlan,
    TrailingStopSettings,
    create_risk_exit_plan,
)


@dataclass(frozen=True)
class LiquiditySweepReversalRiskExitConfig:
    stop_buffer_atr_multiplier: float = 0.10
    target_r_multiple: float = 2.0
    min_gross_rr: float = 1.2
    break_even: BreakEvenSettings = field(default_factory=lambda: BreakEvenSettings(enabled=False))
    trailing_stop: TrailingStopSettings = field(default_factory=TrailingStopSettings)

    def __post_init__(self) -> None:
        if self.stop_buffer_atr_multiplier < 0:
            raise ValueError("stop_buffer_atr_multiplier must be non-negative")
        if self.target_r_multiple <= 0:
            raise ValueError("target_r_multiple must be positive")
        if self.min_gross_rr < 0:
            raise ValueError("min_gross_rr must be non-negative")

    def to_metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "liquidity_sweep_reversal_risk_exit_config_v1",
            "stop_buffer_atr_multiplier": float(self.stop_buffer_atr_multiplier),
            "target_r_multiple": float(self.target_r_multiple),
            "min_gross_rr": float(self.min_gross_rr),
            "scope": "offline_backtest_research_only",
        }


@dataclass(frozen=True)
class LiquiditySweepReversalRiskExitPlan:
    event_id: str
    risk_plan: RiskExitPlan
    structural_stop_source: str
    target_source: str
    target_reference: float
    stop_metadata: dict[str, Any] = field(default_factory=dict)


def create_liquidity_sweep_reversal_risk_exit_plan(
    event: LiquiditySweepReversalEvent,
    *,
    config: LiquiditySweepReversalRiskExitConfig | None = None,
) -> LiquiditySweepReversalRiskExitPlan:
    planner_config = config or LiquiditySweepReversalRiskExitConfig()
    direction = _risk_direction(event.direction)
    atr = _event_atr(event)
    risk_config = RiskExitConfig(
        atr_buffer_multiplier=planner_config.stop_buffer_atr_multiplier,
        r_multiples=(planner_config.target_r_multiple,),
        minimum_first_target_r=planner_config.min_gross_rr,
        break_even=planner_config.break_even,
        trailing_stop=planner_config.trailing_stop,
        partial_exits=(),
    )
    risk_plan = create_risk_exit_plan(
        direction=direction,
        entry_price=event.entry_reference,
        structural_stop=event.stop_reference,
        atr=atr,
        config=risk_config,
        detector_target_reference=event.target_reference,
        atr_metadata={
            **(event.atr_metadata or {}),
            "liquidity_sweep_reversal_stop": {
                "schema_version": "liquidity_sweep_reversal_stop_v1",
                "stop_source": "SWEEP_EXTREME_ATR_BUFFER",
                "sweep_extreme_price": event.sweep_extreme_price,
                "structural_stop": event.stop_reference,
                "stop_buffer_atr_multiplier": planner_config.stop_buffer_atr_multiplier,
                "target_source": event.target_source,
                "target_reference": event.target_reference,
                "no_lookahead": True,
            },
        },
    )
    return LiquiditySweepReversalRiskExitPlan(
        event_id=event.event_id,
        risk_plan=risk_plan,
        structural_stop_source="SWEEP_EXTREME_ATR_BUFFER",
        target_source=event.target_source,
        target_reference=event.target_reference,
        stop_metadata={
            "schema_version": "liquidity_sweep_reversal_stop_v1",
            "direction": direction.value,
            "sweep_extreme_price": event.sweep_extreme_price,
            "entry_reference": event.entry_reference,
            "target_reference": event.target_reference,
            "risk_reward": event.risk_reward,
        },
    )


def _risk_direction(direction: str) -> RiskExitDirection:
    normalized = str(direction).upper()
    if normalized == LiquiditySweepDirection.BULLISH.value:
        return RiskExitDirection.LONG
    if normalized == LiquiditySweepDirection.BEARISH.value:
        return RiskExitDirection.SHORT
    raise ValueError("Liquidity Sweep Reversal direction must be BULLISH or BEARISH")


def _event_atr(event: LiquiditySweepReversalEvent) -> float | None:
    distance = _optional_float(event.sweep_distance)
    distance_atr = _optional_float(event.sweep_distance_atr)
    if distance is None or distance_atr is None or distance_atr <= 0:
        metadata_atr = _optional_float((event.atr_metadata or {}).get("atr"))
        return metadata_atr
    return distance / distance_atr


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
