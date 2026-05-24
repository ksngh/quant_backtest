from pathlib import Path
import ast

import pandas as pd
import pytest

from quant_bitcoin.patterns import (
    RiskExitPlanStatus,
    RiskExitTargetSource,
    TrendlineBreakRiskExitConfig,
    create_trendline_break_risk_exit_plan,
)
from quant_bitcoin.patterns.trendline_break import TrendlineBreakEvent


def _event(direction: str = "BULLISH") -> TrendlineBreakEvent:
    is_bullish = direction == "BULLISH"
    return TrendlineBreakEvent(
        event_id=f"TRENDLINE_BREAK:{direction}:test",
        pattern_type="TRENDLINE_BREAK",
        direction=direction,
        pattern_status="VALID",
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp="2026-05-18T00:02:00Z",
        start_index=0,
        end_index=2,
        trendline_type=(
            "DESCENDING_RESISTANCE" if is_bullish else "ASCENDING_SUPPORT"
        ),
        trendline_slope=-1.0 if is_bullish else 1.0,
        trendline_intercept=102.0 if is_bullish else 98.0,
        touch_count=2,
        fit_pivot_count=2,
        validation_touch_count=0,
        source_pivot_indices=(0, 1),
        fit_pivot_indices=(0, 1),
        validation_touch_indices=(),
        touch_deviations=(0.0, 0.0),
        trendline_value=100.0,
        break_price=102.0 if is_bullish else 98.0,
        break_distance=2.0,
        break_distance_atr=0.2,
        atr=10.0,
        volume_ratio=2.0,
        liquidity_pass=None,
        spread_pass=None,
        displacement_confirmed=True,
        retest_entry_eligible=False,
        retest_wait_bars=None,
        follow_through_bars=0,
        pattern_score=0.8,
        entry_reference=100.0,
        stop_reference=95.0 if is_bullish else 105.0,
        target_reference=116.0 if is_bullish else 84.0,
        risk_reward=2.0,
        reason="test event",
    )


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": "2026-05-18T00:00:00Z", "high": 101.0, "low": 99.0},
            {"timestamp": "2026-05-18T00:01:00Z", "high": 103.0, "low": 97.0},
            {"timestamp": "2026-05-18T00:02:00Z", "high": 104.0, "low": 96.0},
        ]
    )


def test_bullish_stop_uses_min_breakout_low_and_retest_pivot_low() -> None:
    plan = create_trendline_break_risk_exit_plan(
        _event("BULLISH"),
        candles=_candles(),
        retest_pivot_price=94.0,
    )

    assert plan.structural_stop_source == "breakout_candle_and_retest_pivot"
    assert plan.risk_plan.structural_stop == pytest.approx(94.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(2.0)
    assert plan.risk_plan.stop_price == pytest.approx(92.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(8.0)


def test_bullish_fallback_stop_uses_breakout_low_then_event_stop_reference() -> None:
    breakout_plan = create_trendline_break_risk_exit_plan(
        _event("BULLISH"),
        candles=_candles(),
    )
    event_fallback_plan = create_trendline_break_risk_exit_plan(_event("BULLISH"))

    assert breakout_plan.structural_stop_source == "breakout_candle"
    assert breakout_plan.risk_plan.structural_stop == pytest.approx(96.0)
    assert breakout_plan.risk_plan.stop_price == pytest.approx(94.0)
    assert event_fallback_plan.structural_stop_source == "event_stop_reference"
    assert event_fallback_plan.risk_plan.structural_stop == pytest.approx(95.0)
    assert event_fallback_plan.risk_plan.stop_price == pytest.approx(93.0)


def test_bearish_stop_uses_high_side_formula() -> None:
    plan = create_trendline_break_risk_exit_plan(
        _event("BEARISH"),
        candles=_candles(),
        retest_pivot_price=106.0,
    )

    assert plan.structural_stop_source == "breakout_candle_and_retest_pivot"
    assert plan.risk_plan.structural_stop == pytest.approx(106.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(2.0)
    assert plan.risk_plan.stop_price == pytest.approx(108.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(8.0)


def test_r_targets_and_structural_target_metadata_are_present() -> None:
    plan = create_trendline_break_risk_exit_plan(
        _event("BULLISH"),
        candles=_candles(),
        retest_pivot_price=94.0,
        prior_swing_targets=[112.0, 118.0],
    )

    targets = plan.risk_plan.targets
    assert [target.name for target in targets] == ["TP1", "TP2", "TP3"]
    assert targets[0].source == RiskExitTargetSource.R_MULTIPLE
    assert targets[0].price == pytest.approx(108.0)
    assert targets[1].source == RiskExitTargetSource.STRUCTURE
    assert targets[1].price == pytest.approx(112.0)
    assert targets[1].metadata["rule"] == "nearest_actionable_structure"
    assert targets[1].metadata["target_source"] == "STRUCTURE"
    assert plan.structural_targets == pytest.approx((112.0, 118.0, 116.0))
    assert plan.risk_plan.target_semantics["detector_target_reference"] == pytest.approx(116.0)
    assert plan.risk_plan.target_semantics["risk_targets"][1]["source"] == "STRUCTURE"


def test_minimum_target_filter_can_skip_poor_risk_reward_plan() -> None:
    plan = create_trendline_break_risk_exit_plan(
        _event("BULLISH"),
        candles=_candles(),
        config=TrendlineBreakRiskExitConfig(
            r_multiples=(0.5, 2.0, 3.0),
            minimum_first_target_r=0.8,
        ),
    )

    assert plan.risk_plan.status == RiskExitPlanStatus.SKIPPED
    assert "first actionable target is below minimum_first_target_r" in plan.risk_plan.reasons[0]


def test_soft_invalidation_and_time_stop_metadata_are_represented() -> None:
    plan = create_trendline_break_risk_exit_plan(
        _event("BEARISH"),
        config=TrendlineBreakRiskExitConfig(follow_through_bars=7),
    )

    assert plan.soft_invalidation.enabled is True
    assert plan.soft_invalidation.rule == "close_reenters_broken_trendline_side"
    assert plan.soft_invalidation.invalidates_when == "close >= trendline_value"
    assert plan.risk_plan.time_stop.max_bars_in_trade == 7
    assert plan.risk_plan.time_stop.required_r_multiple == pytest.approx(1.0)


def test_rejects_atr_buffer_multiplier_outside_trendline_guidance() -> None:
    with pytest.raises(ValueError, match="atr_buffer_multiplier must be between 0.2 and 0.4"):
        TrendlineBreakRiskExitConfig(atr_buffer_multiplier=0.5)


def test_trendline_break_risk_exit_module_does_not_import_exchange_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/trendline_break_risk_exit.py")
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
