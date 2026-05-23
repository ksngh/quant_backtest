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
                metadata={
                    "action_type": e.action_type,
                    "execution_side": e.execution_side,
                    "position_side": e.position_side,
                    "pattern_event_id": e.pattern_event_id,
                    "pattern_type": (e.metadata or {}).get("pattern_type"),
                    "entry_mode": (e.metadata or {}).get("entry_mode"),
                    "exit_reason": e.exit_reason,
                    "target_name": (e.metadata or {}).get("target_name"),
                    "quantity_ratio": (e.metadata or {}).get("quantity_ratio"),
                    "remaining_quantity_ratio": (e.metadata or {}).get("remaining_quantity_ratio"),
                    "gross_pnl": e.gross_pnl,
                    "net_pnl": e.net_pnl,
                    "realized_r_multiple": e.realized_r_multiple,
                    "fee_cost": e.fee_cost,
                    "spread_cost": e.spread_cost,
                    "slippage_cost": e.slippage_cost,
                    "total_cost": e.total_cost,
                },
            )
            for i, e in enumerate(result.executions, start=1)
        ),
        graph_points=_build_graph_points(result),
    )


def _dt(v):
    return v.to_pydatetime() if hasattr(v, "to_pydatetime") else v


def _build_graph_points(result):
    exec_map: dict[datetime, list[dict[str, Any]]] = {}
    for sequence, execution in enumerate(result.executions, start=1):
        timestamp = _dt(execution.timestamp)
        exec_map.setdefault(timestamp, []).append(
            {
                "trade_sequence": sequence,
                "signal": execution.side,
                "action_type": execution.action_type,
                "position_side": execution.position_side,
                "execution_side": execution.execution_side,
            }
        )

    points = []
    for index, equity_point in enumerate(result.equity_points, start=1):
        timestamp = _dt(equity_point.timestamp)
        trades = exec_map.get(timestamp, [])
        first_trade = trades[0] if trades else None
        points.append(
            BacktestGraphPointPayload(
                sequence=index,
                candle_open_time=timestamp,
                close_price=float(equity_point.mark_price),
                cash=float(equity_point.cash),
                position=float(equity_point.position_quantity),
                equity=float(equity_point.equity),
                trade_sequence=(first_trade["trade_sequence"] if first_trade else None),
                signal=(first_trade["signal"] if first_trade else None),
                metadata={
                    "drawdown": float(equity_point.drawdown),
                    "trades": trades,
                },
            )
        )
    return tuple(points)
