from dataclasses import replace
from pathlib import Path
import ast

import pytest

from quant_bitcoin.patterns import (
    AdamAndEveRiskExitConfig,
    AdamAndEveStopMode,
    RiskExitPlanStatus,
    create_adam_and_eve_risk_exit_plan,
)
from quant_bitcoin.patterns.adam_and_eve import AdamAndEveEvent
from quant_bitcoin.risk import RiskExitTargetSource


def _event() -> AdamAndEveEvent:
    return AdamAndEveEvent(
        event_id="ADAM_AND_EVE_PATTERN:BULLISH:test",
        pattern_type="ADAM_AND_EVE_PATTERN",
        direction="BULLISH",
        pattern_status="VALID",
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp="2026-05-18T00:12:00Z",
        start_index=2,
        end_index=12,
        adam_low_index=2,
        neckline_pivot_index=4,
        eve_low_index=7,
        breakout_index=12,
        adam_low_price=80.0,
        neckline=100.0,
        eve_low_price=81.0,
        bottom_difference_rate=0.0125,
        adam_bottom_duration=3,
        eve_bottom_duration=8,
        eve_bottom_zone_duration=4,
        adam_local_range_atr=1.4,
        eve_local_range_atr=1.2,
        eve_to_adam_duration_ratio=8.0 / 3.0,
        pattern_height=20.0,
        pattern_height_atr=2.0,
        breakout_price=104.0,
        breakout_distance=4.0,
        breakout_distance_atr=0.4,
        atr=10.0,
        volume_ratio=2.0,
        liquidity_pass=None,
        spread_pass=None,
        displacement_confirmed=True,
        pattern_score=0.8,
        entry_reference=104.0,
        stop_reference=80.0,
        target_reference=124.0,
        risk_reward=20.0 / 24.0,
        reason="test event",
    )


def test_eve_low_stop_with_atr_buffer() -> None:
    plan = create_adam_and_eve_risk_exit_plan(
        _event(),
        config=AdamAndEveRiskExitConfig(atr_buffer_multiplier=0.3),
    )

    assert plan.stop_mode == AdamAndEveStopMode.EVE_LOW
    assert plan.structural_stop_source == "eve_low_price"
    assert plan.risk_plan.structural_stop == pytest.approx(81.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(3.0)
    assert plan.risk_plan.stop_price == pytest.approx(78.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(26.0)


def test_wider_min_adam_eve_stop_mode() -> None:
    plan = create_adam_and_eve_risk_exit_plan(
        _event(),
        config=AdamAndEveRiskExitConfig(stop_mode=AdamAndEveStopMode.WIDER_ADAM_EVE_LOW),
    )

    assert plan.stop_mode == AdamAndEveStopMode.WIDER_ADAM_EVE_LOW
    assert plan.structural_stop_source == "min_adam_eve_low"
    assert plan.risk_plan.structural_stop == pytest.approx(80.0)
    assert plan.risk_plan.stop_price == pytest.approx(77.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(27.0)


def test_measured_target_equals_neckline_plus_pattern_height() -> None:
    plan = create_adam_and_eve_risk_exit_plan(_event())

    assert plan.measured_target == pytest.approx(120.0)
    assert [target.name for target in plan.risk_plan.targets] == ["TP1", "TP2", "TP3"]
    assert plan.risk_plan.targets[0].source == RiskExitTargetSource.R_MULTIPLE
    assert plan.risk_plan.targets[2].source == RiskExitTargetSource.MEASURED
    assert plan.risk_plan.targets[2].price == pytest.approx(120.0)


def test_neckline_soft_exit_metadata_is_present() -> None:
    plan = create_adam_and_eve_risk_exit_plan(_event())

    assert plan.neckline_soft_exit.enabled is True
    assert plan.neckline_soft_exit.neckline == pytest.approx(100.0)
    assert plan.neckline_soft_exit.rule == "adam_and_eve_neckline_reentry"
    assert plan.neckline_soft_exit.invalidates_when == "close < neckline_after_breakout"


def test_nearest_structure_target_is_used_when_supplied() -> None:
    plan = create_adam_and_eve_risk_exit_plan(_event(), structural_targets=[116.0, 130.0])

    assert plan.structural_targets == pytest.approx((116.0, 130.0))
    assert plan.risk_plan.targets[1].source == RiskExitTargetSource.STRUCTURE
    assert plan.risk_plan.targets[1].price == pytest.approx(116.0)


def test_minimum_profit_filter_can_skip_poor_risk_reward_plan() -> None:
    plan = create_adam_and_eve_risk_exit_plan(
        _event(),
        config=AdamAndEveRiskExitConfig(
            r_multiples=(0.5, 2.0, 3.0),
            minimum_first_target_r=0.8,
        ),
    )

    assert plan.risk_plan.status == RiskExitPlanStatus.SKIPPED
    assert "first actionable target is below minimum_first_target_r" in plan.risk_plan.reasons[0]


def test_unsupported_inverse_direction_is_rejected() -> None:
    inverse_event = replace(_event(), direction="BEARISH")

    with pytest.raises(ValueError, match="supports only BULLISH"):
        create_adam_and_eve_risk_exit_plan(inverse_event)


def test_adam_and_eve_risk_exit_module_does_not_import_exchange_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/adam_and_eve_risk_exit.py")
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
