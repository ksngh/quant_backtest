from pathlib import Path
import ast

import pandas as pd
import pytest

from quant_bitcoin.patterns import (
    DiamondRiskExitConfig,
    RiskExitPlanStatus,
    create_diamond_risk_exit_plan,
)
from quant_bitcoin.patterns.diamond import DiamondEvent
from quant_bitcoin.risk import RiskExitTargetSource


def _event(direction: str = "BULLISH") -> DiamondEvent:
    is_bullish = direction == "BULLISH"
    return DiamondEvent(
        event_id=f"DIAMOND_PATTERN:{direction}:test",
        pattern_type="DIAMOND_PATTERN",
        direction=direction,
        pattern_status="VALID",
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp="2026-05-18T00:10:00Z",
        start_index=1,
        end_index=10,
        expansion_start_index=1,
        diamond_center_index=4,
        contraction_end_index=8,
        breakout_index=10,
        source_pivot_indices=(1, 2, 3, 4, 5, 6, 7, 8),
        upper_boundary_slope=-3.0,
        upper_boundary_intercept=125.0,
        lower_boundary_slope=3.0,
        lower_boundary_intercept=72.0,
        upper_boundary_value=95.0,
        lower_boundary_value=102.0,
        expansion_high_slope=5.0,
        expansion_low_slope=-5.0,
        contraction_high_slope=-3.0,
        contraction_low_slope=3.0,
        expansion_range_change=20.0,
        expansion_range_change_atr=2.0,
        contraction_range_change=12.0,
        contraction_range_change_rate=0.6,
        pattern_height=30.0,
        pattern_height_atr=3.0,
        breakout_price=112.0 if is_bullish else 85.0,
        breakout_distance=17.0,
        breakout_distance_atr=1.7,
        atr=10.0,
        volume_ratio=2.0,
        liquidity_pass=None,
        spread_pass=None,
        displacement_confirmed=True,
        split_position=4,
        expansion_pivot_count=4,
        contraction_pivot_count=4,
        boundary_touch_count=4,
        boundary_deviation_atr=0.0,
        alternating_pivot_score=1.0,
        pattern_score=0.8,
        entry_reference=112.0 if is_bullish else 85.0,
        stop_reference=102.0 if is_bullish else 95.0,
        target_reference=142.0 if is_bullish else 55.0,
        risk_reward=3.0,
        reason="test event",
    )


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": "2026-05-18T00:00:00Z", "high": 101.0, "low": 99.0},
            {"timestamp": "2026-05-18T00:01:00Z", "high": 105.0, "low": 95.0},
            {"timestamp": "2026-05-18T00:02:00Z", "high": 110.0, "low": 90.0},
            {"timestamp": "2026-05-18T00:03:00Z", "high": 115.0, "low": 85.0},
            {"timestamp": "2026-05-18T00:04:00Z", "high": 109.0, "low": 91.0},
            {"timestamp": "2026-05-18T00:05:00Z", "high": 103.0, "low": 97.0},
            {"timestamp": "2026-05-18T00:06:00Z", "high": 104.0, "low": 96.0},
            {"timestamp": "2026-05-18T00:07:00Z", "high": 108.0, "low": 92.0},
            {"timestamp": "2026-05-18T00:08:00Z", "high": 106.0, "low": 94.0},
            {"timestamp": "2026-05-18T00:09:00Z", "high": 100.0, "low": 98.0},
            {"timestamp": "2026-05-18T00:10:00Z", "high": 114.0, "low": 111.0},
        ]
    )


def test_bullish_hard_stop_from_last_internal_pivot_low_with_atr_buffer() -> None:
    plan = create_diamond_risk_exit_plan(_event("BULLISH"), candles=_candles())

    assert plan.structural_stop_source == "last_internal_pivot_low"
    assert plan.internal_pivot_reference == pytest.approx(94.0)
    assert plan.risk_plan.structural_stop == pytest.approx(94.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(2.0)
    assert plan.risk_plan.stop_price == pytest.approx(92.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(20.0)


def test_bearish_hard_stop_from_last_internal_pivot_high_with_atr_buffer() -> None:
    plan = create_diamond_risk_exit_plan(_event("BEARISH"), candles=_candles())

    assert plan.structural_stop_source == "last_internal_pivot_high"
    assert plan.internal_pivot_reference == pytest.approx(106.0)
    assert plan.risk_plan.structural_stop == pytest.approx(106.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(2.0)
    assert plan.risk_plan.stop_price == pytest.approx(108.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(23.0)


def test_missing_candles_falls_back_to_event_stop_reference() -> None:
    plan = create_diamond_risk_exit_plan(_event("BULLISH"))

    assert plan.structural_stop_source == "event_stop_reference"
    assert plan.internal_pivot_reference is None
    assert plan.risk_plan.structural_stop == pytest.approx(102.0)


def test_measured_target_uses_diamond_height_by_direction() -> None:
    bullish = create_diamond_risk_exit_plan(_event("BULLISH"), candles=_candles())
    bearish = create_diamond_risk_exit_plan(_event("BEARISH"), candles=_candles())

    assert bullish.measured_target == pytest.approx(142.0)
    assert bearish.measured_target == pytest.approx(55.0)
    assert bullish.risk_plan.targets[2].source == RiskExitTargetSource.MEASURED
    assert bullish.risk_plan.targets[2].price == pytest.approx(142.0)
    assert bullish.risk_plan.targets[2].metadata["target_source"] == "MEASURED"
    assert bullish.risk_plan.target_semantics["detector_target_reference"] == pytest.approx(142.0)
    assert bullish.risk_plan.target_semantics["measured_targets"][0]["price"] == pytest.approx(142.0)


def test_soft_invalidation_metadata_for_close_back_inside_range() -> None:
    bullish = create_diamond_risk_exit_plan(_event("BULLISH"), candles=_candles())
    bearish = create_diamond_risk_exit_plan(_event("BEARISH"), candles=_candles())

    assert bullish.soft_invalidation.enabled is True
    assert bullish.soft_invalidation.rule == "diamond_close_back_inside_range"
    assert bullish.soft_invalidation.invalidates_when == "close <= upper_boundary_value"
    assert bearish.soft_invalidation.invalidates_when == "close >= lower_boundary_value"


def test_one_r_time_stop_metadata_and_minimum_filter_skip_case() -> None:
    plan = create_diamond_risk_exit_plan(
        _event("BULLISH"),
        config=DiamondRiskExitConfig(
            time_stop_bars=8,
            r_multiples=(0.5, 2.0, 3.0),
            minimum_first_target_r=0.8,
        ),
    )

    assert plan.risk_plan.time_stop.max_bars_in_trade == 8
    assert plan.risk_plan.time_stop.required_r_multiple == pytest.approx(1.0)
    assert plan.risk_plan.status == RiskExitPlanStatus.SKIPPED
    assert "first actionable target is below minimum_first_target_r" in plan.risk_plan.reasons[0]


def test_rejects_atr_buffer_multiplier_outside_diamond_guidance() -> None:
    with pytest.raises(ValueError, match="atr_buffer_multiplier must be between 0.2 and 0.5"):
        DiamondRiskExitConfig(atr_buffer_multiplier=0.6)


def test_diamond_risk_exit_module_does_not_import_exchange_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/diamond_risk_exit.py")
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
