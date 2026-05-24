from pathlib import Path
import ast

import pytest

from quant_bitcoin.patterns import (
    OrderBlockEntryMode,
    OrderBlockRiskExitConfig,
    RiskExitPlanStatus,
    create_order_block_risk_exit_plan,
)
from quant_bitcoin.risk import RiskExitTargetSource
from quant_bitcoin.patterns.order_block import OrderBlockEvent


def _event(direction: str = "BULLISH") -> OrderBlockEvent:
    is_bullish = direction == "BULLISH"
    return OrderBlockEvent(
        event_id=f"ORDER_BLOCK:{direction}:test",
        pattern_type="ORDER_BLOCK",
        direction=direction,
        pattern_status="VALID",
        symbol="BTCUSDT",
        timeframe="1m",
        timestamp="2026-05-18T00:01:00Z",
        start_index=0,
        end_index=1,
        order_block_state="FRESH",
        source_candle_index=0,
        source_candle_timestamp="2026-05-18T00:00:00Z",
        displacement_candle_index=1,
        displacement_candle_timestamp="2026-05-18T00:01:00Z",
        zone_low=95.0,
        zone_high=105.0,
        zone_mid=100.0,
        zone_size=10.0,
        zone_size_atr=1.0,
        source_mode="SINGLE_CANDLE",
        source_cluster_start_index=0,
        source_cluster_end_index=0,
        source_cluster_size=1,
        zone_definition="FULL_RANGE",
        detector_input_type="OHLCV_HEURISTIC",
        displacement_direction=direction,
        displacement_range_atr=2.0,
        body_ratio=0.8,
        volume_ratio=2.0,
        liquidity_pass=None,
        spread_pass=None,
        structure_confirmed=None,
        structure_event=None,
        support_resistance_context="NO_CONTEXT",
        mitigation_depth=0.0,
        retest_entry_eligible=False,
        retest_wait_bars=None,
        pattern_score=0.8,
        entry_reference=100.0,
        stop_reference=93.0 if is_bullish else 107.0,
        target_reference=116.0 if is_bullish else 84.0,
        risk_reward=2.0,
        reason="test event",
    )


def test_bullish_zone_low_stop_with_default_atr_buffer() -> None:
    plan = create_order_block_risk_exit_plan(_event("BULLISH"))

    assert plan.structural_stop_source == "order_block_zone_low"
    assert plan.entry_mode == OrderBlockEntryMode.ZONE_MID
    assert plan.entry_reference == pytest.approx(100.0)
    assert plan.risk_plan.structural_stop == pytest.approx(95.0)
    assert plan.risk_plan.atr == pytest.approx(10.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(2.0)
    assert plan.risk_plan.stop_price == pytest.approx(93.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(7.0)


def test_bullish_conservative_stop_with_half_atr_buffer() -> None:
    plan = create_order_block_risk_exit_plan(
        _event("BULLISH"),
        config=OrderBlockRiskExitConfig(atr_buffer_multiplier=0.5),
    )

    assert plan.risk_plan.atr_buffer == pytest.approx(5.0)
    assert plan.risk_plan.stop_price == pytest.approx(90.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(10.0)


def test_bearish_mirrored_zone_high_stop() -> None:
    plan = create_order_block_risk_exit_plan(_event("BEARISH"))

    assert plan.structural_stop_source == "order_block_zone_high"
    assert plan.risk_plan.structural_stop == pytest.approx(105.0)
    assert plan.risk_plan.atr_buffer == pytest.approx(2.0)
    assert plan.risk_plan.stop_price == pytest.approx(107.0)
    assert plan.risk_plan.risk_per_unit == pytest.approx(7.0)


def test_zone_midpoint_or_configured_entry_reference_affects_risk_per_unit() -> None:
    midpoint_plan = create_order_block_risk_exit_plan(
        _event("BULLISH"),
        config=OrderBlockRiskExitConfig(entry_mode=OrderBlockEntryMode.ZONE_MID),
    )
    zone_618_plan = create_order_block_risk_exit_plan(
        _event("BULLISH"),
        config=OrderBlockRiskExitConfig(entry_mode=OrderBlockEntryMode.ZONE_618),
    )

    assert midpoint_plan.entry_reference == pytest.approx(100.0)
    assert midpoint_plan.risk_plan.risk_per_unit == pytest.approx(7.0)
    assert zone_618_plan.entry_reference == pytest.approx(98.82)
    assert zone_618_plan.risk_plan.risk_per_unit == pytest.approx(5.82)


def test_structural_targets_include_caller_supplied_and_event_target_metadata() -> None:
    plan = create_order_block_risk_exit_plan(
        _event("BULLISH"),
        structural_targets=[112.0, 118.0],
    )

    assert plan.structural_targets == pytest.approx((112.0, 118.0, 116.0))
    assert [target.name for target in plan.risk_plan.targets] == ["TP1", "TP2", "TP3"]
    assert plan.risk_plan.targets[0].source == RiskExitTargetSource.R_MULTIPLE
    assert plan.risk_plan.targets[1].source == RiskExitTargetSource.STRUCTURE
    assert plan.risk_plan.targets[1].price == pytest.approx(112.0)
    assert plan.risk_plan.targets[1].metadata["rule"] == "nearest_actionable_structure"
    assert plan.risk_plan.targets[1].metadata["target_source"] == "STRUCTURE"
    assert plan.risk_plan.target_semantics["detector_target_reference"] == pytest.approx(116.0)
    assert plan.risk_plan.target_semantics["risk_targets"][1]["source"] == "STRUCTURE"


def test_no_reaction_time_stop_metadata_is_represented_without_trading() -> None:
    plan = create_order_block_risk_exit_plan(
        _event("BULLISH"),
        config=OrderBlockRiskExitConfig(no_reaction_bars=8, no_reaction_required_r=0.5),
    )

    assert plan.no_reaction_stop.enabled is True
    assert plan.no_reaction_stop.rule == "no_reaction_after_order_block_entry"
    assert plan.no_reaction_stop.max_bars_after_entry == 8
    assert plan.no_reaction_stop.required_reaction_r == pytest.approx(0.5)
    assert plan.risk_plan.time_stop.max_bars_in_trade == 8
    assert plan.risk_plan.time_stop.required_r_multiple == pytest.approx(0.5)


def test_minimum_profit_filter_can_skip_poor_risk_reward_plan() -> None:
    plan = create_order_block_risk_exit_plan(
        _event("BULLISH"),
        config=OrderBlockRiskExitConfig(
            r_multiples=(0.5, 2.0, 3.0),
            minimum_first_target_r=0.8,
        ),
    )

    assert plan.risk_plan.status == RiskExitPlanStatus.SKIPPED
    assert "first actionable target is below minimum_first_target_r" in plan.risk_plan.reasons[0]


def test_order_block_risk_exit_module_does_not_import_exchange_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/order_block_risk_exit.py")
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
