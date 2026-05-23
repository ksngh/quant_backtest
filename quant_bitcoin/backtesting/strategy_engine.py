from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.basic import STANDARD_CANDLE_COLUMNS
from quant_bitcoin.backtesting.costs import (
    ExecutionSide as CostExecutionSide,
    LiquidityRole,
    TransactionCostConfig,
    calculate_transaction_cost,
)
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
    transaction_cost_config: TransactionCostConfig | None = None
    default_liquidity_role: LiquidityRole = LiquidityRole.TAKER
    allow_short: bool = True


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
            result = _apply_action(cash, position, avg_entry, close, qty, action, cfg)
            if result is None:
                continue
            cash, position, avg_entry, execution, realized_delta = result
            realized_pnl += realized_delta
            executions.append(execution)

        equity = cash + (position * close)
        peak_equity = max(peak_equity, equity)
        drawdown = 0.0 if peak_equity == 0 else (equity - peak_equity) / peak_equity
        unrealized = (close - avg_entry) * position
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
    closing_execs = [e for e in executions if e.gross_pnl is not None]
    win_count = len([e for e in closing_execs if (e.net_pnl or 0.0) > 0])
    loss_count = len([e for e in closing_execs if (e.net_pnl or 0.0) < 0])
    short_closing_execs = [e for e in closing_execs if e.position_side == "SHORT"]

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
        gross_pnl=sum(e.gross_pnl for e in executions if e.gross_pnl is not None),
        net_pnl=sum(e.net_pnl for e in executions if e.net_pnl is not None),
        average_net_r=(sum(net_rs) / len(net_rs)) if net_rs else None,
        metadata={
            "transaction_cost": {
                "maker_fee_bps": cfg.transaction_cost_config.maker_fee_bps if cfg.transaction_cost_config else 0.0,
                "taker_fee_bps": cfg.transaction_cost_config.taker_fee_bps if cfg.transaction_cost_config else 0.0,
                "spread_bps": cfg.transaction_cost_config.spread_bps if cfg.transaction_cost_config else 0.0,
                "slippage_bps": cfg.transaction_cost_config.slippage_bps if cfg.transaction_cost_config else 0.0,
                "minimum_slippage_bps": cfg.transaction_cost_config.minimum_slippage_bps if cfg.transaction_cost_config else 0.0,
                "volatility_slippage_multiplier": cfg.transaction_cost_config.volatility_slippage_multiplier if cfg.transaction_cost_config else 0.0,
                "default_liquidity_role": cfg.default_liquidity_role.value,
            },
            "limitations": [
                "No borrow fees modeled",
                "No futures funding modeled",
                "No maintenance margin or liquidation model",
            ],
            "short_performance": {
                "short_close_count": len(short_closing_execs),
                "short_win_count": len([e for e in short_closing_execs if (e.net_pnl or 0.0) > 0]),
                "short_loss_count": len([e for e in short_closing_execs if (e.net_pnl or 0.0) < 0]),
            },
        },
    )
    return StrategyBacktestResult(tuple(executions), tuple(equity_points), summary)


def _apply_action(cash: float, position: float, avg_entry: float, close: float, qty: float, action: StrategyAction, cfg: StrategyEngineConfig):
    action_type = action.action_type
    if action_type == StrategyActionType.SKIP:
        return None

    explicit_price, explicit_price_valid = _resolve_requested_price(action)
    if not explicit_price_valid:
        return None
    if action_type in (StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT):
        if action_type == StrategyActionType.ENTER_SHORT and not cfg.allow_short:
            return None
        if position != 0.0:
            side = execution_side_for_action(action_type) or "BUY"
            position_side = position_side_for_action(action_type)
            reason = "OPPOSITE_ENTRY_BLOCKED" if ((position > 0 and action_type == StrategyActionType.ENTER_SHORT) or (position < 0 and action_type == StrategyActionType.ENTER_LONG)) else "ENTRY_BLOCKED_OPEN_POSITION"
            execution = _execution_record(action, side, position_side, close, close, 0.0, cash, position, cash + (position * close), reason=reason)
            return cash, position, avg_entry, execution, 0.0

        return _open_position(cash, close, qty, action, cfg, explicit_price=explicit_price)

    if action_type in (StrategyActionType.EXIT_LONG, StrategyActionType.PARTIAL_EXIT_LONG):
        if position <= 0:
            return None
        return _close_position(cash, position, avg_entry, close, qty, action, cfg, explicit_price=explicit_price)

    if action_type in (StrategyActionType.EXIT_SHORT, StrategyActionType.PARTIAL_EXIT_SHORT):
        if position >= 0:
            return None
        return _close_position(cash, position, avg_entry, close, qty, action, cfg, explicit_price=explicit_price)

    return None


def _open_position(cash, close, qty, action, cfg, *, explicit_price=None):
    is_short = action.action_type == StrategyActionType.ENTER_SHORT
    side = "SELL" if is_short else "BUY"
    signed_qty = -qty if is_short else qty
    raw_price = explicit_price if explicit_price is not None else close
    cost = _cost(raw_price, qty, side, cfg)
    effective_price = cost.effective_price
    notional = effective_price * qty
    if not is_short and (notional + cost.fee_cost) > cash:
        qty = cash / (effective_price + (cost.fee_cost / max(qty, 1e-12)))
        if qty <= 0:
            return None
        signed_qty = qty
        cost = _cost(raw_price, qty, side, cfg)
        effective_price = cost.effective_price
        notional = effective_price * qty

    cash_after = cash + notional - cost.fee_cost if is_short else cash - notional - cost.fee_cost
    position_after = signed_qty
    avg_entry_after = effective_price
    equity_after = cash_after + (position_after * close)
    execution = _execution_record(action, side, "SHORT" if is_short else "LONG", raw_price, effective_price, qty, cash_after, position_after, equity_after, cost=cost)
    return cash_after, position_after, avg_entry_after, execution, 0.0


def _close_position(cash, position, avg_entry, close, qty, action, cfg, *, explicit_price=None):
    close_qty = min(abs(position), qty)
    is_short = position < 0
    side = "BUY" if is_short else "SELL"
    raw_price = explicit_price if explicit_price is not None else close
    cost = _cost(raw_price, close_qty, side, cfg)
    effective_price = cost.effective_price
    notional = effective_price * close_qty
    cash_after = cash - notional - cost.fee_cost if is_short else cash + notional - cost.fee_cost
    if is_short:
        gross = (avg_entry - effective_price) * close_qty
        position_after = position + close_qty
    else:
        gross = (effective_price - avg_entry) * close_qty
        position_after = position - close_qty
    net = gross - cost.total_cost
    avg_entry_after = 0.0 if position_after == 0 else avg_entry
    equity_after = cash_after + (position_after * close)
    execution = _execution_record(action, side, "SHORT" if is_short else "LONG", raw_price, effective_price, close_qty, cash_after, position_after, equity_after, gross=gross, net=net, cost=cost)
    return cash_after, position_after, avg_entry_after, execution, net


def _cost(raw_price, qty, side, cfg):
    if cfg.transaction_cost_config is None:
        class _C: pass
        c = _C(); c.fee_cost = 0.0; c.spread_cost = 0.0; c.slippage_cost = 0.0; c.total_cost = 0.0; c.effective_price = raw_price
        return c
    return calculate_transaction_cost(raw_price, qty, CostExecutionSide(side), cfg.default_liquidity_role, cfg.transaction_cost_config)



def _resolve_requested_price(action: StrategyAction) -> tuple[float | None, bool]:
    requested = action.requested_price
    if requested is None and isinstance(action.metadata, dict):
        requested = action.metadata.get("execution_price", action.metadata.get("fill_price", action.metadata.get("exit_price")))
    if requested is None:
        return None, True
    try:
        value = float(requested)
    except (TypeError, ValueError):
        return None, False
    if not isfinite(value) or value <= 0:
        return None, False
    return value, True

def _execution_record(action, side, position_side, raw_price, effective_price, qty, cash_after, position_after, equity_after, reason=None, gross=None, net=None, cost=None):
    metadata = dict(action.metadata) if isinstance(action.metadata, dict) else {}
    return StrategyExecution(
        timestamp=action.timestamp,
        side=side,
        action_type=action.action_type.value,
        execution_side=execution_side_for_action(action.action_type),
        position_side=position_side,
        price=effective_price,
        raw_price=raw_price,
        effective_price=effective_price,
        quantity=qty,
        notional=effective_price * qty,
        cash_after=cash_after,
        position_after=position_after,
        equity_after=equity_after,
        reason=reason or action.reason,
        pattern_event_id=metadata.get("pattern_event_id"),
        exit_reason=metadata.get("exit_reason"),
        gross_pnl=gross,
        net_pnl=net,
        fee_cost=(cost.fee_cost if cost else 0.0),
        spread_cost=(cost.spread_cost if cost else 0.0),
        slippage_cost=(cost.slippage_cost if cost else 0.0),
        total_cost=(cost.total_cost if cost else 0.0),
        realized_r_multiple=metadata.get("realized_r_multiple"),
        metadata=metadata,
    )


def _validate_candles(frame: pd.DataFrame) -> None:
    missing = [c for c in STANDARD_CANDLE_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"missing candle columns: {missing}")
    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("candles must be sorted ascending by timestamp")
