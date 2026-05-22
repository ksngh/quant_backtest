from __future__ import annotations

import pytest

import pandas as pd

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1},
            {"timestamp": 2, "open": 110, "high": 110, "low": 110, "close": 110, "volume": 1},
            {"timestamp": 3, "open": 120, "high": 120, "low": 120, "close": 120, "volume": 1},
            {"timestamp": 4, "open": 130, "high": 130, "low": 130, "close": 130, "volume": 1},
        ]
    )


def test_cash_equity_move_and_buy_sell_counts() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
        ],
        config=StrategyEngineConfig(starting_cash=10000, trade_quantity=1.0),
    )

    assert [execution.side for execution in result.executions] == ["BUY", "SELL"]
    assert result.summary.buy_count == 1
    assert result.summary.sell_count == 1
    assert result.summary.ending_cash == 10010
    assert result.summary.ending_position == 0
    assert result.summary.final_equity == 10010
    assert result.summary.total_return == 0.001


def test_partial_exit_quantities_sum_to_entry_and_flatten_position() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.PARTIAL_EXIT_LONG, timestamp=2, quantity=0.33),
            StrategyAction(StrategyActionType.PARTIAL_EXIT_LONG, timestamp=3, quantity=0.33),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=4, quantity=0.34),
        ],
    )

    sell_quantities = [execution.quantity for execution in result.executions if execution.side == "SELL"]
    assert sell_quantities == pytest.approx([0.33, 0.33, 0.34])
    assert sum(sell_quantities) == pytest.approx(1.0)
    assert result.summary.ending_position == 0.0


def test_exit_reason_and_research_metadata_preserved() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=1,
                quantity=1.0,
                reason="PATTERN_CONFIRMED",
                metadata={"pattern_event_id": "event-1", "risk_plan_id": "risk-1"},
            ),
            StrategyAction(
                StrategyActionType.PARTIAL_EXIT_LONG,
                timestamp=2,
                quantity=0.25,
                metadata={"exit_reason": "HARD_STOP", "realized_r_multiple": -1.0},
            ),
            StrategyAction(
                StrategyActionType.PARTIAL_EXIT_LONG,
                timestamp=3,
                quantity=0.25,
                metadata={"exit_reason": "TAKE_PROFIT", "realized_r_multiple": 1.2},
            ),
            StrategyAction(
                StrategyActionType.PARTIAL_EXIT_LONG,
                timestamp=4,
                quantity=0.25,
                metadata={"exit_reason": "SOFT_INVALIDATION", "realized_r_multiple": 0.1},
            ),
            StrategyAction(
                StrategyActionType.EXIT_LONG,
                timestamp=4,
                quantity=0.25,
                metadata={"exit_reason": "TIME_STOP", "realized_r_multiple": 0.0},
            ),
        ],
    )

    buy = result.executions[0]
    sells = [execution for execution in result.executions if execution.side == "SELL"]
    assert buy.reason == "PATTERN_CONFIRMED"
    assert buy.pattern_event_id == "event-1"
    assert buy.metadata["risk_plan_id"] == "risk-1"
    assert [execution.exit_reason for execution in sells] == ["HARD_STOP", "TAKE_PROFIT", "SOFT_INVALIDATION", "TIME_STOP"]
    assert result.summary.average_net_r == (-1.0 + 1.2 + 0.1 + 0.0) / 4
