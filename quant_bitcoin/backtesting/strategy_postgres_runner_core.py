from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from datetime import datetime, timezone

import pandas as pd

from quant_bitcoin.backtesting.pattern_action_builder import build_pattern_trade_actions
from quant_bitcoin.backtesting.pattern_detection_cache import (
    IndicatorCache,
    PatternEvaluationContext,
)
from quant_bitcoin.backtesting.strategy_engine import (
    StrategyEngineConfig,
    run_strategy_backtest_engine,
)
from quant_bitcoin.backtesting.strategy_persistence_adapter import (
    build_strategy_engine_persistence_payload,
)
from quant_bitcoin.market_data import PostgresCandleDataProvider
from quant_bitcoin.persistence import (
    BACKTEST_ENGINE_NAME,
    BACKTEST_ENGINE_VERSION,
    PostgresBacktestResultRepository,
)
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType
from quant_bitcoin.strategies.patterns import FairValueGapStrategy, strategy_for_pattern

DEFAULT_DATABASE_URL = "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
DEFAULT_SOURCE = "binance_spot"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"
DEFAULT_STRATEGY = "FAIR_VALUE_GAP"


def build_parser(prog: str, include_strategy: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Run strategy-level backtest from stored 1m candles.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
    )
    parser.add_argument("--source", default=os.environ.get("CANDLE_SOURCE", DEFAULT_SOURCE))
    parser.add_argument("--symbol", default=os.environ.get("SYMBOL", DEFAULT_SYMBOL))
    parser.add_argument("--interval", default=os.environ.get("INTERVAL", DEFAULT_INTERVAL))
    if include_strategy:
        parser.add_argument("--strategy", default=DEFAULT_STRATEGY)
    parser.add_argument("--pattern", default=None)
    parser.add_argument("--start-time", type=_optional_timestamp, default=None)
    parser.add_argument("--end-time", type=_optional_timestamp, default=None)
    parser.add_argument("--starting-cash", type=float, default=10000.0)
    parser.add_argument("--trade-quantity", type=float, default=1.0)
    parser.add_argument("--no-persist", action="store_true")
    return parser


def _optional_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _select_strategy_key(args: argparse.Namespace) -> str:
    return (args.pattern or getattr(args, "strategy", None) or DEFAULT_STRATEGY).upper()


def _build_actions(candles: pd.DataFrame, strategy_key: str):
    strategy = strategy_for_pattern(strategy_key)
    actions: list[StrategyAction] = []
    cache = (
        IndicatorCache.for_fvg(candles, strategy.detector_config)
        if isinstance(strategy, FairValueGapStrategy)
        else None
    )
    seen_event_ids = set()

    for index in range(1, len(candles) + 1):
        raw_actions = (
            strategy.evaluate_at(
                PatternEvaluationContext(
                    candles=candles,
                    current_index=index - 1,
                    indicator_cache=cache,
                    seen_event_ids=seen_event_ids,
                )
            )
            if isinstance(strategy, FairValueGapStrategy)
            else strategy.evaluate(candles.iloc[:index])
        )
        actions.extend(_expand_raw_actions(raw_actions, candles, index))

    return strategy, actions


def _expand_raw_actions(
    raw_actions: Sequence[StrategyAction],
    candles: pd.DataFrame,
    index: int,
) -> list[StrategyAction]:
    expanded: list[StrategyAction] = []
    for action in raw_actions:
        metadata = action.metadata or {}
        if _is_invalid_risk_skip(action):
            expanded.append(action)
            continue
        if action.action_type not in {
            StrategyActionType.ENTER_LONG,
            StrategyActionType.ENTER_SHORT,
        }:
            expanded.append(action)
            continue

        risk_plan = metadata.get("risk_plan")
        side = metadata.get("position_side")
        if risk_plan is None or side not in {"LONG", "SHORT"}:
            expanded.append(_risk_plan_invalid_skip(action, metadata))
            continue
        if getattr(risk_plan, "status", None) != RiskExitPlanStatus.VALID:
            expanded.append(_risk_plan_invalid_skip(action, metadata))
            continue

        event = type("PatternEventProxy", (), metadata)()
        expanded.extend(
            build_pattern_trade_actions(
                event,
                risk_plan,
                candles.iloc[index:],
                entry_action_timestamp=action.timestamp,
                position_side=side,
            )
        )
    return expanded


def _is_invalid_risk_skip(action: StrategyAction) -> bool:
    return action.action_type == StrategyActionType.SKIP and action.reason == "RISK_PLAN_INVALID"


def _risk_plan_invalid_skip(
    action: StrategyAction,
    metadata: dict[str, object],
) -> StrategyAction:
    return StrategyAction(
        StrategyActionType.SKIP,
        timestamp=action.timestamp,
        quantity=0.0,
        reason="RISK_PLAN_INVALID",
        metadata=metadata,
    )


def _empty_output(strategy_key: str, starting_cash: float) -> dict[str, object]:
    return {
        "strategy": {
            "name": f"{strategy_key}_PATTERN_STRATEGY",
            "strategy_type": "single_pattern",
            "pattern": strategy_key,
        },
        "portfolio": {
            "starting_cash": starting_cash,
            "ending_cash": starting_cash,
            "ending_position": 0.0,
            "final_equity": starting_cash,
            "total_return": 0.0,
        },
        "summary": {
            "trade_count": 0,
            "buy_count": 0,
            "sell_count": 0,
            "max_drawdown": 0.0,
        },
        "executions": [],
        "events": [],
        "warnings": ["candle_count = 0"],
    }


def _serialize_output(result, strategy_key: str, strategy_name: str) -> dict[str, object]:
    return {
        "strategy": {
            "name": strategy_name,
            "strategy_type": "single_pattern",
            "pattern": strategy_key,
        },
        "portfolio": {
            "starting_cash": result.summary.starting_cash,
            "ending_cash": result.summary.ending_cash,
            "ending_position": result.summary.ending_position,
            "final_equity": result.summary.final_equity,
            "total_return": result.summary.total_return,
        },
        "summary": {
            "trade_count": result.summary.trade_count,
            "buy_count": result.summary.buy_count,
            "sell_count": result.summary.sell_count,
            "max_drawdown": result.summary.max_drawdown,
        },
        "executions": [
            {
                "timestamp": execution.timestamp.isoformat().replace("+00:00", "Z")
                if hasattr(execution.timestamp, "isoformat")
                else str(execution.timestamp),
                "side": execution.side,
                "price": execution.price,
                "quantity": execution.quantity,
                "reason": execution.reason,
            }
            for execution in result.executions
        ],
        "events": [],
        "warnings": [],
    }


def run(
    argv: Sequence[str] | None = None,
    *,
    prog: str = "quant-bitcoin-strategy-backtest",
    include_strategy: bool = True,
) -> int:
    args = build_parser(prog, include_strategy).parse_args(argv)
    strategy_key = _select_strategy_key(args)

    provider = PostgresCandleDataProvider.from_database_url(
        args.database_url,
        source=args.source,
        symbol=args.symbol,
        interval=args.interval,
        start_time=args.start_time,
        end_time=args.end_time,
    )
    candles = provider.load()
    if candles.empty:
        print(json.dumps(_empty_output(strategy_key, args.starting_cash)))
        return 0

    strategy, actions = _build_actions(candles, strategy_key)
    result = run_strategy_backtest_engine(
        candles,
        actions,
        config=StrategyEngineConfig(
            starting_cash=args.starting_cash,
            trade_quantity=args.trade_quantity,
        ),
    )

    persisted_run_id = None
    if not args.no_persist:
        repository = PostgresBacktestResultRepository(args.database_url)
        payload = build_strategy_engine_persistence_payload(
            result,
            candles,
            source=args.source,
            symbol=args.symbol,
            interval=args.interval,
            start_time=args.start_time,
            end_time=args.end_time,
            strategy_key=strategy.strategy_key.lower(),
            strategy_name=strategy.strategy_name,
            strategy_version="strategy_engine_v1",
            strategy_parameters={"pattern": strategy.strategy_key},
            starting_cash=args.starting_cash,
            trade_quantity=args.trade_quantity,
            engine_name=BACKTEST_ENGINE_NAME,
            engine_version=BACKTEST_ENGINE_VERSION,
        )
        persisted_run_id = repository.save_completed_backtest(payload)

    output = _serialize_output(result, strategy.strategy_key, strategy.strategy_name)
    if persisted_run_id is not None:
        output["backtest_run_id"] = persisted_run_id
    if not actions:
        output["warnings"].append("no strategy events")

    print(json.dumps(output))
    return 0
