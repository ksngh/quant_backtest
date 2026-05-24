"""Deterministic pattern risk/exit plan simulation.

This module evaluates already-provided completed candles against a planned
``RiskExitPlan`` and returns analysis records. It does not fetch market data,
read secrets, call exchange APIs, place paper or real orders, persist records,
or mutate caller data.

Same-candle sequencing is intentionally deterministic and policy-driven:
1. update break-even/trailing stop levels from the candle's favorable extreme;
2. resolve same-candle stop/target ambiguity with ``IntrabarPolicyConfig``;
3. hard stop and take-profit checks in target order;
4. soft invalidation check on close;
5. time-stop check on close.

When a stop and target are both reachable in the same candle, the default
policy remains conservative and resolves to stop.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

import pandas as pd

from quant_bitcoin.backtesting.intrabar_policy import (
    IntrabarPolicyConfig,
    IntrabarSequencingMode,
    detect_intrabar_touches,
    resolve_intrabar_decision,
)
from quant_bitcoin.risk.exit_plan import (
    PartialExitSettings,
    RiskExitDirection,
    RiskExitPlan,
    RiskExitPlanStatus,
    RiskExitTarget,
)

INTRABAR_PRECEDENCE_POLICY = "stop_before_target"


class PatternExitReason(Enum):
    """Supported simulated exit reasons."""

    HARD_STOP = "HARD_STOP"
    TAKE_PROFIT = "TAKE_PROFIT"
    SOFT_INVALIDATION = "SOFT_INVALIDATION"
    TIME_STOP = "TIME_STOP"
    NO_EXIT = "NO_EXIT"


@dataclass(frozen=True)
class SoftInvalidationRule:
    """Close-based soft invalidation rule for the exit simulator."""

    invalidates_when: str
    reference_price: float | None = None


@dataclass(frozen=True)
class PatternExitEvent:
    """One simulated analysis event; this is not an exchange order."""

    timestamp: Any
    candle_index: int
    reason: PatternExitReason
    price: float
    quantity_ratio: float
    remaining_quantity_ratio: float
    target_name: str | None = None
    stop_price: float | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class PatternExitSimulationResult:
    """Deterministic exit simulation result for one risk/exit plan."""

    events: tuple[PatternExitEvent, ...]
    final_reason: PatternExitReason
    final_price: float | None
    remaining_quantity_ratio: float
    bars_evaluated: int


def simulate_pattern_exit(
    plan: RiskExitPlan,
    candles: pd.DataFrame | Iterable[dict[str, Any]],
    *,
    soft_invalidation: SoftInvalidationRule | None = None,
    intrabar_policy_config: IntrabarPolicyConfig | None = None,
) -> PatternExitSimulationResult:
    """Simulate completed candles against a risk/exit plan.

    Args:
        plan: Valid shared risk/exit plan to simulate.
        candles: Completed candles in ascending timestamp order with ``timestamp``,
            ``high``, ``low``, and ``close`` columns.
        soft_invalidation: Optional close-based invalidation metadata supplied by
            pattern-specific planners or tests.

    Raises:
        ValueError: If the plan is not valid enough to simulate, required candle
            fields are missing, or candle timestamps are not sorted ascending.
    """

    _validate_plan(plan)
    frame = _normalize_candles(candles)
    if frame.empty:
        return PatternExitSimulationResult((), PatternExitReason.NO_EXIT, None, 1.0, 0)

    direction = _coerce_direction(plan.direction)
    assert plan.entry_price is not None
    assert plan.stop_price is not None
    assert plan.risk_per_unit is not None

    current_stop = float(plan.stop_price)
    max_favorable_r = 0.0
    remaining_ratio = 1.0
    events: list[PatternExitEvent] = []
    hit_target_names: set[str] = set()

    for candle_index, candle in frame.iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])
        timestamp = candle["timestamp"]
        favorable_r = _favorable_r(direction, plan.entry_price, high, low, plan.risk_per_unit)
        max_favorable_r = max(max_favorable_r, favorable_r)
        current_stop = _move_break_even_stop(direction, plan, current_stop, max_favorable_r)
        current_stop = _move_trailing_stop(direction, plan, current_stop, high, low)

        stop_hit = _stop_hit(direction, current_stop, high, low)
        hit_target = next(
            (
                target
                for target in plan.targets
                if target.name not in hit_target_names and _target_hit(direction, target, high, low)
            ),
            None,
        )
        target_hit = hit_target is not None
        exit_policy_metadata = {
            "intrabar_precedence_policy": INTRABAR_PRECEDENCE_POLICY,
            "ambiguous_stop_target": stop_hit and target_hit,
            "intrabar_policy": (intrabar_policy_config.mode.value if intrabar_policy_config else IntrabarSequencingMode.CONSERVATIVE.value),
            "be_trailing_sequence": "favorable-extreme updates are applied before stop/target checks",
        }

        if stop_hit and target_hit and hit_target is not None:
            touches = detect_intrabar_touches(
                high=high,
                low=low,
                entry_price=plan.entry_price,
                stop_price=current_stop,
                target_price=hit_target.price,
            )
            decision = resolve_intrabar_decision(
                direction=direction.value,
                touches=touches,
                config=intrabar_policy_config,
            )
            exit_policy_metadata.update(
                {
                    "is_ambiguous": decision.is_ambiguous,
                    "decision_reason": decision.reason,
                    "decision_outcome": decision.outcome,
                }
            )
            if decision.skipped:
                continue
            if decision.outcome == "TARGET":
                exit_ratio = min(
                    remaining_ratio,
                    _partial_exit_ratio(plan.partial_exits, hit_target) or remaining_ratio,
                )
                remaining_ratio = round(max(0.0, remaining_ratio - exit_ratio), 12)
                hit_target_names.add(hit_target.name)
                events.append(
                    PatternExitEvent(
                        timestamp=timestamp,
                        candle_index=int(candle_index),
                        reason=PatternExitReason.TAKE_PROFIT,
                        price=hit_target.price,
                        quantity_ratio=exit_ratio,
                        remaining_quantity_ratio=remaining_ratio,
                        target_name=hit_target.name,
                        stop_price=current_stop,
                        metadata={**exit_policy_metadata, "target_source": str(hit_target.source.value if hasattr(hit_target.source, "value") else hit_target.source)},
                    )
                )
                if remaining_ratio <= 0:
                    break
                continue

        if stop_hit:
            events.append(
                PatternExitEvent(
                    timestamp=timestamp,
                    candle_index=int(candle_index),
                    reason=PatternExitReason.HARD_STOP,
                    price=current_stop,
                    quantity_ratio=remaining_ratio,
                    remaining_quantity_ratio=0.0,
                    stop_price=current_stop,
                    metadata={**exit_policy_metadata, "precedence": INTRABAR_PRECEDENCE_POLICY},
                )
            )
            remaining_ratio = 0.0
            break

        for target in plan.targets:
            if target.name in hit_target_names:
                continue
            if not _target_hit(direction, target, high, low):
                continue
            exit_ratio = min(
                remaining_ratio,
                _partial_exit_ratio(plan.partial_exits, target) or remaining_ratio,
            )
            remaining_ratio = round(max(0.0, remaining_ratio - exit_ratio), 12)
            hit_target_names.add(target.name)
            events.append(
                PatternExitEvent(
                    timestamp=timestamp,
                    candle_index=int(candle_index),
                    reason=PatternExitReason.TAKE_PROFIT,
                    price=target.price,
                    quantity_ratio=exit_ratio,
                    remaining_quantity_ratio=remaining_ratio,
                    target_name=target.name,
                    stop_price=current_stop,
                    metadata={**exit_policy_metadata, "target_source": str(target.source.value if hasattr(target.source, "value") else target.source)},
                )
            )
            if remaining_ratio <= 0:
                break
        if remaining_ratio <= 0:
            break

        if soft_invalidation is not None and _soft_invalidated(soft_invalidation, close):
            events.append(
                PatternExitEvent(
                    timestamp=timestamp,
                    candle_index=int(candle_index),
                    reason=PatternExitReason.SOFT_INVALIDATION,
                    price=close,
                    quantity_ratio=remaining_ratio,
                    remaining_quantity_ratio=0.0,
                    stop_price=current_stop,
                    metadata={"rule": soft_invalidation.invalidates_when},
                )
            )
            remaining_ratio = 0.0
            break

        if _time_stop_hit(plan, candle_index + 1, max_favorable_r):
            events.append(
                PatternExitEvent(
                    timestamp=timestamp,
                    candle_index=int(candle_index),
                    reason=PatternExitReason.TIME_STOP,
                    price=close,
                    quantity_ratio=remaining_ratio,
                    remaining_quantity_ratio=0.0,
                    stop_price=current_stop,
                    metadata={"max_favorable_r": max_favorable_r},
                )
            )
            remaining_ratio = 0.0
            break

    final_event = events[-1] if events else None
    return PatternExitSimulationResult(
        events=tuple(events),
        final_reason=final_event.reason if final_event is not None else PatternExitReason.NO_EXIT,
        final_price=final_event.price if final_event is not None else None,
        remaining_quantity_ratio=remaining_ratio,
        bars_evaluated=len(frame) if final_event is None else final_event.candle_index + 1,
    )


def _validate_plan(plan: RiskExitPlan) -> None:
    if plan.status != RiskExitPlanStatus.VALID:
        raise ValueError("only VALID risk/exit plans can be simulated")
    if plan.entry_price is None or plan.stop_price is None or plan.risk_per_unit is None:
        raise ValueError("plan must include entry_price, stop_price, and risk_per_unit")
    if plan.risk_per_unit <= 0:
        raise ValueError("plan risk_per_unit must be positive")


def _normalize_candles(candles: pd.DataFrame | Iterable[dict[str, Any]]) -> pd.DataFrame:
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(list(candles))
    missing = [column for column in ("timestamp", "high", "low", "close") if column not in frame.columns]
    if missing:
        raise ValueError(f"missing required simulation candle columns: {', '.join(missing)}")
    if not frame.empty and not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")
    for column in ("high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if frame[column].isna().any():
            raise ValueError(f"candle column contains missing values: {column}")
    return frame.reset_index(drop=True)


def _coerce_direction(direction: RiskExitDirection | str) -> RiskExitDirection:
    if isinstance(direction, RiskExitDirection):
        return direction
    return RiskExitDirection(str(direction).upper())


def _favorable_r(
    direction: RiskExitDirection,
    entry_price: float,
    high: float,
    low: float,
    risk_per_unit: float,
) -> float:
    if direction == RiskExitDirection.LONG:
        return max(0.0, (high - entry_price) / risk_per_unit)
    return max(0.0, (entry_price - low) / risk_per_unit)


def _move_break_even_stop(
    direction: RiskExitDirection,
    plan: RiskExitPlan,
    current_stop: float,
    max_favorable_r: float,
) -> float:
    if not plan.break_even.enabled or max_favorable_r < plan.break_even.trigger_r_multiple:
        return current_stop
    assert plan.entry_price is not None
    assert plan.risk_per_unit is not None
    if direction == RiskExitDirection.LONG:
        break_even_stop = plan.entry_price + plan.break_even.stop_offset_r_multiple * plan.risk_per_unit
        return max(current_stop, break_even_stop)
    break_even_stop = plan.entry_price - plan.break_even.stop_offset_r_multiple * plan.risk_per_unit
    return min(current_stop, break_even_stop)


def _move_trailing_stop(
    direction: RiskExitDirection,
    plan: RiskExitPlan,
    current_stop: float,
    high: float,
    low: float,
) -> float:
    if (
        not plan.trailing_stop.enabled
        or plan.atr is None
        or plan.risk_per_unit is None
        or _favorable_r(direction, plan.entry_price or 0.0, high, low, plan.risk_per_unit)
        < plan.trailing_stop.activation_r_multiple
    ):
        return current_stop
    trail_distance = plan.atr * plan.trailing_stop.trail_atr_multiplier
    if direction == RiskExitDirection.LONG:
        return max(current_stop, high - trail_distance)
    return min(current_stop, low + trail_distance)


def _stop_hit(direction: RiskExitDirection, stop_price: float, high: float, low: float) -> bool:
    if direction == RiskExitDirection.LONG:
        return low <= stop_price
    return high >= stop_price


def _target_hit(direction: RiskExitDirection, target: RiskExitTarget, high: float, low: float) -> bool:
    if direction == RiskExitDirection.LONG:
        return high >= target.price
    return low <= target.price


def _partial_exit_ratio(partial_exits: tuple[PartialExitSettings, ...], target: RiskExitTarget) -> float | None:
    if target.r_multiple is None:
        return None
    for partial_exit in partial_exits:
        if abs(partial_exit.target_r_multiple - target.r_multiple) < 1e-9:
            return partial_exit.exit_ratio
    return None


def _soft_invalidated(rule: SoftInvalidationRule, close: float) -> bool:
    if rule.reference_price is None:
        return False
    condition = rule.invalidates_when.lower()
    if "<=" in condition:
        return close <= rule.reference_price
    if ">=" in condition:
        return close >= rule.reference_price
    if "<" in condition:
        return close < rule.reference_price
    if ">" in condition:
        return close > rule.reference_price
    return False


def _time_stop_hit(plan: RiskExitPlan, bar_number: int, max_favorable_r: float) -> bool:
    max_bars = plan.time_stop.max_bars_in_trade
    if max_bars is None or bar_number < max_bars:
        return False
    required_r = plan.time_stop.required_r_multiple
    if required_r is None:
        return True
    return max_favorable_r < required_r
