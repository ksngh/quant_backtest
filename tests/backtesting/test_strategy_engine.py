from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.backtesting.sizing import BacktestGuardrailConfig, PositionSizingConfig, PositionSizingMode
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
    assert result.executions[0].position_signal == "LONG_ENTRY"
    assert result.executions[0].position_side == "LONG"
    assert result.executions[1].side == "SELL"
    assert result.executions[1].execution_side == "SELL"
    assert result.executions[1].position_signal == "LONG_PARTIAL_EXIT"
    assert result.executions[1].position_side == "LONG"
    assert result.executions[1].quantity == 0.4
    assert result.executions[2].quantity == 0.6
    assert result.executions[1].exit_reason == "TAKE_PROFIT"
    assert result.equity_points[0].equity == 10000
    assert result.equity_points[1].equity == 10002
    attribution = result.summary.metadata["trade_attribution"]
    assert attribution["trade_metrics"]["completed_trade_count"] == 1
    assert attribution["trade_metrics"]["closing_execution_count"] == 2
    assert attribution["trade_metrics"]["partial_exit_execution_count"] == 1
    assert attribution["trade_metrics"]["expectancy"] == pytest.approx(3.8)
    assert attribution["attribution"]["by_position_side"]["LONG"]["completed_trade_count"] == 1
    assert attribution["attribution"]["by_exit_reason"]["TAKE_PROFIT+TIME_STOP"]["net_pnl"] == pytest.approx(3.8)


def test_engine_rejects_unsorted_candles() -> None:
    candles = _candles().iloc[::-1]
    try:
        run_strategy_backtest_engine(candles, [])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "sorted" in str(exc)


def test_engine_rejects_duplicate_timestamps_before_actions_execute() -> None:
    candles = _candles()
    candles.loc[1, "timestamp"] = candles.loc[0, "timestamp"]
    actions = [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0)]

    with pytest.raises(ValueError, match="duplicate timestamp"):
        run_strategy_backtest_engine(candles, actions)


def test_engine_rejects_invalid_ohlc_before_actions_execute() -> None:
    candles = _candles()
    candles.loc[0, "high"] = 99
    actions = [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0)]

    with pytest.raises(ValueError, match="high below open/close"):
        run_strategy_backtest_engine(candles, actions)


def test_engine_detects_interval_gap_when_configured() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": "2024-01-01T00:02:00Z", "open": 102, "high": 103, "low": 101, "close": 102, "volume": 10},
        ]
    )

    with pytest.raises(ValueError, match="interval gap for 1m"):
        run_strategy_backtest_engine(
            candles,
            [],
            config=StrategyEngineConfig(enforce_candle_continuity=True),
        )


def test_engine_uses_explicit_requested_price_and_fallback_close() -> None:
    candles = _candles()
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0, requested_price=99.0),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
    ]
    result = run_strategy_backtest_engine(candles, actions)
    assert result.executions[0].raw_price == 99.0
    assert result.executions[1].raw_price == 102.0
    assert result.executions[0].execution_equity_after == 10000.0
    assert result.executions[0].mark_to_market_equity_after == 10001.0
    assert result.equity_points[0].equity == 10000.0
    assert result.equity_points[0].equity_valuation_price == 99.0
    assert "entry-candle execution-price equity" in (result.equity_points[0].equity_semantics or "")


def test_entry_candle_equity_uses_execution_price_then_next_close() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 105, "high": 106, "low": 104, "close": 105, "volume": 10},
        ]
    )
    result = run_strategy_backtest_engine(
        candles,
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, requested_price=99.0)],
        config=StrategyEngineConfig(
            starting_cash=10000,
            position_sizing=PositionSizingConfig(PositionSizingMode.CASH_FRACTION, value=1.0),
        ),
    )

    entry = result.executions[0]
    assert entry.quantity == pytest.approx(100.0)
    assert entry.cash_after == pytest.approx(100.0)
    assert entry.execution_equity_after == pytest.approx(10000.0)
    assert entry.mark_to_market_equity_after == pytest.approx(10100.0)
    assert entry.metadata["entry_sizing_valuation_price"] == pytest.approx(100.0)
    assert entry.metadata["conservative_entry_sizing_applied"] is True
    assert result.equity_points[0].equity == pytest.approx(10000.0)
    assert result.equity_points[0].equity_valuation_price == pytest.approx(99.0)
    assert result.equity_points[1].equity == pytest.approx(10600.0)
    assert result.equity_points[1].equity_valuation_price == pytest.approx(105.0)
    assert result.summary.final_equity == pytest.approx(10600.0)
    assert result.summary.metadata["performance_metrics"]["total_return"] == pytest.approx(0.06)


def test_engine_skips_invalid_explicit_price() -> None:
    candles = _candles()
    actions = [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0, requested_price=0.0)]
    result = run_strategy_backtest_engine(candles, actions)
    assert result.summary.trade_count == 0


def test_engine_attaches_market_regime_metadata_without_changing_fills() -> None:
    candles = _candles()
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
    ]
    baseline = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(starting_cash=10000),
    )
    tagged = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(
            starting_cash=10000,
            market_regime_by_timestamp={
                1: {"market_regime": "LOW_VOL_UPTREND", "trend_regime": "UPTREND"},
                2: {"market_regime": "LOW_VOL_UPTREND", "trend_regime": "UPTREND"},
            },
        ),
    )

    assert [execution.price for execution in tagged.executions] == [execution.price for execution in baseline.executions]
    assert [execution.quantity for execution in tagged.executions] == [execution.quantity for execution in baseline.executions]
    assert tagged.executions[0].metadata["market_regime"] == "LOW_VOL_UPTREND"
    assert tagged.executions[0].metadata["market_regime_context"]["trend_regime"] == "UPTREND"
    assert tagged.summary.metadata["trade_attribution"]["attribution"]["by_market_regime"]["LOW_VOL_UPTREND"]["completed_trade_count"] == 1


def test_engine_records_cost_summary_and_volatility_slippage() -> None:
    from quant_bitcoin.backtesting.costs import TransactionCostConfig

    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 110, "low": 90, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 110, "high": 121, "low": 99, "close": 110, "volume": 10},
        ]
    )
    actions = [
        StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
        StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
    ]

    result = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(
            transaction_cost_config=TransactionCostConfig(
                taker_fee_bps=10.0,
                spread_bps=5.0,
                slippage_bps=1.0,
                volatility_slippage_multiplier=0.01,
            )
        ),
    )

    entry, exit_ = result.executions
    assert entry.effective_price > 100.0
    assert exit_.effective_price < 110.0
    assert entry.metadata["volatility_bps"] == pytest.approx(2000.0)
    assert entry.metadata["effective_slippage_bps"] == pytest.approx(21.0)
    assert result.summary.gross_pnl > result.summary.net_pnl
    assert result.summary.metadata["cost_summary"]["total_cost"] == pytest.approx(entry.total_cost + exit_.total_cost)
    assert result.summary.metadata["cost_summary"]["zero_transaction_cost_assumption"] is False
    assert result.summary.metadata["transaction_cost"]["zero_transaction_cost_assumption"] is False


def test_engine_marks_zero_cost_assumption() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0)],
    )

    assert result.summary.metadata["cost_summary"]["zero_transaction_cost_assumption"] is True


def test_engine_sizes_entry_by_equity_risk_fraction() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=1,
                metadata={"risk_per_unit": 100.0},
            )
        ],
        config=StrategyEngineConfig(
            starting_cash=10000.0,
            position_sizing=PositionSizingConfig(PositionSizingMode.EQUITY_RISK_FRACTION, value=0.01),
        ),
    )

    assert result.executions[0].quantity == pytest.approx(1.0)
    assert result.executions[0].metadata["position_sizing_mode"] == "EQUITY_RISK_FRACTION"
    assert result.executions[0].metadata["resolved_risk_amount"] == pytest.approx(100.0)


def test_engine_blocks_risk_fraction_without_risk_per_unit() -> None:
    result = run_strategy_backtest_engine(
        _candles(),
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1)],
        config=StrategyEngineConfig(
            position_sizing=PositionSizingConfig(PositionSizingMode.EQUITY_RISK_FRACTION, value=0.01),
        ),
    )

    assert result.summary.trade_count == 0
    assert result.executions[0].quantity == 0.0
    assert result.executions[0].reason == "MISSING_RISK_PER_UNIT_FOR_RISK_SIZING"
    assert result.executions[0].metadata["block_reason"] == "MISSING_RISK_PER_UNIT_FOR_RISK_SIZING"


def test_engine_blocks_entries_after_consecutive_loss_guard() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
            {"timestamp": 3, "open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
        ]
    )
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=3, quantity=1.0),
        ],
        config=StrategyEngineConfig(guardrails=BacktestGuardrailConfig(max_consecutive_losses=1)),
    )

    assert result.summary.trade_count == 2
    assert result.executions[-1].quantity == 0.0
    assert result.executions[-1].reason == "RISK_GUARD_MAX_CONSECUTIVE_LOSSES"
    assert result.executions[-1].metadata["guardrail_scope"] == "backtest_only"


def test_engine_blocks_entries_after_drawdown_guard() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": 2, "open": 80, "high": 81, "low": 79, "close": 80, "volume": 10},
            {"timestamp": 3, "open": 80, "high": 81, "low": 79, "close": 80, "volume": 10},
        ]
    )
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=1, quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=2, quantity=1.0),
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=3, quantity=1.0),
        ],
        config=StrategyEngineConfig(guardrails=BacktestGuardrailConfig(max_account_drawdown=0.001)),
    )

    assert result.executions[-1].reason == "RISK_GUARD_MAX_DRAWDOWN"


def test_engine_blocks_entries_after_daily_loss_guard() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-01-01T00:00:00Z"), "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": pd.Timestamp("2026-01-01T00:01:00Z"), "open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
            {"timestamp": pd.Timestamp("2026-01-01T00:02:00Z"), "open": 90, "high": 91, "low": 89, "close": 90, "volume": 10},
        ]
    )
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=candles.iloc[1]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[2]["timestamp"], quantity=1.0),
        ],
        config=StrategyEngineConfig(guardrails=BacktestGuardrailConfig(max_daily_loss=5.0)),
    )

    assert result.executions[-1].reason == "RISK_GUARD_MAX_DAILY_LOSS"
