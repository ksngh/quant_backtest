from __future__ import annotations

import json
import socket

import pandas as pd

from quant_bitcoin.backtesting import strategy_postgres_runner_cli
from quant_bitcoin.backtesting import strategy_postgres_runner_core
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType


class FakeProvider:
    def __init__(self, candles: pd.DataFrame) -> None:
        self.candles = candles

    def load(self) -> pd.DataFrame:
        return self.candles


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01T00:00:00Z", periods=2, freq="min"),
            "open": [100.0, 110.0],
            "high": [100.0, 110.0],
            "low": [100.0, 110.0],
            "close": [100.0, 110.0],
            "volume": [1.0, 1.0],
        }
    )


def test_strategy_cli_outputs_buy_sell_not_entry(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *args, **kwargs: FakeProvider(_candles()),
    )

    class StubStrategy:
        strategy_name = "STUB_PATTERN_STRATEGY"
        strategy_key = "STUB"

    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "_build_actions",
        lambda candles, strategy_key: (
            StubStrategy(),
            [
                StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
                StrategyAction(StrategyActionType.EXIT_LONG, timestamp=candles.iloc[1]["timestamp"], quantity=1.0),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert [row["side"] for row in output["executions"]] == ["BUY", "SELL"]
    assert output["summary"]["buy_count"] == 1
    assert output["summary"]["sell_count"] == 1


def test_strategy_cli_no_exchange_network_calls(monkeypatch) -> None:
    def fail_socket(*args, **kwargs):
        raise AssertionError("strategy CLI tests must not open sockets")

    monkeypatch.setattr(socket, "socket", fail_socket)
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *args, **kwargs: FakeProvider(_candles().iloc[:0]),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 0
