from __future__ import annotations

import socket

import pandas as pd
import pytest

from quant_bitcoin.backtesting.basic import BasicBacktester, BacktestResult, BacktestSummary
from quant_bitcoin.market_data import CsvCandleDataProvider
from quant_bitcoin.strategies import RsiStrategy, Signal


class SequenceStrategy:
    def __init__(self, signals: list[Signal]) -> None:
        self.signals = signals
        self.calls: list[pd.DataFrame] = []

    def generate_signal(self, candles: pd.DataFrame) -> Signal:
        self.calls.append(candles)
        return self.signals[len(self.calls) - 1]


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


def test_backtest_simulates_basic_buy_and_sell_result():
    candles = make_candles([100, 110, 120])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.SELL])

    result = BasicBacktester(starting_cash=1_000, trade_quantity=2).run(
        candles, strategy
    )

    assert result.starting_cash == 1_000
    assert result.ending_cash == 1_040
    assert result.ending_position == 0
    assert result.final_price == 120
    assert result.final_equity == 1_040
    assert [(trade.signal, trade.price, trade.quantity) for trade in result.trades] == [
        (Signal.BUY, 100, 2),
        (Signal.SELL, 120, 2),
    ]


def test_backtest_keeps_open_position_in_final_equity():
    candles = make_candles([100, 125])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD])

    result = BasicBacktester(starting_cash=1_000, trade_quantity=1).run(
        candles, strategy
    )

    assert result.ending_cash == 900
    assert result.ending_position == 1
    assert result.final_price == 125
    assert result.final_equity == 1_025
    assert len(result.trades) == 1


def test_backtest_result_includes_deterministic_summary_for_closed_trade():
    candles = make_candles([100, 110, 125])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.SELL])

    result = BasicBacktester(starting_cash=1_000, trade_quantity=2).run(
        candles, strategy
    )

    assert result.summary == BacktestSummary(
        starting_cash=1_000,
        ending_cash=1_050,
        ending_position=0.0,
        final_price=125.0,
        final_equity=1_050.0,
        total_return=0.05,
        trade_count=2,
        buy_count=1,
        sell_count=1,
    )


def test_backtest_summary_reports_open_position_and_trade_counts():
    candles = make_candles([100, 115, 125])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.HOLD])

    result = BasicBacktester(starting_cash=1_000, trade_quantity=2).run(
        candles, strategy
    )

    assert result.summary.starting_cash == 1_000
    assert result.summary.ending_cash == 800
    assert result.summary.ending_position == 2
    assert result.summary.final_price == 125
    assert result.summary.final_equity == 1_050
    assert result.summary.total_return == pytest.approx(0.05)
    assert result.summary.trade_count == 1
    assert result.summary.buy_count == 1
    assert result.summary.sell_count == 0


def test_backtest_summary_handles_zero_starting_cash_without_division_error():
    candles = make_candles([100, 101])
    strategy = SequenceStrategy([Signal.HOLD, Signal.HOLD])

    result = BasicBacktester(starting_cash=0, trade_quantity=1).run(candles, strategy)

    assert result.summary.starting_cash == 0
    assert result.summary.final_equity == 0
    assert result.summary.total_return == 0
    assert result.summary.trade_count == 0


def test_backtest_result_can_be_constructed_with_original_fields():
    result = BacktestResult(
        starting_cash=1_000,
        ending_cash=1_000,
        ending_position=0,
        final_price=None,
        final_equity=1_000,
        trades=(),
    )

    assert result.summary == BacktestSummary(
        starting_cash=0.0,
        ending_cash=0.0,
        ending_position=0.0,
        final_price=None,
        final_equity=0.0,
        total_return=0.0,
        trade_count=0,
        buy_count=0,
        sell_count=0,
    )


def test_backtest_calls_strategy_with_incremental_candle_history():
    candles = make_candles([100, 101, 102])
    strategy = SequenceStrategy([Signal.HOLD, Signal.HOLD, Signal.HOLD])

    result = BasicBacktester().run(candles, strategy)

    assert result.trades == ()
    assert [len(call) for call in strategy.calls] == [1, 2, 3]
    assert all(
        list(call.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
        for call in strategy.calls
    )


def test_backtest_ignores_sell_while_flat_and_duplicate_buy_while_in_position():
    candles = make_candles([100, 110, 120, 130])
    strategy = SequenceStrategy([Signal.SELL, Signal.BUY, Signal.BUY, Signal.SELL])

    result = BasicBacktester(starting_cash=1_000, trade_quantity=1).run(
        candles, strategy
    )

    assert [(trade.signal, trade.price) for trade in result.trades] == [
        (Signal.BUY, 110),
        (Signal.SELL, 130),
    ]
    assert result.final_equity == 1_020


def test_backtest_runs_with_local_csv_provider_fixture(tmp_path):
    csv_path = tmp_path / "candles.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2024-01-01 00:00:00,100,101,99,100,1\n"
        "2024-01-01 00:01:00,110,111,109,110,1\n"
        "2024-01-01 00:02:00,120,121,119,120,1\n"
    )
    candles = CsvCandleDataProvider(csv_path).load()
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.SELL])

    result = BasicBacktester(starting_cash=1_000, trade_quantity=1).run(
        candles, strategy
    )

    assert result.final_equity == 1_020
    assert len(result.trades) == 2


def test_backtest_runs_with_rsi_strategy_default_contract():
    candles = make_candles([100, 99, 98, 99, 100, 101])
    strategy = RsiStrategy(window=2, buy_threshold=30, sell_threshold=70)

    result = BasicBacktester(starting_cash=1_000, trade_quantity=1).run(
        candles, strategy
    )

    assert [(trade.signal, trade.price) for trade in result.trades] == [
        (Signal.BUY, 98),
        (Signal.SELL, 100),
    ]
    assert result.final_equity == 1_002


def test_backtest_rejects_missing_standard_candle_columns():
    candles = make_candles([100, 101]).drop(columns=["volume"])
    strategy = SequenceStrategy([Signal.HOLD, Signal.HOLD])

    with pytest.raises(ValueError, match="missing required columns: volume"):
        BasicBacktester().run(candles, strategy)


def test_backtest_rejects_unsorted_timestamps():
    candles = make_candles([100, 101])
    candles = candles.iloc[[1, 0]].reset_index(drop=True)
    strategy = SequenceStrategy([Signal.HOLD, Signal.HOLD])

    with pytest.raises(ValueError, match="sorted ascending by timestamp"):
        BasicBacktester().run(candles, strategy)


def test_backtest_rejects_non_numeric_close_values():
    candles = make_candles([100, 101])
    candles["close"] = candles["close"].astype(object)
    candles.loc[1, "close"] = "not-a-number"
    strategy = SequenceStrategy([Signal.HOLD, Signal.HOLD])

    with pytest.raises(ValueError, match="non-numeric values in column: close"):
        BasicBacktester().run(candles, strategy)


def test_backtest_rejects_invalid_configuration():
    with pytest.raises(ValueError, match="starting cash must be non-negative"):
        BasicBacktester(starting_cash=-1)
    with pytest.raises(ValueError, match="trade quantity must be positive"):
        BasicBacktester(trade_quantity=0)


def test_backtest_does_not_open_network_connections(monkeypatch):
    candles = make_candles([100, 110, 120])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.SELL])

    def fail_socket_creation(*args, **kwargs):
        raise AssertionError("backtest must not create network sockets")

    monkeypatch.setattr(socket, "socket", fail_socket_creation)

    result = BasicBacktester(starting_cash=1_000, trade_quantity=1).run(
        candles, strategy
    )

    assert result.final_equity == 1_020
