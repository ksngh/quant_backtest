from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd

from quant_bitcoin.backtesting.costs import TransactionCostConfig
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.backtesting.strategy_persistence_adapter import build_strategy_engine_persistence_payload
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType, StrategyQuantityMode


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01T00:00:00Z", periods=3, freq="min"),
            "open": [100.0, 110.0, 105.0],
            "high": [100.0, 110.0, 105.0],
            "low": [100.0, 110.0, 105.0],
            "close": [100.0, 110.0, 105.0],
            "volume": [1.0, 1.0, 1.0],
        }
    )


def _payload():
    candles = _candles()
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=candles.iloc[1]["timestamp"], quantity=1.0),
        ],
    )
    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source="postgres",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        strategy_key="TEST",
        strategy_name="TEST_STRATEGY",
        strategy_version="v1",
        strategy_parameters={"window": 14},
        starting_cash=10000.0,
        trade_quantity=1.0,
        engine_name="strategy_engine",
        engine_version="v1",
    )
    return result, payload


def test_graph_points_use_canonical_equity_values() -> None:
    result, payload = _payload()

    assert len(payload.graph_points) == len(result.equity_points)
    assert payload.graph_points[0].equity == result.equity_points[0].equity
    assert payload.graph_points[1].equity == result.equity_points[1].equity
    assert payload.graph_points[1].equity != payload.run.starting_cash


def test_payload_preserves_configured_million_starting_cash() -> None:
    candles = _candles()
    result = run_strategy_backtest_engine(
        candles,
        [StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0)],
        config=StrategyEngineConfig(starting_cash=1_000_000.0),
    )

    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source="postgres",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        strategy_key="TEST",
        strategy_name="TEST_STRATEGY",
        strategy_version="v1",
        strategy_parameters={"window": 14},
        starting_cash=1_000_000.0,
        trade_quantity=1.0,
        engine_name="strategy_engine",
        engine_version="v1",
    )

    assert result.summary.starting_cash == 1_000_000.0
    assert payload.run.starting_cash == 1_000_000.0
    assert payload.result.starting_cash == 1_000_000.0


def test_trade_metadata_preserves_action_and_position_side() -> None:
    _, payload = _payload()

    first_trade = payload.trades[0]
    assert first_trade.signal == "LONG_ENTRY"
    assert first_trade.metadata["action_type"] == "ENTER_LONG"
    assert first_trade.metadata["position_signal"] == "LONG_ENTRY"
    assert first_trade.metadata["side"] == "BUY"
    assert first_trade.metadata["position_side"] == "LONG"
    assert first_trade.metadata["execution_side"] == "BUY"
    assert payload.result.metadata["performance_metrics"]["interval"] == "1m"
    assert payload.result.metadata["trade_attribution"]["trade_metrics"]["completed_trade_count"] == 1
    assert payload.result.metadata["trade_attribution"]["attribution"]["by_position_side"]["LONG"]["net_pnl"] == 10.0


def test_trade_payload_price_is_raw_and_metadata_preserves_effective_cost_breakdown() -> None:
    candles = _candles()
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=candles.iloc[1]["timestamp"], quantity=1.0),
        ],
        config=StrategyEngineConfig(
            transaction_cost_config=TransactionCostConfig(taker_fee_bps=10.0, spread_bps=10.0, slippage_bps=10.0)
        ),
    )

    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source="postgres",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        strategy_key="TEST",
        strategy_name="TEST_STRATEGY",
        strategy_version="v1",
        strategy_parameters={"window": 14},
        starting_cash=10000.0,
        trade_quantity=1.0,
        engine_name="strategy_engine",
        engine_version="v1",
    )

    entry_execution = result.executions[0]
    entry_trade = payload.trades[0]
    assert entry_trade.price == entry_execution.raw_price
    assert entry_trade.metadata["price_semantics"] == "raw_fill_price"
    assert entry_trade.metadata["raw_price"] == entry_execution.raw_price
    assert entry_trade.metadata["effective_price"] == entry_execution.effective_price
    assert entry_trade.metadata["cost_breakdown"]["fee_cost"] == entry_execution.fee_cost
    assert entry_trade.metadata["cost_breakdown"]["total_cost"] == entry_execution.total_cost


def test_trade_metadata_preserves_unknown_json_safe_diagnostics() -> None:
    candles = _candles()
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(
                StrategyActionType.ENTER_LONG,
                timestamp=candles.iloc[0]["timestamp"],
                quantity=1.0,
                metadata={
                    "fill_price_source": "CONFIRMATION_CLOSE",
                    "custom_timestamp": pd.Timestamp("2026-01-01T00:00:00Z"),
                    "custom_tuple": ("alpha", Decimal("1.5")),
                    "custom_action_type": StrategyActionType.ENTER_LONG,
                },
            )
        ],
    )

    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source="postgres",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        strategy_key="TEST",
        strategy_name="TEST_STRATEGY",
        strategy_version="v1",
        strategy_parameters={"window": 14},
        starting_cash=10000.0,
        trade_quantity=1.0,
        engine_name="strategy_engine",
        engine_version="v1",
    )

    trade_metadata = payload.trades[0].metadata
    assert trade_metadata["fill_price_source"] == "CONFIRMATION_CLOSE"
    assert trade_metadata["custom_timestamp"] == "2026-01-01T00:00:00Z"
    assert trade_metadata["custom_tuple"] == ["alpha", 1.5]
    assert trade_metadata["custom_action_type"] == "ENTER_LONG"
    assert payload.graph_points[0].metadata["trades"][0]["fill_price_source"] == "CONFIRMATION_CLOSE"


def test_trade_metadata_preserves_account_state_fields() -> None:
    candles = _candles()
    result = run_strategy_backtest_engine(
        candles,
        [StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=candles.iloc[0]["timestamp"], quantity=1.0)],
    )
    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source="postgres",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        strategy_key="TEST",
        strategy_name="TEST_STRATEGY",
        strategy_version="v1",
        strategy_parameters={"window": 14},
        starting_cash=10000.0,
        trade_quantity=1.0,
        engine_name="strategy_engine",
        engine_version="v1",
    )

    trade_metadata = payload.trades[0].metadata
    assert payload.trades[0].signal == "SHORT_ENTRY"
    assert trade_metadata["execution_side"] == "SELL"
    assert trade_metadata["position_signal"] == "SHORT_ENTRY"
    assert trade_metadata["cash_balance_after"] == result.executions[0].cash_balance_after
    assert trade_metadata["free_cash_after"] == result.executions[0].free_cash_after
    assert trade_metadata["short_proceeds_locked_after"] == result.executions[0].short_proceeds_locked_after
    assert trade_metadata["short_collateral_locked_after"] == result.executions[0].short_collateral_locked_after
    assert payload.graph_points[0].metadata["free_cash"] == result.equity_points[0].free_cash
    assert payload.graph_points[0].metadata["short_collateral_locked"] == result.equity_points[0].short_collateral_locked
    assert payload.graph_points[0].metadata["equity_valuation_price"] == result.equity_points[0].equity_valuation_price


def test_graph_points_preserve_multiple_same_timestamp_executions() -> None:
    candles = _candles()
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
            StrategyAction(StrategyActionType.EXIT_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
        ],
    )

    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source="postgres",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        strategy_key="TEST",
        strategy_name="TEST_STRATEGY",
        strategy_version="v1",
        strategy_parameters={"window": 14},
        starting_cash=10000.0,
        trade_quantity=1.0,
        engine_name="strategy_engine",
        engine_version="v1",
    )

    marker = payload.graph_points[0]
    assert marker.trade_sequence == 1
    assert marker.signal == "LONG_ENTRY"
    assert [trade["trade_sequence"] for trade in marker.metadata["trades"]] == [1, 2]
    assert [trade["signal"] for trade in marker.metadata["trades"]] == ["LONG_ENTRY", "LONG_EXIT"]
    assert [trade["execution_side"] for trade in marker.metadata["trades"]] == ["BUY", "SELL"]


def test_persistence_preserves_ratio_exit_quantity_metadata() -> None:
    candles = _candles()
    result = run_strategy_backtest_engine(
        candles,
        [
            StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=2.0),
            StrategyAction(
                StrategyActionType.PARTIAL_EXIT_LONG,
                timestamp=candles.iloc[1]["timestamp"],
                quantity=0.25,
                metadata={"quantity_ratio": 0.25},
                quantity_mode=StrategyQuantityMode.POSITION_RATIO,
            ),
        ],
    )

    payload = build_strategy_engine_persistence_payload(
        result,
        candles,
        source="postgres",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        strategy_key="TEST",
        strategy_name="TEST_STRATEGY",
        strategy_version="v1",
        strategy_parameters={"window": 14},
        starting_cash=10000.0,
        trade_quantity=1.0,
        engine_name="strategy_engine",
        engine_version="v1",
    )

    partial = payload.trades[1]
    assert partial.quantity == 0.5
    assert partial.metadata["quantity_mode"] == "POSITION_RATIO"
    assert partial.metadata["quantity_ratio"] == 0.25
    assert partial.metadata["resolved_quantity"] == 0.5
    assert payload.graph_points[1].metadata["trades"][0]["quantity_mode"] == "POSITION_RATIO"
    assert payload.graph_points[1].metadata["trades"][0]["resolved_quantity"] == 0.5


def test_run_metadata_runtime_is_included_without_affecting_run_key() -> None:
    _, payload_without_runtime = _payload()
    _, payload_with_runtime = _payload()
    payload_with_runtime = build_strategy_engine_persistence_payload(
        run_strategy_backtest_engine(
            _candles(),
            [
                StrategyAction(StrategyActionType.ENTER_LONG, timestamp=_candles().iloc[0]["timestamp"], quantity=1.0),
                StrategyAction(StrategyActionType.EXIT_LONG, timestamp=_candles().iloc[1]["timestamp"], quantity=1.0),
            ],
        ),
        _candles(),
        source="postgres",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 1, 0, 2, tzinfo=timezone.utc),
        strategy_key="TEST",
        strategy_name="TEST_STRATEGY",
        strategy_version="v1",
        strategy_parameters={"window": 14},
        starting_cash=10000.0,
        trade_quantity=1.0,
        engine_name="strategy_engine",
        engine_version="v1",
        run_metadata={"runtime": {"total_elapsed_ms": 12.3, "runtime_schema_version": "v1"}},
    )
    assert payload_without_runtime.run.run_key == payload_with_runtime.run.run_key
    assert payload_with_runtime.run.metadata["runtime"]["total_elapsed_ms"] == 12.3
