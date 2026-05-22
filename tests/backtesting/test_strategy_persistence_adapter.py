from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from quant_bitcoin.backtesting.strategy_engine import run_strategy_backtest_engine
from quant_bitcoin.backtesting.strategy_persistence_adapter import build_strategy_engine_persistence_payload
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


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


def test_trade_metadata_preserves_action_and_position_side() -> None:
    _, payload = _payload()

    first_trade = payload.trades[0]
    assert first_trade.signal == "BUY"
    assert first_trade.metadata["action_type"] == "ENTER_LONG"
    assert first_trade.metadata["position_side"] == "LONG"
    assert first_trade.metadata["execution_side"] == "BUY"


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
    assert marker.signal == "BUY"
    assert [trade["trade_sequence"] for trade in marker.metadata["trades"]] == [1, 2]
    assert [trade["signal"] for trade in marker.metadata["trades"]] == ["BUY", "SELL"]
