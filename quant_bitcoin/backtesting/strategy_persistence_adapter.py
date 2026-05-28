from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.json_metadata import json_ready, json_ready_dict
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
    strategy_metadata: dict[str, Any] | None = None,
    starting_cash: float,
    trade_quantity: float,
    engine_name: str,
    engine_version: str,
    run_metadata: dict[str, Any] | None = None,
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
        metadata=strategy_metadata,
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
    metadata = {"schema_version": BACKTEST_SCHEMA_VERSION}
    if run_metadata:
        metadata.update(_json_ready_dict(run_metadata))

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
            metadata=metadata,
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
            metadata=_json_ready_dict(result.summary.metadata),
        ),
        trades=tuple(
            BacktestTradePayload(
                sequence=i,
                candle_open_time=_dt(e.timestamp),
                signal=e.position_signal or e.side,
                price=float(e.price),
                quantity=float(e.quantity),
                cash_after=float(e.cash_after),
                position_after=float(e.position_after),
                metadata=_json_ready_dict(
                    _execution_metadata(e)
                    | {
                        "action_type": e.action_type,
                        "position_signal": e.position_signal,
                        "side": e.side,
                        "execution_side": e.execution_side,
                        "position_side": e.position_side,
                        "cash_balance_after": e.cash_balance_after,
                        "execution_equity_after": e.execution_equity_after,
                        "mark_to_market_equity_after": e.mark_to_market_equity_after,
                        "pattern_event_id": e.pattern_event_id,
                        "pattern_type": (e.metadata or {}).get("pattern_type"),
                        "entry_mode": (e.metadata or {}).get("entry_mode"),
                        "exit_reason": e.exit_reason,
                        "target_name": (e.metadata or {}).get("target_name"),
                        "quantity_ratio": (e.metadata or {}).get("quantity_ratio"),
                        "quantity_mode": (e.metadata or {}).get("quantity_mode"),
                        "requested_quantity": (e.metadata or {}).get("requested_quantity"),
                        "resolved_quantity": (e.metadata or {}).get("resolved_quantity"),
                        "remaining_quantity_ratio": (e.metadata or {}).get("remaining_quantity_ratio"),
                        "gross_pnl": e.gross_pnl,
                        "net_pnl": e.net_pnl,
                        "raw_price": e.raw_price,
                        "effective_price": e.effective_price,
                        "price_semantics": (e.metadata or {}).get("price_semantics", "raw_fill_price"),
                        "effective_price_semantics": (e.metadata or {}).get(
                            "effective_price_semantics",
                            "spread_slippage_adjusted_diagnostic_price",
                        ),
                        "realized_r_multiple": e.realized_r_multiple,
                        "score_components": (e.metadata or {}).get("score_components"),
                        "score_component_sources": (e.metadata or {}).get("score_component_sources"),
                        "score_limitations": (e.metadata or {}).get("score_limitations"),
                        "score_calibration": (e.metadata or {}).get("score_calibration"),
                        "fee_cost": e.fee_cost,
                        "spread_cost": e.spread_cost,
                        "slippage_cost": e.slippage_cost,
                        "total_cost": e.total_cost,
                        "cost_breakdown": (e.metadata or {}).get("cost_breakdown"),
                        "free_cash_after": e.free_cash_after,
                        "margin_used_after": e.margin_used_after,
                        "short_proceeds_locked_after": e.short_proceeds_locked_after,
                        "short_collateral_locked_after": e.short_collateral_locked_after,
                        "available_buying_power_after": e.available_buying_power_after,
                        "cash_after_semantics": e.cash_after_semantics,
                    }
                ),
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
            _json_ready_dict(
                _execution_metadata(execution)
                | {
                    "trade_sequence": sequence,
                    "signal": execution.position_signal or execution.side,
                    "action_type": execution.action_type,
                    "position_signal": execution.position_signal,
                    "position_side": execution.position_side,
                    "side": execution.side,
                    "execution_side": execution.execution_side,
                    "cash_balance_after": execution.cash_balance_after,
                    "execution_equity_after": execution.execution_equity_after,
                    "mark_to_market_equity_after": execution.mark_to_market_equity_after,
                    "free_cash_after": execution.free_cash_after,
                    "margin_used_after": execution.margin_used_after,
                    "short_proceeds_locked_after": execution.short_proceeds_locked_after,
                    "short_collateral_locked_after": execution.short_collateral_locked_after,
                    "available_buying_power_after": execution.available_buying_power_after,
                    "quantity_mode": (execution.metadata or {}).get("quantity_mode"),
                    "quantity_ratio": (execution.metadata or {}).get("quantity_ratio"),
                    "resolved_quantity": (execution.metadata or {}).get("resolved_quantity"),
                }
            )
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
                    "free_cash": equity_point.free_cash,
                    "margin_used": equity_point.margin_used,
                    "short_proceeds_locked": equity_point.short_proceeds_locked,
                    "short_collateral_locked": equity_point.short_collateral_locked,
                    "available_buying_power": equity_point.available_buying_power,
                    "cash_semantics": equity_point.cash_semantics,
                    "equity_semantics": equity_point.equity_semantics,
                    "equity_valuation_price": equity_point.equity_valuation_price,
                    "trades": trades,
                },
            )
        )
    return tuple(points)


def _execution_metadata(execution) -> dict[str, Any]:
    return _json_ready_dict(execution.metadata)


def _json_ready_dict(value: Any) -> dict[str, Any]:
    return json_ready_dict(value)


def _json_ready(value: Any) -> Any:
    return json_ready(value)
