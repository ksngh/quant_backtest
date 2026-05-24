"""PostgreSQL persistence for market data and backtest outputs.

This module owns durable storage for public candle data, ingestion checkpoints,
and simulated backtest results. It does not place orders, sign requests, manage
API keys, or call exchange account/order endpoints.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from quant_bitcoin.persistence.db_commands import execute_initial_db_commands

SOURCE_BINANCE_SPOT = "binance_spot"
HISTORICAL_BACKFILL_MODE = "historical_backfill"
BACKTEST_SCHEMA_VERSION = "backtest_persistence_schema_v1"
BACKTEST_ENGINE_NAME = "BasicBacktester"
BACKTEST_ENGINE_VERSION = "basic_backtester_v1"
RSI_STRATEGY_KEY = "rsi"
RSI_STRATEGY_NAME = "RsiStrategy"
RSI_STRATEGY_VERSION = "rsi_strategy_v1"
COMPLETED_BACKTEST_STATUS = "completed"

CANDLE_TABLE_COLUMNS: tuple[str, ...] = (
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



@dataclass(frozen=True)
class PersistedCandle:
    """A finalized candle row following the accepted Task 013 schema."""

    source: str
    symbol: str
    interval: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_asset_volume: Decimal
    number_of_trades: int
    taker_buy_base_asset_volume: Decimal
    taker_buy_quote_asset_volume: Decimal
    is_closed: bool
    raw_payload: list[Any] | dict[str, Any] | None = None

    def as_insert_row(self) -> dict[str, Any]:
        """Return a row containing the Task 013 candle contract fields."""

        return {column: getattr(self, column) for column in CANDLE_TABLE_COLUMNS}


@dataclass(frozen=True)
class IngestionCheckpoint:
    """Progress record for restartable candle ingestion."""

    source: str
    symbol: str
    interval: str
    mode: str
    last_open_time: datetime | None
    last_close_time: datetime | None
    last_event_time: datetime | None
    status: str
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class StrategyConfigPayload:
    """Deterministic strategy configuration to persist for a backtest run."""

    strategy_key: str
    strategy_name: str
    version: str
    parameters: dict[str, Any]
    parameters_hash: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class BacktestRunPayload:
    """Run metadata and deterministic identity for a persisted backtest."""

    run_key: str
    engine_name: str
    engine_version: str
    candle_source: str
    symbol: str
    interval: str
    requested_start_time: datetime | None
    requested_end_time: datetime | None
    actual_start_time: datetime | None
    actual_end_time: datetime | None
    candle_count: int
    starting_cash: float
    trade_quantity: float
    status: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class BacktestResultPayload:
    """One-row summary values for a persisted backtest."""

    starting_cash: float
    ending_cash: float
    ending_position: float
    final_price: float | None
    final_equity: float
    total_return: float
    trade_count: int
    buy_count: int
    sell_count: int
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class BacktestTradePayload:
    """A deterministic simulated trade row for a persisted backtest."""

    sequence: int
    candle_open_time: datetime
    signal: str
    price: float
    quantity: float
    cash_after: float
    position_after: float
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class BacktestGraphPointPayload:
    """A graph-ready time-series point for a persisted backtest."""

    sequence: int
    candle_open_time: datetime
    close_price: float
    cash: float
    position: float
    equity: float
    trade_sequence: int | None = None
    signal: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class BacktestPersistencePayload:
    """Complete all-or-nothing payload for one completed backtest run."""

    strategy_config: StrategyConfigPayload
    run: BacktestRunPayload
    result: BacktestResultPayload
    trades: tuple[BacktestTradePayload, ...]
    graph_points: tuple[BacktestGraphPointPayload, ...]


@dataclass(frozen=True)
class BacktestStrategyConfigReadModel:
    """Strategy metadata returned with a persisted backtest graph read."""

    id: int
    strategy_key: str
    strategy_name: str
    version: str
    parameters: dict[str, Any]
    parameters_hash: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class BacktestRunMetadataReadModel:
    """Run metadata returned by the read-only graph result model."""

    id: int
    run_key: str
    engine_name: str
    engine_version: str
    candle_source: str
    symbol: str
    interval: str
    requested_start_time: datetime | None
    requested_end_time: datetime | None
    actual_start_time: datetime | None
    actual_end_time: datetime | None
    candle_count: int
    starting_cash: float
    trade_quantity: float
    status: str
    metadata: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True)
class BacktestSummaryReadModel:
    """Summary metrics for one persisted completed backtest."""

    starting_cash: float
    ending_cash: float
    ending_position: float
    final_price: float | None
    final_equity: float
    total_return: float
    trade_count: int
    buy_count: int
    sell_count: int
    metadata: dict[str, Any] | None
    created_at: datetime


@dataclass(frozen=True)
class BacktestTradeReadModel:
    """Deterministically ordered simulated trade returned for graph markers."""

    id: int
    sequence: int
    candle_open_time: datetime
    signal: str
    price: float
    quantity: float
    cash_after: float
    position_after: float
    metadata: dict[str, Any] | None


@dataclass(frozen=True)
class BacktestGraphPointReadModel:
    """Dense graph-ready point for one candle in a saved backtest run."""

    id: int
    sequence: int
    candle_open_time: datetime
    close_price: float
    cash: float
    position: float
    equity: float
    trade_id: int | None
    signal: str | None
    metadata: dict[str, Any] | None


@dataclass(frozen=True)
class BacktestRunReadModel:
    """Complete read-only shape for future graph consumers."""

    run: BacktestRunMetadataReadModel
    strategy_config: BacktestStrategyConfigReadModel
    summary: BacktestSummaryReadModel
    trades: tuple[BacktestTradeReadModel, ...]
    graph_points: tuple[BacktestGraphPointReadModel, ...]


@dataclass(frozen=True)
class BacktestRunListItem:
    """Lightweight completed-run selector row for graph input selection."""

    id: int
    run_key: str
    strategy_config_id: int
    strategy_key: str
    strategy_name: str
    strategy_version: str
    strategy_parameters: dict[str, Any]
    strategy_parameters_hash: str
    candle_source: str
    symbol: str
    interval: str
    actual_start_time: datetime | None
    actual_end_time: datetime | None
    candle_count: int
    final_equity: float
    total_return: float
    trade_count: int
    metadata: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None


class PostgresCandleRepository:
    """PostgreSQL repository for candles and ingestion checkpoints."""

    def __init__(self, database_url: str) -> None:
        if not database_url:
            raise ValueError("database_url must not be blank")
        self.database_url = database_url

    def initialize_schema(self) -> None:
        """Create the local development schema if it does not exist."""

        import psycopg

        with psycopg.connect(self.database_url) as connection:
            execute_initial_db_commands(connection)

    def upsert_candles(self, candles: Iterable[PersistedCandle]) -> int:
        """Insert finalized candles and update duplicates by unique candle key."""

        import psycopg
        from psycopg.types.json import Jsonb

        rows = [candle.as_insert_row() for candle in candles]
        if not rows:
            return 0
        for row in rows:
            row["raw_payload"] = Jsonb(row["raw_payload"])

        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(UPSERT_CANDLE_SQL, rows)
            return len(rows)

    def latest_open_time(
        self, source: str, symbol: str, interval: str
    ) -> datetime | None:
        """Return the latest stored open time for a candle stream."""

        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(
                """
                SELECT MAX(open_time) AS latest_open_time
                FROM candles
                WHERE source = %s AND symbol = %s AND interval = %s
                """,
                (source, symbol, interval),
            ).fetchone()
        latest = row["latest_open_time"] if row else None
        if isinstance(latest, datetime):
            return _as_utc(latest)
        return None

    def load_standard_candles(
        self,
        *,
        source: str,
        symbol: str,
        interval: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Return stored candles normalized to the standard candle schema."""

        import psycopg
        from psycopg.rows import dict_row

        query, params = _build_standard_candle_query(
            source=source,
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
        )
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            {
                "timestamp": _as_utc(row["timestamp"]),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }
            for row in rows
        ]

    def save_checkpoint(self, checkpoint: IngestionCheckpoint) -> None:
        """Insert or update a restart checkpoint."""

        import psycopg
        from psycopg.types.json import Jsonb

        with psycopg.connect(self.database_url) as connection:
            connection.execute(
                UPSERT_CHECKPOINT_SQL,
                {
                    "source": checkpoint.source,
                    "symbol": checkpoint.symbol,
                    "interval": checkpoint.interval,
                    "mode": checkpoint.mode,
                    "last_open_time": checkpoint.last_open_time,
                    "last_close_time": checkpoint.last_close_time,
                    "last_event_time": checkpoint.last_event_time,
                    "status": checkpoint.status,
                    "error_message": checkpoint.error_message,
                    "metadata": Jsonb(checkpoint.metadata),
                },
            )

    def load_checkpoint(
        self, source: str, symbol: str, interval: str, mode: str
    ) -> IngestionCheckpoint | None:
        """Load a restart checkpoint if one exists."""

        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(
                """
                SELECT source, symbol, interval, mode, last_open_time,
                       last_close_time, last_event_time, status, error_message,
                       metadata
                FROM ingestion_checkpoints
                WHERE source = %s AND symbol = %s AND interval = %s AND mode = %s
                """,
                (source, symbol, interval, mode),
            ).fetchone()
        if row is None:
            return None
        return IngestionCheckpoint(
            source=row["source"],
            symbol=row["symbol"],
            interval=row["interval"],
            mode=row["mode"],
            last_open_time=_optional_utc(row["last_open_time"]),
            last_close_time=_optional_utc(row["last_close_time"]),
            last_event_time=_optional_utc(row["last_event_time"]),
            status=row["status"],
            error_message=row["error_message"],
            metadata=row["metadata"],
        )


class PostgresBacktestResultRepository:
    """PostgreSQL repository for simulated backtest output rows."""

    def __init__(self, database_url: str) -> None:
        if not database_url:
            raise ValueError("database_url must not be blank")
        self.database_url = database_url

    def initialize_schema(self) -> None:
        """Create the local development schema if it does not exist."""

        import psycopg

        with psycopg.connect(self.database_url) as connection:
            execute_initial_db_commands(connection)

    def save_completed_backtest(self, payload: BacktestPersistencePayload) -> int:
        """Persist one completed simulated run atomically and return its run id."""

        import psycopg
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.transaction():
                strategy_config_id = _upsert_strategy_config(
                    connection, payload.strategy_config, Jsonb
                )
                backtest_run_id = _upsert_backtest_run(
                    connection, payload.run, strategy_config_id, Jsonb
                )
                _delete_existing_backtest_outputs(connection, backtest_run_id)
                _insert_backtest_result(
                    connection, backtest_run_id, payload.result, Jsonb
                )
                trade_ids = _insert_backtest_trades(
                    connection, backtest_run_id, payload.trades, Jsonb
                )
                _insert_backtest_graph_points(
                    connection,
                    backtest_run_id,
                    payload.graph_points,
                    trade_ids,
                    Jsonb,
                )
                return int(backtest_run_id)

    def load_run_for_graphs(self, backtest_run_id: int) -> BacktestRunReadModel | None:
        """Load one completed run in the read-only shape needed by graph consumers.

        The read path only selects saved rows. It does not call market-data
        providers, strategy code, backtest engines, Binance endpoints, or order
        endpoints. Trades are returned by ascending sequence, and graph points
        are returned by ascending candle timestamp and sequence.
        """

        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(
                SELECT_BACKTEST_RUN_READ_MODEL_SQL,
                {"backtest_run_id": backtest_run_id},
            ).fetchone()
            if row is None:
                return None
            trade_rows = connection.execute(
                SELECT_BACKTEST_TRADES_FOR_GRAPH_SQL,
                {"backtest_run_id": backtest_run_id},
            ).fetchall()
            graph_point_rows = connection.execute(
                SELECT_BACKTEST_GRAPH_POINTS_SQL,
                {"backtest_run_id": backtest_run_id},
            ).fetchall()

        return BacktestRunReadModel(
            run=_map_backtest_run_metadata(row),
            strategy_config=_map_strategy_config(row),
            summary=_map_backtest_summary(row),
            trades=tuple(_map_backtest_trade(trade) for trade in trade_rows),
            graph_points=tuple(
                _map_backtest_graph_point(point) for point in graph_point_rows
            ),
        )

    def list_completed_runs(
        self,
        *,
        source: str | None = None,
        symbol: str | None = None,
        interval: str | None = None,
        actual_start_time: datetime | None = None,
        actual_end_time: datetime | None = None,
        limit: int = 20,
    ) -> tuple[BacktestRunListItem, ...]:
        """List recent completed runs for choosing graph inputs.

        Optional filters narrow by candle source, symbol, interval, and the
        persisted actual candle time range. Results are ordered newest first by
        run creation time and id.
        """

        if limit <= 0:
            raise ValueError("limit must be positive")

        import psycopg
        from psycopg.rows import dict_row

        query, params = _build_completed_runs_query(
            source=source,
            symbol=symbol,
            interval=interval,
            actual_start_time=actual_start_time,
            actual_end_time=actual_end_time,
            limit=limit,
        )
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            rows = connection.execute(query, params).fetchall()

        return tuple(_map_backtest_run_list_item(row) for row in rows)


SELECT_STANDARD_CANDLES_BASE_SQL = """
SELECT open_time AS timestamp, open, high, low, close, volume
FROM candles
WHERE source = %(source)s AND symbol = %(symbol)s AND interval = %(interval)s
  AND is_closed IS TRUE
"""


UPSERT_CANDLE_SQL = """
INSERT INTO candles (
    source, symbol, interval, open_time, close_time, open, high, low, close,
    volume, quote_asset_volume, number_of_trades, taker_buy_base_asset_volume,
    taker_buy_quote_asset_volume, is_closed, raw_payload
) VALUES (
    %(source)s, %(symbol)s, %(interval)s, %(open_time)s, %(close_time)s,
    %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s,
    %(quote_asset_volume)s, %(number_of_trades)s,
    %(taker_buy_base_asset_volume)s, %(taker_buy_quote_asset_volume)s,
    %(is_closed)s, %(raw_payload)s
)
ON CONFLICT (source, symbol, interval, open_time) DO UPDATE SET
    close_time = EXCLUDED.close_time,
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume,
    quote_asset_volume = EXCLUDED.quote_asset_volume,
    number_of_trades = EXCLUDED.number_of_trades,
    taker_buy_base_asset_volume = EXCLUDED.taker_buy_base_asset_volume,
    taker_buy_quote_asset_volume = EXCLUDED.taker_buy_quote_asset_volume,
    is_closed = EXCLUDED.is_closed,
    raw_payload = EXCLUDED.raw_payload,
    updated_at = now()
"""

UPSERT_CHECKPOINT_SQL = """
INSERT INTO ingestion_checkpoints (
    source, symbol, interval, mode, last_open_time, last_close_time,
    last_event_time, status, error_message, metadata
) VALUES (
    %(source)s, %(symbol)s, %(interval)s, %(mode)s, %(last_open_time)s,
    %(last_close_time)s, %(last_event_time)s, %(status)s, %(error_message)s,
    %(metadata)s
)
ON CONFLICT (source, symbol, interval, mode) DO UPDATE SET
    last_open_time = EXCLUDED.last_open_time,
    last_close_time = EXCLUDED.last_close_time,
    last_event_time = EXCLUDED.last_event_time,
    status = EXCLUDED.status,
    error_message = EXCLUDED.error_message,
    metadata = EXCLUDED.metadata,
    updated_at = now()
"""

UPSERT_STRATEGY_CONFIG_SQL = """
INSERT INTO strategy_configs (
    strategy_key, strategy_name, version, parameters, parameters_hash, metadata
) VALUES (
    %(strategy_key)s, %(strategy_name)s, %(version)s, %(parameters)s,
    %(parameters_hash)s, %(metadata)s
)
ON CONFLICT (strategy_key, version, parameters_hash) DO UPDATE SET
    strategy_name = EXCLUDED.strategy_name,
    parameters = EXCLUDED.parameters,
    metadata = EXCLUDED.metadata
RETURNING id
"""

UPSERT_BACKTEST_RUN_SQL = """
INSERT INTO backtest_runs (
    run_key, strategy_config_id, engine_name, engine_version, candle_source,
    symbol, interval, requested_start_time, requested_end_time, actual_start_time,
    actual_end_time, candle_count, starting_cash, trade_quantity, status, metadata,
    completed_at
) VALUES (
    %(run_key)s, %(strategy_config_id)s, %(engine_name)s, %(engine_version)s,
    %(candle_source)s, %(symbol)s, %(interval)s, %(requested_start_time)s,
    %(requested_end_time)s, %(actual_start_time)s, %(actual_end_time)s,
    %(candle_count)s, %(starting_cash)s, %(trade_quantity)s, %(status)s,
    %(metadata)s, %(completed_at)s
)
ON CONFLICT (run_key) DO UPDATE SET
    strategy_config_id = EXCLUDED.strategy_config_id,
    engine_name = EXCLUDED.engine_name,
    engine_version = EXCLUDED.engine_version,
    candle_source = EXCLUDED.candle_source,
    symbol = EXCLUDED.symbol,
    interval = EXCLUDED.interval,
    requested_start_time = EXCLUDED.requested_start_time,
    requested_end_time = EXCLUDED.requested_end_time,
    actual_start_time = EXCLUDED.actual_start_time,
    actual_end_time = EXCLUDED.actual_end_time,
    candle_count = EXCLUDED.candle_count,
    starting_cash = EXCLUDED.starting_cash,
    trade_quantity = EXCLUDED.trade_quantity,
    status = EXCLUDED.status,
    metadata = EXCLUDED.metadata,
    completed_at = EXCLUDED.completed_at
RETURNING id
"""

DELETE_BACKTEST_GRAPH_POINTS_SQL = """
DELETE FROM backtest_graph_points WHERE backtest_run_id = %(backtest_run_id)s
"""

DELETE_BACKTEST_TRADES_SQL = """
DELETE FROM backtest_trades WHERE backtest_run_id = %(backtest_run_id)s
"""

DELETE_BACKTEST_RESULT_SQL = """
DELETE FROM backtest_results WHERE backtest_run_id = %(backtest_run_id)s
"""

INSERT_BACKTEST_RESULT_SQL = """
INSERT INTO backtest_results (
    backtest_run_id, starting_cash, ending_cash, ending_position, final_price,
    final_equity, total_return, trade_count, buy_count, sell_count, metadata
) VALUES (
    %(backtest_run_id)s, %(starting_cash)s, %(ending_cash)s,
    %(ending_position)s, %(final_price)s, %(final_equity)s, %(total_return)s,
    %(trade_count)s, %(buy_count)s, %(sell_count)s, %(metadata)s
)
"""

INSERT_BACKTEST_TRADE_SQL = """
INSERT INTO backtest_trades (
    backtest_run_id, sequence, candle_open_time, signal, price, quantity,
    cash_after, position_after, metadata
) VALUES (
    %(backtest_run_id)s, %(sequence)s, %(candle_open_time)s, %(signal)s,
    %(price)s, %(quantity)s, %(cash_after)s, %(position_after)s, %(metadata)s
)
RETURNING id
"""

INSERT_BACKTEST_GRAPH_POINT_SQL = """
INSERT INTO backtest_graph_points (
    backtest_run_id, sequence, candle_open_time, close_price, cash, position,
    equity, trade_id, signal, metadata
) VALUES (
    %(backtest_run_id)s, %(sequence)s, %(candle_open_time)s, %(close_price)s,
    %(cash)s, %(position)s, %(equity)s, %(trade_id)s, %(signal)s, %(metadata)s
)
"""

SELECT_BACKTEST_RUN_READ_MODEL_SQL = """
SELECT
    br.id AS run_id,
    br.run_key,
    br.engine_name,
    br.engine_version,
    br.candle_source,
    br.symbol,
    br.interval,
    br.requested_start_time,
    br.requested_end_time,
    br.actual_start_time,
    br.actual_end_time,
    br.candle_count,
    br.starting_cash AS run_starting_cash,
    br.trade_quantity,
    br.status,
    br.metadata AS run_metadata,
    br.created_at AS run_created_at,
    br.completed_at,
    sc.id AS strategy_config_id,
    sc.strategy_key,
    sc.strategy_name,
    sc.version AS strategy_version,
    sc.parameters AS strategy_parameters,
    sc.parameters_hash,
    sc.metadata AS strategy_metadata,
    r.starting_cash AS result_starting_cash,
    r.ending_cash,
    r.ending_position,
    r.final_price,
    r.final_equity,
    r.total_return,
    r.trade_count,
    r.buy_count,
    r.sell_count,
    r.metadata AS result_metadata,
    r.created_at AS result_created_at
FROM backtest_runs br
JOIN strategy_configs sc ON sc.id = br.strategy_config_id
JOIN backtest_results r ON r.backtest_run_id = br.id
WHERE br.id = %(backtest_run_id)s
  AND br.status = 'completed'
"""

SELECT_BACKTEST_TRADES_FOR_GRAPH_SQL = """
SELECT id, sequence, candle_open_time, signal, price, quantity, cash_after,
       position_after, metadata
FROM backtest_trades
WHERE backtest_run_id = %(backtest_run_id)s
ORDER BY sequence ASC
"""

SELECT_BACKTEST_GRAPH_POINTS_SQL = """
SELECT id, sequence, candle_open_time, close_price, cash, position, equity,
       trade_id, signal, metadata
FROM backtest_graph_points
WHERE backtest_run_id = %(backtest_run_id)s
ORDER BY candle_open_time ASC, sequence ASC
"""

SELECT_COMPLETED_BACKTEST_RUNS_BASE_SQL = """
SELECT
    br.id,
    br.run_key,
    sc.id AS strategy_config_id,
    sc.strategy_key,
    sc.strategy_name,
    sc.version AS strategy_version,
    sc.parameters AS strategy_parameters,
    sc.parameters_hash AS strategy_parameters_hash,
    br.candle_source,
    br.symbol,
    br.interval,
    br.actual_start_time,
    br.actual_end_time,
    br.candle_count,
    r.final_equity,
    r.total_return,
    r.trade_count,
    br.metadata,
    br.created_at,
    br.completed_at
FROM backtest_runs br
JOIN strategy_configs sc ON sc.id = br.strategy_config_id
JOIN backtest_results r ON r.backtest_run_id = br.id
WHERE br.status = 'completed'
"""


def build_rsi_strategy_config_payload(
    *, window: int, buy_threshold: float, sell_threshold: float
) -> StrategyConfigPayload:
    """Return canonical RSI strategy metadata for persistence."""

    parameters = {
        "buy_threshold": float(buy_threshold),
        "sell_threshold": float(sell_threshold),
        "window": int(window),
    }
    return StrategyConfigPayload(
        strategy_key=RSI_STRATEGY_KEY,
        strategy_name=RSI_STRATEGY_NAME,
        version=RSI_STRATEGY_VERSION,
        parameters=parameters,
        parameters_hash=canonical_hash(parameters),
    )


def build_backtest_run_key(identity: dict[str, Any]) -> str:
    """Return the deterministic SHA-256 identity for a backtest run."""

    return canonical_hash(identity)


def canonical_hash(value: dict[str, Any]) -> str:
    """Hash canonical JSON for deterministic identity fields."""

    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(
        _json_ready(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return _format_timestamp(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _json_ready(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _upsert_strategy_config(
    connection: Any, strategy_config: StrategyConfigPayload, jsonb_factory: Any
) -> int:
    row = connection.execute(
        UPSERT_STRATEGY_CONFIG_SQL,
        {
            "strategy_key": strategy_config.strategy_key,
            "strategy_name": strategy_config.strategy_name,
            "version": strategy_config.version,
            "parameters": jsonb_factory(strategy_config.parameters),
            "parameters_hash": strategy_config.parameters_hash,
            "metadata": jsonb_factory(strategy_config.metadata),
        },
    ).fetchone()
    return int(row["id"])


def _upsert_backtest_run(
    connection: Any,
    run: BacktestRunPayload,
    strategy_config_id: int,
    jsonb_factory: Any,
) -> int:
    row = connection.execute(
        UPSERT_BACKTEST_RUN_SQL,
        {
            "run_key": run.run_key,
            "strategy_config_id": strategy_config_id,
            "engine_name": run.engine_name,
            "engine_version": run.engine_version,
            "candle_source": run.candle_source,
            "symbol": run.symbol,
            "interval": run.interval,
            "requested_start_time": run.requested_start_time,
            "requested_end_time": run.requested_end_time,
            "actual_start_time": run.actual_start_time,
            "actual_end_time": run.actual_end_time,
            "candle_count": run.candle_count,
            "starting_cash": run.starting_cash,
            "trade_quantity": run.trade_quantity,
            "status": run.status,
            "metadata": jsonb_factory(run.metadata),
            "completed_at": datetime.now(timezone.utc),
        },
    ).fetchone()
    return int(row["id"])


def _delete_existing_backtest_outputs(connection: Any, backtest_run_id: int) -> None:
    params = {"backtest_run_id": backtest_run_id}
    connection.execute(DELETE_BACKTEST_GRAPH_POINTS_SQL, params)
    connection.execute(DELETE_BACKTEST_TRADES_SQL, params)
    connection.execute(DELETE_BACKTEST_RESULT_SQL, params)


def _insert_backtest_result(
    connection: Any,
    backtest_run_id: int,
    result: BacktestResultPayload,
    jsonb_factory: Any,
) -> None:
    connection.execute(
        INSERT_BACKTEST_RESULT_SQL,
        {
            "backtest_run_id": backtest_run_id,
            "starting_cash": result.starting_cash,
            "ending_cash": result.ending_cash,
            "ending_position": result.ending_position,
            "final_price": result.final_price,
            "final_equity": result.final_equity,
            "total_return": result.total_return,
            "trade_count": result.trade_count,
            "buy_count": result.buy_count,
            "sell_count": result.sell_count,
            "metadata": jsonb_factory(result.metadata),
        },
    )


def _insert_backtest_trades(
    connection: Any,
    backtest_run_id: int,
    trades: Sequence[BacktestTradePayload],
    jsonb_factory: Any,
) -> dict[int, int]:
    trade_ids: dict[int, int] = {}
    for trade in trades:
        row = connection.execute(
            INSERT_BACKTEST_TRADE_SQL,
            {
                "backtest_run_id": backtest_run_id,
                "sequence": trade.sequence,
                "candle_open_time": trade.candle_open_time,
                "signal": trade.signal,
                "price": trade.price,
                "quantity": trade.quantity,
                "cash_after": trade.cash_after,
                "position_after": trade.position_after,
                "metadata": jsonb_factory(trade.metadata),
            },
        ).fetchone()
        trade_ids[trade.sequence] = int(row["id"])
    return trade_ids


def _insert_backtest_graph_points(
    connection: Any,
    backtest_run_id: int,
    graph_points: Sequence[BacktestGraphPointPayload],
    trade_ids: dict[int, int],
    jsonb_factory: Any,
) -> None:
    for point in graph_points:
        connection.execute(
            INSERT_BACKTEST_GRAPH_POINT_SQL,
            {
                "backtest_run_id": backtest_run_id,
                "sequence": point.sequence,
                "candle_open_time": point.candle_open_time,
                "close_price": point.close_price,
                "cash": point.cash,
                "position": point.position,
                "equity": point.equity,
                "trade_id": (
                    trade_ids[point.trade_sequence]
                    if point.trade_sequence is not None
                    else None
                ),
                "signal": point.signal,
                "metadata": jsonb_factory(point.metadata),
            },
        )


def _build_standard_candle_query(
    *,
    source: str,
    symbol: str,
    interval: str,
    start_time: datetime | None,
    end_time: datetime | None,
) -> tuple[str, dict[str, Any]]:
    query_parts = [SELECT_STANDARD_CANDLES_BASE_SQL]
    params: dict[str, Any] = {
        "source": source,
        "symbol": symbol,
        "interval": interval,
    }
    if start_time is not None:
        query_parts.append("AND open_time >= %(start_time)s")
        params["start_time"] = start_time
    if end_time is not None:
        query_parts.append("AND open_time <= %(end_time)s")
        params["end_time"] = end_time
    query_parts.append("ORDER BY open_time ASC")
    return "\n".join(query_parts), params


def _build_completed_runs_query(
    *,
    source: str | None,
    symbol: str | None,
    interval: str | None,
    actual_start_time: datetime | None,
    actual_end_time: datetime | None,
    limit: int,
) -> tuple[str, dict[str, Any]]:
    query_parts = [SELECT_COMPLETED_BACKTEST_RUNS_BASE_SQL]
    params: dict[str, Any] = {"limit": limit}
    if source is not None:
        query_parts.append("AND br.candle_source = %(source)s")
        params["source"] = source
    if symbol is not None:
        query_parts.append("AND br.symbol = %(symbol)s")
        params["symbol"] = symbol
    if interval is not None:
        query_parts.append("AND br.interval = %(interval)s")
        params["interval"] = interval
    if actual_start_time is not None:
        query_parts.append("AND br.actual_start_time >= %(actual_start_time)s")
        params["actual_start_time"] = actual_start_time
    if actual_end_time is not None:
        query_parts.append("AND br.actual_end_time <= %(actual_end_time)s")
        params["actual_end_time"] = actual_end_time
    query_parts.append("ORDER BY br.created_at DESC, br.id DESC")
    query_parts.append("LIMIT %(limit)s")
    return "\n".join(query_parts), params


def _map_backtest_run_metadata(row: dict[str, Any]) -> BacktestRunMetadataReadModel:
    return BacktestRunMetadataReadModel(
        id=int(row["run_id"]),
        run_key=row["run_key"],
        engine_name=row["engine_name"],
        engine_version=row["engine_version"],
        candle_source=row["candle_source"],
        symbol=row["symbol"],
        interval=row["interval"],
        requested_start_time=_optional_utc(row["requested_start_time"]),
        requested_end_time=_optional_utc(row["requested_end_time"]),
        actual_start_time=_optional_utc(row["actual_start_time"]),
        actual_end_time=_optional_utc(row["actual_end_time"]),
        candle_count=int(row["candle_count"]),
        starting_cash=_as_float(row["run_starting_cash"]),
        trade_quantity=_as_float(row["trade_quantity"]),
        status=row["status"],
        metadata=row["run_metadata"],
        created_at=_as_utc(row["run_created_at"]),
        completed_at=_optional_utc(row["completed_at"]),
    )


def _map_strategy_config(row: dict[str, Any]) -> BacktestStrategyConfigReadModel:
    return BacktestStrategyConfigReadModel(
        id=int(row["strategy_config_id"]),
        strategy_key=row["strategy_key"],
        strategy_name=row["strategy_name"],
        version=row["strategy_version"],
        parameters=row["strategy_parameters"],
        parameters_hash=row["parameters_hash"],
        metadata=row["strategy_metadata"],
    )


def _map_backtest_summary(row: dict[str, Any]) -> BacktestSummaryReadModel:
    return BacktestSummaryReadModel(
        starting_cash=_as_float(row["result_starting_cash"]),
        ending_cash=_as_float(row["ending_cash"]),
        ending_position=_as_float(row["ending_position"]),
        final_price=_optional_float(row["final_price"]),
        final_equity=_as_float(row["final_equity"]),
        total_return=_as_float(row["total_return"]),
        trade_count=int(row["trade_count"]),
        buy_count=int(row["buy_count"]),
        sell_count=int(row["sell_count"]),
        metadata=row["result_metadata"],
        created_at=_as_utc(row["result_created_at"]),
    )


def _map_backtest_trade(row: dict[str, Any]) -> BacktestTradeReadModel:
    return BacktestTradeReadModel(
        id=int(row["id"]),
        sequence=int(row["sequence"]),
        candle_open_time=_as_utc(row["candle_open_time"]),
        signal=row["signal"],
        price=_as_float(row["price"]),
        quantity=_as_float(row["quantity"]),
        cash_after=_as_float(row["cash_after"]),
        position_after=_as_float(row["position_after"]),
        metadata=row["metadata"],
    )


def _map_backtest_graph_point(row: dict[str, Any]) -> BacktestGraphPointReadModel:
    return BacktestGraphPointReadModel(
        id=int(row["id"]),
        sequence=int(row["sequence"]),
        candle_open_time=_as_utc(row["candle_open_time"]),
        close_price=_as_float(row["close_price"]),
        cash=_as_float(row["cash"]),
        position=_as_float(row["position"]),
        equity=_as_float(row["equity"]),
        trade_id=_optional_int(row["trade_id"]),
        signal=row["signal"],
        metadata=row["metadata"],
    )


def _map_backtest_run_list_item(row: dict[str, Any]) -> BacktestRunListItem:
    return BacktestRunListItem(
        id=int(row["id"]),
        run_key=row["run_key"],
        strategy_config_id=int(row["strategy_config_id"]),
        strategy_key=row["strategy_key"],
        strategy_name=row["strategy_name"],
        strategy_version=row["strategy_version"],
        strategy_parameters=row["strategy_parameters"],
        strategy_parameters_hash=row["strategy_parameters_hash"],
        candle_source=row["candle_source"],
        symbol=row["symbol"],
        interval=row["interval"],
        actual_start_time=_optional_utc(row["actual_start_time"]),
        actual_end_time=_optional_utc(row["actual_end_time"]),
        candle_count=int(row["candle_count"]),
        final_equity=_as_float(row["final_equity"]),
        total_return=_as_float(row["total_return"]),
        trade_count=int(row["trade_count"]),
        metadata=row["metadata"],
        created_at=_as_utc(row["created_at"]),
        completed_at=_optional_utc(row["completed_at"]),
    )


def _optional_int(value: Any | None) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any | None) -> float | None:
    if value is None:
        return None
    return _as_float(value)


def _as_float(value: Any) -> float:
    return float(value)


def _optional_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    normalized = _as_utc(value)
    return normalized.isoformat().replace("+00:00", "Z")
