from __future__ import annotations

import ast
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd
import pytest

from quant_bitcoin.backtesting import pattern_postgres_runner_cli
from quant_bitcoin.backtesting.pattern_strategy import (
    SUPPORTED_PATTERNS,
    PatternStrategyBacktestResult,
)
from quant_bitcoin.patterns import PatternExitReason


class FakeRepository:
    def __init__(self, database_url: str = "postgresql://example/test") -> None:
        self.database_url = database_url
        self.payloads: list[Any] = []

    def save_completed_backtest(self, payload: Any) -> int:
        self.payloads.append(payload)
        return 77


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
                "2026-05-18T00:00:00Z", periods=len(closes), freq="min"
            ),
            "open": closes,
            "high": [close + 1 for close in closes],
            "low": [close - 1 for close in closes],
            "close": closes,
            "volume": [1.0] * len(closes),
        }
    )


def test_pattern_postgres_backtest_help_succeeds_without_provider(capsys) -> None:
    def fail_provider_factory(*args: Any, **kwargs: Any) -> FakeProvider:
        raise AssertionError("--help must not connect to PostgreSQL")

    with pytest.raises(SystemExit) as exc_info:
        pattern_postgres_runner_cli.main(
            ["--help"],
            provider_factory=fail_provider_factory,
        )

    assert exc_info.value.code == 0
    assert "quant-bitcoin-pattern-backtest" in capsys.readouterr().out


def test_pattern_postgres_backtest_logs_runtime_error_and_returns_nonzero(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def failing_provider_factory(*args: Any, **kwargs: Any) -> FakeProvider:
        raise RuntimeError("provider exploded")

    with caplog.at_level("ERROR"):
        exit_code = pattern_postgres_runner_cli.main(
            [],
            provider_factory=failing_provider_factory,
        )

    assert exit_code == 1
    assert "runtime failure in quant_bitcoin.backtesting.pattern_postgres_runner_cli" in caplog.text
    assert "provider exploded" in caplog.text


def test_pattern_postgres_backtest_help_names_default_fvg_strategy(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        pattern_postgres_runner_cli.build_parser().parse_args(["--help"])

    help_text = capsys.readouterr().out
    assert exc_info.value.code == 0
    normalized_help = " ".join(help_text.split())
    assert "Run the default Fair Value Gap pattern strategy backtest" in help_text
    assert "FAIR_VALUE_GAP remains the default" in normalized_help
    assert "default is FAIR_VALUE_GAP" in help_text
    for pattern in SUPPORTED_PATTERNS:
        assert pattern in help_text


def test_pattern_postgres_backtest_parser_rejects_unsupported_pattern() -> None:
    with pytest.raises(SystemExit):
        pattern_postgres_runner_cli.build_parser().parse_args(["--pattern", "NOT_A_PATTERN"])


def test_pattern_postgres_backtest_cli_rejects_multiple_patterns_before_provider() -> None:
    def fail_provider_factory(*args: Any, **kwargs: Any) -> FakeProvider:
        raise AssertionError("multiple pattern selections must fail before provider")

    with pytest.raises(ValueError, match="multiple pattern selections are not supported"):
        pattern_postgres_runner_cli.main(
            ["--pattern", "FAIR_VALUE_GAP", "--pattern", "ORDER_BLOCK"],
            provider_factory=fail_provider_factory,
        )


def test_pattern_postgres_backtest_default_output_strategy_name() -> None:
    output = pattern_postgres_runner_cli.build_output(
        PatternStrategyBacktestResult(
            trades=(),
            evaluated_candle_count=0,
            seen_event_ids=(),
        ),
        candle_count=0,
        source="binance_spot",
        symbol="BTCUSDT",
        interval="1m",
        start_time=None,
        end_time=None,
    )

    assert output["strategy"]["name"] == "FAIR_VALUE_GAP_PATTERN_STRATEGY"
    assert output["strategy"]["patterns"] == ["FAIR_VALUE_GAP"]




def test_pattern_postgres_backtest_parser_accepts_starting_cash_and_trade_quantity() -> None:
    args = pattern_postgres_runner_cli.build_parser().parse_args(
        ["--starting-cash", "12345", "--trade-quantity", "0.5"]
    )

    assert args.starting_cash == 12345
    assert args.trade_quantity == 0.5

def test_pattern_postgres_backtest_parser_defaults_to_one_minute_interval() -> None:
    args = pattern_postgres_runner_cli.build_parser().parse_args([])

    assert args.interval == "1m"


def test_pattern_postgres_backtest_parser_rejects_non_one_minute_interval() -> None:
    with pytest.raises(SystemExit):
        pattern_postgres_runner_cli.build_parser().parse_args(["--interval", "5m"])


def test_pattern_postgres_backtest_cli_wires_provider_and_runner(capsys) -> None:
    calls: dict[str, Any] = {}
    provider = FakeProvider(make_candles([100, 101, 103]))

    def provider_factory(database_url: str, **kwargs: Any) -> FakeProvider:
        calls["provider"] = {"database_url": database_url, **kwargs}
        return provider

    def backtest_runner(candles: pd.DataFrame, *, config: Any) -> PatternStrategyBacktestResult:
        calls["backtest"] = {
            "columns": tuple(candles.columns),
            "candle_count": len(candles),
            "symbol": config.symbol,
            "timeframe": config.timeframe,
            "patterns": config.patterns,
        }
        return PatternStrategyBacktestResult(
            trades=(),
            evaluated_candle_count=len(candles),
            seen_event_ids=("fvg-1",),
        )

    exit_code = pattern_postgres_runner_cli.main(
        [
            "--database-url",
            "postgresql://example/test",
            "--source",
            "binance_spot",
            "--symbol",
            "BTCUSDT",
            "--pattern",
            "FAIR_VALUE_GAP",
            "--start-time",
            "2026-05-18T00:00:00Z",
            "--end-time",
            "2026-05-18T00:02:00Z",
        ],
        provider_factory=provider_factory,
        backtest_runner=backtest_runner,
        repository_factory=lambda database_url: FakeRepository(database_url),
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert provider.load_calls == 1
    assert calls["provider"] == {
        "database_url": "postgresql://example/test",
        "source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "start_time": datetime(2026, 5, 18, tzinfo=timezone.utc),
        "end_time": datetime(2026, 5, 18, 0, 2, tzinfo=timezone.utc),
    }
    assert calls["backtest"] == {
        "columns": ("timestamp", "open", "high", "low", "close", "volume"),
        "candle_count": 3,
        "symbol": "BTCUSDT",
        "timeframe": "1m",
        "patterns": ("FAIR_VALUE_GAP",),
    }
    assert output == {
        "candle_count": 3,
        "input": {
            "source": "binance_spot",
            "symbol": "BTCUSDT",
            "interval": "1m",
            "start_time": "2026-05-18T00:00:00Z",
            "end_time": "2026-05-18T00:02:00Z",
        },
        "seen_event_ids": ["fvg-1"],
        "strategy": {
            "name": "FAIR_VALUE_GAP_PATTERN_STRATEGY",
            "patterns": ["FAIR_VALUE_GAP"],
            "entry_rule": "pattern_confirmation_candle",
            "exit_evaluation": "starts_on_candle_after_entry",
        },
        "summary": {
            "evaluated_candle_count": 3,
            "seen_event_count": 1,
            "trade_count": 0,
        },
        "trades": [],
        "backtest_run_id": 77,
    }


@pytest.mark.parametrize("pattern", SUPPORTED_PATTERNS)
def test_pattern_postgres_backtest_cli_passes_each_supported_pattern(
    pattern: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: dict[str, Any] = {}

    def backtest_runner(candles: pd.DataFrame, *, config: Any) -> PatternStrategyBacktestResult:
        captured["patterns"] = config.patterns
        return PatternStrategyBacktestResult(
            trades=(),
            evaluated_candle_count=len(candles),
            seen_event_ids=(f"{pattern.lower()}-event",),
        )

    exit_code = pattern_postgres_runner_cli.main(
        ["--pattern", pattern],
        provider_factory=lambda database_url, **kwargs: FakeProvider(make_candles([100])),
        backtest_runner=backtest_runner,
        repository_factory=lambda database_url: FakeRepository(database_url),
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert captured["patterns"] == (pattern,)
    assert output["strategy"]["patterns"] == [pattern]
    assert output["strategy"]["name"] == f"{pattern}_PATTERN_STRATEGY"


def test_pattern_postgres_backtest_cli_defaults_to_fvg_selection(capsys) -> None:
    captured: dict[str, Any] = {}

    def backtest_runner(candles: pd.DataFrame, *, config: Any) -> PatternStrategyBacktestResult:
        captured["patterns"] = config.patterns
        return PatternStrategyBacktestResult(
            trades=(),
            evaluated_candle_count=len(candles),
            seen_event_ids=(),
        )

    exit_code = pattern_postgres_runner_cli.main(
        [],
        provider_factory=lambda database_url, **kwargs: FakeProvider(make_candles([100])),
        backtest_runner=backtest_runner,
        repository_factory=lambda database_url: FakeRepository(database_url),
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert captured["patterns"] == ("FAIR_VALUE_GAP",)
    assert output["strategy"]["patterns"] == ["FAIR_VALUE_GAP"]
    assert output["strategy"]["name"] == "FAIR_VALUE_GAP_PATTERN_STRATEGY"


def test_pattern_postgres_backtest_cli_reports_empty_candles(capsys) -> None:
    empty_candles = pd.DataFrame(
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    exit_code = pattern_postgres_runner_cli.main(
        [],
        provider_factory=lambda database_url, **kwargs: FakeProvider(empty_candles),
        repository_factory=lambda database_url: FakeRepository(database_url),
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["candle_count"] == 0
    assert output["summary"] == {
        "evaluated_candle_count": 0,
        "seen_event_count": 0,
        "trade_count": 0,
    }
    assert output["trades"] == []


def test_pattern_postgres_backtest_readme_example_matches_cli_options() -> None:
    readme = Path("README.md").read_text()
    help_text = pattern_postgres_runner_cli.build_parser().format_help()

    assert "quant-bitcoin-pattern-backtest" in readme
    assert "--start-time" in readme and "--start-time" in help_text
    assert "--end-time" in readme and "--end-time" in help_text
    assert "--pattern FAIR_VALUE_GAP" in readme
    assert "historical simulation over stored standard candles" in readme
    assert "does not place" in readme


def test_pattern_postgres_backtest_cli_does_not_open_network_connections(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_socket_creation(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("pattern backtest tests must not open network sockets")

    monkeypatch.setattr(socket, "socket", fail_socket_creation)

    exit_code = pattern_postgres_runner_cli.main(
        [],
        provider_factory=lambda database_url, **kwargs: FakeProvider(make_candles([100])),
        repository_factory=lambda database_url: FakeRepository(database_url),
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["candle_count"] == 1


def test_pattern_postgres_backtest_entrypoint_is_registered() -> None:
    pyproject = Path("pyproject.toml").read_text()

    assert (
        'quant-bitcoin-pattern-backtest = "quant_bitcoin.backtesting.'
        'pattern_postgres_runner_cli:main"'
    ) in pyproject


def test_pattern_postgres_backtest_cli_reuses_existing_pattern_backtest_api() -> None:
    source_path = Path("quant_bitcoin/backtesting/pattern_postgres_runner_cli.py")
    tree = ast.parse(source_path.read_text())
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "quant_bitcoin.backtesting.pattern_strategy":
            imported_names.update(alias.name for alias in node.names)

    source = source_path.read_text()
    assert "run_pattern_strategy_backtest" in imported_names
    assert "detect_fair_value_gaps(" not in source
    assert "simulate_pattern_exit(" not in source


def test_pattern_postgres_backtest_cli_does_not_use_order_or_secret_terms() -> None:
    source = Path("quant_bitcoin/backtesting/pattern_postgres_runner_cli.py").read_text().lower()

    assert "api_key" not in source
    assert "dotenv" not in source
    assert "load_dotenv" not in source
    assert "create_order" not in source
    assert "place_order" not in source
    assert "enable_live_trading" not in source
    assert "api.binance.com/api/v3/order" not in source
    assert "paper_trader" not in source


def test_pattern_postgres_backtest_no_persist_skips_repository(capsys) -> None:
    def fail_repository_factory(database_url: str) -> FakeRepository:
        raise AssertionError("repository should not be created when --no-persist is used")

    exit_code = pattern_postgres_runner_cli.main(
        ["--no-persist"],
        provider_factory=lambda database_url, **kwargs: FakeProvider(make_candles([100])),
        repository_factory=fail_repository_factory,
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "backtest_run_id" not in output


def test_pattern_persistence_payload_uses_configured_starting_cash_and_simulated_ending_cash() -> None:
    candles = make_candles([100, 110])
    trade = PatternStrategyBacktestResult(
        trades=(),
        evaluated_candle_count=2,
        seen_event_ids=(),
    )
    payload = pattern_postgres_runner_cli.build_persistence_payload(
        trade,
        candles=candles,
        source="binance_spot",
        symbol="BTCUSDT",
        interval="1m",
        start_time=None,
        end_time=None,
        patterns=("FAIR_VALUE_GAP",),
        starting_cash=10000.0,
        trade_quantity=1.0,
    )

    assert payload.run.starting_cash == 10000.0
    assert payload.result.starting_cash == 10000.0
    assert payload.result.ending_cash == 10000.0
    assert payload.result.final_equity == 10000.0


def _synthetic_trade(*, entry: float, exit: float | None, remaining_ratio: float, reason: PatternExitReason) -> Any:
    return SimpleNamespace(
        event_id="evt-1",
        pattern_type="FAIR_VALUE_GAP",
        pattern_direction="LONG",
        entry_timestamp=datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc),
        entry_price=entry,
        remaining_quantity_ratio=remaining_ratio,
        exit_timestamp=datetime(2026, 5, 18, 0, 1, tzinfo=timezone.utc) if exit is not None else None,
        exit_price=exit,
        exit_reason=reason,
        realized_pnl_per_unit=((exit - entry) if exit is not None else 0.0),
        realized_r_multiple=1.0 if exit is not None else None,
        risk_plan=SimpleNamespace(direction="LONG", entry_price=entry, stop_price=entry - 1, risk_per_unit=1.0, status="VALID", targets=()),
    )


def test_pattern_persistence_payload_records_buy_sell_and_cash_equity_movement() -> None:
    payload = pattern_postgres_runner_cli.build_persistence_payload(
        PatternStrategyBacktestResult(
            trades=(
                _synthetic_trade(entry=100.0, exit=110.0, remaining_ratio=0.0, reason=PatternExitReason.TAKE_PROFIT),
            ),
            evaluated_candle_count=2,
            seen_event_ids=("evt-1",),
        ),
        candles=make_candles([100, 110]),
        source="binance_spot",
        symbol="BTCUSDT",
        interval="1m",
        start_time=None,
        end_time=None,
        patterns=("FAIR_VALUE_GAP",),
        starting_cash=10000.0,
        trade_quantity=1.0,
    )
    assert [trade.signal for trade in payload.trades] == ["BUY", "SELL"]
    assert payload.trades[0].quantity == pytest.approx(1.0)
    assert payload.trades[1].quantity == pytest.approx(1.0)
    assert payload.result.ending_cash == pytest.approx(10010.0)
    assert payload.result.ending_position == pytest.approx(0.0)
    assert payload.result.final_equity == pytest.approx(10010.0)
    assert payload.result.total_return == pytest.approx(0.001)
    assert payload.result.buy_count == 1
    assert payload.result.sell_count == 1


@pytest.mark.parametrize("reason", list(PatternExitReason))
def test_pattern_persistence_payload_preserves_exit_reason(reason: PatternExitReason) -> None:
    payload = pattern_postgres_runner_cli.build_persistence_payload(
        PatternStrategyBacktestResult(
            trades=(_synthetic_trade(entry=100.0, exit=101.0, remaining_ratio=0.0, reason=reason),),
            evaluated_candle_count=2,
            seen_event_ids=("evt-1",),
        ),
        candles=make_candles([100, 101]),
        source="binance_spot",
        symbol="BTCUSDT",
        interval="1m",
        start_time=None,
        end_time=None,
        patterns=("FAIR_VALUE_GAP",),
        starting_cash=10000.0,
        trade_quantity=1.0,
    )
    assert payload.trades[1].metadata["exit_reason"] == reason.value
