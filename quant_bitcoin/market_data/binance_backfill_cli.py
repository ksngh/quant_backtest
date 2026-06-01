"""Command-line runner for PostgreSQL-backed Binance candle backfill.

This CLI wires the market-data-only historical backfiller to PostgreSQL for local
operations. It uses Binance public spot kline endpoints only and never accepts API
keys, signs requests, places orders, or calls exchange order endpoints.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable, Sequence
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from quant_bitcoin.market_data.binance_backfill import (
    BINANCE_MAX_KLINE_LIMIT,
    BinanceHistoricalBackfiller,
    MultiIntervalBinanceBackfillRunner,
    parse_interval_list,
)
from quant_bitcoin.market_data.binance_downloader import (
    DEFAULT_MARKET_DATA_BASE_URL,
    SUPPORTED_KLINE_INTERVALS,
)
from quant_bitcoin.persistence import PostgresCandleRepository
from quant_bitcoin.runtime_logging import log_runtime_exception

DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"
DEFAULT_DATABASE_URL = (
    "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
)
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 3
SUPPORTED_INTERVALS_HELP = ", ".join(SUPPORTED_KLINE_INTERVALS)

RepositoryFactory = Callable[[str], Any]
BackfillerFactory = Callable[..., Any]


def _main_impl(
    argv: Sequence[str] | None = None,
    *,
    repository_factory: RepositoryFactory = PostgresCandleRepository,
    backfiller_factory: BackfillerFactory = BinanceHistoricalBackfiller,
) -> int:
    """Run the Binance historical backfill CLI and return a process exit code."""

    args = build_parser().parse_args(argv)
    intervals = parse_interval_list(args.intervals) if args.intervals else None
    repository = repository_factory(args.database_url)
    if args.initialize_schema:
        repository.initialize_schema()

    backfiller = backfiller_factory(
        repository,
        base_url=args.base_url,
        timeout=args.timeout_seconds,
        max_retries=args.max_retries,
    )
    if intervals is None:
        result = backfiller.run(
            symbol=args.symbol,
            interval=args.interval,
            start_time=args.start_time,
            end_time=args.end_time,
            limit=args.limit,
        )
    else:
        result = MultiIntervalBinanceBackfillRunner(backfiller).run(
            symbol=args.symbol,
            intervals=intervals,
            start_time=args.start_time,
            end_time=args.end_time,
            limit=args.limit,
        )
    _print_json(asdict(result))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="quant-bitcoin-binance-backfill",
        description="Backfill Binance public spot candles into PostgreSQL.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="PostgreSQL connection URL for candle persistence",
    )
    parser.add_argument(
        "--symbol",
        default=os.environ.get("SYMBOL", DEFAULT_SYMBOL),
        help="Binance spot symbol to backfill",
    )
    parser.add_argument(
        "--interval",
        default=os.environ.get("INTERVAL", DEFAULT_INTERVAL),
        help=(
            "Binance kline interval to backfill. "
            f"Supported: {SUPPORTED_INTERVALS_HELP}"
        ),
    )
    parser.add_argument(
        "--intervals",
        default=os.environ.get("INTERVALS"),
        help=(
            "comma-separated Binance kline intervals to backfill in order. "
            f"Supported: {SUPPORTED_INTERVALS_HELP}"
        ),
    )
    parser.add_argument(
        "--start-time",
        type=_optional_timestamp,
        default=_env_optional_timestamp("BACKFILL_START_TIME"),
        help="optional UTC ISO-8601 datetime or millisecond timestamp to start from",
    )
    parser.add_argument(
        "--end-time",
        type=_optional_timestamp,
        default=_env_optional_timestamp("BACKFILL_END_TIME"),
        help="optional UTC ISO-8601 datetime or millisecond timestamp to stop at",
    )
    parser.add_argument(
        "--limit",
        type=_positive_int,
        default=_env_positive_int("BACKFILL_LIMIT", BINANCE_MAX_KLINE_LIMIT),
        help="maximum Binance klines to request per page",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BINANCE_MARKET_DATA_BASE_URL", DEFAULT_MARKET_DATA_BASE_URL),
        help="Binance public market-data REST base URL",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=_positive_float,
        default=_env_positive_float("BACKFILL_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
        help="HTTP timeout in seconds for public market-data requests",
    )
    parser.add_argument(
        "--max-retries",
        type=_non_negative_int,
        default=_env_non_negative_int("BACKFILL_MAX_RETRIES", DEFAULT_MAX_RETRIES),
        help="maximum retries for retryable public market-data responses",
    )
    parser.add_argument(
        "--initialize-schema",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="initialize the local PostgreSQL schema before backfill",
    )
    return parser


def _optional_timestamp(value: str) -> datetime | int | None:
    if value == "":
        return None
    if value.isdecimal():
        timestamp_ms = int(value)
        if timestamp_ms < 0:
            raise argparse.ArgumentTypeError("timestamp must be non-negative")
        return timestamp_ms
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "timestamp must be a millisecond integer or ISO-8601 datetime"
        ) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _positive_int(value: str) -> int:
    integer = int(value)
    if integer < 1:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return integer


def _non_negative_int(value: str) -> int:
    integer = int(value)
    if integer < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative integer")
    return integer


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def _env_optional_timestamp(name: str) -> datetime | int | None:
    value = os.environ.get(name)
    if value is None:
        return None
    return _optional_timestamp(value)


def _env_positive_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    return _positive_int(value)


def _env_non_negative_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    return _non_negative_int(value)


def _env_positive_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return _positive_float(value)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, default=_json_default, sort_keys=True))


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def main(argv=None, **kwargs):
    try:
        return _main_impl(argv, **kwargs)
    except (SystemExit, ValueError):
        raise
    except Exception:
        log_runtime_exception(__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
