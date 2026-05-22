from __future__ import annotations

import pandas as pd

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 102, "high": 103, "low": 101, "close": 102, "volume": 10},
            {"timestamp": 3, "open": 105, "high": 106, "low": 104, "close": 105, "volume": 10},
        ]
    )


def test_engine_buy_sell_and_equity_accounting() -> None:
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0, metadata={"pattern_event_id": "e1"}),
        StrategyAction(StrategyActionType.PARTIAL_EXIT_LONG, timestamp=2, quantity=0.4, metadata={"exit_reason": "TAKE_PROFIT"}),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=3, quantity=0.6, metadata={"exit_reason": "TIME_STOP"}),
    ]

    result = run_strategy_backtest_engine(_candles(), actions, config=StrategyEngineConfig(starting_cash=10000, trade_quantity=1.0))

    assert result.summary.buy_count == 1
    assert result.summary.sell_count == 2
    assert result.summary.trade_count == 3
    assert result.summary.ending_position == 0
    assert result.summary.ending_cash == 10003.8
    assert result.summary.final_equity == 10003.8
    assert result.executions[0].side == "BUY"
    assert result.executions[0].execution_side == "BUY"
    assert result.executions[0].position_side == "LONG"
    assert result.executions[1].side == "SELL"
    assert result.executions[1].execution_side == "SELL"
    assert result.executions[1].position_side == "LONG"
    assert result.executions[1].quantity == 0.4
    assert result.executions[2].quantity == 0.6
    assert result.executions[1].exit_reason == "TAKE_PROFIT"
    assert result.equity_points[0].equity == 10000
    assert result.equity_points[1].equity == 10002


def test_engine_rejects_unsorted_candles() -> None:
    candles = _candles().iloc[::-1]
    try:
        run_strategy_backtest_engine(candles, [])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "sorted" in str(exc)
