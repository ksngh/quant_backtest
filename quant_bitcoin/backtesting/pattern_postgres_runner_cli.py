"""Command-line runner for PostgreSQL-backed pattern strategy backtests.

This CLI is intentionally limited to local backtest orchestration: it reads
already persisted standard 1-minute candle data from PostgreSQL, delegates
pattern simulation to the existing pattern strategy backtest workflow, and
prints a deterministic JSON summary. It does not fetch Binance data, place
orders, create trading clients, sign requests, or call exchange account/order
APIs.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.pattern_strategy import (
    DEFAULT_PATTERN,
    SUPPORTED_PATTERNS,
    PatternStrategyBacktestConfig,
    PatternStrategyBacktestResult,
    PatternStrategyBacktestTrade,
    run_pattern_strategy_backtest,
    strategy_name_for_patterns,
    validate_pattern_selection,
)
from quant_bitcoin.market_data import PostgresCandleDataProvider
from quant_bitcoin.runtime_logging import log_runtime_exception
from quant_bitcoin.market_data.postgres_provider import STANDARD_CANDLE_COLUMNS
from quant_bitcoin.persistence import (
    BACKTEST_ENGINE_NAME,
    BACKTEST_ENGINE_VERSION,
    BACKTEST_SCHEMA_VERSION,
    COMPLETED_BACKTEST_STATUS,
    SOURCE_BINANCE_SPOT,
    BacktestGraphPointPayload,
    BacktestPersistencePayload,
    BacktestResultPayload,
    BacktestRunPayload,
    BacktestTradePayload,
    PostgresBacktestResultRepository,
    StrategyConfigPayload,
    build_backtest_run_key,
    canonical_hash,
)

DEFAULT_DATABASE_URL = (
    "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
)
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"

ProviderFactory = Callable[..., Any]
BacktestRunner = Callable[..., PatternStrategyBacktestResult]
RepositoryFactory = Callable[..., Any]


def _main_impl(
    argv: Sequence[str] | None = None,
    *,
    provider_factory: ProviderFactory = PostgresCandleDataProvider.from_database_url,
    backtest_runner: BacktestRunner = run_pattern_strategy_backtest,
    repository_factory: RepositoryFactory = PostgresBacktestResultRepository,
) -> int:
    """Run the PostgreSQL pattern backtest CLI and return a process exit code."""

    args = build_parser().parse_args(argv)
    selected_patterns = _selected_patterns(args.patterns)
    provider = provider_factory(
        args.database_url,
        source=args.source,
        symbol=args.symbol,
        interval=args.interval,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    candles = provider.load()
    config = PatternStrategyBacktestConfig(
        patterns=selected_patterns,
        symbol=args.symbol,
        timeframe=args.interval,
    )
    result = backtest_runner(candles, config=config)

    persisted_run_id = None
    if args.persist_results:
        repository = repository_factory(args.database_url)
        payload = build_persistence_payload(
            result,
            candles=candles,
            source=args.source,
            symbol=args.symbol,
            interval=args.interval,
            start_time=args.start_time,
            end_time=args.end_time,
            patterns=config.patterns,
            starting_cash=args.starting_cash,
            trade_quantity=args.trade_quantity,
        )
        persisted_run_id = repository.save_completed_backtest(payload)

    _print_json(
        build_output(
            result,
            candle_count=len(candles),
            source=args.source,
            symbol=args.symbol,
            interval=args.interval,
            start_time=args.start_time,
            end_time=args.end_time,
            patterns=config.patterns,
            backtest_run_id=persisted_run_id,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="quant-bitcoin-pattern-backtest",
        description=(
            "Run the default Fair Value Gap pattern strategy backtest from "
            "completed 1-minute candles already stored in PostgreSQL. "
            "FAIR_VALUE_GAP remains the default; explicit single-pattern "
            "selection is supported for implemented detector/planner pairs."
        ),
        epilog=(
            "Pattern selection: the default is FAIR_VALUE_GAP. Supported "
            f"single-pattern choices: {', '.join(SUPPORTED_PATTERNS)}. "
            "Multiple --pattern values and unsupported pattern selections fail "
            "before any provider or backtest runs."
        ),
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="PostgreSQL connection URL containing previously stored candles",
    )
    parser.add_argument(
        "--source",
        default=os.environ.get("CANDLE_SOURCE", SOURCE_BINANCE_SPOT),
        help="stored candle source to read",
    )
    parser.add_argument(
        "--symbol",
        default=os.environ.get("SYMBOL", DEFAULT_SYMBOL),
        help="stored candle symbol to read",
    )
    parser.add_argument(
        "--interval",
        type=_one_minute_interval,
        default=os.environ.get("INTERVAL", DEFAULT_INTERVAL),
        help="stored candle interval to read; only 1m is supported by this task",
    )
    parser.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        type=_pattern_name,
        default=None,
        metavar="PATTERN",
        help=(
            "single pattern strategy to backtest; default is FAIR_VALUE_GAP "
            f"(supported choices: {', '.join(SUPPORTED_PATTERNS)})"
        ),
    )
    parser.add_argument(
        "--start-time",
        type=_optional_timestamp,
        default=_env_optional_timestamp("BACKTEST_START_TIME"),
        help="optional UTC ISO-8601 datetime for the first candle open time",
    )
    parser.add_argument(
        "--end-time",
        type=_optional_timestamp,
        default=_env_optional_timestamp("BACKTEST_END_TIME"),
        help="optional UTC ISO-8601 datetime for the last candle open time",
    )
    parser.add_argument(
        "--starting-cash",
        type=float,
        default=10000.0,
        help="starting cash for the simulated pattern backtest",
    )
    parser.add_argument(
        "--trade-quantity",
        type=float,
        default=1.0,
        help="fixed trade quantity used to map pattern trades into cash/equity summaries",
    )
    parser.add_argument(
        "--no-persist",
        action="store_false",
        dest="persist_results",
        help="print the backtest JSON without saving simulated results to PostgreSQL",
    )
    parser.set_defaults(persist_results=True)
    return parser


def build_output(
    result: PatternStrategyBacktestResult,
    *,
    candle_count: int,
    source: str,
    symbol: str,
    interval: str,
    start_time: datetime | None,
    end_time: datetime | None,
    patterns: Sequence[str] = (DEFAULT_PATTERN,),
    backtest_run_id: int | None = None,
) -> dict[str, Any]:
    """Return a deterministic JSON-serializable pattern backtest output object."""

    output = {
        "candle_count": candle_count,
        "input": {
            "source": source,
            "symbol": symbol,
            "interval": interval,
            "start_time": _serialize_optional_datetime(start_time),
            "end_time": _serialize_optional_datetime(end_time),
        },
        "strategy": {
            "name": strategy_name_for_patterns(patterns),
            "patterns": list(validate_pattern_selection(patterns)),
            "entry_rule": "pattern_confirmation_candle",
            "exit_evaluation": "starts_on_candle_after_entry",
        },
        "summary": {
            "evaluated_candle_count": result.evaluated_candle_count,
            "seen_event_count": len(result.seen_event_ids),
            "trade_count": result.trade_count,
        },
        "seen_event_ids": list(result.seen_event_ids),
        "trades": [_serialize_trade(trade) for trade in result.trades],
    }
    if backtest_run_id is not None:
        output["backtest_run_id"] = backtest_run_id
    return output



def build_persistence_payload(
    result: PatternStrategyBacktestResult,
    *,
    candles: pd.DataFrame,
    source: str,
    symbol: str,
    interval: str,
    start_time: datetime | None,
    end_time: datetime | None,
    patterns: Sequence[str],
    starting_cash: float,
    trade_quantity: float,
) -> BacktestPersistencePayload:
    normalized = candles.loc[:, ["timestamp", "close"]].copy() if not candles.empty else candles.copy()
    if not normalized.empty:
        normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="raise")
        normalized["close"] = pd.to_numeric(normalized["close"], errors="raise")
        normalized = normalized.sort_values("timestamp", kind="mergesort").reset_index(drop=True)

    actual_start_time = _to_datetime(normalized.iloc[0]["timestamp"]) if not normalized.empty else None
    actual_end_time = _to_datetime(normalized.iloc[-1]["timestamp"]) if not normalized.empty else None
    validated_patterns = validate_pattern_selection(patterns)
    strategy_name = strategy_name_for_patterns(validated_patterns)
    strategy_parameters = {"patterns": list(validated_patterns)}
    strategy_config = StrategyConfigPayload(
        strategy_key="pattern",
        strategy_name=strategy_name,
        version="pattern_strategy_v1",
        parameters=strategy_parameters,
        parameters_hash=canonical_hash(strategy_parameters),
    )
    identity = {
        "schema_version": BACKTEST_SCHEMA_VERSION,
        "engine_name": BACKTEST_ENGINE_NAME,
        "engine_version": BACKTEST_ENGINE_VERSION,
        "strategy_name": strategy_name,
        "strategy_version": strategy_config.version,
        "strategy_parameters": strategy_parameters,
        "candle_source": source,
        "symbol": symbol,
        "interval": interval,
        "requested_start_time": start_time,
        "requested_end_time": end_time,
        "actual_start_time": actual_start_time,
        "actual_end_time": actual_end_time,
        "candle_count": len(normalized),
    }
    run_key = build_backtest_run_key(identity)
    cash = float(starting_cash)
    position = 0.0
    trades_payload: list[BacktestTradePayload] = []
    for index, trade in enumerate(result.trades, start=1):
        entry_time = _to_datetime(trade.entry_timestamp)
        quantity = float(trade_quantity) * float(trade.remaining_quantity_ratio)
        if quantity > 0:
            cash -= float(trade.entry_price) * quantity
            position += quantity
        if trade.exit_timestamp is not None and trade.exit_price is not None and quantity > 0:
            cash += float(trade.exit_price) * quantity
            position -= quantity
        trades_payload.append(
            BacktestTradePayload(
                sequence=index,
                candle_open_time=entry_time,
                signal="ENTRY",
                price=float(trade.entry_price),
                quantity=quantity,
                cash_after=cash,
                position_after=position,
                metadata={
                    "event_id": trade.event_id,
                    "pattern_type": trade.pattern_type,
                    "pattern_direction": trade.pattern_direction,
                    "exit_reason": _enum_value(trade.exit_reason),
                    "exit_timestamp": _serialize_optional_timestamp_like(trade.exit_timestamp),
                    "exit_price": trade.exit_price,
                    "realized_pnl_per_unit": trade.realized_pnl_per_unit,
                    "realized_r_multiple": trade.realized_r_multiple,
                },
            )
        )

    final_price = float(normalized.iloc[-1]["close"]) if not normalized.empty else None
    final_equity = cash + (position * final_price if final_price is not None else 0.0)

    graph_points = tuple(
        BacktestGraphPointPayload(
            sequence=index,
            candle_open_time=_to_datetime(row.timestamp),
            close_price=float(row.close),
            cash=cash,
            position=position,
            equity=cash + (position * float(row.close)),
        )
        for index, row in enumerate(normalized.itertuples(index=False), start=1)
    )
    trades = tuple(trades_payload)
    return BacktestPersistencePayload(
        strategy_config=strategy_config,
        run=BacktestRunPayload(
            run_key=run_key,
            engine_name=BACKTEST_ENGINE_NAME,
            engine_version=BACKTEST_ENGINE_VERSION,
            candle_source=source,
            symbol=symbol,
            interval=interval,
            requested_start_time=start_time,
            requested_end_time=end_time,
            actual_start_time=actual_start_time,
            actual_end_time=actual_end_time,
            candle_count=len(normalized),
            starting_cash=float(starting_cash),
            trade_quantity=float(trade_quantity),
            status=COMPLETED_BACKTEST_STATUS,
            metadata={"schema_version": BACKTEST_SCHEMA_VERSION, "mode": "pattern"},
        ),
        result=BacktestResultPayload(
            starting_cash=float(starting_cash),
            ending_cash=float(cash),
            ending_position=0.0,
            final_price=final_price,
            final_equity=float(final_equity),
            total_return=((float(final_equity)-float(starting_cash))/float(starting_cash)) if float(starting_cash) != 0 else 0.0,
            trade_count=result.trade_count,
            buy_count=0,
            sell_count=0,
            metadata={"seen_event_count": len(result.seen_event_ids)},
        ),
        trades=trades,
        graph_points=graph_points,
    )

def _serialize_trade(trade: PatternStrategyBacktestTrade) -> dict[str, Any]:
    return {
        "event_id": trade.event_id,
        "pattern_type": trade.pattern_type,
        "pattern_direction": trade.pattern_direction,
        "pattern_status": trade.pattern_status,
        "pattern_timestamp": _serialize_timestamp_like(trade.pattern_timestamp),
        "entry_timestamp": _serialize_timestamp_like(trade.entry_timestamp),
        "entry_candle_index": trade.entry_candle_index,
        "entry_price": trade.entry_price,
        "exit_reason": _enum_value(trade.exit_reason),
        "exit_timestamp": _serialize_optional_timestamp_like(trade.exit_timestamp),
        "exit_candle_index": trade.exit_candle_index,
        "exit_price": trade.exit_price,
        "realized_pnl_per_unit": trade.realized_pnl_per_unit,
        "realized_r_multiple": trade.realized_r_multiple,
        "remaining_quantity_ratio": trade.remaining_quantity_ratio,
        "risk_plan": {
            "direction": _enum_value(trade.risk_plan.direction),
            "entry_price": trade.risk_plan.entry_price,
            "stop_price": trade.risk_plan.stop_price,
            "risk_per_unit": trade.risk_plan.risk_per_unit,
            "status": _enum_value(trade.risk_plan.status),
            "target_count": len(trade.risk_plan.targets),
        },
        "metadata": dict(trade.metadata),
    }


def _selected_patterns(values: Sequence[str] | None) -> tuple[str, ...]:
    return validate_pattern_selection(values or (DEFAULT_PATTERN,))


def _pattern_name(value: str) -> str:
    try:
        return validate_pattern_selection((value,))[0]
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def _one_minute_interval(value: str) -> str:
    if value != DEFAULT_INTERVAL:
        raise argparse.ArgumentTypeError(
            "only completed 1m candles are supported by this task"
        )
    return value


def _optional_timestamp(value: str) -> datetime | None:
    if value == "":
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "timestamp must be an ISO-8601 datetime"
        ) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _env_optional_timestamp(name: str) -> datetime | None:
    value = os.environ.get(name)
    if value is None:
        return None
    return _optional_timestamp(value)


def _serialize_optional_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _serialize_datetime(value)


def _serialize_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_optional_timestamp_like(value: Any | None) -> str | None:
    if value is None:
        return None
    return _serialize_timestamp_like(value)


def _serialize_timestamp_like(value: Any) -> str:
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return _serialize_datetime(value)
    return str(value)


def _enum_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return value


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


# Keep the standard schema visible to contract tests without redefining it.
__all__ = [
    "STANDARD_CANDLE_COLUMNS",
    "build_output",
    "build_parser",
    "main",
]


def main(argv=None, **kwargs):
    try:
        return _main_impl(argv, **kwargs)
    except (SystemExit, ValueError):
        raise
    except Exception:
        log_runtime_exception(__name__)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
