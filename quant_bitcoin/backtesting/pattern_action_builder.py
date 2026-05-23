from __future__ import annotations

from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.intrabar_policy import IntrabarPolicyConfig, detect_intrabar_touches, resolve_intrabar_decision
from quant_bitcoin.patterns.entry_simulation import (
    PatternEntryConfig,
    PatternEntryMode,
    PatternEntryStatus,
    create_entry_plan_from_event,
    simulate_pattern_entry,
)
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
    entry_action_timestamp: Any | None = None,
    position_side: str,
    soft_invalidation: SoftInvalidationRule | None = None,
    entry_config: PatternEntryConfig | None = None,
    entry_mode: PatternEntryMode = PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
    intrabar_policy_config: IntrabarPolicyConfig | None = None,
    max_wait_bars: int | None = None,
) -> list[StrategyAction]:
    side = str(position_side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("position_side must be LONG or SHORT")

    frame = future_candles.copy(deep=False) if isinstance(future_candles, pd.DataFrame) else pd.DataFrame(future_candles)
    if "open" not in frame.columns and "close" in frame.columns:
        frame["open"] = frame["close"]
    for col in ("timestamp", "open", "high", "low", "close"):
        if col not in frame.columns:
            frame[col] = pd.Series(dtype="float64") if col != "timestamp" else pd.Series(dtype="object")
    frame = frame[["timestamp", "open", "high", "low", "close"]]
    confirmation_candle = {
        "timestamp": entry_action_timestamp,
        "open": risk_plan.entry_price,
        "high": risk_plan.entry_price,
        "low": risk_plan.entry_price,
        "close": risk_plan.entry_price,
    }
    plan = create_entry_plan_from_event(
        event,
        entry_mode,
        side,
        max_wait_bars=max_wait_bars if max_wait_bars is not None else (entry_config.max_wait_bars if entry_config else None),
    )
    if entry_config is not None:
        plan = plan.__class__(**{**plan.__dict__, "config": entry_config})
    entry = simulate_pattern_entry(plan, confirmation_candle, frame)

    event_metadata = {
        "pattern_event_id": getattr(event, "event_id", None),
        "pattern_type": getattr(event, "pattern_type", None),
        "entry_price": risk_plan.entry_price,
        "risk_per_unit": risk_plan.risk_per_unit,
        "entry_mode": plan.mode.value,
    }
    entry_action_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT

    if entry.status != PatternEntryStatus.FILLED:
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason="ENTRY_NOT_FILLED",
                metadata={**event_metadata, "entry_status": entry.status.value, "bars_waited": entry.bars_waited, "reason": entry.reason},
            )
        ]

    actions: list[StrategyAction] = [
        StrategyAction(
            action_type=entry_action_type,
            timestamp=entry.fill_timestamp,
            quantity=1.0,
            reason="PATTERN_CONFIRMED",
            metadata={**event_metadata, "fill_price": entry.fill_price, "fill_timestamp": entry.fill_timestamp, "fill_candle_index": entry.fill_candle_index, "intrabar_policy": intrabar_policy_config.mode.value if intrabar_policy_config else "CONSERVATIVE"},
            requested_price=entry.fill_price,
        )
    ]

    if risk_plan.status != RiskExitPlanStatus.VALID:
        actions[0] = StrategyAction(action_type=entry_action_type, timestamp=entry.fill_timestamp, quantity=1.0, reason="RISK_PLAN_INVALID", metadata={**event_metadata, "risk_plan_status": str(risk_plan.status)})
        return actions

    start = 0 if entry.fill_candle_index is None else entry.fill_candle_index
    simulation = simulate_pattern_exit(risk_plan, frame.iloc[start:], soft_invalidation=soft_invalidation)
    for exit_event in simulation.events:
        actions.append(_to_exit_action(exit_event, risk_plan, side, event_metadata))
    return actions


def _to_exit_action(exit_event: PatternExitEvent, risk_plan: RiskExitPlan, position_side: str, base_metadata: dict[str, Any]) -> StrategyAction:
    final_exit = exit_event.remaining_quantity_ratio <= 0
    action_type = StrategyActionType.EXIT_LONG if (position_side == "LONG" and final_exit) else StrategyActionType.PARTIAL_EXIT_LONG if position_side == "LONG" else StrategyActionType.EXIT_SHORT if final_exit else StrategyActionType.PARTIAL_EXIT_SHORT
    metadata = {**base_metadata, "exit_reason": exit_event.reason.value, "target_name": exit_event.target_name, "stop_price": exit_event.stop_price, "exit_price": exit_event.price, "quantity_ratio": exit_event.quantity_ratio, "remaining_quantity_ratio": exit_event.remaining_quantity_ratio}
    realized_r = _realized_r_multiple(exit_event, risk_plan)
    if realized_r is not None:
        metadata["realized_r_multiple"] = realized_r
    if exit_event.metadata:
        metadata["exit_metadata"] = dict(exit_event.metadata)
    return StrategyAction(action_type=action_type, timestamp=exit_event.timestamp, quantity=exit_event.quantity_ratio, reason=exit_event.reason.value, metadata=metadata, requested_price=exit_event.price)


def _realized_r_multiple(exit_event: PatternExitEvent, risk_plan: RiskExitPlan) -> float | None:
    if risk_plan.entry_price is None or risk_plan.risk_per_unit is None or risk_plan.risk_per_unit <= 0:
        return None
    direction = _coerce_direction(risk_plan.direction)
    raw_r = (exit_event.price - risk_plan.entry_price) / risk_plan.risk_per_unit if direction == RiskExitDirection.LONG else (risk_plan.entry_price - exit_event.price) / risk_plan.risk_per_unit
    return round(raw_r, 10)


def _coerce_direction(direction: RiskExitDirection | str) -> RiskExitDirection:
    if isinstance(direction, RiskExitDirection):
        return direction
    return RiskExitDirection(str(direction).upper())
