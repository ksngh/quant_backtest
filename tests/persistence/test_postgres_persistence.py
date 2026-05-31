from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from quant_bitcoin.persistence import (
    CANDLE_TABLE_COLUMNS,
    BacktestGraphPointPayload,
    BacktestPersistencePayload,
    BacktestResultPayload,
    BacktestRunPayload,
    BacktestTradePayload,
    IngestionCheckpoint,
    PersistedCandle,
    PostgresBacktestResultRepository,
    PostgresCandleRepository,
    build_rsi_strategy_config_payload,
)
from quant_bitcoin.persistence.db_commands import (
    DB_CHANGES_DIR,
    DbCommandFile,
    execute_db_commands,
    load_change_db_commands,
    load_initial_db_commands,
    load_sql_command_files,
)
from quant_bitcoin.persistence.postgres import (
    SELECT_STANDARD_CANDLES_BASE_SQL,
    UPSERT_CANDLE_SQL,
)


EXPECTED_CANDLE_COLUMNS = (
    "source",
    "symbol",
    "interval",
    "open_time",
    "close_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "is_closed",
    "raw_payload",
)


def managed_schema_sql() -> str:
    return "\n".join(command.sql for command in load_initial_db_commands())


class FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows


class FakeConnection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.executed_query: str | None = None
        self.executed_params: dict[str, Any] | None = None

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str, params: dict[str, Any]) -> FakeResult:
        self.executed_query = query
        self.executed_params = params
        return FakeResult(self.rows)


class FakeSchemaConnection:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def __enter__(self) -> "FakeSchemaConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str) -> object:
        self.executed.append(query)
        return object()


def test_db_command_loader_returns_sql_files_in_deterministic_order(tmp_path):
    (tmp_path / "020_second.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "010_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "README.md").write_text("ignored", encoding="utf-8")

    commands = load_sql_command_files(tmp_path)

    assert [command.path.name for command in commands] == [
        "010_first.sql",
        "020_second.sql",
    ]
    assert [command.sql for command in commands] == ["SELECT 1;", "SELECT 2;"]


def test_db_command_executor_runs_loaded_files_in_order():
    connection = FakeSchemaConnection()
    commands = (
        DbCommandFile(path=DB_CHANGES_DIR / "010_first.sql", sql="SELECT 1;"),
        DbCommandFile(path=DB_CHANGES_DIR / "020_second.sql", sql="SELECT 2;"),
    )

    execute_db_commands(connection, commands)

    assert connection.executed == ["SELECT 1;", "SELECT 2;"]


def test_empty_change_command_directory_is_explicitly_supported():
    assert load_change_db_commands() == ()


def test_repository_initialize_schema_executes_managed_db_command_files(monkeypatch):
    import psycopg

    fake_connection = FakeSchemaConnection()
    monkeypatch.setattr(psycopg, "connect", lambda database_url: fake_connection)

    PostgresCandleRepository("postgresql://example/test").initialize_schema()

    assert fake_connection.executed == [
        command.sql for command in load_initial_db_commands()
    ]
    assert fake_connection.executed
    assert all(
        "CREATE TABLE IF NOT EXISTS" in sql for sql in fake_connection.executed
    )


def test_backtest_repository_initialize_schema_executes_managed_db_command_files(
    monkeypatch,
):
    import psycopg

    fake_connection = FakeSchemaConnection()
    monkeypatch.setattr(psycopg, "connect", lambda database_url: fake_connection)

    PostgresBacktestResultRepository("postgresql://example/test").initialize_schema()

    assert fake_connection.executed == [
        command.sql for command in load_initial_db_commands()
    ]


def persisted_candle(open_price: str = "42000") -> PersistedCandle:
    return PersistedCandle(
        source="binance_spot",
        symbol="BTCUSDT",
        interval="1m",
        open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        close_time=datetime(2024, 1, 1, 0, 0, 59, 999000, tzinfo=timezone.utc),
        open=Decimal(open_price),
        high=Decimal("42100"),
        low=Decimal("41900"),
        close=Decimal("42050"),
        volume=Decimal("12.5"),
        quote_asset_volume=Decimal("525625"),
        number_of_trades=123,
        taker_buy_base_asset_volume=Decimal("6.1"),
        taker_buy_quote_asset_volume=Decimal("256405"),
        is_closed=True,
        raw_payload=["raw"],
    )


def test_candle_contract_columns_match_task_013_schema():
    assert CANDLE_TABLE_COLUMNS == EXPECTED_CANDLE_COLUMNS
    for column in EXPECTED_CANDLE_COLUMNS:
        assert column in managed_schema_sql()


def test_schema_enforces_accepted_uniqueness_rules():
    assert "UNIQUE (source, symbol, interval, open_time)" in managed_schema_sql()
    assert "UNIQUE (source, symbol, interval, mode)" in managed_schema_sql()


def test_standard_candle_select_uses_open_time_timestamp_mapping():
    assert "SELECT open_time AS timestamp, open, high, low, close, volume" in (
        SELECT_STANDARD_CANDLES_BASE_SQL
    )
    assert "FROM candles" in SELECT_STANDARD_CANDLES_BASE_SQL
    assert "is_closed IS TRUE" in SELECT_STANDARD_CANDLES_BASE_SQL


def test_repository_load_standard_candles_maps_rows_and_filters(monkeypatch):
    import psycopg

    row_open_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    start_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc)
    fake_connection = FakeConnection(
        [
            {
                "timestamp": row_open_time,
                "open": Decimal("100"),
                "high": Decimal("101"),
                "low": Decimal("99"),
                "close": Decimal("100.5"),
                "volume": Decimal("12.5"),
                "source": "binance_spot",
                "raw_payload": ["ignored"],
            }
        ]
    )

    def fake_connect(database_url: str, **kwargs: Any) -> FakeConnection:
        assert database_url == "postgresql://example/test"
        assert "row_factory" in kwargs
        return fake_connection

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    rows = PostgresCandleRepository("postgresql://example/test").load_standard_candles(
        source="binance_spot",
        symbol="BTCUSDT",
        interval="1m",
        start_time=start_time,
        end_time=end_time,
    )

    assert rows == [
        {
            "timestamp": row_open_time,
            "open": Decimal("100"),
            "high": Decimal("101"),
            "low": Decimal("99"),
            "close": Decimal("100.5"),
            "volume": Decimal("12.5"),
        }
    ]
    assert fake_connection.executed_params == {
        "source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "start_time": start_time,
        "end_time": end_time,
    }
    assert fake_connection.executed_query is not None
    assert "open_time >= %(start_time)s" in fake_connection.executed_query
    assert "open_time <= %(end_time)s" in fake_connection.executed_query
    assert "ORDER BY open_time ASC" in fake_connection.executed_query

def test_upsert_sql_is_duplicate_safe_for_candle_identity():
    assert (
        "ON CONFLICT (source, symbol, interval, open_time) DO UPDATE"
        in UPSERT_CANDLE_SQL
    )
    assert "updated_at = now()" in UPSERT_CANDLE_SQL


def test_persisted_candle_insert_row_contains_all_contract_fields():
    row = persisted_candle().as_insert_row()

    assert tuple(row) == EXPECTED_CANDLE_COLUMNS
    assert row["source"] == "binance_spot"
    assert row["symbol"] == "BTCUSDT"
    assert row["interval"] == "1m"
    assert row["open"] == Decimal("42000")


@pytest.mark.skipif(
    not os.environ.get("QUANT_BITCOIN_TEST_DATABASE_URL"),
    reason="QUANT_BITCOIN_TEST_DATABASE_URL is not configured",
)
def test_postgres_repository_upserts_duplicate_candles_idempotently():
    repository = PostgresCandleRepository(os.environ["QUANT_BITCOIN_TEST_DATABASE_URL"])
    repository.initialize_schema()

    repository.upsert_candles([persisted_candle("42000")])
    repository.upsert_candles([persisted_candle("42001")])

    latest = repository.latest_open_time("binance_spot", "BTCUSDT", "1m")
    assert latest == datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    repository.save_checkpoint(
        IngestionCheckpoint(
            source="binance_spot",
            symbol="BTCUSDT",
            interval="1m",
            mode="historical_backfill",
            last_open_time=latest,
            last_close_time=datetime(
                2024, 1, 1, 0, 0, 59, 999000, tzinfo=timezone.utc
            ),
            last_event_time=None,
            status="completed",
            metadata={"stored_candles": 1},
        )
    )
    checkpoint = repository.load_checkpoint(
        "binance_spot", "BTCUSDT", "1m", "historical_backfill"
    )
    assert checkpoint is not None
    assert checkpoint.last_open_time == latest


class FakeFetchOneResult:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row or {"id": 1}

    def fetchone(self) -> dict[str, Any]:
        return self.row


class FakeTransaction:
    def __init__(self) -> None:
        self.entered = False
        self.exit_exc_type: type[BaseException] | None = None

    def __enter__(self) -> "FakeTransaction":
        self.entered = True
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *args: object) -> None:
        self.exit_exc_type = exc_type
        return None


class FakeBacktestConnection:
    def __init__(self, *, fail_on_graph_point: bool = False) -> None:
        self.fail_on_graph_point = fail_on_graph_point
        self.executed: list[tuple[str, dict[str, Any]]] = []
        self.transaction_context = FakeTransaction()
        self.next_id = 100

    def __enter__(self) -> "FakeBacktestConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def transaction(self) -> FakeTransaction:
        return self.transaction_context

    def execute(self, query: str, params: dict[str, Any]) -> FakeFetchOneResult:
        if self.fail_on_graph_point and "INSERT INTO backtest_graph_points" in query:
            raise RuntimeError("simulated graph point insert failure")
        self.executed.append((query, params))
        self.next_id += 1
        return FakeFetchOneResult({"id": self.next_id})


def backtest_payload() -> BacktestPersistencePayload:
    strategy_config = build_rsi_strategy_config_payload(
        window=2, buy_threshold=30, sell_threshold=70
    )
    run_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return BacktestPersistencePayload(
        strategy_config=strategy_config,
        run=BacktestRunPayload(
            run_key="run-key",
            engine_name="BasicBacktester",
            engine_version="basic_backtester_v1",
            candle_source="binance_spot",
            symbol="BTCUSDT",
            interval="1m",
            requested_start_time=run_time,
            requested_end_time=run_time,
            actual_start_time=run_time,
            actual_end_time=run_time,
            candle_count=1,
            starting_cash=1000.0,
            trade_quantity=1.0,
            status="completed",
            metadata={"schema_version": "backtest_persistence_schema_v1"},
        ),
        result=BacktestResultPayload(
            starting_cash=1000.0,
            ending_cash=900.0,
            ending_position=1.0,
            final_price=100.0,
            final_equity=1000.0,
            total_return=0.0,
            trade_count=1,
            buy_count=1,
            sell_count=0,
        ),
        trades=(
            BacktestTradePayload(
                sequence=1,
                candle_open_time=run_time,
                signal="BUY",
                price=100.0,
                quantity=1.0,
                cash_after=900.0,
                position_after=1.0,
            ),
        ),
        graph_points=(
            BacktestGraphPointPayload(
                sequence=1,
                candle_open_time=run_time,
                close_price=100.0,
                cash=900.0,
                position=1.0,
                equity=1000.0,
                trade_sequence=1,
                signal="BUY",
            ),
        ),
    )


def test_schema_contains_graph_ready_backtest_tables_and_constraints():
    for table_name in (
        "strategy_configs",
        "backtest_runs",
        "backtest_results",
        "backtest_trades",
        "backtest_graph_points",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in managed_schema_sql()
    assert "UNIQUE (strategy_key, version, parameters_hash)" in managed_schema_sql()
    assert (
        "CONSTRAINT backtest_runs_run_key_key UNIQUE (run_key)"
        in managed_schema_sql()
    )
    assert "UNIQUE (backtest_run_id, sequence)" in managed_schema_sql()
    assert "UNIQUE (backtest_run_id, candle_open_time)" in managed_schema_sql()


def test_rsi_strategy_config_payload_is_canonical():
    payload = build_rsi_strategy_config_payload(
        window=14, buy_threshold=30, sell_threshold=70
    )
    same_payload = build_rsi_strategy_config_payload(
        window=14, buy_threshold=30.0, sell_threshold=70.0
    )
    changed_payload = build_rsi_strategy_config_payload(
        window=7, buy_threshold=30, sell_threshold=70
    )

    assert payload.strategy_key == "rsi"
    assert payload.strategy_name == "RsiStrategy"
    assert payload.parameters == {
        "buy_threshold": 30.0,
        "sell_threshold": 70.0,
        "window": 14,
    }
    assert payload.parameters_hash == same_payload.parameters_hash
    assert payload.parameters_hash != changed_payload.parameters_hash


def test_backtest_repository_maps_payload_and_uses_transaction(monkeypatch):
    import psycopg

    fake_connection = FakeBacktestConnection()

    def fake_connect(database_url: str, **kwargs: Any) -> FakeBacktestConnection:
        assert database_url == "postgresql://example/test"
        assert "row_factory" in kwargs
        return fake_connection

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    run_id = PostgresBacktestResultRepository(
        "postgresql://example/test"
    ).save_completed_backtest(backtest_payload())

    assert run_id == 102
    assert fake_connection.transaction_context.entered is True
    assert fake_connection.transaction_context.exit_exc_type is None
    executed_sql = "\n".join(query for query, _ in fake_connection.executed)
    assert "INSERT INTO strategy_configs" in executed_sql
    assert "ON CONFLICT (run_key) DO UPDATE SET" in executed_sql
    assert "DELETE FROM backtest_graph_points" in executed_sql
    assert "DELETE FROM backtest_trades" in executed_sql
    assert "DELETE FROM backtest_results" in executed_sql
    assert "INSERT INTO backtest_runs" in executed_sql
    assert "INSERT INTO backtest_results" in executed_sql
    assert "INSERT INTO backtest_trades" in executed_sql
    assert "INSERT INTO backtest_graph_points" in executed_sql

    graph_params = next(
        params
        for query, params in fake_connection.executed
        if "INSERT INTO backtest_graph_points" in query
    )
    assert graph_params["trade_id"] == 107
    assert graph_params["sequence"] == 1
    assert graph_params["signal"] == "BUY"
    assert graph_params["equity"] == 1000.0


def test_backtest_repository_failure_exits_transaction_with_error(monkeypatch):
    import psycopg

    fake_connection = FakeBacktestConnection(fail_on_graph_point=True)

    monkeypatch.setattr(
        psycopg,
        "connect",
        lambda database_url, **kwargs: fake_connection,
    )

    with pytest.raises(RuntimeError, match="simulated graph point insert failure"):
        PostgresBacktestResultRepository(
            "postgresql://example/test"
        ).save_completed_backtest(backtest_payload())

    assert fake_connection.transaction_context.entered is True
    assert fake_connection.transaction_context.exit_exc_type is RuntimeError

class FakeReadResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def fetchone(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows


class FakeBacktestReadConnection:
    def __init__(self, responses: list[list[dict[str, Any]]]) -> None:
        self.responses = responses
        self.executed: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> "FakeBacktestReadConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str, params: dict[str, Any]) -> FakeReadResult:
        self.executed.append((query, params))
        return FakeReadResult(self.responses.pop(0))


def read_run_row() -> dict[str, Any]:
    created_at = datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc)
    return {
        "run_id": 42,
        "run_key": "run-key",
        "engine_name": "BasicBacktester",
        "engine_version": "basic_backtester_v1",
        "candle_source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "requested_start_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "requested_end_time": datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc),
        "actual_start_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "actual_end_time": datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc),
        "candle_count": 3,
        "run_starting_cash": Decimal("1000"),
        "trade_quantity": Decimal("1"),
        "status": "completed",
        "run_metadata": {"schema_version": "backtest_persistence_schema_v1"},
        "run_created_at": created_at,
        "completed_at": created_at,
        "strategy_config_id": 7,
        "strategy_key": "rsi",
        "strategy_name": "RsiStrategy",
        "strategy_version": "rsi_strategy_v1",
        "strategy_parameters": {"window": 2, "buy_threshold": 30.0, "sell_threshold": 70.0},
        "parameters_hash": "hash",
        "strategy_metadata": None,
        "result_starting_cash": Decimal("1000"),
        "ending_cash": Decimal("900"),
        "ending_position": Decimal("1"),
        "final_price": Decimal("110"),
        "final_equity": Decimal("1010"),
        "total_return": Decimal("0.01"),
        "trade_count": 1,
        "buy_count": 1,
        "sell_count": 0,
        "result_metadata": {
            "source": "unit-test",
            "performance_metrics": {"schema_version": "performance_metrics_v1"},
        },
        "result_created_at": created_at,
    }


def test_backtest_read_model_loads_run_summary_trades_and_graph_points(monkeypatch):
    import psycopg

    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc)
    t2 = datetime(2024, 1, 1, 0, 2, tzinfo=timezone.utc)
    fake_connection = FakeBacktestReadConnection(
        [
            [read_run_row()],
            [
                {
                    "id": 101,
                    "sequence": 1,
                    "candle_open_time": t1,
                    "signal": "BUY",
                    "price": Decimal("100"),
                    "quantity": Decimal("1"),
                    "cash_after": Decimal("900"),
                    "position_after": Decimal("1"),
                    "metadata": {"kind": "simulated"},
                }
            ],
            [
                {
                    "id": 201,
                    "sequence": 1,
                    "candle_open_time": t0,
                    "close_price": Decimal("95"),
                    "cash": Decimal("1000"),
                    "position": Decimal("0"),
                    "equity": Decimal("1000"),
                    "trade_id": None,
                    "signal": None,
                    "metadata": None,
                },
                {
                    "id": 202,
                    "sequence": 2,
                    "candle_open_time": t1,
                    "close_price": Decimal("100"),
                    "cash": Decimal("900"),
                    "position": Decimal("1"),
                    "equity": Decimal("1000"),
                    "trade_id": 101,
                    "signal": "BUY",
                    "metadata": {"trade_sequence": 1},
                },
                {
                    "id": 203,
                    "sequence": 3,
                    "candle_open_time": t2,
                    "close_price": Decimal("110"),
                    "cash": Decimal("900"),
                    "position": Decimal("1"),
                    "equity": Decimal("1010"),
                    "trade_id": None,
                    "signal": None,
                    "metadata": None,
                },
            ],
        ]
    )

    monkeypatch.setattr(psycopg, "connect", lambda database_url, **kwargs: fake_connection)

    model = PostgresBacktestResultRepository(
        "postgresql://example/test"
    ).load_run_for_graphs(42)

    assert model is not None
    assert model.run.id == 42
    assert model.run.symbol == "BTCUSDT"
    assert model.strategy_config.parameters["window"] == 2
    assert model.summary.final_equity == 1010.0
    assert model.summary.metadata["performance_metrics"]["schema_version"] == "performance_metrics_v1"
    assert [trade.sequence for trade in model.trades] == [1]
    assert model.trades[0].signal == "BUY"
    assert [point.candle_open_time for point in model.graph_points] == [t0, t1, t2]
    assert model.graph_points[1].trade_id == 101
    assert model.graph_points[1].signal == "BUY"
    assert model.graph_points[2].equity == 1010.0
    assert all(params == {"backtest_run_id": 42} for _, params in fake_connection.executed)
    executed_sql = "\n".join(query for query, _ in fake_connection.executed)
    assert "SELECT" in executed_sql
    assert "INSERT" not in executed_sql
    assert "UPDATE" not in executed_sql
    assert "DELETE" not in executed_sql


def test_backtest_read_model_orders_trades_and_graph_points_in_sql(monkeypatch):
    import psycopg

    fake_connection = FakeBacktestReadConnection([[read_run_row()], [], []])
    monkeypatch.setattr(psycopg, "connect", lambda database_url, **kwargs: fake_connection)

    PostgresBacktestResultRepository("postgresql://example/test").load_run_for_graphs(42)

    trade_query = fake_connection.executed[1][0]
    graph_query = fake_connection.executed[2][0]
    assert "ORDER BY sequence ASC" in trade_query
    assert "ORDER BY candle_open_time ASC, sequence ASC" in graph_query


def test_backtest_read_model_missing_run_returns_none(monkeypatch):
    import psycopg

    fake_connection = FakeBacktestReadConnection([[]])
    monkeypatch.setattr(psycopg, "connect", lambda database_url, **kwargs: fake_connection)

    model = PostgresBacktestResultRepository(
        "postgresql://example/test"
    ).load_run_for_graphs(404)

    assert model is None
    assert len(fake_connection.executed) == 1


def test_backtest_read_model_lists_completed_runs_with_filters(monkeypatch):
    import psycopg

    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 2, tzinfo=timezone.utc)
    fake_connection = FakeBacktestReadConnection(
        [
            [
                {
                    "id": 42,
                    "run_key": "run-key",
                    "strategy_config_id": 7,
                    "strategy_key": "rsi",
                    "strategy_name": "RsiStrategy",
                    "strategy_version": "rsi_strategy_v1",
                    "strategy_parameters": {"window": 14},
                    "strategy_parameters_hash": "strategy-hash",
                    "candle_source": "binance_spot",
                    "symbol": "BTCUSDT",
                    "interval": "1m",
                    "actual_start_time": t0,
                    "actual_end_time": t1,
                    "candle_count": 100,
                    "final_equity": Decimal("1010"),
                    "total_return": Decimal("0.01"),
                    "trade_count": 2,
                    "metadata": {"runtime": {"total_elapsed_ms": 12.0}},
                    "created_at": t1,
                    "completed_at": t1,
                }
            ]
        ]
    )
    monkeypatch.setattr(psycopg, "connect", lambda database_url, **kwargs: fake_connection)

    rows = PostgresBacktestResultRepository("postgresql://example/test").list_completed_runs(
        source="binance_spot",
        symbol="BTCUSDT",
        interval="1m",
        strategy_key="rsi",
        actual_start_time=t0,
        actual_end_time=t1,
        created_start_time=t0,
        created_end_time=t1,
        min_total_return=-0.01,
        max_total_return=0.05,
        cost_profile="conservative_crypto_1m",
        limit=5,
    )

    assert len(rows) == 1
    assert rows[0].id == 42
    assert rows[0].strategy_config_id == 7
    assert rows[0].strategy_key == "rsi"
    assert rows[0].strategy_name == "RsiStrategy"
    assert rows[0].strategy_version == "rsi_strategy_v1"
    assert rows[0].strategy_parameters == {"window": 14}
    assert rows[0].strategy_parameters_hash == "strategy-hash"
    assert rows[0].final_equity == 1010.0
    assert rows[0].metadata == {"runtime": {"total_elapsed_ms": 12.0}}
    query, params = fake_connection.executed[0]
    assert "sc.id AS strategy_config_id" in query
    assert "sc.strategy_key" in query
    assert "sc.parameters AS strategy_parameters" in query
    assert "sc.parameters_hash AS strategy_parameters_hash" in query
    assert "br.metadata" in query
    assert "JOIN strategy_configs sc ON sc.id = br.strategy_config_id" in query
    assert "br.candle_source = %(source)s" in query
    assert "br.symbol = %(symbol)s" in query
    assert "br.interval = %(interval)s" in query
    assert "sc.strategy_key = %(strategy_key)s" in query
    assert "br.actual_start_time >= %(actual_start_time)s" in query
    assert "br.actual_end_time <= %(actual_end_time)s" in query
    assert "br.created_at >= %(created_start_time)s" in query
    assert "br.created_at <= %(created_end_time)s" in query
    assert "r.total_return >= %(min_total_return)s" in query
    assert "r.total_return <= %(max_total_return)s" in query
    assert "br.metadata #>> '{cost_profile,profile_key}' = %(cost_profile)s" in query
    assert "r.metadata #>> '{cost_profile,profile_key}' = %(cost_profile)s" in query
    assert "sc.parameters ->> 'cost.profile' = %(cost_profile)s" in query
    assert "sc.parameters #>> '{cost_profile}' = %(cost_profile)s" in query
    assert "ORDER BY br.created_at DESC, br.id DESC" in query
    assert "LIMIT %(limit)s" in query
    assert params == {
        "source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "strategy_key": "rsi",
        "actual_start_time": t0,
        "actual_end_time": t1,
        "created_start_time": t0,
        "created_end_time": t1,
        "min_total_return": -0.01,
        "max_total_return": 0.05,
        "cost_profile": "conservative_crypto_1m",
        "limit": 5,
    }


def test_backtest_read_model_rejects_non_positive_list_limit():
    with pytest.raises(ValueError, match="limit must be positive"):
        PostgresBacktestResultRepository("postgresql://example/test").list_completed_runs(
            limit=0
        )


def test_backtest_read_model_rejects_invalid_list_filter_ranges():
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 2, tzinfo=timezone.utc)
    repository = PostgresBacktestResultRepository("postgresql://example/test")

    with pytest.raises(ValueError, match="actual_start_time"):
        repository.list_completed_runs(actual_start_time=t1, actual_end_time=t0)

    with pytest.raises(ValueError, match="created_start_time"):
        repository.list_completed_runs(created_start_time=t1, created_end_time=t0)

    with pytest.raises(ValueError, match="min_total_return"):
        repository.list_completed_runs(min_total_return=0.1, max_total_return=-0.1)
