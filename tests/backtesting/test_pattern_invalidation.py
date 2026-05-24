from __future__ import annotations

from types import SimpleNamespace

from quant_bitcoin.backtesting.pattern_invalidation import soft_invalidation_for_event
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
    rule = soft_invalidation_for_event(
        SimpleNamespace(pattern_type="FAIR_VALUE_GAP", zone_mid=99.5),
        _plan(),
    )

    assert rule is not None
    assert rule.invalidates_when == "close <= fvg_midpoint"
    assert rule.reference_price == 99.5


def test_trendline_break_soft_invalidation_uses_trendline_value() -> None:
    rule = soft_invalidation_for_event(
        SimpleNamespace(pattern_type="TRENDLINE_BREAK", trendline_value=101.0),
        _plan(RiskExitDirection.SHORT),
    )

    assert rule is not None
    assert rule.invalidates_when == "close >= trendline_value"
    assert rule.reference_price == 101.0


def test_neckline_soft_invalidation_uses_neckline_when_present() -> None:
    rule = soft_invalidation_for_event(
        SimpleNamespace(pattern_type="CUP_AND_HANDLE", neckline=98.0),
        _plan(),
    )

    assert rule is not None
    assert rule.invalidates_when == "close < neckline_after_breakout"
    assert rule.reference_price == 98.0


def test_missing_soft_invalidation_fields_omit_rule() -> None:
    assert soft_invalidation_for_event(SimpleNamespace(pattern_type="FAIR_VALUE_GAP"), _plan()) is None
