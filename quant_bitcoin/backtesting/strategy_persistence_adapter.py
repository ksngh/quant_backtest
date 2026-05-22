from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from quant_bitcoin.persistence import (
    BACKTEST_SCHEMA_VERSION,
    COMPLETED_BACKTEST_STATUS,
    BacktestGraphPointPayload,
    BacktestPersistencePayload,
    BacktestResultPayload,
    BacktestRunPayload,
    BacktestTradePayload,
    StrategyConfigPayload,
    build_backtest_run_key,
    canonical_hash,
)


def build_strategy_engine_persistence_payload(
    result,
    candles: pd.DataFrame,
    *,
    source: str,
    symbol: str,
    interval: str,
    start_time: datetime | None,
    end_time: datetime | None,
    strategy_key: str,
    strategy_name: str,
    strategy_version: str,
    strategy_parameters: dict[str, Any],
    starting_cash: float,
    trade_quantity: float,
    engine_name: str,
    engine_version: str,
) -> BacktestPersistencePayload:
    normalized = candles.copy()
    actual_start = _dt(normalized.iloc[0]["timestamp"]) if not normalized.empty else None
    actual_end = _dt(normalized.iloc[-1]["timestamp"]) if not normalized.empty else None
    strategy_config = StrategyConfigPayload(
        strategy_key=strategy_key,
        strategy_name=strategy_name,
        version=strategy_version,
        parameters=strategy_parameters,
        parameters_hash=canonical_hash(strategy_parameters),
    )
    run_key = build_backtest_run_key(
        {
            "schema_version": BACKTEST_SCHEMA_VERSION,
            "engine_name": engine_name,
            "engine_version": engine_version,
            "strategy_name": strategy_config.strategy_name,
            "strategy_version": strategy_config.version,
            "strategy_parameters": strategy_config.parameters,
            "candle_source": source,
            "symbol": symbol,
            "interval": interval,
            "requested_start_time": start_time,
            "requested_end_time": end_time,
            "actual_start_time": actual_start,
            "actual_end_time": actual_end,
            "candle_count": len(normalized),
            "starting_cash": float(starting_cash),
            "trade_quantity": float(trade_quantity),
        }
    )
    return BacktestPersistencePayload(
        strategy_config=strategy_config,
        run=BacktestRunPayload(
            run_key=run_key,
            engine_name=engine_name,
            engine_version=engine_version,
            candle_source=source,
            symbol=symbol,
            interval=interval,
            requested_start_time=start_time,
            requested_end_time=end_time,
            actual_start_time=actual_start,
            actual_end_time=actual_end,
            candle_count=len(normalized),
            starting_cash=float(starting_cash),
            trade_quantity=float(trade_quantity),
            status=COMPLETED_BACKTEST_STATUS,
            metadata={"schema_version": BACKTEST_SCHEMA_VERSION},
        ),
        result=BacktestResultPayload(
            starting_cash=float(result.summary.starting_cash),
            ending_cash=float(result.summary.ending_cash),
            ending_position=float(result.summary.ending_position),
            final_price=float(result.summary.final_price) if result.summary.final_price is not None else None,
            final_equity=float(result.summary.final_equity),
            total_return=float(result.summary.total_return),
            trade_count=int(result.summary.trade_count),
            buy_count=int(result.summary.buy_count),
            sell_count=int(result.summary.sell_count),
            metadata=dict(result.summary.metadata or {}),
        ),
        trades=tuple(
            BacktestTradePayload(
                sequence=i,
                candle_open_time=_dt(e.timestamp),
                signal=e.side,
                price=float(e.price),
                quantity=float(e.quantity),
                cash_after=float(e.cash_after),
                position_after=float(e.position_after),
                metadata={"action_type": e.action_type, "position_side": e.position_side, "execution_side": e.execution_side},
            )
            for i, e in enumerate(result.executions, start=1)
        ),
        graph_points=_build_graph_points(result),
    )


def _dt(v):
    return v.to_pydatetime() if hasattr(v, "to_pydatetime") else v


def _build_graph_points(result):
    exec_map = {_dt(e.timestamp): (i, e.side) for i, e in enumerate(result.executions, start=1)}
    points=[]
    for i,p in enumerate(result.equity_points, start=1):
        trade=exec_map.get(_dt(p.timestamp))
        points.append(BacktestGraphPointPayload(sequence=i,candle_open_time=_dt(p.timestamp),close_price=float(p.mark_price),cash=float(p.cash),position=float(p.position_quantity),equity=float(p.equity),trade_sequence=(trade[0] if trade else None),signal=(trade[1] if trade else None),metadata={"drawdown":float(p.drawdown)}))
    return tuple(points)
