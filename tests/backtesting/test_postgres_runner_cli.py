from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import pytest

from quant_bitcoin.backtesting import BasicBacktester
from quant_bitcoin.backtesting import postgres_runner_cli
from quant_bitcoin.strategies import RsiActionStrategy, RsiStrategy


class FakeRepository:
    def __init__(self, database_url: str = "postgresql://example/test") -> None:
        self.database_url = database_url
        self.payloads: list[Any] = []

    def save_completed_backtest(self, payload: Any) -> int:
        self.payloads.append(payload)
        return 42


class FakeProvider:
    def __init__(self, candles: pd.DataFrame) -> None:
        self.candles = candles
        self.load_calls = 0

    def load(self) -> pd.DataFrame:
        self.load_calls += 1
        return self.candles


def make_candles(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2024-01-01T00:00:00Z", periods=len(closes), freq="min"
            ),
            "open": closes,
            "high": [close + 1 for close in closes],
            "low": [close - 1 for close in closes],
            "close": closes,
            "volume": [1.0] * len(closes),
        }
    )


def test_parser_accepts_postgres_backtest_configuration():
    args = postgres_runner_cli.build_parser().parse_args(
        [
            "--database-url",
            "postgresql://example/test",
            "--source",
            "binance_spot",
            "--symbol",
            "ETHUSDT",
            "--interval",
            "5m",
            "--start-time",
            "2024-01-01T00:00:00Z",
            "--end-time",
            "2024-01-02T00:00:00+00:00",
            "--starting-cash",
            "2500",
            "--trade-quantity",
            "0.25",
            "--rsi-window",
            "7",
            "--rsi-buy-threshold",
            "20",
            "--rsi-sell-threshold",
            "80",
        ]
    )

    assert args.database_url == "postgresql://example/test"
    assert args.source == "binance_spot"
    assert args.symbol == "ETHUSDT"
    assert args.interval == "5m"
    assert args.start_time == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert args.end_time == datetime(2024, 1, 2, tzinfo=timezone.utc)
    assert args.starting_cash == 2500
    assert args.trade_quantity == 0.25
    assert args.rsi_window == 7
    assert args.rsi_buy_threshold == 20
    assert args.rsi_sell_threshold == 80


def test_postgres_backtest_cli_wires_provider_strategy_and_backtester(capsys):
    calls: dict[str, Any] = {}
    provider = FakeProvider(make_candles([100, 95, 90, 85, 80]))

    def provider_factory(database_url: str, **kwargs: Any) -> FakeProvider:
        calls["provider"] = {"database_url": database_url, **kwargs}
        return provider

    repository = FakeRepository()

    exit_code = postgres_runner_cli.main(
        [
            "--database-url",
            "postgresql://example/test",
            "--source",
            "binance_spot",
            "--symbol",
            "BTCUSDT",
            "--interval",
            "1m",
            "--start-time",
            "2024-01-01T00:00:00Z",
            "--end-time",
            "2024-01-01T00:04:00Z",
            "--starting-cash",
            "1000",
            "--trade-quantity",
            "1",
            "--rsi-window",
            "2",
            "--rsi-buy-threshold",
            "30",
            "--rsi-sell-threshold",
            "70",
        ],
        provider_factory=provider_factory,
        strategy_factory=RsiActionStrategy,
        repository_factory=lambda database_url: repository,
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert provider.load_calls == 1
    assert repository.database_url == "postgresql://example/test"
    assert len(repository.payloads) == 1
    assert output["backtest_run_id"] == 42
    assert calls["provider"] == {
        "database_url": "postgresql://example/test",
        "source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "start_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "end_time": datetime(2024, 1, 1, 0, 4, tzinfo=timezone.utc),
    }
    assert output["candle_count"] == 5
    assert output["input"] == {
        "source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-01T00:04:00Z",
    }
    assert output["strategy"] == {
        "name": "RSI",
        "window": 2,
        "buy_threshold": 30.0,
        "sell_threshold": 70.0,
    }
    assert output["summary"]["starting_cash"] == 1000.0
    assert output["summary"]["trade_count"] == 1
    assert output["trades"] == [
        {
            "cash_after": 910.0,
            "position_after": 1.0,
            "price": 90.0,
            "quantity": 1.0,
            "signal": "BUY",
            "timestamp": "2024-01-01T00:02:00Z",
        }
    ]


def test_postgres_backtest_cli_reports_empty_candles(capsys):
    empty_candles = pd.DataFrame(
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    repository = FakeRepository()

    exit_code = postgres_runner_cli.main(
        [],
        provider_factory=lambda database_url, **kwargs: FakeProvider(empty_candles),
        repository_factory=lambda database_url: repository,
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["candle_count"] == 0
    assert output["summary"] == {
        "buy_count": 0,
        "ending_cash": 10000.0,
        "ending_position": 0.0,
        "final_equity": 10000.0,
        "final_price": None,
        "sell_count": 0,
        "starting_cash": 10000.0,
        "total_return": 0.0,
        "trade_count": 0,
    }
    assert output["trades"] == []
    assert output["backtest_run_id"] == 42
    assert repository.payloads[0].graph_points == ()


def test_postgres_backtest_cli_does_not_open_network_connections(monkeypatch, capsys):
    def fail_socket_creation(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("PostgreSQL backtest tests must not open network sockets")

    monkeypatch.setattr(socket, "socket", fail_socket_creation)

    exit_code = postgres_runner_cli.main(
        [],
        provider_factory=lambda database_url, **kwargs: FakeProvider(make_candles([100])),
        repository_factory=lambda database_url: FakeRepository(database_url),
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["candle_count"] == 1




def test_postgres_backtest_cli_logs_runtime_error_and_returns_nonzero(caplog) -> None:
    caplog.set_level("ERROR")

    def failing_provider_factory(database_url: str, **kwargs: Any) -> FakeProvider:
        raise RuntimeError("boom")

    exit_code = postgres_runner_cli.main([], provider_factory=failing_provider_factory)

    assert exit_code == 1
    assert "runtime failure in quant_bitcoin.backtesting.postgres_runner_cli" in caplog.text
    assert "RuntimeError: boom" in caplog.text

def test_postgres_backtest_cli_rejects_invalid_thresholds():
    with pytest.raises(SystemExit):
        postgres_runner_cli.build_parser().parse_args(["--rsi-buy-threshold", "-1"])


def test_parser_defaults_to_persisting_results_and_accepts_no_persist():
    default_args = postgres_runner_cli.build_parser().parse_args([])
    no_persist_args = postgres_runner_cli.build_parser().parse_args(["--no-persist"])

    assert default_args.persist_results is True
    assert no_persist_args.persist_results is False


def test_no_persist_skips_repository_and_omits_run_id(capsys):
    def fail_repository_factory(database_url: str) -> FakeRepository:
        raise AssertionError("repository should not be created when --no-persist is used")

    exit_code = postgres_runner_cli.main(
        ["--no-persist"],
        provider_factory=lambda database_url, **kwargs: FakeProvider(make_candles([100])),
        repository_factory=fail_repository_factory,
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "backtest_run_id" not in output


def test_persistence_payload_contains_ordered_trades_and_graph_points():
    candles = make_candles([100, 95, 90, 85, 120])
    result = BasicBacktester(starting_cash=1000, trade_quantity=1).run(
        candles, RsiStrategy(window=2, buy_threshold=30, sell_threshold=70)
    )

    payload = postgres_runner_cli.build_persistence_payload(
        result,
        candles=candles,
        source="binance_spot",
        symbol="BTCUSDT",
        interval="1m",
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 1, 0, 4, tzinfo=timezone.utc),
        starting_cash=1000,
        trade_quantity=1,
        rsi_window=2,
        rsi_buy_threshold=30,
        rsi_sell_threshold=70,
    )

    assert payload.strategy_config.parameters == {
        "buy_threshold": 30.0,
        "sell_threshold": 70.0,
        "window": 2,
    }
    assert [trade.sequence for trade in payload.trades] == [1, 2]
    assert [trade.signal for trade in payload.trades] == ["BUY", "SELL"]
    assert [point.sequence for point in payload.graph_points] == [1, 2, 3, 4, 5]
    assert [point.candle_open_time for point in payload.graph_points] == sorted(
        point.candle_open_time for point in payload.graph_points
    )
    assert payload.graph_points[2].trade_sequence == 1
    assert payload.graph_points[2].signal == "BUY"
    assert payload.graph_points[2].cash == 910.0
    assert payload.graph_points[2].position == 1.0
    assert payload.graph_points[2].equity == 1000.0
    assert payload.graph_points[4].trade_sequence == 2
    assert payload.graph_points[4].signal == "SELL"
    assert payload.graph_points[4].cash == 1030.0
    assert payload.graph_points[4].position == 0.0
    assert payload.graph_points[4].equity == 1030.0


def test_persistence_payload_run_key_is_deterministic_and_sensitive_to_inputs():
    candles = make_candles([100, 95, 90])
    result = BasicBacktester(starting_cash=1000, trade_quantity=1).run(
        candles, RsiStrategy(window=2, buy_threshold=30, sell_threshold=70)
    )
    kwargs = {
        "result": result,
        "candles": candles,
        "source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "start_time": None,
        "end_time": None,
        "starting_cash": 1000,
        "trade_quantity": 1,
        "rsi_window": 2,
        "rsi_buy_threshold": 30,
        "rsi_sell_threshold": 70,
    }

    first = postgres_runner_cli.build_persistence_payload(**kwargs)
    second = postgres_runner_cli.build_persistence_payload(**kwargs)
    changed = postgres_runner_cli.build_persistence_payload(
        **{**kwargs, "trade_quantity": 2}
    )

    assert first.run.run_key == second.run.run_key
    assert first.run.run_key != changed.run.run_key
