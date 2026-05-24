from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ExecutionSide = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class StrategyExecution:
    timestamp: Any
    side: ExecutionSide
    action_type: str
    price: float
    quantity: float
    notional: float
    cash_after: float
    position_after: float
    equity_after: float
    position_signal: str | None = None
    cash_balance_after: float | None = None
    execution_equity_after: float | None = None
    mark_to_market_equity_after: float | None = None
    free_cash_after: float | None = None
    margin_used_after: float | None = None
    short_proceeds_locked_after: float | None = None
    short_collateral_locked_after: float | None = None
    available_buying_power_after: float | None = None
    cash_after_semantics: str | None = None
    execution_side: ExecutionSide | None = None
    position_side: Literal["LONG", "SHORT"] | None = None
    raw_price: float | None = None
    effective_price: float | None = None
    fee_cost: float | None = None
    spread_cost: float | None = None
    slippage_cost: float | None = None
    total_cost: float | None = None
    reason: str | None = None
    pattern_event_id: str | None = None
    exit_reason: str | None = None
    gross_pnl: float | None = None
    net_pnl: float | None = None
    realized_r_multiple: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyEquityPoint:
    timestamp: Any
    cash: float
    position_quantity: float
    mark_price: float
    equity: float
    unrealized_pnl: float
    realized_pnl: float
    drawdown: float
    equity_valuation_price: float | None = None
    free_cash: float | None = None
    margin_used: float | None = None
    short_proceeds_locked: float | None = None
    short_collateral_locked: float | None = None
    available_buying_power: float | None = None
    cash_semantics: str | None = None
    equity_semantics: str | None = None
    short_carrying_cost_cumulative: float | None = None
    short_would_liquidate: bool | None = None
    short_liquidation_buffer_ratio: float | None = None


@dataclass(frozen=True)
class StrategyBacktestSummary:
    starting_cash: float
    ending_cash: float
    ending_position: float
    final_price: float
    final_equity: float
    total_return: float
    trade_count: int
    buy_count: int
    sell_count: int
    win_count: int
    loss_count: int
    max_drawdown: float
    gross_pnl: float
    net_pnl: float
    average_net_r: float | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyBacktestResult:
    executions: tuple[StrategyExecution, ...]
    equity_points: tuple[StrategyEquityPoint, ...]
    summary: StrategyBacktestSummary
