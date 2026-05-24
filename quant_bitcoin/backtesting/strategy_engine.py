from __future__ import annotations

from dataclasses import dataclass, replace
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
from quant_bitcoin.backtesting.performance_metrics import (
    calculate_performance_metrics,
    calculate_trade_attribution_metrics,
)
from quant_bitcoin.backtesting.sizing import (
    BacktestGuardrailConfig,
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
    SimulatedMarginConfig,
)
from quant_bitcoin.backtesting.strategy_models import (
    StrategyBacktestResult,
    StrategyBacktestSummary,
    StrategyEquityPoint,
    StrategyExecution,
)
from quant_bitcoin.market_data.candle_validation import (
    CandleValidationConfig,
    validate_standard_candles,
)
from quant_bitcoin.strategies.actions import (
    StrategyAction,
    StrategyActionType,
    StrategyQuantityMode,
    execution_side_for_action,
    position_signal_for_action,
    position_side_for_action,
)

_CANDLE_CLOSE_EQUITY_SEMANTICS = "candle-close mark-to-market equity after applying actions at this timestamp"
_ENTRY_EXECUTION_EQUITY_SEMANTICS = (
    "entry-candle execution-price equity; subsequent candles use candle-close mark-to-market"
)
_ENTRY_SIZING_PRICE_POLICY = "CONSERVATIVE_MAX_EXECUTION_OR_CLOSE"


@dataclass(frozen=True)
class StrategyEngineConfig:
    starting_cash: float = 10000.0
    trade_quantity: float = 1.0
    transaction_cost_config: TransactionCostConfig | None = None
    default_liquidity_role: LiquidityRole = LiquidityRole.TAKER
    allow_short: bool = True
    interval: str = "1m"
    risk_free_rate: float = 0.0
    position_sizing: PositionSizingConfig | None = None
    short_exposure_mode: ShortExposureMode = ShortExposureMode.CASH_BOUNDED
    simulated_margin: SimulatedMarginConfig | None = None
    enforce_candle_continuity: bool = False
    guardrails: BacktestGuardrailConfig | None = None
    market_regime_by_timestamp: dict[Any, dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.trade_quantity, (int, float)) or not isfinite(float(self.trade_quantity)) or float(self.trade_quantity) <= 0:
            raise ValueError("trade_quantity must be a positive finite number")
        sizing = self.position_sizing or PositionSizingConfig()
        if not isinstance(sizing, PositionSizingConfig):
            raise ValueError("position_sizing must be a PositionSizingConfig")
        short_mode = self.short_exposure_mode
        if not isinstance(short_mode, ShortExposureMode):
            short_mode = ShortExposureMode(str(short_mode).upper())
        margin = self.simulated_margin or SimulatedMarginConfig()
        if not isinstance(margin, SimulatedMarginConfig):
            raise ValueError("simulated_margin must be a SimulatedMarginConfig")
        if short_mode is ShortExposureMode.SIMULATED_MARGIN and not margin.enabled:
            raise ValueError("SIMULATED_MARGIN short exposure requires simulated_margin.enabled=True")
        guardrails = self.guardrails or BacktestGuardrailConfig()
        if not isinstance(guardrails, BacktestGuardrailConfig):
            raise ValueError("guardrails must be a BacktestGuardrailConfig")
        if self.market_regime_by_timestamp is not None and not isinstance(self.market_regime_by_timestamp, dict):
            raise ValueError("market_regime_by_timestamp must be a dictionary when provided")
        object.__setattr__(self, "position_sizing", sizing)
        object.__setattr__(self, "short_exposure_mode", short_mode)
        object.__setattr__(self, "simulated_margin", margin)
        object.__setattr__(self, "guardrails", guardrails)


def run_strategy_backtest_engine(
    candles: pd.DataFrame | list[dict[str, Any]],
    actions: list[StrategyAction],
    *,
    config: StrategyEngineConfig | None = None,
) -> StrategyBacktestResult:
    cfg = config or StrategyEngineConfig()
    frame = candles.copy(deep=True) if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    _validate_candles(frame, cfg)
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
    guard_state: dict[str, object] = {
        "consecutive_losses": 0,
        "daily_realized_pnl": {},
        "trades_by_day": {},
    }

    equity_points: list[StrategyEquityPoint] = []

    for _, candle in frame.iterrows():
        timestamp = candle["timestamp"]
        close = float(candle["close"])
        volatility_bps = _candle_volatility_bps(candle)
        current_equity = cash + (position * close)
        current_drawdown = 0.0 if peak_equity == 0 else (current_equity - peak_equity) / peak_equity
        entry_equity_mark_price: float | None = None
        for action in actions_by_ts.get(timestamp, []):
            action = _action_with_regime_metadata(action, cfg.market_regime_by_timestamp.get(timestamp) if cfg.market_regime_by_timestamp else None)
            result = _apply_action(
                cash,
                position,
                avg_entry,
                close,
                action,
                cfg,
                volatility_bps=volatility_bps,
                account_equity=current_equity,
                current_drawdown=current_drawdown,
                guard_state=guard_state,
            )
            if result is None:
                continue
            cash, position, avg_entry, execution, realized_delta = result
            realized_pnl += realized_delta
            executions.append(execution)
            _update_guard_state(guard_state, execution)
            if (
                execution.quantity > 0
                and execution.action_type in (StrategyActionType.ENTER_LONG.value, StrategyActionType.ENTER_SHORT.value)
                and execution.position_after != 0
            ):
                entry_equity_mark_price = float(execution.effective_price or execution.price)

        equity_valuation_price = entry_equity_mark_price if position != 0.0 and entry_equity_mark_price is not None else close
        equity_semantics = _ENTRY_EXECUTION_EQUITY_SEMANTICS if equity_valuation_price != close else _CANDLE_CLOSE_EQUITY_SEMANTICS
        equity = cash + (position * equity_valuation_price)
        peak_equity = max(peak_equity, equity)
        drawdown = 0.0 if peak_equity == 0 else (equity - peak_equity) / peak_equity
        unrealized = (equity_valuation_price - avg_entry) * position
        account_state = _account_state(cash, position, equity_valuation_price, avg_entry, cfg, equity_semantics=equity_semantics)
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
                equity_valuation_price=equity_valuation_price,
                free_cash=account_state["free_cash_after"],
                margin_used=account_state["margin_used_after"],
                short_proceeds_locked=account_state["short_proceeds_locked_after"],
                short_collateral_locked=account_state["short_collateral_locked_after"],
                available_buying_power=account_state["available_buying_power_after"],
                cash_semantics=account_state["cash_after_semantics"],
                equity_semantics=account_state["equity_after_semantics"],
            )
        )

    final_price = float(frame.iloc[-1]["close"])
    final_equity_point = equity_points[-1]
    final_equity = final_equity_point.equity
    final_equity_valuation_price = final_equity_point.equity_valuation_price or final_price
    net_rs = [e.realized_r_multiple for e in executions if e.realized_r_multiple is not None]
    filled_execs = [e for e in executions if e.quantity > 0]
    sell_execs = [e for e in filled_execs if e.side == "SELL"]
    closing_execs = [e for e in executions if e.gross_pnl is not None]
    total_fee_cost = sum(e.fee_cost for e in executions)
    total_spread_cost = sum(e.spread_cost for e in executions)
    total_slippage_cost = sum(e.slippage_cost for e in executions)
    total_cost = sum(e.total_cost for e in executions)
    gross_pnl_total = sum(e.gross_pnl for e in executions if e.gross_pnl is not None)
    net_pnl_total = sum(e.net_pnl for e in executions if e.net_pnl is not None)
    win_count = len([e for e in closing_execs if (e.net_pnl or 0.0) > 0])
    loss_count = len([e for e in closing_execs if (e.net_pnl or 0.0) < 0])
    short_closing_execs = [e for e in closing_execs if e.position_side == "SHORT"]
    skipped_action_count = len([a for a in actions if a.action_type == StrategyActionType.SKIP])
    blocked_action_count = len([e for e in executions if e.quantity == 0 and e.reason])
    entry_count = len([e for e in filled_execs if e.action_type in (StrategyActionType.ENTER_LONG.value, StrategyActionType.ENTER_SHORT.value)])
    exit_count = len([e for e in filled_execs if e.gross_pnl is not None])
    partial_exit_count = len([e for e in filled_execs if e.action_type in (StrategyActionType.PARTIAL_EXIT_LONG.value, StrategyActionType.PARTIAL_EXIT_SHORT.value)])
    full_exit_count = len([e for e in filled_execs if e.action_type in (StrategyActionType.EXIT_LONG.value, StrategyActionType.EXIT_SHORT.value)])

    summary = StrategyBacktestSummary(
        starting_cash=cfg.starting_cash,
        ending_cash=cash,
        ending_position=position,
        final_price=final_price,
        final_equity=final_equity,
        total_return=0.0 if cfg.starting_cash == 0 else (final_equity - cfg.starting_cash) / cfg.starting_cash,
        trade_count=len(filled_execs),
        buy_count=len([e for e in filled_execs if e.side == "BUY"]),
        sell_count=len(sell_execs),
        win_count=win_count,
        loss_count=loss_count,
        max_drawdown=min([p.drawdown for p in equity_points], default=0.0),
        gross_pnl=gross_pnl_total,
        net_pnl=net_pnl_total,
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
                "zero_transaction_cost_assumption": _zero_transaction_cost_assumption(cfg),
                "volatility_slippage_source": "candle high-low range divided by close, in basis points",
            },
            "cost_summary": {
                "total_fee_cost": total_fee_cost,
                "total_spread_cost": total_spread_cost,
                "total_slippage_cost": total_slippage_cost,
                "total_cost": total_cost,
                "gross_pnl": gross_pnl_total,
                "net_pnl": net_pnl_total,
                "cost_to_gross_pnl_ratio": None if gross_pnl_total == 0 else total_cost / abs(gross_pnl_total),
                "zero_transaction_cost_assumption": _zero_transaction_cost_assumption(cfg),
                "volatility_slippage_source": "candle high-low range divided by close, in basis points",
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
            "position_sizing": cfg.position_sizing.to_metadata(),
            "short_exposure_policy": {
                "mode": cfg.short_exposure_mode.value,
                "default_policy": "short exposure is bounded by cash unless explicit simulated-margin mode is enabled",
                "scope": "backtest_only",
                "spot_short_execution": "simulated only; not a real spot exchange order capability",
                "modeled_economics": {
                    "borrow_fees": False,
                    "futures_funding": False,
                    "maintenance_margin": False,
                    "liquidation": False,
                    "initial_margin": cfg.short_exposure_mode is ShortExposureMode.SIMULATED_MARGIN and cfg.simulated_margin.enabled,
                },
                "unsupported_economics": [
                    "No borrow fees modeled",
                    "No futures funding modeled",
                    "No maintenance margin or liquidation model",
                ],
            },
            "short_economics": {
                "scope": "backtest_only_simulation",
                "cash_bounded_short": cfg.short_exposure_mode is ShortExposureMode.CASH_BOUNDED,
                "simulated_margin": cfg.short_exposure_mode is ShortExposureMode.SIMULATED_MARGIN and cfg.simulated_margin.enabled,
                "real_spot_short_execution": False,
                "real_futures_or_margin_execution": False,
                "borrow_fees_modeled": False,
                "futures_funding_modeled": False,
                "maintenance_margin_modeled": False,
                "liquidation_modeled": False,
                "warning": "Short results are simulation-only and exclude borrow fees, futures funding, maintenance margin, and liquidation.",
            },
            "simulated_margin": cfg.simulated_margin.to_metadata(),
            "guardrails": cfg.guardrails.to_metadata(),
            "account_state": _account_state(
                cash,
                position,
                final_equity_valuation_price,
                avg_entry,
                cfg,
                equity_semantics=final_equity_point.equity_semantics,
            ),
            "equity_semantics": {
                "execution_equity_after": "net account value immediately after the fill at effective execution price",
                "mark_to_market_equity_after": "net account value after the fill marked to the candle close",
                "equity_points.equity": "primary equity series; new entry candles use execution-price valuation to avoid same-candle fill/close PnL, other candles use candle-close mark-to-market",
                "equity_points.mark_price": "candle close retained for market-price reference",
                "equity_points.equity_valuation_price": "price used for primary equity at that point",
                "final_equity": "last value from the primary equity series",
            },
            "execution_metrics": {
                "filled_execution_count": len(filled_execs),
                "skipped_action_count": skipped_action_count,
                "blocked_action_count": blocked_action_count,
                "entry_count": entry_count,
                "exit_count": exit_count,
                "partial_exit_count": partial_exit_count,
                "full_exit_count": full_exit_count,
                "open_ending_position": position,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": final_equity_point.unrealized_pnl,
                "gross_pnl": gross_pnl_total,
                "net_pnl": net_pnl_total,
                "total_cost": total_cost,
                "max_drawdown": min([p.drawdown for p in equity_points], default=0.0),
            },
            "performance_metrics": calculate_performance_metrics(
                equity_points,
                interval=cfg.interval,
                risk_free_rate=cfg.risk_free_rate,
            ).to_metadata(),
            "trade_attribution": calculate_trade_attribution_metrics(executions, equity_points),
        },
    )
    return StrategyBacktestResult(tuple(executions), tuple(equity_points), summary)


def _apply_action(
    cash: float,
    position: float,
    avg_entry: float,
    close: float,
    action: StrategyAction,
    cfg: StrategyEngineConfig,
    *,
    volatility_bps: float | None = None,
    account_equity: float | None = None,
    current_drawdown: float = 0.0,
    guard_state: dict[str, object] | None = None,
):
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
            execution = _execution_record(action, side, position_side, close, close, 0.0, cash, position, cash + (position * close), reason=reason, account_state=_account_state(cash, position, close, avg_entry, cfg))
            return cash, position, avg_entry, execution, 0.0
        guard_reason, guard_metadata = _entry_guardrail_decision(cfg, guard_state or {}, current_drawdown)
        if guard_reason is not None:
            side = execution_side_for_action(action_type) or "BUY"
            position_side = position_side_for_action(action_type)
            execution = _execution_record(
                action,
                side,
                position_side,
                close,
                close,
                0.0,
                cash,
                position,
                cash + (position * close),
                reason=guard_reason,
                extra_metadata=guard_metadata,
                account_state=_account_state(cash, position, close, avg_entry, cfg),
            )
            return cash, position, avg_entry, execution, 0.0
        qty, sizing_metadata = _resolve_entry_quantity(action, cash, close, cfg, explicit_price=explicit_price, account_equity=account_equity)
        if sizing_metadata.get("block_reason"):
            side = execution_side_for_action(action_type) or "BUY"
            position_side = position_side_for_action(action_type)
            execution = _execution_record(
                action,
                side,
                position_side,
                close,
                close,
                0.0,
                cash,
                position,
                cash + (position * close),
                reason=str(sizing_metadata["block_reason"]),
                extra_metadata=sizing_metadata,
                account_state=_account_state(cash, position, close, avg_entry, cfg),
            )
            return cash, position, avg_entry, execution, 0.0
        if qty <= 0:
            return None
        return _open_position(cash, close, qty, action, cfg, explicit_price=explicit_price, sizing_metadata=sizing_metadata, volatility_bps=volatility_bps)

    if action_type in (StrategyActionType.EXIT_LONG, StrategyActionType.PARTIAL_EXIT_LONG):
        if position <= 0:
            return None
        qty, quantity_metadata, quantity_reason = _resolve_exit_quantity(action, position, cfg)
        if quantity_reason is not None:
            return _blocked_exit_quantity(cash, position, avg_entry, close, action, cfg, quantity_reason, quantity_metadata)
        if qty <= 0:
            return None
        return _close_position(cash, position, avg_entry, close, qty, action, cfg, explicit_price=explicit_price, quantity_metadata=quantity_metadata, volatility_bps=volatility_bps)

    if action_type in (StrategyActionType.EXIT_SHORT, StrategyActionType.PARTIAL_EXIT_SHORT):
        if position >= 0:
            return None
        qty, quantity_metadata, quantity_reason = _resolve_exit_quantity(action, position, cfg)
        if quantity_reason is not None:
            return _blocked_exit_quantity(cash, position, avg_entry, close, action, cfg, quantity_reason, quantity_metadata)
        if qty <= 0:
            return None
        return _close_position(cash, position, avg_entry, close, qty, action, cfg, explicit_price=explicit_price, quantity_metadata=quantity_metadata, volatility_bps=volatility_bps)

    return None


def _action_with_regime_metadata(
    action: StrategyAction,
    regime_context: dict[str, Any] | None,
) -> StrategyAction:
    if not regime_context:
        return action
    metadata = dict(action.metadata) if isinstance(action.metadata, dict) else {}
    clean_context = {key: value for key, value in regime_context.items() if value is not None}
    if not clean_context:
        return action
    for key in (
        "market_regime",
        "volatility_regime",
        "liquidity_regime",
        "spread_regime",
        "trend_regime",
        "mean_reversion_regime",
    ):
        if key in clean_context:
            metadata.setdefault(key, clean_context[key])
    metadata.setdefault("market_regime_context", clean_context)
    return replace(action, metadata=metadata)


def _open_position(cash, close, qty, action, cfg, *, explicit_price=None, sizing_metadata=None, volatility_bps=None):
    is_short = action.action_type == StrategyActionType.ENTER_SHORT
    side = "SELL" if is_short else "BUY"
    requested_qty = qty
    raw_price = explicit_price if explicit_price is not None else close
    cost = _cost(raw_price, qty, side, cfg, volatility_bps=volatility_bps)
    effective_price = cost.effective_price
    notional = effective_price * qty
    reason = None
    extra_metadata = dict(sizing_metadata or {})
    extra_metadata["requested_quantity"] = requested_qty
    if not is_short:
        qty, cost, reason, affordability_metadata = _apply_entry_affordability(
            cash,
            raw_price,
            qty,
            side,
            cfg,
            required_cash=notional + cost.fee_cost,
            reason="INSUFFICIENT_CASH_FOR_LONG",
            policy=cfg.position_sizing.insufficient_funds_policy,
            volatility_bps=volatility_bps,
        )
        extra_metadata.update(affordability_metadata)
    elif cfg.short_exposure_mode is ShortExposureMode.CASH_BOUNDED:
        qty, cost, reason, affordability_metadata = _apply_entry_affordability(
            cash,
            raw_price,
            qty,
            side,
            cfg,
            required_cash=notional + cost.fee_cost,
            reason="INSUFFICIENT_BUYING_POWER_FOR_SHORT",
            policy=cfg.position_sizing.insufficient_funds_policy,
            volatility_bps=volatility_bps,
        )
        extra_metadata.update(affordability_metadata)
    else:
        margin = cfg.simulated_margin
        required_margin = margin.required_initial_margin(notional)
        qty, cost, reason, affordability_metadata = _apply_entry_affordability(
            cash,
            raw_price,
            qty,
            side,
            cfg,
            required_cash=required_margin + cost.fee_cost,
            reason="INSUFFICIENT_INITIAL_MARGIN",
            policy=margin.insufficient_margin_policy,
            required_margin=required_margin,
            volatility_bps=volatility_bps,
        )
        extra_metadata.update(affordability_metadata)

    if reason is not None:
        account_state = _account_state(cash, 0.0, close, 0.0, cfg)
        execution = _execution_record(
            action,
            side,
            "SHORT" if is_short else "LONG",
            raw_price,
            raw_price,
            0.0,
            cash,
            0.0,
            cash,
            reason=reason,
            extra_metadata=extra_metadata,
            account_state=account_state,
        )
        return cash, 0.0, 0.0, execution, 0.0

    effective_price = cost.effective_price
    notional = effective_price * qty
    signed_qty = -qty if is_short else qty
    extra_metadata["filled_quantity"] = qty
    if requested_qty != qty:
        extra_metadata["quantity_was_resized"] = True

    cash_after = cash + notional - cost.fee_cost if is_short else cash - notional - cost.fee_cost
    position_after = signed_qty
    avg_entry_after = effective_price
    equity_after = cash_after + (position_after * close)
    execution_equity_after = cash_after + (position_after * effective_price)
    execution = _execution_record(
        action,
        side,
        "SHORT" if is_short else "LONG",
        raw_price,
        effective_price,
        qty,
        cash_after,
        position_after,
        equity_after,
        cost=cost,
        extra_metadata=extra_metadata,
        account_state=_account_state(cash_after, position_after, close, avg_entry_after, cfg),
        execution_equity_after=execution_equity_after,
    )
    return cash_after, position_after, avg_entry_after, execution, 0.0


def _close_position(cash, position, avg_entry, close, qty, action, cfg, *, explicit_price=None, quantity_metadata=None, volatility_bps=None):
    close_qty = min(abs(position), qty)
    is_short = position < 0
    side = "BUY" if is_short else "SELL"
    raw_price = explicit_price if explicit_price is not None else close
    cost = _cost(raw_price, close_qty, side, cfg, volatility_bps=volatility_bps)
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
    execution_equity_after = cash_after + (position_after * effective_price)
    execution = _execution_record(
        action,
        side,
        "SHORT" if is_short else "LONG",
        raw_price,
        effective_price,
        close_qty,
        cash_after,
        position_after,
        equity_after,
        gross=gross,
        net=net,
        cost=cost,
        extra_metadata=quantity_metadata,
        account_state=_account_state(cash_after, position_after, close, avg_entry_after, cfg),
        execution_equity_after=execution_equity_after,
    )
    return cash_after, position_after, avg_entry_after, execution, net


def _resolve_entry_quantity(action: StrategyAction, cash: float, close: float, cfg: StrategyEngineConfig, *, explicit_price=None, account_equity=None) -> tuple[float, dict[str, object]]:
    raw_price = explicit_price if explicit_price is not None else close
    if action.quantity is not None:
        qty = float(action.quantity)
        return qty, {
            "position_sizing_source": "ACTION_QUANTITY",
            "position_sizing_mode": PositionSizingMode.FIXED_QUANTITY.value,
        }
    sizing = cfg.position_sizing
    valuation_price = max(float(raw_price), float(close))
    if sizing.mode is PositionSizingMode.FIXED_QUANTITY:
        qty = float(sizing.value if sizing.value is not None else cfg.trade_quantity)
    elif sizing.mode is PositionSizingMode.CASH_FRACTION:
        qty = (cash * float(sizing.value)) / valuation_price
    elif sizing.mode is PositionSizingMode.TARGET_NOTIONAL:
        qty = float(sizing.value) / valuation_price
    elif sizing.mode is PositionSizingMode.EQUITY_RISK_FRACTION:
        risk_per_unit = _action_risk_per_unit(action)
        metadata = {
            "position_sizing_source": "ENGINE_CONFIG",
            "position_sizing_mode": sizing.mode.value,
            "position_sizing_value": sizing.value,
            "risk_per_unit": risk_per_unit,
            "account_equity_for_risk_sizing": account_equity if account_equity is not None else cash,
        }
        if risk_per_unit is None or risk_per_unit <= 0:
            metadata["block_reason"] = "MISSING_RISK_PER_UNIT_FOR_RISK_SIZING"
            return 0.0, metadata
        qty = ((account_equity if account_equity is not None else cash) * float(sizing.value)) / risk_per_unit
        metadata["resolved_risk_amount"] = (account_equity if account_equity is not None else cash) * float(sizing.value)
        metadata["resolved_quantity"] = qty
        return qty, metadata
    else:
        raise ValueError(f"unsupported position sizing mode: {sizing.mode}")
    metadata = {
        "position_sizing_source": "ENGINE_CONFIG",
        "position_sizing_mode": sizing.mode.value,
        "position_sizing_value": sizing.value,
        "entry_sizing_price_policy": _ENTRY_SIZING_PRICE_POLICY,
        "entry_sizing_execution_price": raw_price,
        "entry_sizing_candle_close": close,
        "entry_sizing_valuation_price": valuation_price,
    }
    if valuation_price != raw_price:
        metadata["conservative_entry_sizing_applied"] = True
    return qty, metadata


def _resolve_exit_quantity(action: StrategyAction, position: float, cfg: StrategyEngineConfig) -> tuple[float, dict[str, object], str | None]:
    mode = action.quantity_mode
    if not isinstance(mode, StrategyQuantityMode):
        mode = StrategyQuantityMode(str(mode).upper())
    raw_quantity = float(action.quantity if action.quantity is not None else cfg.trade_quantity)
    metadata: dict[str, object] = {
        "quantity_mode": mode.value,
        "requested_quantity": raw_quantity,
    }
    if mode is StrategyQuantityMode.POSITION_RATIO:
        metadata["quantity_ratio"] = raw_quantity
        if raw_quantity < 0.0 or raw_quantity > 1.0:
            metadata["block_reason"] = "INVALID_EXIT_QUANTITY_RATIO"
            return 0.0, metadata, "INVALID_EXIT_QUANTITY_RATIO"
        resolved = abs(position) * raw_quantity
        metadata["resolved_quantity"] = resolved
        return resolved, metadata, None
    metadata["resolved_quantity"] = raw_quantity
    return raw_quantity, metadata, None


def _action_risk_per_unit(action: StrategyAction) -> float | None:
    if not isinstance(action.metadata, dict):
        return None
    raw = action.metadata.get("risk_per_unit")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not isfinite(value):
        return None
    return value


def _entry_guardrail_decision(
    cfg: StrategyEngineConfig,
    guard_state: dict[str, object],
    current_drawdown: float,
) -> tuple[str | None, dict[str, object]]:
    guardrails = cfg.guardrails
    metadata = {"guardrail_scope": "backtest_only"}
    if guardrails.max_account_drawdown is not None and current_drawdown <= -float(guardrails.max_account_drawdown):
        metadata.update({"current_drawdown": current_drawdown, "max_account_drawdown": guardrails.max_account_drawdown})
        return "RISK_GUARD_MAX_DRAWDOWN", metadata
    consecutive_losses = int(guard_state.get("consecutive_losses", 0))
    if guardrails.max_consecutive_losses is not None and consecutive_losses >= guardrails.max_consecutive_losses:
        metadata.update({"consecutive_losses": consecutive_losses, "max_consecutive_losses": guardrails.max_consecutive_losses})
        return "RISK_GUARD_MAX_CONSECUTIVE_LOSSES", metadata
    if guardrails.max_daily_loss is not None:
        daily = guard_state.get("daily_realized_pnl", {})
        if isinstance(daily, dict):
            worst_daily = min(daily.values(), default=0.0)
            if worst_daily <= -float(guardrails.max_daily_loss):
                metadata.update({"worst_daily_realized_pnl": worst_daily, "max_daily_loss": guardrails.max_daily_loss})
                return "RISK_GUARD_MAX_DAILY_LOSS", metadata
    return None, {}


def _update_guard_state(guard_state: dict[str, object], execution: StrategyExecution) -> None:
    if execution.quantity <= 0 or execution.gross_pnl is None:
        return
    net = float(execution.net_pnl or 0.0)
    guard_state["consecutive_losses"] = int(guard_state.get("consecutive_losses", 0)) + 1 if net < 0 else 0
    day_key = str(pd.Timestamp(execution.timestamp).date()) if not isinstance(execution.timestamp, (int, float)) else "numeric"
    daily = guard_state.setdefault("daily_realized_pnl", {})
    if isinstance(daily, dict):
        daily[day_key] = float(daily.get(day_key, 0.0)) + net


def _blocked_exit_quantity(cash, position, avg_entry, close, action, cfg, reason, quantity_metadata):
    side = execution_side_for_action(action.action_type) or ("BUY" if position < 0 else "SELL")
    position_side = position_side_for_action(action.action_type)
    execution = _execution_record(
        action,
        side,
        position_side,
        close,
        close,
        0.0,
        cash,
        position,
        cash + (position * close),
        reason=reason,
        extra_metadata=quantity_metadata,
        account_state=_account_state(cash, position, close, avg_entry, cfg),
    )
    return cash, position, avg_entry, execution, 0.0


def _apply_entry_affordability(
    available_cash: float,
    raw_price: float,
    qty: float,
    side: str,
    cfg: StrategyEngineConfig,
    *,
    required_cash: float,
    reason: str,
    policy: InsufficientFundsPolicy,
    required_margin: float | None = None,
    volatility_bps: float | None = None,
):
    metadata: dict[str, object] = {
        "entry_affordability_policy": policy.value,
        "required_cash": required_cash,
        "available_cash": available_cash,
    }
    if required_margin is not None:
        metadata["required_initial_margin"] = required_margin
        metadata["simulated_margin_leverage"] = cfg.simulated_margin.leverage
    if required_cash <= available_cash:
        return qty, _cost(raw_price, qty, side, cfg, volatility_bps=volatility_bps), None, metadata
    if policy is InsufficientFundsPolicy.BLOCK:
        metadata["block_reason"] = reason
        return qty, _cost(raw_price, qty, side, cfg, volatility_bps=volatility_bps), reason, metadata
    per_unit_required = required_cash / max(qty, 1e-12)
    resized_qty = available_cash / per_unit_required if per_unit_required > 0 else 0.0
    if resized_qty <= 0:
        metadata["block_reason"] = reason
        return qty, _cost(raw_price, qty, side, cfg, volatility_bps=volatility_bps), reason, metadata
    resized_cost = _cost(raw_price, resized_qty, side, cfg, volatility_bps=volatility_bps)
    metadata.update(
        {
            "resize_reason": reason,
            "requested_quantity": qty,
            "filled_quantity": resized_qty,
            "requested_required_cash": required_cash,
            "resized_required_cash": available_cash,
        }
    )
    if required_margin is not None:
        metadata["required_initial_margin"] = cfg.simulated_margin.required_initial_margin(resized_cost.effective_price * resized_qty)
    return resized_qty, resized_cost, None, metadata


def _cost(raw_price, qty, side, cfg, *, volatility_bps=None):
    if cfg.transaction_cost_config is None:
        class _C: pass
        c = _C(); c.fee_cost = 0.0; c.spread_cost = 0.0; c.slippage_cost = 0.0; c.total_cost = 0.0; c.effective_price = raw_price; c.effective_slippage_bps = 0.0; c.volatility_bps = volatility_bps
        return c
    return calculate_transaction_cost(raw_price, qty, CostExecutionSide(side), cfg.default_liquidity_role, cfg.transaction_cost_config, volatility_bps=volatility_bps)



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

def _account_state(cash_after: float, position_after: float, mark_price: float, avg_entry: float, cfg: StrategyEngineConfig, *, equity_semantics: str | None = None) -> dict[str, object]:
    equity_after = cash_after + (position_after * mark_price)
    if position_after < 0:
        short_proceeds_locked = abs(position_after) * avg_entry
        short_collateral_locked = 0.0
        margin_used = 0.0
        if cfg.short_exposure_mode is ShortExposureMode.SIMULATED_MARGIN and cfg.simulated_margin.enabled:
            margin_used = cfg.simulated_margin.required_initial_margin(short_proceeds_locked)
            semantics = "cash_after is cash balance including short-sale proceeds; free_cash_after excludes locked proceeds and simulated initial margin"
        else:
            short_collateral_locked = short_proceeds_locked
            semantics = "cash_after is cash balance including short-sale proceeds; free_cash_after excludes locked proceeds and cash-bounded short collateral"
        free_cash = cash_after - short_proceeds_locked - short_collateral_locked - margin_used
    elif position_after > 0:
        short_proceeds_locked = 0.0
        short_collateral_locked = 0.0
        margin_used = 0.0
        free_cash = cash_after
        semantics = "cash_after is cash balance; equity_after includes long position market value"
    else:
        short_proceeds_locked = 0.0
        short_collateral_locked = 0.0
        margin_used = 0.0
        free_cash = cash_after
        semantics = "cash_after equals free_cash_after when flat"
    return {
        "free_cash_after": free_cash,
        "margin_used_after": margin_used,
        "short_proceeds_locked_after": short_proceeds_locked,
        "short_collateral_locked_after": short_collateral_locked,
        "available_buying_power_after": max(0.0, free_cash),
        "cash_after_semantics": semantics,
        "equity_after": equity_after,
        "equity_after_semantics": equity_semantics or _CANDLE_CLOSE_EQUITY_SEMANTICS,
    }


def _candle_volatility_bps(candle: pd.Series) -> float | None:
    try:
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])
    except (KeyError, TypeError, ValueError):
        return None
    if close <= 0:
        return None
    return max(0.0, ((high - low) / close) * 10_000.0)


def _zero_transaction_cost_assumption(cfg: StrategyEngineConfig) -> bool:
    cost = cfg.transaction_cost_config
    if cost is None:
        return True
    return (
        cost.maker_fee_bps == 0
        and cost.taker_fee_bps == 0
        and cost.spread_bps == 0
        and cost.slippage_bps == 0
        and cost.minimum_slippage_bps == 0
        and cost.volatility_slippage_multiplier == 0
    )


def _execution_record(action, side, position_side, raw_price, effective_price, qty, cash_after, position_after, equity_after, reason=None, gross=None, net=None, cost=None, extra_metadata=None, account_state=None, execution_equity_after=None):
    metadata = dict(action.metadata) if isinstance(action.metadata, dict) else {}
    if extra_metadata:
        metadata.update(extra_metadata)
    if cost:
        metadata["effective_slippage_bps"] = getattr(cost, "effective_slippage_bps", 0.0)
        if getattr(cost, "volatility_bps", None) is not None:
            metadata["volatility_bps"] = getattr(cost, "volatility_bps")
    account_state = account_state or {}
    return StrategyExecution(
        timestamp=action.timestamp,
        side=side,
        action_type=action.action_type.value,
        position_signal=position_signal_for_action(action.action_type),
        execution_side=execution_side_for_action(action.action_type),
        position_side=position_side,
        price=effective_price,
        raw_price=raw_price,
        effective_price=effective_price,
        quantity=qty,
        notional=effective_price * qty,
        cash_after=cash_after,
        cash_balance_after=cash_after,
        position_after=position_after,
        equity_after=equity_after,
        execution_equity_after=execution_equity_after if execution_equity_after is not None else cash_after + (position_after * effective_price),
        mark_to_market_equity_after=equity_after,
        free_cash_after=account_state.get("free_cash_after"),
        margin_used_after=account_state.get("margin_used_after"),
        short_proceeds_locked_after=account_state.get("short_proceeds_locked_after"),
        short_collateral_locked_after=account_state.get("short_collateral_locked_after"),
        available_buying_power_after=account_state.get("available_buying_power_after"),
        cash_after_semantics=account_state.get("cash_after_semantics"),
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


def _validate_candles(frame: pd.DataFrame, cfg: StrategyEngineConfig) -> None:
    validate_standard_candles(
        frame,
        CandleValidationConfig(
            interval=cfg.interval,
            enforce_continuity=cfg.enforce_candle_continuity,
            allow_empty=True,
            context="Strategy engine candle data",
        ),
    )
