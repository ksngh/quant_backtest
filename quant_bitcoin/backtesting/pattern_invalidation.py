"""Active soft-invalidation rules for canonical pattern backtests."""

from __future__ import annotations

from typing import Any

from quant_bitcoin.risk.exit_plan import RiskExitDirection, RiskExitPlan
from quant_bitcoin.risk.exit_simulation import SoftInvalidationRule


def soft_invalidation_for_event(event: Any, plan: RiskExitPlan) -> SoftInvalidationRule | None:
    direction = _coerce_direction(plan.direction)
    pattern_type = str(_field(event, "pattern_type") or "").upper()
    if pattern_type == "FAIR_VALUE_GAP":
        reference = _optional_float(_field(event, "zone_mid"))
        if reference is None:
            return None
        operator = "<=" if direction == RiskExitDirection.LONG else ">="
        return SoftInvalidationRule(
            invalidates_when=f"close {operator} fvg_midpoint",
            reference_price=reference,
        )
    if pattern_type == "TRENDLINE_BREAK":
        reference = _optional_float(_field(event, "trendline_value"))
        if reference is None:
            return None
        operator = "<=" if direction == RiskExitDirection.LONG else ">="
        return SoftInvalidationRule(
            invalidates_when=f"close {operator} trendline_value",
            reference_price=reference,
        )
    if pattern_type == "CUP_AND_HANDLE":
        reference = _optional_float(_field(event, "neckline"))
        if reference is None:
            return None
        return SoftInvalidationRule(
            invalidates_when="close < neckline_after_breakout",
            reference_price=reference,
        )
    if pattern_type in {"DIAMOND", "DIAMOND_PATTERN"}:
        if direction == RiskExitDirection.LONG:
            reference = _optional_float(_field(event, "upper_boundary_value"))
            if reference is None:
                return None
            return SoftInvalidationRule(
                invalidates_when="close <= upper_boundary_value",
                reference_price=reference,
            )
        reference = _optional_float(_field(event, "lower_boundary_value"))
        if reference is None:
            return None
        return SoftInvalidationRule(
            invalidates_when="close >= lower_boundary_value",
            reference_price=reference,
        )
    if pattern_type in {"ADAM_AND_EVE", "ADAM_AND_EVE_PATTERN"}:
        reference = _optional_float(_field(event, "neckline"))
        if reference is None:
            return None
        return SoftInvalidationRule(
            invalidates_when="close < neckline_after_breakout",
            reference_price=reference,
        )
    return None


def _field(event: Any, name: str) -> Any:
    if isinstance(event, dict):
        return event.get(name)
    return getattr(event, name, None)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_direction(direction: RiskExitDirection | str) -> RiskExitDirection:
    if isinstance(direction, RiskExitDirection):
        return direction
    return RiskExitDirection(str(direction).upper())
