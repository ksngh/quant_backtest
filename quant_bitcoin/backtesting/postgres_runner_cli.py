"""Deprecated command-line runner for PostgreSQL-backed RSI backtests.

Deprecated: use ``quant_bitcoin.backtesting.strategy_postgres_runner_cli``
(``quant-bitcoin-strategy-backtest`` entrypoint).

This CLI is intentionally limited to local backtest wiring: it reads already
persisted standard candle data from PostgreSQL, runs the existing RSI strategy
through the existing basic backtester, and prints a deterministic JSON summary.
It does not fetch Binance data, place orders, sign requests, or call exchange
account APIs.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable, Sequence
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.basic import BacktestResult
from quant_bitcoin.backtesting.strategy_models import (
    StrategyBacktestResult,
    StrategyBacktestSummary,
)
from quant_bitcoin.market_data import PostgresCandleDataProvider
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
    build_backtest_run_key,
    build_rsi_strategy_config_payload,
)
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig, run_strategy_backtest_engine
from quant_bitcoin.backtesting.strategy_persistence_adapter import build_strategy_engine_persistence_payload
from quant_bitcoin.strategies import RsiActionStrategy
from quant_bitcoin.runtime_logging import log_runtime_exception

DEFAULT_DATABASE_URL = (
    "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
)
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"
DEFAULT_STARTING_CASH = 10_000.0
DEFAULT_TRADE_QUANTITY = 0.01
DEFAULT_RSI_WINDOW = 14
DEFAULT_RSI_BUY_THRESHOLD = 30.0
DEFAULT_RSI_SELL_THRESHOLD = 70.0

ProviderFactory = Callable[..., Any]
StrategyFactory = Callable[..., Any]
BacktesterFactory = Callable[..., Any]
RepositoryFactory = Callable[..., Any]


def _main_impl(
    argv: Sequence[str] | None = None,
    *,
    provider_factory: ProviderFactory = PostgresCandleDataProvider.from_database_url,
    strategy_factory: StrategyFactory = RsiActionStrategy,
    backtester_factory: BacktesterFactory = run_strategy_backtest_engine,
    repository_factory: RepositoryFactory = PostgresBacktestResultRepository,
) -> int:
    """Run the PostgreSQL RSI backtest CLI and return a process exit code."""

    args = build_parser().parse_args(argv)
    provider = provider_factory(
        args.database_url,
        source=args.source,
        symbol=args.symbol,
        interval=args.interval,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    candles = provider.load()

    strategy = strategy_factory(
        window=args.rsi_window,
        buy_threshold=args.rsi_buy_threshold,
        sell_threshold=args.rsi_sell_threshold,
    )
    if candles.empty:
        result = StrategyBacktestResult(
            executions=(),
            equity_points=(),
            summary=StrategyBacktestSummary(
                starting_cash=float(args.starting_cash),
                ending_cash=float(args.starting_cash),
                ending_position=0.0,
                final_price=None,
                final_equity=float(args.starting_cash),
                total_return=0.0,
                trade_count=0,
                buy_count=0,
                sell_count=0,
                win_count=0,
                loss_count=0,
                max_drawdown=0.0,
                gross_pnl=0.0,
                net_pnl=0.0,
                average_net_r=None,
                metadata={},
            ),
        )
    else:
        actions = []
        position = 0.0
        for idx in range(len(candles)):
            window = candles.iloc[: idx + 1]
            emitted = strategy.evaluate(window, portfolio_state={"position": position})
            for action in emitted:
                actions.append(action)
                if action.action_type.value == "ENTER_LONG":
                    position = 1.0
                elif action.action_type.value == "EXIT_LONG":
                    position = 0.0

        result = backtester_factory(
            candles,
            actions,
            config=StrategyEngineConfig(
                starting_cash=args.starting_cash,
                trade_quantity=args.trade_quantity,
                allow_short=False,
            ),
        )

    persisted_run_id = None
    if args.persist_results:
        repository = repository_factory(args.database_url)
        payload = build_strategy_engine_persistence_payload(
            result, candles, source=args.source, symbol=args.symbol, interval=args.interval,
            start_time=args.start_time, end_time=args.end_time,
            strategy_key="rsi", strategy_name="RsiStrategy", strategy_version="rsi_strategy_v1",
            strategy_parameters={"window": args.rsi_window, "buy_threshold": float(args.rsi_buy_threshold), "sell_threshold": float(args.rsi_sell_threshold)},
            starting_cash=args.starting_cash, trade_quantity=args.trade_quantity,
            engine_name=BACKTEST_ENGINE_NAME, engine_version=BACKTEST_ENGINE_VERSION,
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
            rsi_window=args.rsi_window,
            rsi_buy_threshold=args.rsi_buy_threshold,
            rsi_sell_threshold=args.rsi_sell_threshold,
            backtest_run_id=persisted_run_id,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="quant-bitcoin-postgres-backtest",
        description="Run an RSI backtest from candles already stored in PostgreSQL.",
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
        default=os.environ.get("INTERVAL", DEFAULT_INTERVAL),
        help="stored candle interval to read",
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
        type=_non_negative_float,
        default=_env_non_negative_float(
            "BACKTEST_STARTING_CASH", DEFAULT_STARTING_CASH
        ),
        help="starting cash for the simulated backtest",
    )
    parser.add_argument(
        "--trade-quantity",
        type=_positive_float,
        default=_env_positive_float("BACKTEST_TRADE_QUANTITY", DEFAULT_TRADE_QUANTITY),
        help="fixed simulated quantity per backtest trade",
    )
    parser.add_argument(
        "--rsi-window",
        type=_positive_int,
        default=_env_positive_int("BACKTEST_RSI_WINDOW", DEFAULT_RSI_WINDOW),
        help="RSI rolling window",
    )
    parser.add_argument(
        "--rsi-buy-threshold",
        type=_threshold_float,
        default=_env_threshold_float(
            "BACKTEST_RSI_BUY_THRESHOLD", DEFAULT_RSI_BUY_THRESHOLD
        ),
        help="RSI value at or below which the strategy returns BUY",
    )
    parser.add_argument(
        "--rsi-sell-threshold",
        type=_threshold_float,
        default=_env_threshold_float(
            "BACKTEST_RSI_SELL_THRESHOLD", DEFAULT_RSI_SELL_THRESHOLD
        ),
        help="RSI value at or above which the strategy returns SELL",
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
    result,
    *,
    candle_count: int,
    source: str,
    symbol: str,
    interval: str,
    start_time: datetime | None,
    end_time: datetime | None,
    rsi_window: int,
    rsi_buy_threshold: float,
    rsi_sell_threshold: float,
    backtest_run_id: int | None = None,
) -> dict[str, Any]:
    """Return a deterministic JSON-serializable backtest output object."""

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
            "name": "RSI",
            "window": rsi_window,
            "buy_threshold": rsi_buy_threshold,
            "sell_threshold": rsi_sell_threshold,
        },
        "summary": _strategy_summary_to_legacy(result),
        "trades": [
            {
                "timestamp": _serialize_datetime(_to_datetime(trade.timestamp)),
                "signal": _trade_signal(trade),
                "price": trade.price,
                "quantity": trade.quantity,
                "cash_after": trade.cash_after,
                "position_after": trade.position_after,
            }
            for trade in _result_trades(result)
        ],
    }
    if backtest_run_id is not None:
        output["backtest_run_id"] = backtest_run_id
    return output


def build_persistence_payload(
    result,
    *,
    candles: pd.DataFrame,
    source: str,
    symbol: str,
    interval: str,
    start_time: datetime | None,
    end_time: datetime | None,
    starting_cash: float,
    trade_quantity: float,
    rsi_window: int,
    rsi_buy_threshold: float,
    rsi_sell_threshold: float,
) -> BacktestPersistencePayload:
    """Build the graph-ready persistence payload for one completed run."""

    normalized_candles = _normalize_candles_for_persistence(candles)
    actual_start_time = (
        _to_datetime(normalized_candles.iloc[0]["timestamp"])
        if not normalized_candles.empty
        else None
    )
    actual_end_time = (
        _to_datetime(normalized_candles.iloc[-1]["timestamp"])
        if not normalized_candles.empty
        else None
    )
    strategy_config = build_rsi_strategy_config_payload(
        window=rsi_window,
        buy_threshold=rsi_buy_threshold,
        sell_threshold=rsi_sell_threshold,
    )
    identity = {
        "schema_version": BACKTEST_SCHEMA_VERSION,
        "engine_name": BACKTEST_ENGINE_NAME,
        "engine_version": BACKTEST_ENGINE_VERSION,
        "strategy_name": strategy_config.strategy_name,
        "strategy_version": strategy_config.version,
        "strategy_parameters": strategy_config.parameters,
        "candle_source": source,
        "symbol": symbol,
        "interval": interval,
        "requested_start_time": start_time,
        "requested_end_time": end_time,
        "actual_start_time": actual_start_time,
        "actual_end_time": actual_end_time,
        "candle_count": len(normalized_candles),
        "starting_cash": float(starting_cash),
        "trade_quantity": float(trade_quantity),
    }
    run_key = build_backtest_run_key(identity)
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
            candle_count=len(normalized_candles),
            starting_cash=float(starting_cash),
            trade_quantity=float(trade_quantity),
            status=COMPLETED_BACKTEST_STATUS,
            metadata={"schema_version": BACKTEST_SCHEMA_VERSION},
        ),
        result=BacktestResultPayload(**_strategy_summary_to_legacy(result)),
        trades=_build_trade_payloads(result),
        graph_points=_build_graph_point_payloads(
            normalized_candles, result, starting_cash=float(starting_cash)
        ),
    )


def _build_trade_payloads(result) -> tuple[BacktestTradePayload, ...]:
    return tuple(
        BacktestTradePayload(
            sequence=index,
            candle_open_time=_to_datetime(trade.timestamp),
            signal=_trade_signal(trade),
            price=float(trade.price),
            quantity=float(trade.quantity),
            cash_after=float(trade.cash_after),
            position_after=float(trade.position_after),
        )
        for index, trade in enumerate(_result_trades(result), start=1)
    )


def _build_graph_point_payloads(
    candles: pd.DataFrame, result, *, starting_cash: float
) -> tuple[BacktestGraphPointPayload, ...]:
    trades_by_timestamp = {
        _to_datetime(trade.timestamp): (index, trade)
        for index, trade in enumerate(_result_trades(result), start=1)
    }
    cash = float(starting_cash)
    position = 0.0
    points: list[BacktestGraphPointPayload] = []
    for sequence, row in enumerate(candles.itertuples(index=False), start=1):
        candle_open_time = _to_datetime(row.timestamp)
        close_price = float(row.close)
        trade_entry = trades_by_timestamp.get(candle_open_time)
        trade_sequence = None
        signal = None
        if trade_entry is not None:
            trade_sequence, trade = trade_entry
            cash = float(trade.cash_after)
            position = float(trade.position_after)
            signal = _trade_signal(trade)
        points.append(
            BacktestGraphPointPayload(
                sequence=sequence,
                candle_open_time=candle_open_time,
                close_price=close_price,
                cash=cash,
                position=position,
                equity=cash + position * close_price,
                trade_sequence=trade_sequence,
                signal=signal,
            )
        )
    return tuple(points)


def _normalize_candles_for_persistence(candles: pd.DataFrame) -> pd.DataFrame:
    if candles.empty:
        return candles.copy()
    normalized = candles.loc[:, ["timestamp", "close"]].copy()
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="raise")
    normalized["close"] = pd.to_numeric(normalized["close"], errors="raise")
    return normalized.sort_values("timestamp", kind="mergesort").reset_index(drop=True)


def _strategy_summary_to_legacy(result) -> dict[str, Any]:
    summary = asdict(result.summary)
    legacy = {
        "starting_cash": summary["starting_cash"],
        "ending_cash": summary["ending_cash"],
        "ending_position": summary["ending_position"],
        "final_price": summary["final_price"],
        "final_equity": summary["final_equity"],
        "total_return": summary["total_return"],
        "trade_count": summary["trade_count"],
        "buy_count": summary["buy_count"],
        "sell_count": summary["sell_count"],
    }
    metadata = summary.get("metadata")
    if metadata:
        legacy["metadata"] = metadata
    return legacy


def _result_trades(result) -> tuple[Any, ...]:
    return tuple(getattr(result, "executions", getattr(result, "trades", ())))


def _trade_signal(trade: Any) -> str:
    side = getattr(trade, "side", None)
    if side is not None:
        return str(side)
    signal = getattr(trade, "signal")
    return signal.value if hasattr(signal, "value") else str(signal)

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


def _positive_int(value: str) -> int:
    integer = int(value)
    if integer < 1:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return integer


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def _non_negative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return number


def _threshold_float(value: str) -> float:
    number = float(value)
    if not 0 <= number <= 100:
        raise argparse.ArgumentTypeError("RSI threshold must be between 0 and 100")
    return number


def _env_optional_timestamp(name: str) -> datetime | None:
    value = os.environ.get(name)
    if value is None:
        return None
    return _optional_timestamp(value)


def _env_positive_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    return _positive_int(value)


def _env_positive_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return _positive_float(value)


def _env_non_negative_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return _non_negative_float(value)


def _env_threshold_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    return _threshold_float(value)


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


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


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
