from __future__ import annotations

from typing import Any

import pandas as pd

from quant_bitcoin.risk.exit_plan import RiskExitDirection, RiskExitPlan, RiskExitPlanStatus
from quant_bitcoin.risk.exit_simulation import (
    PatternExitEvent,
    PatternExitReason,
    SoftInvalidationRule,
    simulate_pattern_exit,
)
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def build_pattern_trade_actions(
    event: Any,
    risk_plan: RiskExitPlan,
    future_candles: pd.DataFrame | list[dict[str, Any]],
    *,
    entry_action_timestamp: Any,
    position_side: str,
    soft_invalidation: SoftInvalidationRule | None = None,
) -> list[StrategyAction]:
    """Build canonical strategy actions from pattern event + risk/exit plan.

    Initial quantity semantics use ratio-based quantities from exit simulation.
    Caller-side orchestration may scale these ratios to absolute quantity.
    """

    side = str(position_side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("position_side must be LONG or SHORT")

    event_metadata = {
        "pattern_event_id": getattr(event, "event_id", None),
        "pattern_type": getattr(event, "pattern_type", None),
        "entry_price": risk_plan.entry_price,
        "risk_per_unit": risk_plan.risk_per_unit,
    }

    entry_action_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT
    actions: list[StrategyAction] = [
        StrategyAction(
            action_type=entry_action_type,
            timestamp=entry_action_timestamp,
            quantity=1.0,
            reason="PATTERN_CONFIRMED",
            metadata=event_metadata,
        )
    ]

    if risk_plan.status != RiskExitPlanStatus.VALID:
        actions[0] = StrategyAction(
            action_type=entry_action_type,
            timestamp=entry_action_timestamp,
            quantity=1.0,
            reason="RISK_PLAN_INVALID",
            metadata={**event_metadata, "risk_plan_status": str(risk_plan.status)},
        )
        return actions

    simulation = simulate_pattern_exit(risk_plan, future_candles, soft_invalidation=soft_invalidation)
    for exit_event in simulation.events:
        actions.append(_to_exit_action(exit_event, risk_plan, side, event_metadata))
    return actions


def _to_exit_action(
    exit_event: PatternExitEvent,
    risk_plan: RiskExitPlan,
    position_side: str,
    base_metadata: dict[str, Any],
) -> StrategyAction:
    final_exit = exit_event.remaining_quantity_ratio <= 0
    if position_side == "LONG":
        action_type = StrategyActionType.EXIT_LONG if final_exit else StrategyActionType.PARTIAL_EXIT_LONG
    else:
        action_type = StrategyActionType.EXIT_SHORT if final_exit else StrategyActionType.PARTIAL_EXIT_SHORT

    metadata = {
        **base_metadata,
        "exit_reason": exit_event.reason.value,
        "target_name": exit_event.target_name,
        "stop_price": exit_event.stop_price,
        "exit_price": exit_event.price,
        "quantity_ratio": exit_event.quantity_ratio,
        "remaining_quantity_ratio": exit_event.remaining_quantity_ratio,
    }
    realized_r = _realized_r_multiple(exit_event, risk_plan)
    if realized_r is not None:
        metadata["realized_r_multiple"] = realized_r
    if exit_event.metadata:
        metadata["exit_metadata"] = dict(exit_event.metadata)

    return StrategyAction(
        action_type=action_type,
        timestamp=exit_event.timestamp,
        quantity=exit_event.quantity_ratio,
        reason=exit_event.reason.value,
        metadata=metadata,
    )


def _realized_r_multiple(exit_event: PatternExitEvent, risk_plan: RiskExitPlan) -> float | None:
    if risk_plan.entry_price is None or risk_plan.risk_per_unit is None or risk_plan.risk_per_unit <= 0:
        return None
    direction = _coerce_direction(risk_plan.direction)
    if direction == RiskExitDirection.LONG:
        raw_r = (exit_event.price - risk_plan.entry_price) / risk_plan.risk_per_unit
    else:
        raw_r = (risk_plan.entry_price - exit_event.price) / risk_plan.risk_per_unit
    return round(raw_r, 10)


def _coerce_direction(direction: RiskExitDirection | str) -> RiskExitDirection:
    if isinstance(direction, RiskExitDirection):
        return direction
    return RiskExitDirection(str(direction).upper())
