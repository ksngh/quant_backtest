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


class CapturingRepository:
    payloads = []

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def save_completed_backtest(self, payload):
        self.payloads.append(payload)
        return 77


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
        strategy_name = "FAIR_VALUE_GAP_PATTERN_STRATEGY"
        strategy_key = "FAIR_VALUE_GAP"

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
    assert "zero_transaction_cost_assumption" in output["warnings"]


def test_strategy_cli_accepts_equity_risk_fraction_sizing(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *args, **kwargs: FakeProvider(_candles()),
    )

    class StubStrategy:
        strategy_name = "FAIR_VALUE_GAP_PATTERN_STRATEGY"
        strategy_key = "FAIR_VALUE_GAP"

    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "_build_actions",
        lambda candles, strategy_key, *args, **kwargs: (
            StubStrategy(),
            [
                StrategyAction(
                    StrategyActionType.ENTER_LONG,
                    timestamp=candles.iloc[0]["timestamp"],
                    metadata={"risk_per_unit": 100.0},
                ),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist", "--position-sizing-mode", "equity_risk_fraction", "--position-sizing-value", "0.01"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["executions"][0]["quantity"] == 1.0
    assert output["summary"]["metadata"]["position_sizing"]["mode"] == "EQUITY_RISK_FRACTION"


def test_strategy_cli_warns_for_short_simulation_economics(monkeypatch, capsys) -> None:
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
                StrategyAction(StrategyActionType.ENTER_SHORT, timestamp=candles.iloc[0]["timestamp"], quantity=0.1),
                StrategyAction(StrategyActionType.EXIT_SHORT, timestamp=candles.iloc[1]["timestamp"], quantity=0.1),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert "short_economics_simulation_only" in output["warnings"]
    assert output["summary"]["metadata"]["short_economics"]["real_futures_or_margin_execution"] is False


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


def test_reproducibility_metadata_hashes_are_stable_and_sensitive_values_redacted() -> None:
    parser = strategy_postgres_runner_core.build_parser("test")
    args = parser.parse_args(
        [
            "--database-url",
            "postgresql://user:supersecret@localhost:5432/quant",
            "--start-time",
            "2026-01-01T00:00:00Z",
            "--end-time",
            "2026-01-01T00:01:00Z",
            "--maker-fee-bps",
            "1.0",
        ]
    )
    entry_filter = strategy_postgres_runner_core._build_pattern_entry_filter_config(args)
    transaction_cost, liquidity_role = strategy_postgres_runner_core._build_transaction_cost_config(args)
    position_sizing = strategy_postgres_runner_core._build_position_sizing_config(args)
    _, simulated_margin = strategy_postgres_runner_core._build_simulated_margin_config(args)
    policy_metadata = {
        "short_exposure_policy": {
            "mode": args.short_exposure_mode.upper(),
            "default_policy": "test",
        }
    }
    params = strategy_postgres_runner_core._build_strategy_parameters(
        strategy_key="FAIR_VALUE_GAP",
        entry_filter_config=entry_filter,
        transaction_cost_config=transaction_cost,
        default_liquidity_role=liquidity_role,
        position_sizing=position_sizing,
        policy_metadata=policy_metadata,
        simulated_margin=simulated_margin,
        risk_free_rate=args.risk_free_rate,
    )

    first = strategy_postgres_runner_core._build_reproducibility_metadata(
        args=args,
        candles=_candles(),
        strategy_key="FAIR_VALUE_GAP",
        strategy_name="FAIR_VALUE_GAP_PATTERN_STRATEGY",
        strategy_version="strategy_engine_v1",
        strategy_parameters=params,
        engine_name="BasicBacktester",
        engine_version="basic_backtester_v1",
    )
    second = strategy_postgres_runner_core._build_reproducibility_metadata(
        args=args,
        candles=_candles(),
        strategy_key="FAIR_VALUE_GAP",
        strategy_name="FAIR_VALUE_GAP_PATTERN_STRATEGY",
        strategy_version="strategy_engine_v1",
        strategy_parameters=params,
        engine_name="BasicBacktester",
        engine_version="basic_backtester_v1",
    )

    changed_params = dict(params)
    changed_params["transaction_cost"] = dict(params["transaction_cost"])
    changed_params["transaction_cost"]["maker_fee_bps"] = 2.0
    changed = strategy_postgres_runner_core._build_reproducibility_metadata(
        args=args,
        candles=_candles(),
        strategy_key="FAIR_VALUE_GAP",
        strategy_name="FAIR_VALUE_GAP_PATTERN_STRATEGY",
        strategy_version="strategy_engine_v1",
        strategy_parameters=changed_params,
        engine_name="BasicBacktester",
        engine_version="basic_backtester_v1",
    )

    assert first["config_hashes"] == second["config_hashes"]
    assert first["config_hashes"]["strategy_parameters"] != changed["config_hashes"]["strategy_parameters"]
    serialized = json.dumps(first)
    assert "supersecret" not in serialized
    assert first["environment"]["database_url"] == "postgresql://***:***@localhost:5432/quant"


def test_strategy_cli_outputs_reproducibility_metadata_without_secrets(monkeypatch, capsys) -> None:
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
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(
        ["--no-persist", "--database-url", "postgresql://user:secret@localhost:5432/db"]
    ) == 0
    output = json.loads(capsys.readouterr().out)
    reproducibility = output["reproducibility"]

    assert reproducibility["dataset"]["source"] == "binance_spot"
    assert reproducibility["dataset"]["candle_count"] == 2
    assert reproducibility["dataset"]["actual_start_time"] == "2026-01-01T00:00:00Z"
    assert reproducibility["dataset"]["quality"]["interval_gap_count"] == 0
    assert "strategy_parameters" in reproducibility["config_hashes"]
    assert "secret" not in json.dumps(output)


def test_strategy_cli_persists_reproducibility_metadata(monkeypatch, capsys) -> None:
    CapturingRepository.payloads = []
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *args, **kwargs: FakeProvider(_candles()),
    )
    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "PostgresBacktestResultRepository",
        CapturingRepository,
    )

    class StubStrategy:
        strategy_name = "FAIR_VALUE_GAP_PATTERN_STRATEGY"
        strategy_key = "FAIR_VALUE_GAP"

    monkeypatch.setattr(
        strategy_postgres_runner_core,
        "_build_actions",
        lambda candles, strategy_key, *args, **kwargs: (
            StubStrategy(),
            [
                StrategyAction(StrategyActionType.ENTER_LONG, timestamp=candles.iloc[0]["timestamp"], quantity=1.0),
            ],
        ),
    )

    assert strategy_postgres_runner_cli.main(
        ["--database-url", "postgresql://user:secret@localhost:5432/db"]
    ) == 0
    output = json.loads(capsys.readouterr().out)
    payload = CapturingRepository.payloads[0]

    assert output["backtest_run_id"] == 77
    assert "reproducibility" in payload.run.metadata
    assert payload.run.metadata["reproducibility"]["dataset"]["candle_count"] == 2
    assert "secret" not in json.dumps(payload.run.metadata)


def test_strategy_cli_exception_logging_uses_current_signature(monkeypatch) -> None:
    calls: list[str] = []

    def fail_run(argv=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(strategy_postgres_runner_cli, "run", fail_run)
    monkeypatch.setattr(strategy_postgres_runner_cli, "log_runtime_exception", calls.append)

    assert strategy_postgres_runner_cli.main(["--no-persist"]) == 1
    assert calls == [strategy_postgres_runner_cli.__name__]
