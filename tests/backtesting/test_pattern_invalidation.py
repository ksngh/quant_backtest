from __future__ import annotations

from types import SimpleNamespace

from quant_bitcoin.backtesting.pattern_invalidation import (
    pattern_soft_invalidation_for_event,
    soft_invalidation_for_event,
)
from quant_bitcoin.risk.exit_plan import RiskExitDirection, RiskExitPlan, RiskExitPlanStatus


def _plan(direction=RiskExitDirection.LONG) -> RiskExitPlan:
    return RiskExitPlan(
        direction=direction,
        entry_price=100.0,
        structural_stop=90.0,
        atr=1.0,
        atr_buffer_multiplier=0.0,
        atr_buffer=0.0,
        stop_price=90.0 if direction == RiskExitDirection.LONG else 110.0,
        risk_per_unit=10.0,
        targets=(),
        status=RiskExitPlanStatus.VALID,
    )


def test_fvg_soft_invalidation_uses_midpoint() -> None:
    result = pattern_soft_invalidation_for_event(
        SimpleNamespace(pattern_type="FAIR_VALUE_GAP", zone_mid=99.5, zone_low=98.0, zone_high=101.0),
        _plan(),
    )
    rule = result.rule

    assert rule is not None
    assert rule.invalidates_when == "fvg_midpoint_reaction_failure"
    assert rule.reference_price == 99.5
    assert rule.favorable_close_condition == "close > fvg_midpoint"
    assert rule.max_bars_after_entry == 1
    assert rule.metadata["schema_version"] == "fvg_reaction_failure_soft_invalidation_v1"
    assert result.metadata["schema_version"] == "pattern_soft_invalidation_v1"
    assert result.metadata["source"] == "fair_value_gap.reaction_failure"


def test_trendline_break_soft_invalidation_uses_trendline_value() -> None:
    result = pattern_soft_invalidation_for_event(
        SimpleNamespace(pattern_type="TRENDLINE_BREAK", trendline_value=101.0),
        _plan(RiskExitDirection.SHORT),
    )
    rule = result.rule

    assert rule is not None
    assert rule.invalidates_when == "close >= trendline_value"
    assert rule.reference_price == 101.0
    assert result.metadata["source"] == "trendline_break.soft_invalidation"
    assert result.metadata["reference_field"] == "trendline_value"


def test_neckline_soft_invalidation_uses_neckline_when_present() -> None:
    result = pattern_soft_invalidation_for_event(
        SimpleNamespace(pattern_type="CUP_AND_HANDLE", neckline=98.0),
        _plan(),
    )
    rule = result.rule

    assert rule is not None
    assert rule.invalidates_when == "close < neckline_after_breakout"
    assert rule.reference_price == 98.0
    assert result.metadata["source"] == "cup_and_handle.neckline_soft_exit"


def test_diamond_soft_invalidation_uses_breakout_boundary() -> None:
    bullish = pattern_soft_invalidation_for_event(
        SimpleNamespace(pattern_type="DIAMOND", upper_boundary_value=101.0, lower_boundary_value=90.0),
        _plan(),
    )
    bearish = pattern_soft_invalidation_for_event(
        SimpleNamespace(pattern_type="DIAMOND", upper_boundary_value=110.0, lower_boundary_value=99.0),
        _plan(RiskExitDirection.SHORT),
    )

    assert bullish.rule is not None
    assert bullish.rule.invalidates_when == "close <= upper_boundary_value"
    assert bullish.rule.reference_price == 101.0
    assert bullish.metadata["source"] == "diamond.soft_invalidation"
    assert bearish.rule is not None
    assert bearish.rule.invalidates_when == "close >= lower_boundary_value"
    assert bearish.rule.reference_price == 99.0


def test_adam_and_eve_soft_invalidation_uses_neckline() -> None:
    result = pattern_soft_invalidation_for_event(
        SimpleNamespace(pattern_type="ADAM_AND_EVE", neckline=98.0),
        _plan(),
    )

    assert result.rule is not None
    assert result.rule.invalidates_when == "close < neckline_after_breakout"
    assert result.rule.reference_price == 98.0
    assert result.metadata["source"] == "adam_and_eve.neckline_soft_exit"


def test_order_block_no_reaction_emits_limitation_metadata() -> None:
    result = pattern_soft_invalidation_for_event(
        SimpleNamespace(pattern_type="ORDER_BLOCK"),
        _plan(),
    )

    assert result.rule is None
    assert result.metadata["schema_version"] == "pattern_soft_invalidation_v1"
    assert result.metadata["supported"] is False
    assert result.metadata["source"] == "order_block.no_reaction_stop"
    assert "not expressible as a simple close rule" in result.metadata["limitation"]


def test_missing_soft_invalidation_fields_omit_rule() -> None:
    assert soft_invalidation_for_event(SimpleNamespace(pattern_type="FAIR_VALUE_GAP"), _plan()) is None
