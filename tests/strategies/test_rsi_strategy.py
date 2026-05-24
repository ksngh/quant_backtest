from __future__ import annotations

import socket

import pandas as pd
import pytest

from quant_bitcoin.strategies import (
    RsiSignalMode,
    RsiSmoothingMethod,
    RsiStrategy,
    Signal,
    calculate_rsi,
)
from quant_bitcoin.strategies.rsi import STANDARD_CANDLE_COLUMNS

from quant_bitcoin.strategies.actions import StrategyActionType
from quant_bitcoin.strategies.rsi_actions import RsiActionStrategy


def make_candles(closes: list[float]) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01", periods=len(closes), freq="min")
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": closes,
            "high": [close + 1 for close in closes],
            "low": [close - 1 for close in closes],
            "close": closes,
            "volume": [1.0] * len(closes),
        }
    )


def test_rsi_strategy_returns_buy_when_latest_rsi_is_below_buy_threshold():
    candles = make_candles([100, 99, 98, 97, 96, 95])

    signal = RsiStrategy(window=3, buy_threshold=30, sell_threshold=70).generate_signal(
        candles
    )

    assert signal is Signal.BUY


def test_rsi_strategy_returns_sell_when_latest_rsi_is_above_sell_threshold():
    candles = make_candles([100, 101, 102, 103, 104, 105])

    signal = RsiStrategy(window=3, buy_threshold=30, sell_threshold=70).generate_signal(
        candles
    )

    assert signal is Signal.SELL


def test_rsi_strategy_returns_hold_when_latest_rsi_is_between_thresholds():
    candles = make_candles([100, 101, 100, 101, 100, 101])

    signal = RsiStrategy(window=3, buy_threshold=30, sell_threshold=70).generate_signal(
        candles
    )

    assert signal is Signal.HOLD


def test_rsi_strategy_returns_hold_when_not_enough_candles_for_rsi():
    candles = make_candles([100, 99, 98])

    signal = RsiStrategy(window=5, buy_threshold=30, sell_threshold=70).generate_signal(
        candles
    )

    assert signal is Signal.HOLD


def test_calculate_rsi_consumes_standard_candle_schema():
    candles = make_candles([100, 101, 102, 101, 103])

    rsi = calculate_rsi(candles, window=3)

    assert list(candles.columns) == list(STANDARD_CANDLE_COLUMNS)
    assert len(rsi) == len(candles)
    assert rsi.iloc[-1] == pytest.approx(75.0)


def test_calculate_rsi_supports_wilder_smoothing_when_opted_in():
    candles = make_candles([100, 101, 102, 101, 103, 104])

    rsi = calculate_rsi(
        candles,
        window=3,
        smoothing_method=RsiSmoothingMethod.WILDER,
    )

    assert pd.isna(rsi.iloc[0])
    assert pd.isna(rsi.iloc[1])
    assert pd.isna(rsi.iloc[2])
    assert rsi.iloc[3] == pytest.approx(66.6666667)
    assert rsi.iloc[4] == pytest.approx(83.3333333)
    assert rsi.iloc[5] == pytest.approx(87.8787879)


def test_calculate_rsi_rejects_missing_standard_candle_columns():
    candles = make_candles([100, 101, 102]).drop(columns=["volume"])

    with pytest.raises(ValueError, match="missing required columns: volume"):
        calculate_rsi(candles, window=2)


def test_calculate_rsi_rejects_non_numeric_close_values():
    candles = make_candles([100, 101, 102])
    candles["close"] = candles["close"].astype(object)
    candles.loc[1, "close"] = "not-a-number"

    with pytest.raises(ValueError, match="non-numeric close values"):
        calculate_rsi(candles, window=2)


def test_calculate_rsi_rejects_unknown_smoothing_method():
    candles = make_candles([100, 101, 102])

    with pytest.raises(ValueError, match="smoothing method must be SIMPLE or WILDER"):
        calculate_rsi(candles, window=2, smoothing_method="ema")


@pytest.mark.parametrize(
    "strategy_kwargs",
    [
        {"window": 0},
        {"buy_threshold": -1},
        {"sell_threshold": 101},
        {"buy_threshold": 70, "sell_threshold": 30},
    ],
)
def test_rsi_strategy_rejects_invalid_configuration(strategy_kwargs):
    with pytest.raises(ValueError):
        RsiStrategy(**strategy_kwargs)


def test_rsi_strategy_rejects_invalid_signal_mode():
    with pytest.raises(ValueError, match="signal mode must be LEVEL or CROSSING"):
        RsiStrategy(signal_mode="pulse")


def test_rsi_strategy_does_not_open_network_connections(monkeypatch):
    candles = make_candles([100, 99, 98, 97, 96, 95])

    def fail_socket_creation(*args, **kwargs):
        raise AssertionError("RSI strategy must not create network sockets")

    monkeypatch.setattr(socket, "socket", fail_socket_creation)

    signal = RsiStrategy(window=3, buy_threshold=30, sell_threshold=70).generate_signal(
        candles
    )

    assert signal is Signal.BUY


def test_rsi_level_mode_preserves_repeated_threshold_signal_contract():
    candles = make_candles([100, 101, 102, 101, 100, 99])

    crossing_signal = RsiStrategy(
        window=3,
        buy_threshold=40,
        sell_threshold=70,
        signal_mode=RsiSignalMode.CROSSING,
    ).generate_signal(candles.iloc[:5])
    repeated_level_signal = RsiStrategy(
        window=3,
        buy_threshold=40,
        sell_threshold=70,
        signal_mode=RsiSignalMode.LEVEL,
    ).generate_signal(candles)

    assert crossing_signal is Signal.BUY
    assert repeated_level_signal is Signal.BUY


def test_rsi_crossing_mode_suppresses_repeated_oversold_buy_signal():
    candles = make_candles([100, 101, 102, 101, 100, 99])
    strategy = RsiStrategy(
        window=3,
        buy_threshold=40,
        sell_threshold=70,
        signal_mode=RsiSignalMode.CROSSING,
    )

    assert strategy.generate_signal(candles.iloc[:5]) is Signal.BUY
    assert strategy.generate_signal(candles) is Signal.HOLD


def test_rsi_crossing_mode_suppresses_repeated_overbought_sell_signal():
    candles = make_candles([100, 99, 98, 99, 100, 101])
    strategy = RsiStrategy(
        window=3,
        buy_threshold=30,
        sell_threshold=60,
        signal_mode=RsiSignalMode.CROSSING,
    )

    assert strategy.generate_signal(candles.iloc[:5]) is Signal.SELL
    assert strategy.generate_signal(candles) is Signal.HOLD


def test_rsi_action_strategy_emits_enter_long_when_oversold_and_flat():
    candles = make_candles([100, 99, 98, 97, 96, 95])
    actions = RsiActionStrategy(window=3, buy_threshold=30, sell_threshold=70).evaluate(
        candles, portfolio_state={"position": 0.0}
    )
    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.ENTER_LONG


def test_rsi_action_strategy_emits_exit_long_when_overbought_and_long():
    candles = make_candles([100, 101, 102, 103, 104, 105])
    actions = RsiActionStrategy(window=3, buy_threshold=30, sell_threshold=70).evaluate(
        candles, portfolio_state={"position": 1.0}
    )
    assert len(actions) == 1
    assert actions[0].action_type is StrategyActionType.EXIT_LONG


def test_rsi_action_strategy_crossing_mode_suppresses_repeated_flat_entry():
    candles = make_candles([100, 101, 102, 101, 100, 99])
    strategy = RsiActionStrategy(
        window=3,
        buy_threshold=40,
        sell_threshold=70,
        signal_mode=RsiSignalMode.CROSSING,
    )

    crossing_actions = strategy.evaluate(
        candles.iloc[:5], portfolio_state={"position": 0.0}
    )
    repeated_actions = strategy.evaluate(candles, portfolio_state={"position": 0.0})

    assert len(crossing_actions) == 1
    assert crossing_actions[0].action_type is StrategyActionType.ENTER_LONG
    assert repeated_actions == []
