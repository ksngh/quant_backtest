from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.strategies.actions import StrategyActionType, StrategyQuantityMode
from quant_bitcoin.strategies.lookback_return_momentum import (
    LookbackReturnMomentumConfig,
    LookbackReturnSignal,
    build_lookback_return_momentum_actions,
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


def test_fixed_percent_risk_levels_are_side_specific() -> None:
    config = LookbackReturnMomentumConfig(risk_distance_pct=0.002, stop_loss_r=1.0, take_profit_r=1.5)

    long_risk = calculate_risk_levels(100.0, "LONG", config)
    short_risk = calculate_risk_levels(100.0, "SHORT", config)

    assert long_risk.r_distance == pytest.approx(0.2)
    assert long_risk.stop_price == pytest.approx(99.8)
    assert long_risk.take_profit_price == pytest.approx(100.3)
    assert short_risk.r_distance == pytest.approx(0.2)
    assert short_risk.stop_price == pytest.approx(100.2)
    assert short_risk.take_profit_price == pytest.approx(99.7)


def test_build_actions_blocks_duplicate_entries_while_position_is_open() -> None:
    config = LookbackReturnMomentumConfig(
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
    config = LookbackReturnMomentumConfig(lookback_bars=1, entry_threshold=0.001)
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
    config = LookbackReturnMomentumConfig(lookback_bars=1, entry_threshold=0.001)
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


def test_timeframe_defaults() -> None:
    assert config_for_timeframe("1m").lookback_bars == 20
    assert config_for_timeframe("5m").lookback_bars == 12
    assert config_for_timeframe("15m").lookback_bars == 8
    assert config_for_timeframe("15m").entry_threshold == pytest.approx(0.002)
