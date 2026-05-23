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


def test_strategy_cli_outputs_position_signal_and_execution_side(monkeypatch, capsys) -> None:
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
        lambda candles, strategy_key, *args, **kwargs: (
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
    assert [row["position_signal"] for row in output["executions"]] == ["LONG_ENTRY", "LONG_EXIT"]
    assert [row["execution_side"] for row in output["executions"]] == ["BUY", "SELL"]
    assert output["summary"]["buy_count"] == 1
    assert output["summary"]["sell_count"] == 1
    assert output["summary"]["metadata"]["performance_metrics"]["interval"] == "1m"


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


def test_strategy_cli_enriched_execution_and_events(monkeypatch, capsys) -> None:
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
        lambda candles, strategy_key, *args, **kwargs: (
            StubStrategy(),
            [
                StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
                StrategyAction(StrategyActionType.EXIT_LONG, timestamp=candles.iloc[1]["timestamp"], quantity=1.0),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert "diagnostics" in output
    assert "execution_side" in output["executions"][0]
    assert "position_signal" in output["executions"][0]
    assert output["diagnostics"]["execution_count"] == 2


def test_strategy_cli_adds_invalid_risk_and_no_fill_warnings(monkeypatch, capsys) -> None:
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
        lambda candles, strategy_key, *args, **kwargs: (
            StubStrategy(),
            [
                StrategyAction(
                    StrategyActionType.SKIP,
                    timestamp=candles.iloc[0]["timestamp"],
                    quantity=0.0,
                    reason="RISK_PLAN_INVALID",
                    metadata={"position_side": "LONG"},
                ),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["summary"]["metadata"]["performance_metrics"]["period_count"] == 1
    assert "invalid risk plan" in output["warnings"]
    assert "no fills" in output["warnings"]


def test_strategy_cli_json_serializes_timestamp_metadata(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *args, **kwargs: FakeProvider(_candles()),
    )

    class StubStrategy:
        strategy_name = "STUB_PATTERN_STRATEGY"
        strategy_key = "STUB"

    def build_actions(candles, strategy_key, *args, **kwargs):
        return (
            StubStrategy(),
            [
                StrategyAction(
                    StrategyActionType.ENTER_LONG,
                    timestamp=candles.iloc[0]["timestamp"],
                    quantity=1.0,
                    metadata={
                        "fill_timestamp": candles.iloc[0]["timestamp"],
                        "nested": {"exit_timestamp": candles.iloc[1]["timestamp"]},
                    },
                ),
                StrategyAction(
                    StrategyActionType.EXIT_LONG,
                    timestamp=candles.iloc[1]["timestamp"],
                    quantity=1.0,
                    metadata={"exit_timestamp": pd.Timestamp("2026-01-01T00:01:00Z")},
                ),
            ],
        )

    monkeypatch.setattr(strategy_postgres_runner_core, "_build_actions", build_actions)

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["executions"][0]["metadata"]["fill_timestamp"] == "2026-01-01T00:00:00Z"
    assert output["executions"][0]["metadata"]["nested"]["exit_timestamp"] == "2026-01-01T00:01:00Z"
    assert output["executions"][1]["metadata"]["exit_timestamp"] == "2026-01-01T00:01:00Z"


def test_strategy_cli_exception_logging_uses_current_signature(monkeypatch) -> None:
    calls: list[str] = []

    def fail_run(argv=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(strategy_postgres_runner_cli, "run", fail_run)
    monkeypatch.setattr(strategy_postgres_runner_cli, "log_runtime_exception", calls.append)

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 1
    assert calls == [strategy_postgres_runner_cli.__name__]
