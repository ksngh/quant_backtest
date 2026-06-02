from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.strategies.actions import StrategyActionType, StrategyQuantityMode
from quant_bitcoin.strategies.lookback_return_momentum import (
    LookbackReturnMomentumCostAwareConfig,
    LookbackReturnMomentumConfig,
    LookbackReturnSignal,
    build_lookback_return_momentum_actions,
    calculate_atr_risk_context,
    cost_aware_entry_filter_decision,
    calculate_lookback_return_momentum_signal,
    calculate_momentum_return,
    calculate_risk_levels,
    config_for_timeframe,
)


def _candles(closes: list[float], *, highs: list[float] | None = None, lows: list[float] | None = None) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-05-20T00:00:00Z", periods=len(closes), freq="min"),
            "open": closes,
            "high": highs if highs is not None else closes,
            "low": lows if lows is not None else closes,
            "close": closes,
            "volume": [1.0] * len(closes),
        }
    )


def test_momentum_return_uses_current_and_lookback_close() -> None:
    candles = _candles([100.0, 101.0, 103.0])

    assert calculate_momentum_return(candles, lookback_bars=2) == pytest.approx(0.03)


def test_momentum_return_sign_for_rising_falling_and_unchanged_prices() -> None:
    assert calculate_momentum_return(_candles([100.0, 101.0]), lookback_bars=1) > 0
    assert calculate_momentum_return(_candles([100.0, 99.0]), lookback_bars=1) < 0
    assert calculate_momentum_return(_candles([100.0, 100.0]), lookback_bars=1) == pytest.approx(0.0)


def test_signal_threshold_boundaries() -> None:
    config = LookbackReturnMomentumConfig(lookback_bars=1, entry_threshold=0.01)

    assert calculate_lookback_return_momentum_signal(_candles([100.0, 101.0]), config).signal is LookbackReturnSignal.LONG
    assert calculate_lookback_return_momentum_signal(_candles([100.0, 99.0]), config).signal is LookbackReturnSignal.SHORT
    assert calculate_lookback_return_momentum_signal(_candles([100.0, 100.5]), config).signal is LookbackReturnSignal.NONE


def test_insufficient_lookback_and_invalid_denominator_do_not_signal() -> None:
    config = LookbackReturnMomentumConfig(lookback_bars=2, entry_threshold=0.01)

    insufficient = calculate_lookback_return_momentum_signal(_candles([100.0, 101.0]), config)
    invalid = calculate_lookback_return_momentum_signal(_candles([0.0, 100.0, 101.0]), config)

    assert insufficient.signal is LookbackReturnSignal.NONE
    assert insufficient.reason == "INSUFFICIENT_LOOKBACK"
    assert invalid.signal is LookbackReturnSignal.NONE
    assert invalid.reason == "INVALID_CLOSE"


def test_fixed_percent_risk_levels_are_side_specific_when_explicit() -> None:
    config = LookbackReturnMomentumConfig(
        risk_distance_mode="fixed_pct",
        risk_distance_pct=0.002,
        stop_loss_r=1.0,
        take_profit_r=1.5,
    )

    long_risk = calculate_risk_levels(100.0, "LONG", config)
    short_risk = calculate_risk_levels(100.0, "SHORT", config)

    assert long_risk.r_distance == pytest.approx(0.2)
    assert long_risk.stop_price == pytest.approx(99.8)
    assert long_risk.take_profit_price == pytest.approx(100.3)
    assert short_risk.r_distance == pytest.approx(0.2)
    assert short_risk.stop_price == pytest.approx(100.2)
    assert short_risk.take_profit_price == pytest.approx(99.7)


def test_atr_risk_levels_are_side_specific() -> None:
    config = LookbackReturnMomentumConfig(
        risk_distance_mode="atr",
        stop_loss_atr_multiple=1.0,
        take_profit_atr_multiple=1.0,
    )

    long_risk = calculate_risk_levels(100.0, "LONG", config, atr_value=2.0)
    short_risk = calculate_risk_levels(100.0, "SHORT", config, atr_value=2.0)

    assert long_risk.risk_distance_mode == "atr"
    assert long_risk.r_distance == pytest.approx(2.0)
    assert long_risk.stop_price == pytest.approx(98.0)
    assert long_risk.take_profit_price == pytest.approx(102.0)
    assert long_risk.atr_value == pytest.approx(2.0)
    assert short_risk.r_distance == pytest.approx(2.0)
    assert short_risk.stop_price == pytest.approx(102.0)
    assert short_risk.take_profit_price == pytest.approx(98.0)


def test_strategy_version_flows_to_config_and_action_metadata() -> None:
    config = LookbackReturnMomentumConfig(
        strategy_version="v2",
        risk_distance_mode="atr",
        atr_period=1,
        lookback_bars=1,
        entry_threshold=0.001,
    )

    actions = build_lookback_return_momentum_actions(
        _candles([100.0, 101.0], highs=[101.0, 102.0], lows=[99.0, 100.0]),
        config=config,
    )

    assert config.to_metadata()["strategy_version"] == "v2"
    assert actions[0].action_type is StrategyActionType.ENTER_LONG
    assert actions[0].metadata["strategy_version"] == "v2"


def test_atr_context_uses_completed_signal_candle_without_future_candle() -> None:
    config = LookbackReturnMomentumConfig(risk_distance_mode="atr", atr_period=2)
    candles = _candles(
        [100.0, 101.0, 200.0],
        highs=[101.0, 103.0, 250.0],
        lows=[99.0, 100.0, 150.0],
    )

    signal_context = calculate_atr_risk_context(candles.iloc[:2], config)
    future_context = calculate_atr_risk_context(candles, config)

    assert signal_context["atr_is_valid"] is True
    assert signal_context["atr_value"] == pytest.approx(2.5)
    assert signal_context["current_candle_included"] is True
    assert signal_context["requires_closed_candle"] is True
    assert future_context["atr_value"] != pytest.approx(signal_context["atr_value"])


def test_build_actions_blocks_duplicate_entries_while_position_is_open() -> None:
    config = LookbackReturnMomentumConfig(
        risk_distance_mode="fixed_pct",
        lookback_bars=1,
        entry_threshold=0.001,
        holding_bars=3,
        stop_loss_r=100.0,
        take_profit_r=100.0,
    )
    candles = _candles(
        [100.0, 101.0, 102.0, 90.0, 91.0],
        highs=[100.0, 101.0, 102.0, 90.0, 91.0],
        lows=[100.0, 101.0, 102.0, 90.0, 91.0],
    )

    actions = build_lookback_return_momentum_actions(candles, config=config)

    entries = [action for action in actions if action.action_type in (StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT)]
    exits = [action for action in actions if action.action_type in (StrategyActionType.EXIT_LONG, StrategyActionType.EXIT_SHORT)]
    assert len(entries) == 1
    assert entries[0].action_type is StrategyActionType.ENTER_LONG
    assert len(exits) == 1
    assert exits[0].metadata["exit_reason"] == "TIME_EXIT"


def test_time_exit_closes_at_close_after_holding_bars() -> None:
    config = LookbackReturnMomentumConfig(
        risk_distance_mode="fixed_pct",
        lookback_bars=1,
        entry_threshold=0.001,
        holding_bars=2,
        stop_loss_r=100.0,
        take_profit_r=100.0,
    )
    candles = _candles([100.0, 101.0, 101.5, 102.0])

    actions = build_lookback_return_momentum_actions(candles, config=config)

    assert actions[-1].action_type is StrategyActionType.EXIT_LONG
    assert actions[-1].requested_price == pytest.approx(102.0)
    assert actions[-1].quantity == 1.0
    assert actions[-1].quantity_mode is StrategyQuantityMode.POSITION_RATIO
    assert actions[-1].metadata["exit_reason"] == "TIME_EXIT"
    assert actions[-1].metadata["bars_since_entry"] == 2


def test_long_same_candle_stop_and_target_resolves_to_stop_first() -> None:
    config = LookbackReturnMomentumConfig(risk_distance_mode="fixed_pct", lookback_bars=1, entry_threshold=0.001)
    candles = _candles(
        [100.0, 101.0, 101.0],
        highs=[100.0, 101.0, 101.5],
        lows=[100.0, 101.0, 100.7],
    )

    actions = build_lookback_return_momentum_actions(candles, config=config)

    assert actions[0].action_type is StrategyActionType.ENTER_LONG
    assert actions[1].action_type is StrategyActionType.EXIT_LONG
    assert actions[1].requested_price == pytest.approx(100.798)
    assert actions[1].metadata["exit_reason"] == "STOP_LOSS"
    assert actions[1].metadata["ambiguous_stop_target"] is True
    assert actions[1].metadata["realized_r_multiple"] == pytest.approx(-1.0)


def test_short_stop_and_target_are_calculated_separately() -> None:
    config = LookbackReturnMomentumConfig(risk_distance_mode="fixed_pct", lookback_bars=1, entry_threshold=0.001)
    candles = _candles(
        [100.0, 99.0, 99.0],
        highs=[100.0, 99.0, 99.1],
        lows=[100.0, 99.0, 98.6],
    )

    actions = build_lookback_return_momentum_actions(candles, config=config)

    assert actions[0].action_type is StrategyActionType.ENTER_SHORT
    assert actions[1].action_type is StrategyActionType.EXIT_SHORT
    assert actions[1].requested_price == pytest.approx(98.703)
    assert actions[1].metadata["exit_reason"] == "TAKE_PROFIT"
    assert actions[1].metadata["realized_r_multiple"] == pytest.approx(1.5)


def test_cost_aware_filter_blocks_infeasible_long_entry() -> None:
    config = LookbackReturnMomentumConfig(risk_distance_mode="atr", atr_period=1, lookback_bars=1, entry_threshold=0.001)
    cost_config = LookbackReturnMomentumCostAwareConfig(
        enabled=True,
        min_net_reward_bps=0.0,
        min_net_rr=1.0,
        fee_bps=20.0,
        spread_bps=0.0,
        slippage_bps=0.0,
        liquidity_role="TAKER",
        cost_profile_name="unit_test",
    )

    actions = build_lookback_return_momentum_actions(
        _candles([100.0, 101.0], highs=[101.0, 102.0], lows=[99.0, 100.0]),
        config=config,
        cost_aware_config=cost_config,
    )

    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.SKIP
    assert actions[0].reason == "COST_INFEASIBLE_NET_RR"
    metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert metadata["blocked"] is True
    assert metadata["estimated_round_trip_cost_bps"] == pytest.approx(40.0)
    assert metadata["net_reward_bps"] > 0.0
    assert metadata["net_rr"] < 1.0
    assert metadata["risk_distance_mode"] == "atr"
    assert metadata["atr_period"] == 1
    assert actions[0].metadata["entry_status"] == "REJECTED"


def test_cost_aware_filter_blocks_infeasible_short_entry() -> None:
    config = LookbackReturnMomentumConfig(risk_distance_mode="atr", atr_period=1, lookback_bars=1, entry_threshold=0.001)
    cost_config = LookbackReturnMomentumCostAwareConfig(
        enabled=True,
        min_net_reward_bps=0.0,
        min_net_rr=1.0,
        fee_bps=20.0,
        spread_bps=0.0,
        slippage_bps=0.0,
        liquidity_role="TAKER",
        cost_profile_name="unit_test",
    )

    actions = build_lookback_return_momentum_actions(
        _candles([100.0, 99.0], highs=[101.0, 100.0], lows=[99.0, 98.0]),
        config=config,
        cost_aware_config=cost_config,
    )

    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.SKIP
    assert actions[0].reason == "COST_INFEASIBLE_NET_RR"
    metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert metadata["blocked"] is True
    assert metadata["estimated_round_trip_cost_bps"] == pytest.approx(40.0)
    assert metadata["net_reward_bps"] > 0.0
    assert metadata["net_rr"] < 1.0
    assert metadata["risk_distance_mode"] == "atr"
    assert metadata["atr_period"] == 1


def test_cost_aware_filter_attaches_metadata_to_accepted_long_entry() -> None:
    config = LookbackReturnMomentumConfig(risk_distance_mode="atr", atr_period=1, lookback_bars=1, entry_threshold=0.001)
    cost_config = LookbackReturnMomentumCostAwareConfig(
        enabled=True,
        min_net_reward_bps=0.0,
        min_net_rr=1.0,
        fee_bps=0.0,
        spread_bps=0.0,
        slippage_bps=0.0,
        liquidity_role="TAKER",
        cost_profile_name="unit_test",
    )

    actions = build_lookback_return_momentum_actions(
        _candles([100.0, 101.0], highs=[101.0, 102.0], lows=[99.0, 100.0]),
        config=config,
        cost_aware_config=cost_config,
    )

    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.ENTER_LONG
    metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert metadata["blocked"] is False
    assert metadata["net_reward_bps"] > 0.0
    assert metadata["net_rr"] == pytest.approx(1.0)
    assert metadata["risk_distance_mode"] == "atr"
    assert metadata["atr_period"] == 1
    assert metadata["block_reason"] is None


def test_minimum_atr_bps_filter_blocks_small_atr_candidate() -> None:
    config = LookbackReturnMomentumConfig(
        risk_distance_mode="atr",
        atr_period=1,
        lookback_bars=1,
        entry_threshold=0.001,
        minimum_atr_bps=250.0,
    )

    actions = build_lookback_return_momentum_actions(
        _candles([100.0, 101.0], highs=[101.0, 102.0], lows=[99.0, 100.0]),
        config=config,
    )

    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.SKIP
    assert actions[0].reason == "ATR_TOO_SMALL_FOR_COST"
    assert actions[0].metadata["entry_status"] == "REJECTED"
    assert actions[0].metadata["atr_bps"] == pytest.approx(2.0 / 101.0 * 10_000.0)
    minimum_filter = actions[0].metadata["minimum_atr_bps_filter"]
    assert minimum_filter["enabled"] is True
    assert minimum_filter["blocked"] is True
    assert minimum_filter["minimum_atr_bps"] == pytest.approx(250.0)
    assert minimum_filter["block_reason"] == "ATR_TOO_SMALL_FOR_COST"


def test_asymmetric_atr_target_can_pass_cost_aware_gate_after_costs() -> None:
    config = LookbackReturnMomentumConfig(
        risk_distance_mode="atr",
        atr_period=1,
        lookback_bars=1,
        entry_threshold=0.001,
        stop_loss_atr_multiple=1.0,
        take_profit_atr_multiple=3.0,
        minimum_atr_bps=100.0,
    )
    cost_config = LookbackReturnMomentumCostAwareConfig(
        enabled=True,
        min_net_reward_bps=0.0,
        min_net_rr=1.0,
        fee_bps=20.0,
        spread_bps=0.0,
        slippage_bps=0.0,
        liquidity_role="TAKER",
        cost_profile_name="unit_test",
    )

    actions = build_lookback_return_momentum_actions(
        _candles([100.0, 101.0], highs=[101.0, 102.0], lows=[99.0, 100.0]),
        config=config,
        cost_aware_config=cost_config,
    )

    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.ENTER_LONG
    assert "minimum_atr_bps_filter_v1" in actions[0].metadata["filters_enabled"]
    assert "cost_aware_entry_filter_v1" in actions[0].metadata["filters_enabled"]
    assert actions[0].metadata["minimum_atr_bps"] == pytest.approx(100.0)
    assert actions[0].metadata["atr_bps"] == pytest.approx(2.0 / 101.0 * 10_000.0)
    cost_metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert cost_metadata["blocked"] is False
    assert cost_metadata["estimated_round_trip_cost_bps"] == pytest.approx(40.0)
    assert cost_metadata["net_reward_bps"] > 0.0
    assert cost_metadata["net_rr"] > 1.0
    assert cost_metadata["take_profit_atr_multiple"] == pytest.approx(3.0)


def test_cost_aware_filter_attaches_metadata_to_accepted_short_entry() -> None:
    config = LookbackReturnMomentumConfig(risk_distance_mode="atr", atr_period=1, lookback_bars=1, entry_threshold=0.001)
    cost_config = LookbackReturnMomentumCostAwareConfig(
        enabled=True,
        min_net_reward_bps=0.0,
        min_net_rr=1.0,
        fee_bps=0.0,
        spread_bps=0.0,
        slippage_bps=0.0,
        liquidity_role="TAKER",
        cost_profile_name="unit_test",
    )

    actions = build_lookback_return_momentum_actions(
        _candles([100.0, 99.0], highs=[101.0, 100.0], lows=[99.0, 98.0]),
        config=config,
        cost_aware_config=cost_config,
    )

    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.ENTER_SHORT
    metadata = actions[0].metadata["cost_aware_entry_filter"]
    assert metadata["blocked"] is False
    assert metadata["net_reward_bps"] > 0.0
    assert metadata["net_rr"] == pytest.approx(1.0)
    assert metadata["risk_distance_mode"] == "atr"
    assert metadata["atr_period"] == 1
    assert "cost_aware_entry_filter_v1" in actions[0].metadata["filters_enabled"]


def test_cost_aware_filter_uses_volatility_adjusted_slippage() -> None:
    config = LookbackReturnMomentumCostAwareConfig(
        enabled=True,
        min_net_reward_bps=0.0,
        min_net_rr=1.0,
        slippage_bps=1.0,
        minimum_slippage_bps=2.0,
        volatility_slippage_multiplier=0.1,
    )
    risk = calculate_risk_levels(
        100.0,
        "LONG",
        LookbackReturnMomentumConfig(risk_distance_mode="fixed_pct"),
    )

    decision = cost_aware_entry_filter_decision(
        risk,
        {"high": 102.0, "low": 98.0, "close": 100.0},
        config,
    )

    assert decision["volatility_bps"] == pytest.approx(400.0)
    assert decision["effective_slippage_bps"] == pytest.approx(41.0)


def test_timeframe_defaults() -> None:
    assert config_for_timeframe("1m").lookback_bars == 20
    assert config_for_timeframe("5m").lookback_bars == 12
    assert config_for_timeframe("15m").lookback_bars == 8
    assert config_for_timeframe("15m").entry_threshold == pytest.approx(0.002)
    assert config_for_timeframe("15m").risk_distance_mode == "atr"
    assert config_for_timeframe("15m").atr_period == 14
    assert config_for_timeframe("15m").minimum_atr_bps == pytest.approx(0.0)


def test_invalid_atr_blocks_entry_with_diagnostic_metadata() -> None:
    config = LookbackReturnMomentumConfig(
        risk_distance_mode="atr",
        atr_period=14,
        lookback_bars=1,
        entry_threshold=0.001,
    )

    actions = build_lookback_return_momentum_actions(
        _candles([100.0, 101.0], highs=[101.0, 102.0], lows=[99.0, 100.0]),
        config=config,
    )

    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.SKIP
    assert actions[0].reason == "INVALID_ATR_RISK_DISTANCE"
    assert actions[0].metadata["entry_status"] == "REJECTED"
    assert actions[0].metadata["atr_is_valid"] is False
    assert actions[0].metadata["atr_metadata"]["atr_period"] == 14
