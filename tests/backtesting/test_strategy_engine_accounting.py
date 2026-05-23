from __future__ import annotations

import pytest
import pandas as pd

from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


def _candles() -> pd.DataFrame:
    return pd.DataFrame([
        {"timestamp": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1},
        {"timestamp": 2, "open": 110, "high": 110, "low": 110, "close": 110, "volume": 1},
        {"timestamp": 3, "open": 90, "high": 90, "low": 90, "close": 90, "volume": 1},
        {"timestamp": 4, "open": 95, "high": 95, "low": 95, "close": 95, "volume": 1},
    ])


def test_long_and_short_zero_cost_accounting() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1),
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=3, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=4, quantity=1),
    ])
    assert [e.side for e in result.executions] == ["BUY", "SELL", "SELL", "BUY"]
    assert result.summary.ending_position == 0
    assert result.summary.net_pnl == pytest.approx(5.0)


def test_partial_long_and_short_exits() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=2),
        StrategyAction(StrategyActionType.PARTIAL_EXIT_SHORT, timestamp=2, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=3, quantity=1),
    ])
    qtys = [e.quantity for e in result.executions if e.gross_pnl is not None]
    assert qtys == [1, 1]
    assert result.summary.ending_position == 0


def test_opposite_entry_skip_deterministic() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=2, quantity=1),
    ])
    assert len(result.executions) == 2
    assert result.executions[1].quantity == 0.0
    assert result.executions[1].reason == "OPPOSITE_ENTRY_BLOCKED"
    metrics = result.summary.metadata["execution_metrics"]
    assert result.summary.trade_count == 1
    assert metrics["filled_execution_count"] == 1
    assert metrics["blocked_action_count"] == 1


def test_cost_applied_once_fee_and_not_double_counted() -> None:
    cfg = StrategyEngineConfig(
        transaction_cost_config=TransactionCostConfig(taker_fee_bps=10, spread_bps=10, slippage_bps=10),
        default_liquidity_role=LiquidityRole.TAKER,
    )
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1),
    ], config=cfg)
    entry, exit_ = result.executions
    assert entry.effective_price > entry.raw_price
    assert exit_.effective_price < exit_.raw_price
    assert exit_.net_pnl < exit_.gross_pnl
    assert exit_.net_pnl == pytest.approx(exit_.gross_pnl - exit_.total_cost)


def test_short_drawdown_tracked() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=4, quantity=1),
    ])
    assert result.summary.max_drawdown < 0


def test_profitable_short_realized_pnl_and_win_count() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=2, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=3, quantity=1),
    ])
    close_execution = result.executions[-1]
    assert close_execution.side == "BUY"
    assert close_execution.gross_pnl == pytest.approx(20.0)
    assert close_execution.net_pnl == pytest.approx(20.0)
    assert result.equity_points[-1].realized_pnl == pytest.approx(20.0)
    assert result.summary.win_count == 1
    assert result.summary.loss_count == 0


def test_losing_short_realized_pnl_and_loss_count() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=2, quantity=1),
    ])
    close_execution = result.executions[-1]
    assert close_execution.side == "BUY"
    assert close_execution.gross_pnl == pytest.approx(-10.0)
    assert close_execution.net_pnl == pytest.approx(-10.0)
    assert result.equity_points[-1].realized_pnl == pytest.approx(-10.0)
    assert result.summary.win_count == 0
    assert result.summary.loss_count == 1


def test_allow_short_false_blocks_short_entries_deterministically() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=1, quantity=1)],
        config=StrategyEngineConfig(allow_short=False),
    )
    assert result.summary.trade_count == 0
    assert result.summary.ending_position == 0
    assert result.summary.ending_cash == pytest.approx(10000.0)


def test_summary_includes_short_model_limitations_and_short_performance_metadata() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=2, quantity=1),
        StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=3, quantity=1),
    ])
    metadata = result.summary.metadata
    assert metadata["limitations"] == [
        "No borrow fees modeled",
        "No futures funding modeled",
        "No maintenance margin or liquidation model",
    ]
    assert metadata["short_performance"] == {
        "short_close_count": 1,
        "short_win_count": 1,
        "short_loss_count": 0,
    }


def test_summary_includes_skip_and_partial_exit_metrics() -> None:
    result = run_strategy_backtest_engine(_candles(), [
        StrategyAction(StrategyActionType.SKIP, timestamp=1, quantity=1),
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=2, quantity=2),
        StrategyAction(StrategyActionType.PARTIAL_EXIT_LONG, timestamp=3, quantity=1),
    ])
    metrics = result.summary.metadata["execution_metrics"]
    assert metrics["skipped_action_count"] == 1
    assert metrics["entry_count"] == 1
    assert metrics["exit_count"] == 1
    assert metrics["partial_exit_count"] == 1
    assert metrics["full_exit_count"] == 0
    assert metrics["open_ending_position"] == pytest.approx(1.0)
