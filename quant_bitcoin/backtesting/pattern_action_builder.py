from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.costs import (
    LiquidityRole,
    TransactionCostConfig,
    effective_slippage_bps,
    is_zero_transaction_cost_config,
)
from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES
from quant_bitcoin.backtesting.intrabar_policy import IntrabarPolicyConfig, detect_intrabar_touches, resolve_intrabar_decision
from quant_bitcoin.backtesting.pattern_invalidation import (
    PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION,
    pattern_soft_invalidation_for_event,
)
from quant_bitcoin.backtesting.sizing import SizingRiskSource
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
    target_semantics_metadata,
)
from quant_bitcoin.risk.exit_simulation import (
    PatternExitEvent,
    PatternExitReason,
    SoftInvalidationRule,
    simulate_pattern_exit,
)
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType, StrategyQuantityMode

_UNSET = object()
PATTERN_EXECUTION_PATH_CANONICAL_FILL_AWARE = "CANONICAL_FILL_AWARE_ACTION_BUILDER"


@dataclass(frozen=True)
class CostAwareEntryFilterConfig:
    enabled: bool = False
    min_net_reward_bps: float = 20.0
    min_net_rr: float = 1.5
    transaction_cost_config: TransactionCostConfig | None = None
    liquidity_role: LiquidityRole = LiquidityRole.TAKER
    cost_profile_name: str | None = None


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
    entry_custom_price: float | None = None,
    intrabar_policy_config: IntrabarPolicyConfig | None = None,
    max_wait_bars: int | None = None,
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
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
                    **_pattern_event_metadata(event, side, risk_plan),
                    "risk_plan_status": _status_value(risk_plan_status),
                    "risk_plan_reasons": tuple(getattr(risk_plan, "reasons", ()) or ()),
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
        custom_price=entry_custom_price,
        max_wait_bars=max_wait_bars if max_wait_bars is not None else (entry_config.max_wait_bars if entry_config else None),
    )
    if entry_config is not None:
        plan = plan.__class__(**{**plan.__dict__, "config": entry_config})
    entry = simulate_pattern_entry(plan, confirmation_candle, frame)

    event_metadata = {
        **_pattern_event_metadata(event, side, risk_plan),
        "entry_price": risk_plan.entry_price,
        "entry_reference": risk_plan.entry_price,
        "risk_per_unit": risk_plan.risk_per_unit,
        "entry_mode": plan.mode.value,
        "entry_trigger": entry.entry_trigger,
        "fill_assumption": _fill_assumption(plan.mode),
        "fill_price_source": _fill_price_source(plan.mode),
        "confirmation_close": _candle_value(confirmation_candle, "close"),
        "entry_custom_price": entry_custom_price,
        "entry_quantity_source": "ACTION_OVERRIDE" if entry_quantity is not None else "ENGINE_CONFIG",
        "engine_sizing_allowed": entry_quantity is None,
        "sizing_risk_source": (
            SizingRiskSource.ACTION_OVERRIDE.value
            if entry_quantity is not None
            else SizingRiskSource.ORIGINAL_REFERENCE.value
        ),
    }
    entry_policy = _entry_policy_metadata(
        event=event,
        plan=plan,
        entry=entry,
        entry_reference=risk_plan.entry_price,
        requested_price=entry.fill_price,
        confirmation_close=_candle_value(confirmation_candle, "close"),
        fill_assumption=event_metadata["fill_assumption"],
        fill_price_source=event_metadata["fill_price_source"],
    )
    event_metadata["pattern_entry_policy"] = entry_policy
    event_metadata["pattern_entry_policy_schema_version"] = "pattern_entry_policy_v1"
    if entry_quantity is not None:
        event_metadata["raw_action_quantity"] = entry_quantity
        event_metadata["pattern_quantity_override"] = entry_quantity
    entry_action_type = StrategyActionType.ENTER_LONG if side == "LONG" else StrategyActionType.ENTER_SHORT

    if entry.status != PatternEntryStatus.FILLED:
        skip_reason = "ENTRY_MODE_INVALID" if entry.status == PatternEntryStatus.INVALID else "ENTRY_NOT_FILLED"
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason=skip_reason,
            metadata={
                **event_metadata,
                "entry_status": entry.status.value,
                "bars_waited": entry.bars_waited,
                "reason": entry.reason,
                "touch_timestamp": entry.touch_timestamp,
                "touch_candle_index": entry.touch_candle_index,
                "reaction_timestamp": entry.reaction_timestamp,
                "reaction_candle_index": entry.reaction_candle_index,
            },
            )
        ]

    aligned_risk_plan = _align_risk_plan_to_fill_price(risk_plan, entry.fill_price)
    aligned_status = getattr(aligned_risk_plan, "status", None)
    if aligned_status != RiskExitPlanStatus.VALID:
        invalid_metadata = _metadata_with_aligned_risk_plan(event_metadata, risk_plan, aligned_risk_plan)
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry_action_timestamp,
                quantity=0.0,
                reason="RISK_PLAN_INVALID_AFTER_FILL",
                metadata={
                    **invalid_metadata,
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

    cost_filter = _cost_aware_entry_filter_decision(
        aligned_risk_plan,
        frame,
        entry.fill_candle_index,
        cost_aware_entry_filter_config,
    )
    if cost_filter:
        event_metadata["cost_aware_entry_filter"] = cost_filter
        if cost_filter.get("blocked"):
            return [
                StrategyAction(
                    action_type=StrategyActionType.SKIP,
                    timestamp=entry.fill_timestamp,
                    quantity=0.0,
                    reason="COST_INFEASIBLE_NET_RR",
                    metadata={
                        **_metadata_with_aligned_risk_plan(event_metadata, risk_plan, aligned_risk_plan),
                        "entry_status": entry.status.value,
                        "fill_price": entry.fill_price,
                        "fill_timestamp": entry.fill_timestamp,
                        "fill_candle_index": entry.fill_candle_index,
                        "bars_waited": entry.bars_waited,
                        "cost_aware_entry_filter": cost_filter,
                    },
                )
            ]

    active_soft_invalidation, pattern_soft_invalidation_metadata = _resolve_pattern_soft_invalidation(
        event,
        aligned_risk_plan,
        soft_invalidation,
    )
    event_metadata["pattern_soft_invalidation"] = pattern_soft_invalidation_metadata
    event_metadata["pattern_soft_invalidation_schema_version"] = PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION

    entry_filled_on_first_candle = _entry_fill_is_first_future_candle(frame, entry.fill_candle_index, entry.fill_timestamp)
    combined_decision_metadata = _combined_entry_exit_metadata(
        aligned_risk_plan,
        frame,
        entry.fill_candle_index,
        intrabar_policy_config,
        entry_filled_on_first_candle=entry_filled_on_first_candle,
    )
    if combined_decision_metadata.get("skipped"):
        skip_metadata = {
            **event_metadata,
            **_metadata_with_aligned_risk_plan(event_metadata, risk_plan, aligned_risk_plan),
            "entry_status": entry.status.value,
            "fill_price": entry.fill_price,
            "fill_timestamp": entry.fill_timestamp,
            "fill_candle_index": entry.fill_candle_index,
            "bars_waited": entry.bars_waited,
            "intrabar_policy": intrabar_policy_config.mode.value if intrabar_policy_config else "CONSERVATIVE",
            "combined_intrabar_decision": combined_decision_metadata,
        }
        return [
            StrategyAction(
                action_type=StrategyActionType.SKIP,
                timestamp=entry.fill_timestamp,
                quantity=0.0,
                reason="ENTRY_EXIT_AMBIGUOUS",
                metadata=skip_metadata,
            )
        ]

    event_metadata = _metadata_with_aligned_risk_plan(event_metadata, risk_plan, aligned_risk_plan)
    if combined_decision_metadata:
        event_metadata["combined_intrabar_decision"] = combined_decision_metadata
    actions: list[StrategyAction] = [
        StrategyAction(
            action_type=entry_action_type,
            timestamp=entry.fill_timestamp,
            quantity=entry_quantity,
            reason="PATTERN_CONFIRMED",
            metadata={
                **event_metadata,
                "requested_price": entry.fill_price,
                "fill_price": entry.fill_price,
                "fill_timestamp": entry.fill_timestamp,
                "fill_candle_index": entry.fill_candle_index,
                "bars_waited": entry.bars_waited,
                "touch_timestamp": entry.touch_timestamp,
                "touch_candle_index": entry.touch_candle_index,
                "reaction_timestamp": entry.reaction_timestamp,
                "reaction_candle_index": entry.reaction_candle_index,
                "intrabar_policy": intrabar_policy_config.mode.value if intrabar_policy_config else "CONSERVATIVE",
            },
            requested_price=entry.fill_price,
        )
    ]

    start = 0 if entry.fill_candle_index is None else entry.fill_candle_index
    simulation = simulate_pattern_exit(
        aligned_risk_plan,
        frame.iloc[start:],
        soft_invalidation=active_soft_invalidation,
        intrabar_policy_config=intrabar_policy_config,
        entry_filled_on_first_candle=entry_filled_on_first_candle,
    )
    for exit_event in simulation.events:
        actions.append(_to_exit_action(exit_event, aligned_risk_plan, side, event_metadata))
    return actions


def _cost_aware_entry_filter_decision(
    risk_plan: RiskExitPlan,
    frame: pd.DataFrame,
    fill_candle_index: int | None,
    config: CostAwareEntryFilterConfig | None,
) -> dict[str, Any]:
    if config is None or not config.enabled:
        return {}

    entry_price = _positive_float(risk_plan.entry_price)
    stop_price = _positive_float(risk_plan.stop_price)
    if entry_price is None or stop_price is None or not risk_plan.targets:
        return {
            "schema_version": "cost_aware_entry_filter_v1",
            "enabled": True,
            "blocked": True,
            "block_reason": "COST_FILTER_INVALID_RISK_PLAN",
        }

    direction = _coerce_direction(risk_plan.direction)
    target_price = float(risk_plan.targets[0].price)
    if direction == RiskExitDirection.LONG:
        gross_reward_bps = ((target_price - entry_price) / entry_price) * 10_000.0
        gross_risk_bps = ((entry_price - stop_price) / entry_price) * 10_000.0
    else:
        gross_reward_bps = ((entry_price - target_price) / entry_price) * 10_000.0
        gross_risk_bps = ((stop_price - entry_price) / entry_price) * 10_000.0

    volatility_bps = _entry_candle_volatility_bps(frame, fill_candle_index)
    cost_config = config.transaction_cost_config or TransactionCostConfig()
    fee_bps = cost_config.maker_fee_bps if config.liquidity_role is LiquidityRole.MAKER else cost_config.taker_fee_bps
    slippage_bps = effective_slippage_bps(cost_config, volatility_bps)
    one_side_cost_bps = fee_bps + cost_config.spread_bps + slippage_bps
    round_trip_cost_bps = 2.0 * one_side_cost_bps
    net_reward_bps = gross_reward_bps - round_trip_cost_bps
    net_risk_bps = gross_risk_bps + round_trip_cost_bps
    net_rr = None if net_risk_bps <= 0 else net_reward_bps / net_risk_bps
    blocked = (
        gross_reward_bps <= 0
        or gross_risk_bps <= 0
        or net_reward_bps < config.min_net_reward_bps
        or net_rr is None
        or net_rr < config.min_net_rr
    )
    return {
        "schema_version": "cost_aware_entry_filter_v1",
        "enabled": True,
        "blocked": blocked,
        "block_reason": "COST_INFEASIBLE_NET_RR" if blocked else None,
        "min_net_reward_bps": config.min_net_reward_bps,
        "min_net_rr": config.min_net_rr,
        "gross_reward_bps": gross_reward_bps,
        "gross_risk_bps": gross_risk_bps,
        "estimated_one_side_cost_bps": one_side_cost_bps,
        "estimated_round_trip_cost_bps": round_trip_cost_bps,
        "net_reward_bps": net_reward_bps,
        "net_risk_bps": net_risk_bps,
        "net_rr": net_rr,
        "fee_bps": fee_bps,
        "spread_bps": cost_config.spread_bps,
        "slippage_bps": slippage_bps,
        "effective_slippage_bps": slippage_bps,
        "volatility_bps": volatility_bps,
        "cost_profile_name": config.cost_profile_name or _cost_profile_name(cost_config),
        "liquidity_role": config.liquidity_role.value,
    }


def _entry_candle_volatility_bps(frame: pd.DataFrame, fill_candle_index: int | None) -> float | None:
    if fill_candle_index is None or fill_candle_index < 0 or fill_candle_index >= len(frame):
        return None
    candle = frame.iloc[fill_candle_index]
    high = _positive_float(candle.get("high"))
    low = _positive_float(candle.get("low"))
    close = _positive_float(candle.get("close"))
    if high is None or low is None or close is None:
        return None
    return ((high - low) / close) * 10_000.0


def _cost_profile_name(config: TransactionCostConfig | None) -> str:
    if is_zero_transaction_cost_config(config):
        return "zero"
    for key, profile in COST_PROFILES.items():
        if profile.config == config:
            return key
    return "manual"


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
        if "target_source" in exit_event.metadata:
            metadata["target_source"] = exit_event.metadata["target_source"]
    return StrategyAction(action_type=action_type, timestamp=exit_event.timestamp, quantity=action_quantity_ratio, reason=exit_event.reason.value, metadata=metadata, requested_price=exit_event.price, quantity_mode=StrategyQuantityMode.POSITION_RATIO)


def _resolve_pattern_soft_invalidation(
    event: Any,
    risk_plan: RiskExitPlan,
    explicit_soft_invalidation: SoftInvalidationRule | None,
) -> tuple[SoftInvalidationRule | None, dict[str, Any]]:
    if explicit_soft_invalidation is not None:
        return explicit_soft_invalidation, {
            "schema_version": PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION,
            "enabled": True,
            "supported": True,
            "source": "explicit_soft_invalidation_argument",
            "rule": explicit_soft_invalidation.metadata.get("rule") if explicit_soft_invalidation.metadata else None,
            "invalidates_when": explicit_soft_invalidation.invalidates_when,
            "reference_field": explicit_soft_invalidation.metadata.get("reference_field") if explicit_soft_invalidation.metadata else None,
            "reference_price": explicit_soft_invalidation.reference_price,
            "max_bars_after_entry": explicit_soft_invalidation.max_bars_after_entry,
        }
    adapted = pattern_soft_invalidation_for_event(event, risk_plan)
    return adapted.rule, adapted.metadata


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
            target_semantics=_aligned_target_semantics(risk_plan, direction, fill, risk_per_unit, targets),
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
        target_semantics=_aligned_target_semantics(risk_plan, direction, fill, risk_per_unit, targets),
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
    target_semantics: dict[str, Any] | object = _UNSET,
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
        atr_metadata=risk_plan.atr_metadata,
        target_semantics=risk_plan.target_semantics if target_semantics is _UNSET else target_semantics,
    )


def _metadata_with_aligned_risk_plan(
    metadata: dict[str, Any],
    original_plan: RiskExitPlan,
    aligned_plan: RiskExitPlan,
) -> dict[str, Any]:
    aligned = not _same_number(original_plan.entry_price, aligned_plan.entry_price)
    if metadata.get("entry_quantity_source") == "ACTION_OVERRIDE":
        sizing_risk_source = SizingRiskSource.ACTION_OVERRIDE.value
    elif aligned_plan.risk_per_unit is None or aligned_plan.risk_per_unit <= 0:
        sizing_risk_source = SizingRiskSource.MISSING.value
    else:
        sizing_risk_source = SizingRiskSource.FILL_ADJUSTED.value
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
        "sizing_risk_source": sizing_risk_source,
        "target_semantics": _metadata_target_semantics(metadata, aligned_plan),
    }


def _aligned_target_semantics(
    original_plan: RiskExitPlan,
    direction: RiskExitDirection,
    entry_price: float,
    risk_per_unit: float,
    targets: tuple[RiskExitTarget, ...],
) -> dict[str, Any]:
    original_semantics = dict(getattr(original_plan, "target_semantics", {}) or {})
    return target_semantics_metadata(
        direction=direction,
        entry_price=entry_price,
        risk_per_unit=risk_per_unit,
        detector_target_reference=original_semantics.get("detector_target_reference"),
        r_multiple_targets=tuple(
            target
            for target in targets
            if _coerce_target_source(target.source) == RiskExitTargetSource.R_MULTIPLE
        ),
        structural_targets=_semantic_prices(original_semantics, "structural_targets"),
        measured_targets=_semantic_prices(original_semantics, "measured_targets"),
        risk_targets=targets,
    )


def _metadata_target_semantics(metadata: dict[str, Any], risk_plan: RiskExitPlan) -> dict[str, Any]:
    target_semantics = dict(getattr(risk_plan, "target_semantics", {}) or {})
    if not target_semantics:
        return {}
    if target_semantics.get("detector_target_reference") is None:
        target_semantics["detector_target_reference"] = metadata.get("event_target_reference")
    return target_semantics


def _semantic_prices(target_semantics: dict[str, Any], key: str) -> tuple[float, ...]:
    prices: list[float] = []
    for target in target_semantics.get(key, ()) or ():
        if isinstance(target, dict) and target.get("price") is not None:
            prices.append(float(target["price"]))
    return tuple(prices)


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


def _entry_policy_metadata(
    *,
    event: Any,
    plan: Any,
    entry: Any,
    entry_reference: float | None,
    requested_price: float | None,
    confirmation_close: Any,
    fill_assumption: str,
    fill_price_source: str,
) -> dict[str, Any]:
    return {
        "schema_version": "pattern_entry_policy_v1",
        "pattern_type": getattr(event, "pattern_type", None),
        "entry_mode": plan.mode.value,
        "fill_assumption": fill_assumption,
        "fill_price_source": fill_price_source,
        "entry_trigger": entry.plan.config.entry_trigger.value if hasattr(entry.plan.config.entry_trigger, "value") else str(entry.plan.config.entry_trigger),
        "entry_reference": entry_reference,
        "requested_price": requested_price,
        "confirmation_close": confirmation_close,
        "bars_waited": entry.bars_waited,
        "touch_timestamp": entry.touch_timestamp,
        "touch_candle_index": entry.touch_candle_index,
        "reaction_timestamp": entry.reaction_timestamp,
        "reaction_candle_index": entry.reaction_candle_index,
        "entry_status": entry.status.value,
        "limit_price": plan.limit_price,
        "max_wait_bars": plan.config.max_wait_bars,
        "expire_status": plan.config.expire_status.value,
        "invalid_reason": entry.reason if entry.status == PatternEntryStatus.INVALID else None,
        "supported_modes": _supported_entry_modes(getattr(event, "pattern_type", None)),
        "contract": "requested_price is the simulated fill price used by strategy-engine sizing and costs; entry_reference is research metadata only.",
        "entry_mode_hypothesis": _entry_mode_hypothesis(getattr(event, "pattern_type", None), plan.mode),
        "entry_style": _entry_style(plan.mode),
        "entry_reference_distance": _distance(requested_price, entry_reference),
        "zone_distance": _zone_distance(event, requested_price),
        "zone_boundary_variant": _zone_boundary_variant(plan.mode),
    }


def _combined_entry_exit_metadata(
    risk_plan: RiskExitPlan,
    frame: pd.DataFrame,
    fill_candle_index: int | None,
    intrabar_policy_config: IntrabarPolicyConfig | None,
    *,
    entry_filled_on_first_candle: bool,
) -> dict[str, Any]:
    if not entry_filled_on_first_candle or fill_candle_index is None or frame.empty or not risk_plan.targets:
        return {}
    candle = frame.iloc[fill_candle_index]
    first_target = risk_plan.targets[0]
    touches = detect_intrabar_touches(
        high=float(candle["high"]),
        low=float(candle["low"]),
        entry_price=float(risk_plan.entry_price),
        stop_price=float(risk_plan.stop_price),
        target_price=float(first_target.price),
    )
    if not (touches.entry_touched and (touches.stop_touched or touches.target_touched)):
        return {}
    decision = resolve_intrabar_decision(
        direction=str(risk_plan.direction.value if hasattr(risk_plan.direction, "value") else risk_plan.direction),
        touches=touches,
        config=intrabar_policy_config,
    )
    return {
        "schema_version": "combined_entry_exit_intrabar_decision_v1",
        "intrabar_policy": intrabar_policy_config.mode.value if intrabar_policy_config else "CONSERVATIVE",
        "entry_touched": touches.entry_touched,
        "stop_touched": touches.stop_touched,
        "target_touched": touches.target_touched,
        "ambiguous_stop_target": touches.ambiguous_stop_target,
        "ambiguous_entry_stop_target": touches.ambiguous_entry_stop_target,
        "is_ambiguous": decision.is_ambiguous,
        "decision_reason": decision.reason,
        "decision_outcome": decision.outcome,
        "skipped": decision.skipped,
        "candle_index": fill_candle_index,
    }


def _entry_fill_is_first_future_candle(frame: pd.DataFrame, fill_candle_index: int | None, fill_timestamp: Any) -> bool:
    if fill_candle_index is None or frame.empty or fill_candle_index != 0:
        return False
    return _same_value(frame.iloc[0]["timestamp"], fill_timestamp)


def _same_value(left: Any, right: Any) -> bool:
    try:
        return bool(left == right)
    except ValueError:
        return False


def _supported_entry_modes(pattern_type: Any) -> tuple[str, ...]:
    pattern = str(pattern_type or "").upper()
    base_modes = (
        PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE.value,
        PatternEntryMode.MARKET_ON_NEXT_OPEN.value,
        PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE.value,
        PatternEntryMode.LIMIT_AT_CUSTOM_PRICE.value,
    )
    zone_modes = (
        PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT.value,
        PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY.value,
        PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY.value,
        PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY.value,
    )
    order_block_modes = (
        PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT.value,
    )
    if pattern in {"FAIR_VALUE_GAP", "ORDER_BLOCK", "DIAMOND"}:
        modes = (*base_modes, *zone_modes)
        if pattern == "ORDER_BLOCK":
            return (*modes, *order_block_modes)
        return modes
    if pattern in {"TRENDLINE_BREAK", "CUP_AND_HANDLE", "ADAM_AND_EVE"}:
        if pattern == "TRENDLINE_BREAK":
            return (*base_modes, PatternEntryMode.LIMIT_AT_TRENDLINE_RETEST.value)
        if pattern == "CUP_AND_HANDLE":
            return (*base_modes, PatternEntryMode.LIMIT_AT_NECKLINE_RETEST.value)
        return base_modes
    return (*base_modes, *zone_modes)


def _pattern_event_metadata(event: Any, position_side: str, risk_plan: RiskExitPlan) -> dict[str, Any]:
    return {
        "pattern_execution_path": PATTERN_EXECUTION_PATH_CANONICAL_FILL_AWARE,
        "canonical_pattern_action": True,
        "canonical_expansion_required": False,
        "pattern_event_id": getattr(event, "event_id", None),
        "event_id": getattr(event, "event_id", None),
        "pattern_type": getattr(event, "pattern_type", None),
        "pattern_direction": str(getattr(event, "pattern_direction", getattr(event, "direction", ""))).upper(),
        "position_side": position_side,
        "pattern_status": getattr(event, "pattern_status", None),
        "pattern_score": getattr(event, "pattern_score", None),
        "executable_pattern_score": getattr(
            event,
            "executable_pattern_score",
            getattr(event, "pattern_score", None),
        ),
        "diagnostic_pattern_score": getattr(event, "diagnostic_pattern_score", None),
        "risk_reward": getattr(event, "risk_reward", None),
        "event_entry_reference": getattr(event, "entry_reference", None),
        "event_stop_reference": getattr(event, "stop_reference", None),
        "event_target_reference": getattr(event, "target_reference", None),
        "target_semantics": _event_target_semantics(event, risk_plan),
        "stop_reference": getattr(event, "stop_reference", getattr(risk_plan, "structural_stop", None)),
        "target_reference": getattr(event, "target_reference", None),
        "zone_mid": getattr(event, "zone_mid", None),
        "zone_low": getattr(event, "zone_low", None),
        "zone_high": getattr(event, "zone_high", None),
        "trendline_value": getattr(event, "trendline_value", None),
        "neckline": getattr(event, "neckline", None),
        "upper_boundary_value": getattr(event, "upper_boundary_value", None),
        "lower_boundary_value": getattr(event, "lower_boundary_value", None),
        "risk_plan_status": _status_value(getattr(risk_plan, "status", None)),
        "risk_plan_reasons": tuple(getattr(risk_plan, "reasons", ()) or ()),
        "atr_metadata": getattr(event, "atr_metadata", {}) or getattr(risk_plan, "atr_metadata", {}),
        "mtf_trend_score": getattr(event, "mtf_trend_score", None),
        "mtf_trend_direction": getattr(event, "mtf_trend_direction", None),
        "mtf_trend_aligned": getattr(event, "mtf_trend_aligned", None),
        "mtf_trend_metadata": getattr(event, "mtf_trend_metadata", {}),
        "fib_confluence_pass": getattr(event, "fib_confluence_pass", None),
        "fib_retracement_level": getattr(event, "fib_retracement_level", None),
        "fib_metadata": getattr(event, "fib_metadata", {}),
        "risk_plan_atr_metadata": getattr(risk_plan, "atr_metadata", {}),
        "atr_buffer_multiplier": getattr(risk_plan, "atr_buffer_multiplier", None),
        **_score_metadata_from_event(event),
    }


def _event_target_semantics(event: Any, risk_plan: RiskExitPlan) -> dict[str, Any]:
    target_semantics = dict(getattr(risk_plan, "target_semantics", {}) or {})
    if not target_semantics:
        return {}
    if target_semantics.get("detector_target_reference") is None:
        target_semantics["detector_target_reference"] = getattr(event, "target_reference", None)
    return target_semantics


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
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY:
        return "PATTERN_NEAR_BOUNDARY"
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY:
        return "PATTERN_FAR_BOUNDARY"
    if mode == PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT:
        return "ORDER_BLOCK_618_RETRACEMENT"
    if mode == PatternEntryMode.LIMIT_AT_TRENDLINE_RETEST:
        return "TRENDLINE_RETEST"
    if mode == PatternEntryMode.LIMIT_AT_NECKLINE_RETEST:
        return "NECKLINE_RETEST"
    return "CUSTOM_PRICE"


def _entry_style(mode: PatternEntryMode) -> str:
    if mode in (PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, PatternEntryMode.MARKET_ON_NEXT_OPEN):
        return "CHASE_OR_MOMENTUM"
    return "RETEST_LIMIT"


def _zone_boundary_variant(mode: PatternEntryMode) -> str | None:
    if mode == PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY:
        return "NEAR_BOUNDARY"
    if mode in (PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY, PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY):
        return "FAR_OR_STOP_SIDE_BOUNDARY"
    return None


def _entry_mode_hypothesis(pattern_type: Any, mode: PatternEntryMode) -> str:
    pattern = str(pattern_type or "").upper()
    if mode == PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE:
        return "CHASE_MOMENTUM_CONFIRMATION_CLOSE" if pattern in {"FAIR_VALUE_GAP", "ORDER_BLOCK"} else "CONFIRMATION_CLOSE"
    if mode == PatternEntryMode.MARKET_ON_NEXT_OPEN:
        return "CHASE_MOMENTUM_NEXT_OPEN" if pattern in {"FAIR_VALUE_GAP", "ORDER_BLOCK"} else "NEXT_OPEN"
    if pattern == "FAIR_VALUE_GAP":
        if mode == PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT:
            return "RETEST_GAP_MIDPOINT"
        if mode == PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY:
            return "RETEST_NEAR_GAP_BOUNDARY"
        if mode in (PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY, PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY):
            return "RETEST_DEEP_GAP_BOUNDARY"
    if pattern == "ORDER_BLOCK":
        if mode == PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT:
            return "RETEST_ORDER_BLOCK_MIDPOINT"
        if mode == PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT:
            return "RETEST_ORDER_BLOCK_618_RETRACEMENT"
        if mode == PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY:
            return "RETEST_ORDER_BLOCK_STOP_SIDE_BOUNDARY"
    if mode == PatternEntryMode.LIMIT_AT_CUSTOM_PRICE:
        return "CUSTOM_RESEARCH_PRICE"
    return "LEGACY_OR_REFERENCE_LIMIT"


def _distance(left: float | int | None, right: float | int | None) -> float | None:
    if left is None or right is None:
        return None
    try:
        return float(left) - float(right)
    except (TypeError, ValueError):
        return None


def _zone_distance(event: Any, price: float | int | None) -> dict[str, float] | None:
    if price is None:
        return None
    zone_low = _positive_float(getattr(event, "zone_low", None))
    zone_high = _positive_float(getattr(event, "zone_high", None))
    if zone_low is None or zone_high is None:
        return None
    zone_mid = (zone_low + zone_high) / 2.0
    fill = float(price)
    return {
        "from_zone_low": fill - zone_low,
        "from_zone_mid": fill - zone_mid,
        "from_zone_high": fill - zone_high,
    }


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
