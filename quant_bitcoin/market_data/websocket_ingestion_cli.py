"""Command-line helpers for market-data-only WebSocket ingestion.

The CLI is intended for local operations and Docker Compose wiring. It supports
configuration readiness checks without external I/O, unbounded long-running
public market WebSocket ingestion into PostgreSQL, and explicit bounded smoke
checks. It does not place orders, call account APIs, or run strategy/execution
logic.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections.abc import Callable, Sequence
from dataclasses import asdict
from typing import Any

from quant_bitcoin.market_data.binance_websocket import (
    DEFAULT_RECONNECT_DELAY_SECONDS,
    DEFAULT_WEBSOCKET_BASE_URL,
    BinanceWebSocketCandleIngestor,
    WebSocketIngestionResult,
    WebSocketReadinessReport,
    check_websocket_ingestion_readiness,
)
from quant_bitcoin.persistence import PostgresCandleRepository
from quant_bitcoin.runtime_logging import log_runtime_exception

DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"
UNBOUNDED_MAX_MESSAGE_VALUES = {"", "0", "none", "null", "unbounded"}
DEFAULT_DATABASE_URL = (
    "postgresql://quant_bitcoin:quant_bitcoin_dev@postgres:5432/quant_bitcoin"
)

ReadinessChecker = Callable[..., WebSocketReadinessReport]
RepositoryFactory = Callable[[str], Any]
IngestorFactory = Callable[..., Any]


def _main_impl(
    argv: Sequence[str] | None = None,
    *,
    readiness_checker: ReadinessChecker = check_websocket_ingestion_readiness,
    repository_factory: RepositoryFactory = PostgresCandleRepository,
    ingestor_factory: IngestorFactory = BinanceWebSocketCandleIngestor,
) -> int:
    """Run the WebSocket ingestion CLI and return a process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "readiness":
        return _run_readiness(args, readiness_checker=readiness_checker)
    if args.command == "ingest":
        return asyncio.run(
            _run_ingestion(
                args,
                repository_factory=repository_factory,
                ingestor_factory=ingestor_factory,
            )
        )
    parser.error("a command is required")
    return 2


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="quant-bitcoin-websocket-ingestion",
        description="Market-data-only Binance WebSocket ingestion utilities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    readiness = subparsers.add_parser(
        "readiness",
        help="validate ingestion configuration without network or database access",
    )
    _add_common_ingestion_options(readiness)

    ingest = subparsers.add_parser(
        "ingest",
        help="run public WebSocket candle ingestion into PostgreSQL",
    )
    _add_common_ingestion_options(ingest)
    ingest.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="PostgreSQL connection URL for candle persistence",
    )
    max_messages = ingest.add_mutually_exclusive_group()
    max_messages.add_argument(
        "--max-messages",
        type=_positive_int,
        default=_env_optional_positive_int("INGEST_MAX_MESSAGES"),
        help=(
            "maximum WebSocket messages to process before exiting; use this for "
            "bounded smoke checks"
        ),
    )
    max_messages.add_argument(
        "--no-max-messages",
        action="store_const",
        const=None,
        dest="max_messages",
        help=(
            "run without a message limit; overrides INGEST_MAX_MESSAGES for "
            "long-running ingestion"
        ),
    )
    ingest.add_argument(
        "--initialize-schema",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="initialize the local PostgreSQL schema before ingestion",
    )
    return parser


def _add_common_ingestion_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--symbol",
        default=os.environ.get("SYMBOL", DEFAULT_SYMBOL),
        help="Binance spot symbol to ingest",
    )
    parser.add_argument(
        "--interval",
        default=os.environ.get("INTERVAL", DEFAULT_INTERVAL),
        help="Binance kline interval to ingest",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BINANCE_WEBSOCKET_BASE_URL", DEFAULT_WEBSOCKET_BASE_URL),
        help="Binance public WebSocket base URL",
    )
    parser.add_argument(
        "--reconnect-delay-seconds",
        type=float,
        default=_env_float(
            "RECONNECT_DELAY_SECONDS", DEFAULT_RECONNECT_DELAY_SECONDS
        ),
        help="seconds to wait before reconnect attempts",
    )
    parser.add_argument(
        "--max-reconnects",
        type=_non_negative_int,
        default=_env_non_negative_int("MAX_RECONNECTS", 3),
        help="maximum reconnect attempts before failing",
    )


def _run_readiness(
    args: argparse.Namespace,
    *,
    readiness_checker: ReadinessChecker,
) -> int:
    report = readiness_checker(
        symbol=args.symbol,
        interval=args.interval,
        base_url=args.base_url,
        reconnect_delay_seconds=args.reconnect_delay_seconds,
        max_reconnects=args.max_reconnects,
    )
    _print_json(_readiness_report_to_dict(report))
    return 0 if report.ready else 1


async def _run_ingestion(
    args: argparse.Namespace,
    *,
    repository_factory: RepositoryFactory,
    ingestor_factory: IngestorFactory,
) -> int:
    repository = repository_factory(args.database_url)
    if args.initialize_schema:
        repository.initialize_schema()

    ingestor = ingestor_factory(
        repository,
        base_url=args.base_url,
        reconnect_delay_seconds=args.reconnect_delay_seconds,
        max_reconnects=args.max_reconnects,
    )
    result = await ingestor.run(
        symbol=args.symbol,
        interval=args.interval,
        max_messages=args.max_messages,
    )
    _print_json(asdict(result))
    return 0


def _readiness_report_to_dict(report: WebSocketReadinessReport) -> dict[str, object]:
    return {
        "ready": report.ready,
        "symbol": report.symbol,
        "interval": report.interval,
        "stream_url": report.stream_url,
        "checks": [asdict(check) for check in report.checks],
    }


def _print_json(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True, default=str))


def _env_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return float(raw_value)


def _env_optional_positive_int(name: str) -> int | None:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return None
    normalized = raw_value.strip().lower()
    if normalized in UNBOUNDED_MAX_MESSAGE_VALUES:
        return None
    return _positive_int(raw_value)


def _env_non_negative_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return _non_negative_int(raw_value)


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
