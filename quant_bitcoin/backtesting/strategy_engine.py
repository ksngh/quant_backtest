from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.basic import STANDARD_CANDLE_COLUMNS
from quant_bitcoin.backtesting.strategy_models import (
    StrategyBacktestResult,
    StrategyBacktestSummary,
    StrategyEquityPoint,
    StrategyExecution,
)
from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    execution_side_for_action,
    position_side_for_action,
)


@dataclass(frozen=True)
class StrategyEngineConfig:
    starting_cash: float = 10000.0
    trade_quantity: float = 1.0


def run_strategy_backtest_engine(
    candles: pd.DataFrame | list[dict[str, Any]],
    actions: list[StrategyAction],
    *,
    config: StrategyEngineConfig | None = None,
) -> StrategyBacktestResult:
    cfg = config or StrategyEngineConfig()
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    _validate_candles(frame)
    if frame.empty:
        raise ValueError("candles must not be empty")

    by_ts = {row["timestamp"]: row for _, row in frame.iterrows()}
    cash = float(cfg.starting_cash)
    position = 0.0
    avg_entry = 0.0
    realized_pnl = 0.0
    peak_equity = cash
    executions: list[StrategyExecution] = []
    actions_by_ts: dict[Any, list[StrategyAction]] = {}
    for action in actions:
        actions_by_ts.setdefault(action.timestamp, []).append(action)

    equity_points: list[StrategyEquityPoint] = []

    for _, candle in frame.iterrows():
        timestamp = candle["timestamp"]
        close = float(candle["close"])
        for action in actions_by_ts.get(timestamp, []):
            qty = float(action.quantity if action.quantity is not None else cfg.trade_quantity)
            if qty <= 0:
                continue
            if action.action_type == StrategyActionType.ENTER_LONG:
                notional = close * qty
                if notional > cash:
                    qty = cash / close
                    notional = close * qty
                if qty <= 0:
                    continue
                cash -= notional
                new_position = position + qty
                avg_entry = ((avg_entry * position) + (close * qty)) / new_position if new_position > 0 else 0.0
                position = new_position
                side = "BUY"
                gross = None
                net = None
            elif action.action_type in (StrategyActionType.EXIT_LONG, StrategyActionType.PARTIAL_EXIT_LONG):
                if position <= 0:
                    continue
                sell_qty = min(position, qty)
                notional = close * sell_qty
                cash += notional
                gross_trade = (close - avg_entry) * sell_qty
                realized_pnl += gross_trade
                position -= sell_qty
                if position == 0:
                    avg_entry = 0.0
                side = "SELL"
                gross = gross_trade
                net = gross_trade
                qty = sell_qty
            else:
                continue

            equity = cash + (position * close)
            peak_equity = max(peak_equity, equity)
            executions.append(
                StrategyExecution(
                    timestamp=timestamp,
                    side=side,
                    action_type=action.action_type.value,
                    execution_side=execution_side_for_action(action.action_type),
                    position_side=position_side_for_action(action.action_type),
                    price=close,
                    quantity=qty,
                    notional=close * qty,
                    cash_after=cash,
                    position_after=position,
                    equity_after=equity,
                    reason=action.reason,
                    pattern_event_id=action.metadata.get("pattern_event_id") if isinstance(action.metadata, dict) else None,
                    exit_reason=action.metadata.get("exit_reason") if isinstance(action.metadata, dict) else None,
                    gross_pnl=gross,
                    net_pnl=net,
                    realized_r_multiple=action.metadata.get("realized_r_multiple") if isinstance(action.metadata, dict) else None,
                    metadata=dict(action.metadata) if isinstance(action.metadata, dict) else {},
                )
            )

        equity = cash + (position * close)
        peak_equity = max(peak_equity, equity)
        drawdown = 0.0 if peak_equity == 0 else (equity - peak_equity) / peak_equity
        unrealized = (close - avg_entry) * position if position > 0 else 0.0
        equity_points.append(
            StrategyEquityPoint(
                timestamp=timestamp,
                cash=cash,
                position_quantity=position,
                mark_price=close,
                equity=equity,
                unrealized_pnl=unrealized,
                realized_pnl=realized_pnl,
                drawdown=drawdown,
            )
        )

    final_price = float(frame.iloc[-1]["close"])
    final_equity = cash + (position * final_price)
    net_rs = [e.realized_r_multiple for e in executions if e.realized_r_multiple is not None]
    sell_execs = [e for e in executions if e.side == "SELL"]
    win_count = len([e for e in sell_execs if (e.net_pnl or 0.0) > 0])
    loss_count = len([e for e in sell_execs if (e.net_pnl or 0.0) < 0])

    summary = StrategyBacktestSummary(
        starting_cash=cfg.starting_cash,
        ending_cash=cash,
        ending_position=position,
        final_price=final_price,
        final_equity=final_equity,
        total_return=0.0 if cfg.starting_cash == 0 else (final_equity - cfg.starting_cash) / cfg.starting_cash,
        trade_count=len(executions),
        buy_count=len([e for e in executions if e.side == "BUY"]),
        sell_count=len(sell_execs),
        win_count=win_count,
        loss_count=loss_count,
        max_drawdown=min([p.drawdown for p in equity_points], default=0.0),
        gross_pnl=realized_pnl,
        net_pnl=realized_pnl,
        average_net_r=(sum(net_rs) / len(net_rs)) if net_rs else None,
        metadata={},
    )
    return StrategyBacktestResult(tuple(executions), tuple(equity_points), summary)


def _validate_candles(frame: pd.DataFrame) -> None:
    missing = [c for c in STANDARD_CANDLE_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"missing candle columns: {missing}")
    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")
