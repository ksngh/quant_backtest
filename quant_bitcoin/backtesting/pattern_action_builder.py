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
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType, StrategyQuantityMode


def build_pattern_trade_actions(
    event: Any,
    risk_plan: RiskExitPlan,
    future_candles: pd.DataFrame | list[dict[str, Any]],
    *,
    entry_action_timestamp: Any | None = None,
    confirmation_candle: dict[str, Any] | pd.Series | None = None,
    position_side: str,
    entry_quantity: float | None = None,
    soft_invalidation: SoftInvalidationRule | None = None,
    entry_config: PatternEntryConfig | None = None,
    entry_mode: PatternEntryMode = PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
    intrabar_policy_config: IntrabarPolicyConfig | None = None,
    max_wait_bars: int | None = None,
) -> list[StrategyAction]:
    side = str(position_side).upper()
    if side not in {"LONG", "SHORT"}:
        raise ValueError("position_side must be LONG or SHORT")

    risk_plan_status = getattr(risk_plan, "status", None)
    if risk_plan_status != RiskExitPlanStatus.VALID:
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason="RISK_PLAN_INVALID",
                metadata={
                    "pattern_event_id": getattr(event, "event_id", None),
                    "pattern_type": getattr(event, "pattern_type", None),
                    "position_side": side,
                    "risk_plan_status": _status_value(risk_plan_status),
                    "risk_plan_reasons": tuple(getattr(risk_plan, "reasons", ()) or ()),
                    **_score_metadata_from_event(event),
                },
            )
        ]

    frame = future_candles.copy(deep=False) if isinstance(future_candles, pd.DataFrame) else pd.DataFrame(future_candles)
    if "open" not in frame.columns and "close" in frame.columns:
        frame["open"] = frame["close"]
    for col in ("timestamp", "open", "high", "low", "close"):
        if col not in frame.columns:
            frame[col] = pd.Series(dtype="float64") if col != "timestamp" else pd.Series(dtype="object")
    frame = frame[["timestamp", "open", "high", "low", "close"]]
    if confirmation_candle is None:
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
        "entry_reference": risk_plan.entry_price,
        "risk_per_unit": risk_plan.risk_per_unit,
        "entry_mode": plan.mode.value,
        "fill_assumption": _fill_assumption(plan.mode),
        "fill_price_source": _fill_price_source(plan.mode),
        "confirmation_close": _candle_value(confirmation_candle, "close"),
        "entry_quantity_source": "ACTION_OVERRIDE" if entry_quantity is not None else "ENGINE_CONFIG",
        "engine_sizing_allowed": entry_quantity is None,
        **_score_metadata_from_event(event),
    }
    if entry_quantity is not None:
        event_metadata["raw_action_quantity"] = entry_quantity
        event_metadata["pattern_quantity_override"] = entry_quantity
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
            quantity=entry_quantity,
            reason="PATTERN_CONFIRMED",
            metadata={**event_metadata, "fill_price": entry.fill_price, "fill_timestamp": entry.fill_timestamp, "fill_candle_index": entry.fill_candle_index, "bars_waited": entry.bars_waited, "intrabar_policy": intrabar_policy_config.mode.value if intrabar_policy_config else "CONSERVATIVE"},
            requested_price=entry.fill_price,
        )
    ]

    start = 0 if entry.fill_candle_index is None else entry.fill_candle_index
    simulation = simulate_pattern_exit(
        risk_plan,
        frame.iloc[start:],
        soft_invalidation=soft_invalidation,
        intrabar_policy_config=intrabar_policy_config,
    )
    for exit_event in simulation.events:
        actions.append(_to_exit_action(exit_event, risk_plan, side, event_metadata))
    return actions


def _to_exit_action(exit_event: PatternExitEvent, risk_plan: RiskExitPlan, position_side: str, base_metadata: dict[str, Any]) -> StrategyAction:
    final_exit = exit_event.remaining_quantity_ratio <= 0
    action_type = StrategyActionType.EXIT_LONG if (position_side == "LONG" and final_exit) else StrategyActionType.PARTIAL_EXIT_LONG if position_side == "LONG" else StrategyActionType.EXIT_SHORT if final_exit else StrategyActionType.PARTIAL_EXIT_SHORT
    action_quantity_ratio = 1.0 if final_exit else exit_event.quantity_ratio
    metadata = {**base_metadata, "exit_reason": exit_event.reason.value, "target_name": exit_event.target_name, "stop_price": exit_event.stop_price, "exit_price": exit_event.price, "quantity_ratio": exit_event.quantity_ratio, "action_quantity_ratio": action_quantity_ratio, "remaining_quantity_ratio": exit_event.remaining_quantity_ratio, "quantity_mode": StrategyQuantityMode.POSITION_RATIO.value}
    realized_r = _realized_r_multiple(exit_event, risk_plan)
    if realized_r is not None:
        metadata["realized_r_multiple"] = realized_r
    if exit_event.metadata:
        metadata["exit_metadata"] = dict(exit_event.metadata)
    return StrategyAction(action_type=action_type, timestamp=exit_event.timestamp, quantity=action_quantity_ratio, reason=exit_event.reason.value, metadata=metadata, requested_price=exit_event.price, quantity_mode=StrategyQuantityMode.POSITION_RATIO)


def _realized_r_multiple(exit_event: PatternExitEvent, risk_plan: RiskExitPlan) -> float | None:
    if risk_plan.entry_price is None or risk_plan.risk_per_unit is None or risk_plan.risk_per_unit <= 0:
        return None
    direction = _coerce_direction(risk_plan.direction)
    raw_r = (exit_event.price - risk_plan.entry_price) / risk_plan.risk_per_unit if direction == RiskExitDirection.LONG else (risk_plan.entry_price - exit_event.price) / risk_plan.risk_per_unit
    return round(raw_r, 10)


def _score_metadata_from_event(event: Any) -> dict[str, Any]:
    return {
        "score_components": getattr(event, "score_components", {}),
        "score_component_sources": getattr(event, "score_component_sources", {}),
        "score_limitations": getattr(event, "score_limitations", ()),
        "score_calibration": getattr(event, "score_calibration", {}),
    }


def _fill_assumption(mode: PatternEntryMode) -> str:
    if mode in (PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, PatternEntryMode.MARKET_ON_NEXT_OPEN):
        return "MARKET"
    return "REFERENCE_LIMIT"


def _fill_price_source(mode: PatternEntryMode) -> str:
    if mode == PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE:
        return "CONFIRMATION_CLOSE"
    if mode == PatternEntryMode.MARKET_ON_NEXT_OPEN:
        return "NEXT_OPEN"
    if mode == PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE:
        return "ENTRY_REFERENCE"
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT:
        return "PATTERN_MIDPOINT"
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY:
        return "PATTERN_BOUNDARY"
    return "CUSTOM_PRICE"


def _candle_value(candle: dict[str, Any] | pd.Series, name: str) -> Any:
    return candle.get(name) if isinstance(candle, dict) else candle[name]


def _status_value(status: Any) -> str | None:
    if status is None:
        return None
    return str(status.value if hasattr(status, "value") else status)


def _coerce_direction(direction: RiskExitDirection | str) -> RiskExitDirection:
    if isinstance(direction, RiskExitDirection):
        return direction
    return RiskExitDirection(str(direction).upper())
