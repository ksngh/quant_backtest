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
from quant_bitcoin.market_data.postgres_provider import STANDARD_CANDLE_COLUMNS
from quant_bitcoin.persistence import SOURCE_BINANCE_SPOT

DEFAULT_DATABASE_URL = (
    "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
)
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"

ProviderFactory = Callable[..., Any]
BacktestRunner = Callable[..., PatternStrategyBacktestResult]


def main(
    argv: Sequence[str] | None = None,
    *,
    provider_factory: ProviderFactory = PostgresCandleDataProvider.from_database_url,
    backtest_runner: BacktestRunner = run_pattern_strategy_backtest,
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
) -> dict[str, Any]:
    """Return a deterministic JSON-serializable pattern backtest output object."""

    return {
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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
