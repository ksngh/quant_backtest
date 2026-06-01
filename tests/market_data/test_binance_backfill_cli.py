from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from quant_bitcoin.market_data.binance_backfill import BackfillResult
from quant_bitcoin.market_data.binance_backfill_cli import build_parser, main


def _json_output(capsys):
    return json.loads(capsys.readouterr().out)


def test_cli_wires_postgres_repository_and_backfiller_without_network(capsys):
    calls = {"repositories": [], "backfillers": []}

    class FakeRepository:
        def __init__(self, database_url: str) -> None:
            self.database_url = database_url
            self.initialized = False
            calls["repositories"].append(self)

        def initialize_schema(self) -> None:
            self.initialized = True

    class FakeBackfiller:
        def __init__(self, repository, **kwargs) -> None:
            self.repository = repository
            self.kwargs = kwargs
            self.run_kwargs = None
            calls["backfillers"].append(self)

        def run(self, **kwargs):
            self.run_kwargs = kwargs
            return BackfillResult(
                symbol=kwargs["symbol"],
                interval=kwargs["interval"],
                requested_start_time=kwargs["start_time"],
                requested_end_time=kwargs["end_time"],
                stored_candles=12,
                pages_fetched=2,
            )

    exit_code = main(
        [
            "--database-url",
            "postgresql://user:pass@localhost:5432/example",
            "--symbol",
            "ethusdt",
            "--interval",
            "3m",
            "--start-time",
            "2024-01-01T00:00:00Z",
            "--end-time",
            "1704067380000",
            "--limit",
            "500",
            "--base-url",
            "https://data-api.binance.vision",
            "--timeout-seconds",
            "2.5",
            "--max-retries",
            "1",
        ],
        repository_factory=FakeRepository,
        backfiller_factory=FakeBackfiller,
    )
    output = _json_output(capsys)

    assert exit_code == 0
    assert output == {
        "interval": "3m",
        "pages_fetched": 2,
        "requested_end_time": 1_704_067_380_000,
        "requested_start_time": "2024-01-01T00:00:00+00:00",
        "stored_candles": 12,
        "symbol": "ethusdt",
    }
    repository = calls["repositories"][0]
    backfiller = calls["backfillers"][0]
    assert repository.database_url == "postgresql://user:pass@localhost:5432/example"
    assert repository.initialized is True
    assert backfiller.repository is repository
    assert backfiller.kwargs == {
        "base_url": "https://data-api.binance.vision",
        "timeout": 2.5,
        "max_retries": 1,
    }
    assert backfiller.run_kwargs == {
        "symbol": "ethusdt",
        "interval": "3m",
        "start_time": datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        "end_time": 1_704_067_380_000,
        "limit": 500,
    }


def test_cli_can_skip_schema_initialization_for_prepared_database(capsys):
    class FakeRepository:
        def __init__(self, database_url: str) -> None:
            self.database_url = database_url
            self.initialized = False

        def initialize_schema(self) -> None:
            self.initialized = True

    class FakeBackfiller:
        def __init__(self, repository, **kwargs) -> None:
            self.repository = repository

        def run(self, **kwargs):
            assert self.repository.initialized is False
            return BackfillResult(
                symbol="BTCUSDT",
                interval="1m",
                requested_start_time=None,
                requested_end_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
                stored_candles=0,
                pages_fetched=0,
            )

    exit_code = main(
        ["--no-initialize-schema"],
        repository_factory=FakeRepository,
        backfiller_factory=FakeBackfiller,
    )
    output = _json_output(capsys)

    assert exit_code == 0
    assert output["stored_candles"] == 0


def test_cli_runs_multi_interval_backfill_once_per_requested_interval(capsys):
    calls = {"repositories": [], "run_kwargs": []}

    class FakeRepository:
        def __init__(self, database_url: str) -> None:
            calls["repositories"].append(self)

        def initialize_schema(self) -> None:
            return None

    class FakeBackfiller:
        def __init__(self, repository, **kwargs) -> None:
            self.repository = repository

        def run(self, **kwargs):
            calls["run_kwargs"].append(kwargs)
            return BackfillResult(
                symbol=kwargs["symbol"],
                interval=kwargs["interval"],
                requested_start_time=kwargs["start_time"],
                requested_end_time=kwargs["end_time"],
                stored_candles=7,
                pages_fetched=1,
            )

    exit_code = main(
        ["--symbol", "btcusdt", "--intervals", "1m, 1h,1d,1h"],
        repository_factory=FakeRepository,
        backfiller_factory=FakeBackfiller,
    )
    output = _json_output(capsys)

    assert exit_code == 0
    assert output["symbol"] == "BTCUSDT"
    assert output["intervals"] == ["1m", "1h", "1d"]
    assert [call["interval"] for call in calls["run_kwargs"]] == ["1m", "1h", "1d"]
    assert output["results"][1]["interval"] == "1h"
    assert output["results"][1]["stored_candles"] == 7


def test_cli_rejects_invalid_interval_list_before_database_or_network_work():
    class UnexpectedRepository:
        def __init__(self, database_url: str) -> None:
            raise AssertionError("database should not be opened for invalid intervals")

    try:
        main(["--intervals", "1m,2h"], repository_factory=UnexpectedRepository)
    except ValueError as error:
        assert "supported Binance kline interval" in str(error)
    else:
        raise AssertionError("expected invalid interval list to fail")


def test_cli_rejects_invalid_limit_before_any_database_or_network_work():
    class UnexpectedRepository:
        def __init__(self, database_url: str) -> None:
            raise AssertionError("database should not be opened for invalid CLI input")

    try:
        main(["--limit", "0"], repository_factory=UnexpectedRepository)
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("expected argparse to stop on invalid limit")


def test_cli_help_lists_hour_and_day_backfill_intervals():
    help_text = build_parser().format_help()

    assert "1h" in help_text
    assert "1d" in help_text


def test_backfill_console_script_is_registered():
    pyproject = Path("pyproject.toml").read_text()

    assert (
        'quant-bitcoin-binance-backfill = '
        '"quant_bitcoin.market_data.binance_backfill_cli:main"'
    ) in pyproject


def test_backfill_cli_logs_runtime_error_and_returns_nonzero(caplog) -> None:
    class FailingRepository:
        def __init__(self, database_url: str) -> None:
            self.database_url = database_url

        def initialize_schema(self) -> None:
            return None

    class FailingBackfiller:
        def __init__(self, repository, **kwargs) -> None:
            self.repository = repository

        def run(self, **kwargs):
            raise RuntimeError("backfill failed")

    with caplog.at_level("ERROR"):
        exit_code = main(
            [],
            repository_factory=FailingRepository,
            backfiller_factory=FailingBackfiller,
        )

    assert exit_code == 1
    assert "runtime failure in quant_bitcoin.market_data.binance_backfill_cli" in caplog.text
    assert "backfill failed" in caplog.text
