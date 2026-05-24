from dataclasses import replace
from pathlib import Path
import ast

import pytest

from quant_bitcoin.patterns import (
    CupAndHandleRiskExitConfig,
    RiskExitPlanStatus,
    create_cup_and_handle_risk_exit_plan,
)
from quant_bitcoin.patterns.cup_and_handle import CupAndHandleEvent
from quant_bitcoin.risk import RiskExitTargetSource


def _event() -> CupAndHandleEvent:
    return CupAndHandleEvent(
        event_id="CUP_AND_HANDLE:BULLISH:test",
        pattern_type="CUP_AND_HANDLE",
        direction="BULLISH",
        pattern_status="VALID",
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp="2026-05-18T00:11:00Z",
        start_index=1,
        end_index=11,
        left_rim_index=1,
        cup_bottom_index=4,
        right_rim_index=7,
        handle_low_index=9,
        breakout_index=11,
        left_rim_price=100.0,
        cup_bottom_price=80.0,
        right_rim_price=99.0,
        handle_low_price=94.0,
        neckline=100.0,
        cup_depth=20.0,
        cup_depth_rate=0.2,
        cup_duration=6,
        bottom_zone_duration=3,
        duration_ratio=1.0,
        handle_depth=6.0,
        handle_depth_ratio=0.3,
        handle_duration=4,
        breakout_price=103.0,
        breakout_distance=3.0,
        breakout_distance_atr=0.3,
        atr=10.0,
        volume_ratio=2.0,
        liquidity_pass=None,
        spread_pass=None,
        displacement_confirmed=True,
        prior_uptrend_method="LOCAL",
        prior_uptrend_strength=0.05,
        neckline_retest_status="NOT_REQUESTED",
        neckline_retest_wait_bars=None,
        breakout_follow_through_bars=0,
        handle_quality={
            "handle_depth_ratio": 0.3,
            "handle_duration": 4.0,
            "handle_low_above_cup_midpoint": 1.0,
        },
        detector_target_reference_semantics="detector target_reference = breakout entry_reference + cup_depth; risk planner may rebuild measured targets from neckline/cup_depth.",
        pattern_score=0.8,
        entry_reference=103.0,
        stop_reference=94.0,
        target_reference=123.0,
        risk_reward=20.0 / 9.0,
        reason="test event",
    )


def test_long_handle_low_stop_with_configured_atr_buffer() -> None:
    plan = create_cup_and_handle_risk_exit_plan(
        _event(),
        config=CupAndHandleRiskExitConfig(atr_buffer_multiplier=0.3),
    )

    assert plan.structural_stop_source == "handle_low_price"
    assert plan.risk_plan.structural_stop == pytest.approx(94.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(3.0)
    assert plan.risk_plan.stop_price == pytest.approx(91.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(12.0)
    assert plan.hard_stop.rule == "handle_low_minus_atr_buffer"
    assert plan.hard_stop.structural_stop == pytest.approx(94.0)


def test_measured_target_equals_neckline_plus_cup_depth() -> None:
    plan = create_cup_and_handle_risk_exit_plan(_event())

    assert plan.measured_target == pytest.approx(120.0)
    assert [target.name for target in plan.risk_plan.targets] == ["TP1", "TP2", "TP3"]
    assert plan.risk_plan.targets[0].source == RiskExitTargetSource.R_MULTIPLE
    assert plan.risk_plan.targets[2].source == RiskExitTargetSource.MEASURED
    assert plan.risk_plan.targets[2].price == pytest.approx(120.0)
    assert plan.risk_plan.targets[2].metadata["rule"] == "nearest_actionable_measured"
    assert plan.risk_plan.targets[2].metadata["target_source"] == "MEASURED"
    semantics = plan.risk_plan.target_semantics
    assert semantics["schema_version"] == "target_semantics_v1"
    assert semantics["detector_target_reference"] == pytest.approx(123.0)
    assert semantics["measured_targets"][0]["price"] == pytest.approx(120.0)
    assert semantics["risk_targets"][2]["source"] == "MEASURED"


def test_neckline_soft_exit_metadata_is_present() -> None:
    plan = create_cup_and_handle_risk_exit_plan(_event())

    assert plan.neckline_soft_exit.enabled is True
    assert plan.neckline_soft_exit.neckline == pytest.approx(100.0)
    assert plan.neckline_soft_exit.rule == "cup_and_handle_neckline_reentry"
    assert plan.neckline_soft_exit.invalidates_when == "close < neckline_after_breakout"


def test_nearest_structure_target_is_used_when_supplied() -> None:
    plan = create_cup_and_handle_risk_exit_plan(_event(), structural_targets=[114.0, 130.0])

    assert plan.structural_targets == pytest.approx((114.0, 130.0))
    assert plan.risk_plan.targets[1].source == RiskExitTargetSource.STRUCTURE
    assert plan.risk_plan.targets[1].price == pytest.approx(114.0)
    assert plan.risk_plan.target_semantics["structural_targets"][0]["price"] == pytest.approx(114.0)


def test_minimum_profit_filter_can_skip_poor_risk_reward_plan() -> None:
    plan = create_cup_and_handle_risk_exit_plan(
        _event(),
        config=CupAndHandleRiskExitConfig(
            r_multiples=(0.5, 2.0, 3.0),
            minimum_first_target_r=0.8,
        ),
    )

    assert plan.risk_plan.status == RiskExitPlanStatus.SKIPPED
    assert "first actionable target is below minimum_first_target_r" in plan.risk_plan.reasons[0]


def test_unsupported_inverse_direction_is_rejected() -> None:
    inverse_event = replace(_event(), direction="BEARISH")

    with pytest.raises(ValueError, match="supports only BULLISH"):
        create_cup_and_handle_risk_exit_plan(inverse_event)


def test_rejects_atr_buffer_multiplier_outside_cup_and_handle_guidance() -> None:
    with pytest.raises(ValueError, match="atr_buffer_multiplier must be between 0.3 and 0.6"):
        CupAndHandleRiskExitConfig(atr_buffer_multiplier=0.2)


def test_cup_and_handle_risk_exit_module_does_not_import_exchange_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/cup_and_handle_risk_exit.py")
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
