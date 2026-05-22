from pathlib import Path
import ast

import pytest

from quant_bitcoin.patterns import (
    FairValueGapRiskExitConfig,
    RiskExitPlanStatus,
    create_fair_value_gap_risk_exit_plan,
)
from quant_bitcoin.patterns.fair_value_gap import PatternEvent
from quant_bitcoin.risk import RiskExitTargetSource


def _event(direction: str = "BULLISH") -> PatternEvent:
    is_bullish = direction == "BULLISH"
    return PatternEvent(
        event_id=f"FAIR_VALUE_GAP:{direction}:test",
        pattern_type="FAIR_VALUE_GAP",
        direction=direction,
        pattern_status="VALID",
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp="2026-05-18T00:02:00Z",
        start_index=0,
        end_index=2,
        candle_1_index=0,
        candle_2_index=1,
        candle_3_index=2,
        zone_low=100.0,
        zone_high=110.0,
        zone_mid=105.0,
        gap_size=10.0,
        gap_size_atr=1.0,
        fill_ratio=0.0,
        fvg_state="FRESH",
        displacement_confirmed=True,
        displacement_direction=direction,
        volume_ratio=2.0,
        liquidity_pass=None,
        spread_pass=None,
        structure_context=None,
        support_resistance_context=None,
        pattern_score=0.8,
        entry_reference=105.0,
        stop_reference=98.0 if is_bullish else 112.0,
        target_reference=119.0 if is_bullish else 91.0,
        risk_reward=2.0,
        reason="test event",
    )


def test_bullish_fvg_low_stop_with_atr_buffer() -> None:
    plan = create_fair_value_gap_risk_exit_plan(_event("BULLISH"))

    assert plan.structural_stop_source == "fvg_zone_low"
    assert plan.risk_plan.structural_stop == pytest.approx(100.0)
    assert plan.risk_plan.atr == pytest.approx(10.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(2.0)
    assert plan.risk_plan.stop_price == pytest.approx(98.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(7.0)


def test_bearish_fvg_high_stop_with_atr_buffer() -> None:
    plan = create_fair_value_gap_risk_exit_plan(_event("BEARISH"))

    assert plan.structural_stop_source == "fvg_zone_high"
    assert plan.risk_plan.structural_stop == pytest.approx(110.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(2.0)
    assert plan.risk_plan.stop_price == pytest.approx(112.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(7.0)


def test_fvg_midpoint_reaction_rule_metadata_for_long_and_short() -> None:
    long_plan = create_fair_value_gap_risk_exit_plan(
        _event("BULLISH"),
        config=FairValueGapRiskExitConfig(reaction_failure_bars=6),
    )
    short_plan = create_fair_value_gap_risk_exit_plan(
        _event("BEARISH"),
        config=FairValueGapRiskExitConfig(reaction_failure_bars=7),
    )

    assert long_plan.reaction_failure.enabled is True
    assert long_plan.reaction_failure.rule == "fvg_midpoint_reaction_failure"
    assert long_plan.reaction_failure.midpoint_price == pytest.approx(105.0)
    assert long_plan.reaction_failure.favorable_close_condition == "close > fvg_midpoint"
    assert long_plan.reaction_failure.max_bars_after_entry == 6
    assert long_plan.risk_plan.time_stop.max_bars_in_trade == 6
    assert short_plan.reaction_failure.favorable_close_condition == "close < fvg_midpoint"
    assert short_plan.reaction_failure.max_bars_after_entry == 7


def test_targets_include_r_multiple_fvg_boundary_and_structure_candidates() -> None:
    plan = create_fair_value_gap_risk_exit_plan(
        _event("BULLISH"),
        structural_targets=[116.0, 125.0],
    )

    assert plan.fvg_boundary_target == pytest.approx(110.0)
    assert plan.structural_targets == pytest.approx((110.0, 116.0, 125.0, 119.0))
    assert [target.name for target in plan.risk_plan.targets] == ["TP1", "TP2", "TP3"]
    assert plan.risk_plan.targets[0].source == RiskExitTargetSource.R_MULTIPLE
    assert plan.risk_plan.targets[0].price == pytest.approx(112.0)
    assert plan.risk_plan.targets[1].source == RiskExitTargetSource.STRUCTURE
    assert plan.risk_plan.targets[1].price == pytest.approx(110.0)
    assert plan.risk_plan.targets[1].metadata == {"rule": "nearest_actionable_structure"}


def test_missing_liquidity_targets_are_optional_and_not_fabricated() -> None:
    plan = create_fair_value_gap_risk_exit_plan(_event("BULLISH"))

    assert plan.structural_targets == pytest.approx((110.0, 119.0))


def test_minimum_profit_filter_can_skip_poor_risk_reward_plan() -> None:
    plan = create_fair_value_gap_risk_exit_plan(
        _event("BULLISH"),
        config=FairValueGapRiskExitConfig(
            r_multiples=(0.5, 2.0, 3.0),
            minimum_first_target_r=0.8,
        ),
    )

    assert plan.risk_plan.status == RiskExitPlanStatus.SKIPPED
    assert "first actionable target is below minimum_first_target_r" in plan.risk_plan.reasons[0]


def test_rejects_atr_buffer_multiplier_outside_fvg_guidance() -> None:
    with pytest.raises(ValueError, match="atr_buffer_multiplier must be between 0.1 and 0.3"):
        FairValueGapRiskExitConfig(atr_buffer_multiplier=0.5)


def test_fair_value_gap_risk_exit_module_does_not_import_exchange_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/fair_value_gap_risk_exit.py")
    tree = ast.parse(source_path.read_text())
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)

    assert not any(module.startswith("quant_bitcoin.market_data") for module in imported_modules)
    assert not any(module.startswith("quant_bitcoin.execution") for module in imported_modules)
    assert not any("binance" in module.lower() for module in imported_modules)
