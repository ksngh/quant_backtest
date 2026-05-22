from __future__ import annotations

import json
import logging
from pathlib import Path

from quant_bitcoin.market_data.binance_websocket import WebSocketIngestionResult
from quant_bitcoin.market_data.websocket_ingestion_cli import main


def _json_output(capsys):
    return json.loads(capsys.readouterr().out)


def test_cli_readiness_defaults_return_success_without_network_or_database(capsys):
    exit_code = main(["readiness"])
    output = _json_output(capsys)

    assert exit_code == 0
    assert output["ready"] is True
    assert output["symbol"] == "BTCUSDT"
    assert output["interval"] == "1m"
    assert output["stream_url"] == "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"


def test_cli_readiness_invalid_configuration_returns_nonzero(capsys):
    exit_code = main(
        [
            "readiness",
            "--symbol",
            " ",
            "--interval",
            "2h",
            "--reconnect-delay-seconds",
            "-1",
        ]
    )
    output = _json_output(capsys)

    assert exit_code == 1
    assert output["ready"] is False
    failed_checks = {check["name"] for check in output["checks"] if not check["passed"]}
    assert {"symbol", "interval", "reconnect_delay_seconds", "stream_url"}.issubset(
        failed_checks
    )


def test_cli_bounded_ingestion_wires_repository_and_ingestor_without_network(capsys):
    calls = {"repositories": [], "ingestors": []}

    class FakeRepository:
        def __init__(self, database_url: str) -> None:
            self.database_url = database_url
            self.initialized = False
            calls["repositories"].append(self)

        def initialize_schema(self) -> None:
            self.initialized = True

    class FakeIngestor:
        def __init__(self, repository, **kwargs) -> None:
            self.repository = repository
            self.kwargs = kwargs
            self.run_kwargs = None
            calls["ingestors"].append(self)

        async def run(self, **kwargs):
            self.run_kwargs = kwargs
            return WebSocketIngestionResult(
                symbol=kwargs["symbol"],
                interval=kwargs["interval"],
                messages_seen=kwargs["max_messages"],
                candles_persisted=1,
                reconnects=0,
            )

    exit_code = main(
        [
            "ingest",
            "--database-url",
            "postgresql://user:pass@db:5432/example",
            "--symbol",
            "ETHUSDT",
            "--interval",
            "3m",
            "--max-messages",
            "2",
            "--base-url",
            "wss://stream.binance.com:9443/ws",
            "--reconnect-delay-seconds",
            "0.25",
            "--max-reconnects",
            "1",
        ],
        repository_factory=FakeRepository,
        ingestor_factory=FakeIngestor,
    )
    output = _json_output(capsys)

    assert exit_code == 0
    assert output == {
        "candles_persisted": 1,
        "interval": "3m",
        "messages_seen": 2,
        "reconnects": 0,
        "symbol": "ETHUSDT",
    }
    repository = calls["repositories"][0]
    ingestor = calls["ingestors"][0]
    assert repository.database_url == "postgresql://user:pass@db:5432/example"
    assert repository.initialized is True
    assert ingestor.repository is repository
    assert ingestor.kwargs == {
        "base_url": "wss://stream.binance.com:9443/ws",
        "reconnect_delay_seconds": 0.25,
        "max_reconnects": 1,
    }
    assert ingestor.run_kwargs == {
        "symbol": "ETHUSDT",
        "interval": "3m",
        "max_messages": 2,
    }


def test_cli_unbounded_ingestion_is_default_without_env(monkeypatch, capsys):
    monkeypatch.delenv("INGEST_MAX_MESSAGES", raising=False)
    calls = {"ingestors": []}

    class FakeRepository:
        def __init__(self, database_url: str) -> None:
            self.database_url = database_url

        def initialize_schema(self) -> None:
            return None

    class FakeIngestor:
        def __init__(self, repository, **kwargs) -> None:
            self.repository = repository
            self.run_kwargs = None
            calls["ingestors"].append(self)

        async def run(self, **kwargs):
            self.run_kwargs = kwargs
            return WebSocketIngestionResult(
                symbol=kwargs["symbol"],
                interval=kwargs["interval"],
                messages_seen=0,
                candles_persisted=0,
                reconnects=0,
            )

    exit_code = main(
        ["ingest", "--no-initialize-schema"],
        repository_factory=FakeRepository,
        ingestor_factory=FakeIngestor,
    )
    output = _json_output(capsys)

    assert exit_code == 0
    assert output["messages_seen"] == 0
    assert calls["ingestors"][0].run_kwargs["max_messages"] is None


def test_cli_ingest_max_messages_env_policy_and_no_max_override(monkeypatch, capsys):
    class FakeRepository:
        def __init__(self, database_url: str) -> None:
            self.database_url = database_url

        def initialize_schema(self) -> None:
            return None

    class FakeIngestor:
        instances = []

        def __init__(self, repository, **kwargs) -> None:
            self.repository = repository
            self.run_kwargs = None
            self.instances.append(self)

        async def run(self, **kwargs):
            self.run_kwargs = kwargs
            return WebSocketIngestionResult(
                symbol=kwargs["symbol"],
                interval=kwargs["interval"],
                messages_seen=kwargs["max_messages"] or 0,
                candles_persisted=0,
                reconnects=0,
            )

    for raw_value in ("", "0", "none", "null", "unbounded"):
        FakeIngestor.instances.clear()
        monkeypatch.setenv("INGEST_MAX_MESSAGES", raw_value)
        assert main(
            ["ingest", "--no-initialize-schema"],
            repository_factory=FakeRepository,
            ingestor_factory=FakeIngestor,
        ) == 0
        _json_output(capsys)
        assert FakeIngestor.instances[0].run_kwargs["max_messages"] is None

    FakeIngestor.instances.clear()
    monkeypatch.setenv("INGEST_MAX_MESSAGES", "3")
    assert main(
        ["ingest", "--no-initialize-schema"],
        repository_factory=FakeRepository,
        ingestor_factory=FakeIngestor,
    ) == 0
    _json_output(capsys)
    assert FakeIngestor.instances[0].run_kwargs["max_messages"] == 3

    FakeIngestor.instances.clear()
    monkeypatch.setenv("INGEST_MAX_MESSAGES", "3")
    assert main(
        ["ingest", "--no-initialize-schema", "--no-max-messages"],
        repository_factory=FakeRepository,
        ingestor_factory=FakeIngestor,
    ) == 0
    _json_output(capsys)
    assert FakeIngestor.instances[0].run_kwargs["max_messages"] is None




def test_websocket_ingestion_cli_logs_runtime_error_and_returns_nonzero(caplog) -> None:
    class FakeRepository:
        def __init__(self, database_url: str) -> None:
            self.database_url = database_url

        def initialize_schema(self) -> None:
            return None

    class FailingIngestor:
        def __init__(self, repository, **kwargs) -> None:
            self.repository = repository

        async def run(self, **kwargs):
            raise RuntimeError("ws boom")

    caplog.set_level(logging.ERROR)
    exit_code = main(
        ["ingest", "--no-initialize-schema"],
        repository_factory=FakeRepository,
        ingestor_factory=FailingIngestor,
    )

    assert exit_code == 1
    assert "runtime failure in quant_bitcoin.market_data.websocket_ingestion_cli" in caplog.text
    assert "RuntimeError: ws boom" in caplog.text

def test_docker_compose_defines_postgres_and_unbounded_websocket_ingestor_service():
    compose = Path("docker-compose.yml").read_text()

    assert "postgres:" in compose
    assert "websocket-ingestor:" in compose
    assert "build: ." in compose
    assert "DATABASE_URL: postgresql://${POSTGRES_USER:-quant_bitcoin}:${POSTGRES_PASSWORD:-quant_bitcoin_dev}@postgres:5432/${POSTGRES_DB:-quant_bitcoin}" in compose
    assert "INGEST_MAX_MESSAGES: ${INGEST_MAX_MESSAGES:-unbounded}" in compose
    assert "INGEST_MAX_MESSAGES: ${INGEST_MAX_MESSAGES:-5}" not in compose
    assert "quant-bitcoin-websocket-ingestion" in compose
    assert "- ingest" in compose
    assert "condition: service_healthy" in compose


def test_dockerfile_installs_package_and_defaults_to_readiness_command():
    dockerfile = Path("Dockerfile").read_text()

    assert "FROM python:3.12-slim" in dockerfile
    assert "python -m pip install --no-cache-dir ." in dockerfile
    assert 'CMD ["quant-bitcoin-websocket-ingestion", "readiness"]' in dockerfile
