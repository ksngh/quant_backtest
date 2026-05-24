from __future__ import annotations

from math import isfinite
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
from quant_bitcoin.risk.exit_plan import (
    RiskExitDirection,
    RiskExitPlan,
    RiskExitPlanStatus,
    RiskExitTarget,
    RiskExitTargetSource,
)
from quant_bitcoin.risk.exit_simulation import (
    PatternExitEvent,
    PatternExitReason,
    SoftInvalidationRule,
    simulate_pattern_exit,
)
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType, StrategyQuantityMode

_UNSET = object()


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

    aligned_risk_plan = _align_risk_plan_to_fill_price(risk_plan, entry.fill_price)
    aligned_status = getattr(aligned_risk_plan, "status", None)
    if aligned_status != RiskExitPlanStatus.VALID:
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason="RISK_PLAN_INVALID_AFTER_FILL",
                metadata={
                    **event_metadata,
                    "entry_status": entry.status.value,
                    "fill_price": entry.fill_price,
                    "fill_timestamp": entry.fill_timestamp,
                    "fill_candle_index": entry.fill_candle_index,
                    "bars_waited": entry.bars_waited,
                    "risk_plan_status": _status_value(aligned_status),
                    "risk_plan_reasons": tuple(getattr(aligned_risk_plan, "reasons", ()) or ()),
                    "risk_plan_aligned_to_fill": True,
                },
            )
        ]

    event_metadata = _metadata_with_aligned_risk_plan(event_metadata, risk_plan, aligned_risk_plan)
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
        aligned_risk_plan,
        frame.iloc[start:],
        soft_invalidation=soft_invalidation,
        intrabar_policy_config=intrabar_policy_config,
    )
    for exit_event in simulation.events:
        actions.append(_to_exit_action(exit_event, aligned_risk_plan, side, event_metadata))
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


def _align_risk_plan_to_fill_price(risk_plan: RiskExitPlan, fill_price: float | int | None) -> RiskExitPlan:
    fill = _positive_float(fill_price)
    if fill is None:
        return _risk_plan_copy(
            risk_plan,
            status=RiskExitPlanStatus.INVALID,
            reasons=("fill_price must be a finite positive number",),
            targets=(),
        )
    try:
        direction = _coerce_direction(risk_plan.direction)
    except ValueError:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            status=RiskExitPlanStatus.INVALID,
            reasons=("direction must be LONG or SHORT",),
            targets=(),
        )

    stop_reference = _positive_float(risk_plan.structural_stop)
    atr_value = _non_negative_float(risk_plan.atr)
    if stop_reference is None or atr_value is None:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            status=RiskExitPlanStatus.INVALID,
            reasons=("structural_stop and atr are required to align risk plan to fill price",),
            targets=(),
        )

    atr_buffer_multiplier = float(risk_plan.atr_buffer_multiplier)
    atr_buffer = atr_value * atr_buffer_multiplier
    if direction == RiskExitDirection.LONG:
        stop_price = stop_reference - atr_buffer
        risk_per_unit = fill - stop_price
    else:
        stop_price = stop_reference + atr_buffer
        risk_per_unit = stop_price - fill

    reasons: list[str] = []
    if stop_price <= 0 or not isfinite(stop_price):
        reasons.append("stop_price must be a finite positive number after fill alignment")
    if risk_per_unit <= 0 or not isfinite(risk_per_unit):
        reasons.append("risk_per_unit must be positive after fill alignment")
    if reasons:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            atr_buffer=atr_buffer,
            stop_price=stop_price,
            risk_per_unit=risk_per_unit,
            status=RiskExitPlanStatus.INVALID,
            reasons=tuple(reasons),
            targets=(),
        )

    targets = _aligned_targets(risk_plan, direction, fill, risk_per_unit)
    if not targets:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            atr_buffer=atr_buffer,
            stop_price=stop_price,
            risk_per_unit=risk_per_unit,
            status=RiskExitPlanStatus.INVALID,
            reasons=("at least one actionable target is required after fill alignment",),
            targets=(),
        )

    first_target_r = targets[0].r_multiple
    if first_target_r is not None and first_target_r < risk_plan.minimum_first_target_r:
        return _risk_plan_copy(
            risk_plan,
            entry_price=fill,
            atr_buffer=atr_buffer,
            stop_price=stop_price,
            risk_per_unit=risk_per_unit,
            status=RiskExitPlanStatus.SKIPPED,
            reasons=(
                "first actionable target is below minimum_first_target_r "
                f"({first_target_r} < {risk_plan.minimum_first_target_r}) after fill alignment",
            ),
            targets=targets,
        )

    return _risk_plan_copy(
        risk_plan,
        entry_price=fill,
        atr_buffer=atr_buffer,
        stop_price=stop_price,
        risk_per_unit=risk_per_unit,
        status=RiskExitPlanStatus.VALID,
        reasons=(),
        targets=targets,
    )


def _aligned_targets(
    risk_plan: RiskExitPlan,
    direction: RiskExitDirection,
    entry_price: float,
    risk_per_unit: float,
) -> tuple[RiskExitTarget, ...]:
    r_multiples = []
    candidates: list[RiskExitTarget] = []

    for target in risk_plan.targets:
        source = _coerce_target_source(target.source)
        if source == RiskExitTargetSource.R_MULTIPLE and target.r_multiple is not None:
            r_multiples.append(float(target.r_multiple))
            continue

        target_price = _positive_float(target.price)
        if target_price is None or not _is_actionable_target(direction, entry_price, target_price):
            continue
        r_multiple = _target_r_multiple(direction, entry_price, target_price, risk_per_unit)
        if r_multiple < risk_plan.minimum_first_target_r:
            continue
        candidates.append(
            RiskExitTarget(
                name=target.name,
                price=target_price,
                source=source,
                r_multiple=r_multiple,
                metadata={**dict(target.metadata), "fill_adjusted": True},
            )
        )

    if not r_multiples:
        r_multiples = [float(target.r_multiple) for target in risk_plan.targets if target.r_multiple is not None]
    if not r_multiples:
        r_multiples = [1.0, 2.0, 3.0]

    for multiple in dict.fromkeys(r_multiples):
        price = entry_price + (risk_per_unit * multiple) if direction == RiskExitDirection.LONG else entry_price - (risk_per_unit * multiple)
        candidates.append(
            RiskExitTarget(
                name="TP",
                price=price,
                source=RiskExitTargetSource.R_MULTIPLE,
                r_multiple=multiple,
                metadata={"rule": "r_multiple", "fill_adjusted": True},
            )
        )

    candidates.sort(key=lambda target: target.price, reverse=direction == RiskExitDirection.SHORT)
    return tuple(
        RiskExitTarget(
            name=f"TP{index}",
            price=target.price,
            source=target.source,
            r_multiple=target.r_multiple,
            metadata=dict(target.metadata),
        )
        for index, target in enumerate(candidates, start=1)
        if _is_actionable_target(direction, entry_price, target.price)
    )


def _risk_plan_copy(
    risk_plan: RiskExitPlan,
    *,
    entry_price: float | None | object = _UNSET,
    atr_buffer: float | None | object = _UNSET,
    stop_price: float | None | object = _UNSET,
    risk_per_unit: float | None | object = _UNSET,
    targets: tuple[RiskExitTarget, ...] | object = _UNSET,
    status: RiskExitPlanStatus | object = _UNSET,
    reasons: tuple[str, ...] | object = _UNSET,
) -> RiskExitPlan:
    return RiskExitPlan(
        direction=risk_plan.direction,
        entry_price=risk_plan.entry_price if entry_price is _UNSET else entry_price,
        structural_stop=risk_plan.structural_stop,
        atr=risk_plan.atr,
        atr_buffer_multiplier=risk_plan.atr_buffer_multiplier,
        atr_buffer=risk_plan.atr_buffer if atr_buffer is _UNSET else atr_buffer,
        stop_price=risk_plan.stop_price if stop_price is _UNSET else stop_price,
        risk_per_unit=risk_plan.risk_per_unit if risk_per_unit is _UNSET else risk_per_unit,
        targets=risk_plan.targets if targets is _UNSET else targets,
        status=risk_plan.status if status is _UNSET else status,
        reasons=risk_plan.reasons if reasons is _UNSET else reasons,
        minimum_first_target_r=risk_plan.minimum_first_target_r,
        time_stop=risk_plan.time_stop,
        break_even=risk_plan.break_even,
        trailing_stop=risk_plan.trailing_stop,
        partial_exits=risk_plan.partial_exits,
    )


def _metadata_with_aligned_risk_plan(
    metadata: dict[str, Any],
    original_plan: RiskExitPlan,
    aligned_plan: RiskExitPlan,
) -> dict[str, Any]:
    aligned = not _same_number(original_plan.entry_price, aligned_plan.entry_price)
    return {
        **metadata,
        "entry_price": aligned_plan.entry_price,
        "entry_reference": original_plan.entry_price,
        "risk_per_unit": aligned_plan.risk_per_unit,
        "original_risk_plan_entry_price": original_plan.entry_price,
        "original_risk_per_unit": original_plan.risk_per_unit,
        "fill_adjusted_risk_plan_entry_price": aligned_plan.entry_price,
        "fill_adjusted_risk_per_unit": aligned_plan.risk_per_unit,
        "risk_plan_aligned_to_fill": aligned,
    }


def _target_r_multiple(
    direction: RiskExitDirection,
    entry_price: float,
    target_price: float,
    risk_per_unit: float,
) -> float:
    if direction == RiskExitDirection.LONG:
        return (target_price - entry_price) / risk_per_unit
    return (entry_price - target_price) / risk_per_unit


def _is_actionable_target(direction: RiskExitDirection, entry_price: float, target_price: float) -> bool:
    if direction == RiskExitDirection.LONG:
        return target_price > entry_price
    return target_price < entry_price


def _coerce_target_source(source: RiskExitTargetSource | str) -> RiskExitTargetSource:
    if isinstance(source, RiskExitTargetSource):
        return source
    return RiskExitTargetSource(str(source).split(".")[-1].upper())


def _positive_float(value: float | int | None) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(result) or result <= 0:
        return None
    return result


def _non_negative_float(value: float | int | None) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(result) or result < 0:
        return None
    return result


def _same_number(left: float | int | None, right: float | int | None) -> bool:
    try:
        return abs(float(left) - float(right)) < 1e-12
    except (TypeError, ValueError):
        return left == right


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
