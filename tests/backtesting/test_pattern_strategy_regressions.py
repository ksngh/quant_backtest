from __future__ import annotations

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def test_full_exit_does_not_use_remaining_quantity_as_entry_quantity() -> None:
    candles = [
        {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1},
        {"timestamp": 2, "open": 99, "high": 99, "low": 99, "close": 99, "volume": 1},
    ]
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=0.8),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=0.8, metadata={"remaining_quantity_ratio": 0.0}),
        ],
        config=StrategyEngineConfig(starting_cash=10000, trade_quantity=1.0),
    )

    assert result.executions[0].side == "BUY"
    assert result.executions[0].quantity > 0
    assert result.executions[1].side == "SELL"
    assert result.executions[1].quantity > 0


def test_zero_cost_engine_has_equal_gross_and_net_pnl() -> None:
    candles = [
        {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1},
        {"timestamp": 2, "open": 110, "high": 110, "low": 110, "close": 110, "volume": 1},
    ]
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
        ],
    )

    assert result.summary.gross_pnl == result.summary.net_pnl
    for execution in result.executions:
        if execution.side == "SELL":
            assert execution.gross_pnl == execution.net_pnl
