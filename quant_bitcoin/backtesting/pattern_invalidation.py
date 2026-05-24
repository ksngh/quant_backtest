"""Active soft-invalidation rules for canonical pattern backtests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_bitcoin.patterns.fair_value_gap_risk_exit import FairValueGapReactionFailureRule
from quant_bitcoin.risk.exit_plan import RiskExitDirection, RiskExitPlan
from quant_bitcoin.risk.exit_simulation import SoftInvalidationRule

PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION = "pattern_soft_invalidation_v1"


@dataclass(frozen=True)
class PatternSoftInvalidationAdapterResult:
    """Pattern-specific soft invalidation adapter output."""

    rule: SoftInvalidationRule | None
    metadata: dict[str, Any]


def soft_invalidation_for_event(event: Any, plan: RiskExitPlan) -> SoftInvalidationRule | None:
    """Return only the simulator rule for legacy callers."""

    return pattern_soft_invalidation_for_event(event, plan).rule


def pattern_soft_invalidation_for_event(
    event: Any,
    plan: RiskExitPlan,
) -> PatternSoftInvalidationAdapterResult:
    """Adapt supported pattern soft-invalidation semantics to the simulator.

    Unsupported pattern-specific invalidation concepts intentionally return
    metadata without fabricating a simple close-threshold rule.
    """

    direction = _coerce_direction(plan.direction)
    pattern_type = str(_field(event, "pattern_type") or "").upper()
    if pattern_type == "FAIR_VALUE_GAP":
        reference = _optional_float(_field(event, "zone_mid"))
        if reference is None:
            return _missing_reference(pattern_type, direction, "zone_mid", "fvg_reaction_failure")
        max_bars = plan.time_stop.max_bars_in_trade
        rule = FairValueGapReactionFailureRule(
            enabled=True,
            max_bars_after_entry=max_bars if max_bars is not None else 1,
            midpoint_price=reference,
            favorable_close_condition="close > fvg_midpoint" if direction == RiskExitDirection.LONG else "close < fvg_midpoint",
        )
        adapted = soft_invalidation_from_fvg_reaction_failure(
            rule,
            event=event,
            direction=direction,
        )
        return PatternSoftInvalidationAdapterResult(
            rule=adapted,
            metadata=_adapter_metadata(
                pattern_type,
                direction,
                source="fair_value_gap.reaction_failure",
                rule_name=rule.rule,
                invalidates_when=rule.rule,
                reference_field="zone_mid",
                reference_price=reference,
                max_bars_after_entry=rule.max_bars_after_entry,
                supported=adapted is not None,
            ),
        )
    if pattern_type == "TRENDLINE_BREAK":
        reference = _optional_float(_field(event, "trendline_value"))
        if reference is None:
            return _missing_reference(pattern_type, direction, "trendline_value", "close_reenters_broken_trendline_side")
        operator = "<=" if direction == RiskExitDirection.LONG else ">="
        invalidates_when = f"close {operator} trendline_value"
        return _adapted_rule(
            pattern_type,
            direction,
            source="trendline_break.soft_invalidation",
            rule_name="close_reenters_broken_trendline_side",
            invalidates_when=invalidates_when,
            reference_field="trendline_value",
            reference_price=reference,
        )
    if pattern_type == "ORDER_BLOCK":
        return _unsupported_complex_rule(
            pattern_type,
            direction,
            source="order_block.no_reaction_stop",
            rule_name="no_reaction_after_order_block_entry",
            limitation=(
                "Order Block no-reaction invalidation requires path-dependent "
                "R-multiple reaction state and is not expressible as a simple close rule."
            ),
        )
    if pattern_type == "CUP_AND_HANDLE":
        reference = _optional_float(_field(event, "neckline"))
        if reference is None:
            return _missing_reference(pattern_type, direction, "neckline", "cup_and_handle_neckline_reentry")
        return _adapted_rule(
            pattern_type,
            direction,
            source="cup_and_handle.neckline_soft_exit",
            rule_name="cup_and_handle_neckline_reentry",
            invalidates_when="close < neckline_after_breakout",
            reference_price=reference,
            reference_field="neckline",
        )
    if pattern_type in {"DIAMOND", "DIAMOND_PATTERN"}:
        if direction == RiskExitDirection.LONG:
            reference = _optional_float(_field(event, "upper_boundary_value"))
            if reference is None:
                return _missing_reference(pattern_type, direction, "upper_boundary_value", "diamond_close_back_inside_range")
            return _adapted_rule(
                pattern_type,
                direction,
                source="diamond.soft_invalidation",
                rule_name="diamond_close_back_inside_range",
                invalidates_when="close <= upper_boundary_value",
                reference_price=reference,
                reference_field="upper_boundary_value",
            )
        reference = _optional_float(_field(event, "lower_boundary_value"))
        if reference is None:
            return _missing_reference(pattern_type, direction, "lower_boundary_value", "diamond_close_back_inside_range")
        return _adapted_rule(
            pattern_type,
            direction,
            source="diamond.soft_invalidation",
            rule_name="diamond_close_back_inside_range",
            invalidates_when="close >= lower_boundary_value",
            reference_price=reference,
            reference_field="lower_boundary_value",
        )
    if pattern_type in {"ADAM_AND_EVE", "ADAM_AND_EVE_PATTERN"}:
        reference = _optional_float(_field(event, "neckline"))
        if reference is None:
            return _missing_reference(pattern_type, direction, "neckline", "adam_and_eve_neckline_reentry")
        return _adapted_rule(
            pattern_type,
            direction,
            source="adam_and_eve.neckline_soft_exit",
            rule_name="adam_and_eve_neckline_reentry",
            invalidates_when="close < neckline_after_breakout",
            reference_price=reference,
            reference_field="neckline",
        )
    return PatternSoftInvalidationAdapterResult(
        rule=None,
        metadata=_adapter_metadata(
            pattern_type,
            direction,
            source="none",
            rule_name=None,
            invalidates_when=None,
            reference_field=None,
            reference_price=None,
            supported=False,
            enabled=False,
            limitation="No pattern-specific soft invalidation adapter is defined.",
        ),
    )


def soft_invalidation_from_fvg_reaction_failure(
    rule: FairValueGapReactionFailureRule,
    *,
    event: Any,
    direction: RiskExitDirection | str,
) -> SoftInvalidationRule | None:
    if not rule.enabled:
        return None
    normalized_direction = _coerce_direction(direction)
    return SoftInvalidationRule(
        invalidates_when=rule.rule,
        reference_price=rule.midpoint_price,
        max_bars_after_entry=rule.max_bars_after_entry,
        favorable_close_condition=rule.favorable_close_condition,
        metadata={
            "schema_version": "fvg_reaction_failure_soft_invalidation_v1",
            "pattern_soft_invalidation_schema_version": PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION,
            "pattern_soft_invalidation_source": "fair_value_gap.reaction_failure",
            "pattern_soft_invalidation_supported": True,
            "pattern_type": "FAIR_VALUE_GAP",
            "direction": normalized_direction.value,
            "rule": rule.rule,
            "invalidates_when": rule.rule,
            "reference_field": "zone_mid",
            "zone_low": _optional_float(_field(event, "zone_low")),
            "zone_high": _optional_float(_field(event, "zone_high")),
            "fvg_midpoint": rule.midpoint_price,
        },
    )


def _adapted_rule(
    pattern_type: str,
    direction: RiskExitDirection,
    *,
    source: str,
    rule_name: str,
    invalidates_when: str,
    reference_field: str,
    reference_price: float,
) -> PatternSoftInvalidationAdapterResult:
    metadata = _adapter_metadata(
        pattern_type,
        direction,
        source=source,
        rule_name=rule_name,
        invalidates_when=invalidates_when,
        reference_field=reference_field,
        reference_price=reference_price,
        supported=True,
    )
    return PatternSoftInvalidationAdapterResult(
        rule=SoftInvalidationRule(
            invalidates_when=invalidates_when,
            reference_price=reference_price,
            metadata={
                "pattern_soft_invalidation_schema_version": PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION,
                "pattern_soft_invalidation_source": source,
                "pattern_soft_invalidation_supported": True,
                "pattern_type": pattern_type,
                "direction": direction.value,
                "rule": rule_name,
                "invalidates_when": invalidates_when,
                "reference_field": reference_field,
                "reference_price": reference_price,
            },
        ),
        metadata=metadata,
    )


def _adapter_metadata(
    pattern_type: str,
    direction: RiskExitDirection,
    *,
    source: str,
    rule_name: str | None,
    invalidates_when: str | None,
    reference_field: str | None,
    reference_price: float | None,
    supported: bool,
    enabled: bool = True,
    max_bars_after_entry: int | None = None,
    limitation: str | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "schema_version": PATTERN_SOFT_INVALIDATION_SCHEMA_VERSION,
        "enabled": enabled,
        "supported": supported,
        "pattern_type": pattern_type,
        "direction": direction.value,
        "source": source,
        "rule": rule_name,
        "invalidates_when": invalidates_when,
        "reference_field": reference_field,
        "reference_price": reference_price,
    }
    if max_bars_after_entry is not None:
        metadata["max_bars_after_entry"] = max_bars_after_entry
    if limitation is not None:
        metadata["limitation"] = limitation
    return metadata


def _missing_reference(
    pattern_type: str,
    direction: RiskExitDirection,
    reference_field: str,
    rule_name: str,
) -> PatternSoftInvalidationAdapterResult:
    return PatternSoftInvalidationAdapterResult(
        rule=None,
        metadata=_adapter_metadata(
            pattern_type,
            direction,
            source="missing_reference",
            rule_name=rule_name,
            invalidates_when=None,
            reference_field=reference_field,
            reference_price=None,
            supported=False,
            enabled=False,
            limitation=f"Missing {reference_field}; cannot adapt pattern soft invalidation to a close rule.",
        ),
    )


def _unsupported_complex_rule(
    pattern_type: str,
    direction: RiskExitDirection,
    *,
    source: str,
    rule_name: str,
    limitation: str,
) -> PatternSoftInvalidationAdapterResult:
    return PatternSoftInvalidationAdapterResult(
        rule=None,
        metadata=_adapter_metadata(
            pattern_type,
            direction,
            source=source,
            rule_name=rule_name,
            invalidates_when=None,
            reference_field=None,
            reference_price=None,
            supported=False,
            enabled=False,
            limitation=limitation,
        ),
    )


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
