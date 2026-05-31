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
    is_zero_transaction_cost_config,
    transaction_cost_profile_metadata,
)
from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES, break_even_cost_bps
from quant_bitcoin.backtesting.performance_metrics import (
    calculate_performance_metrics,
    calculate_trade_attribution_metrics,
)
from quant_bitcoin.backtesting.performance_diagnostics import calculate_backtest_performance_diagnostics
from quant_bitcoin.backtesting.timing_diagnostics import calculate_trade_timing_diagnostics
from quant_bitcoin.backtesting.risk_exit_audit import calculate_risk_exit_audit
from quant_bitcoin.backtesting.score_calibration import calculate_score_calibration_diagnostics
from quant_bitcoin.backtesting.sizing import (
    BacktestGuardrailConfig,
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    SizingRiskSource,
    ShortExposureMode,
    ShortEconomicsConfig,
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
from quant_bitcoin.indicators.market_regime import (
    PatternRegimeThresholdConfig,
    evaluate_pattern_regime_thresholds,
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
    "entry-candle execution-price equity using raw fill price; subsequent candles use candle-close mark-to-market"
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
    pattern_regime_thresholds: PatternRegimeThresholdConfig | None = None
    strict_zero_cost_1m_pattern_runs: bool = False
    include_cost_sensitivity_report: bool = False
    short_economics: ShortEconomicsConfig | None = None
    strict_fill_adjusted_risk_sizing: bool = True

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
        if self.pattern_regime_thresholds is not None and not isinstance(self.pattern_regime_thresholds, PatternRegimeThresholdConfig):
            raise ValueError("pattern_regime_thresholds must be a PatternRegimeThresholdConfig when provided")
        short_economics = self.short_economics or ShortEconomicsConfig()
        if not isinstance(short_economics, ShortEconomicsConfig):
            raise ValueError("short_economics must be a ShortEconomicsConfig")
        object.__setattr__(self, "position_sizing", sizing)
        object.__setattr__(self, "short_exposure_mode", short_mode)
        object.__setattr__(self, "simulated_margin", margin)
        object.__setattr__(self, "guardrails", guardrails)
        object.__setattr__(self, "short_economics", short_economics)


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
    _validate_cost_failsafe(cfg, actions)

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
    previous_timestamp: Any | None = None
    total_short_borrow_cost = 0.0
    total_short_funding_cost = 0.0
    total_short_carrying_cost = 0.0
    short_funding_event_count = 0
    short_liquidation_events: list[dict[str, object]] = []
    minimum_short_liquidation_buffer_ratio: float | None = None

    equity_points: list[StrategyEquityPoint] = []

    for _, candle in frame.iterrows():
        timestamp = candle["timestamp"]
        close = float(candle["close"])
        volatility_bps = _candle_volatility_bps(candle)
        if position < 0 and previous_timestamp is not None:
            carry = _short_carrying_cost(
                cfg,
                position,
                close,
                _elapsed_days(previous_timestamp, timestamp, cfg.interval),
            )
            if carry["total_cost"] > 0:
                cash -= carry["total_cost"]
                realized_pnl -= carry["total_cost"]
                total_short_borrow_cost += carry["borrow_cost"]
                total_short_funding_cost += carry["funding_cost"]
                total_short_carrying_cost += carry["total_cost"]
                if carry["funding_cost"] > 0:
                    short_funding_event_count += 1
        current_equity = cash + (position * close)
        current_drawdown = 0.0 if peak_equity == 0 else (current_equity - peak_equity) / peak_equity
        entry_equity_mark_price: float | None = None
        for action in actions_by_ts.get(timestamp, []):
            action = _action_with_regime_metadata(
                action,
                cfg.market_regime_by_timestamp.get(timestamp)
                if cfg.market_regime_by_timestamp
                else None,
                cfg.pattern_regime_thresholds,
            )
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
                entry_equity_mark_price = float(execution.raw_price or execution.price)

        forced_exit = _apply_forced_guardrail_exit(
            cash,
            position,
            avg_entry,
            close,
            timestamp,
            cfg,
            peak_equity,
            guard_state,
            volatility_bps=volatility_bps,
        )
        if forced_exit is not None:
            cash, position, avg_entry, execution, realized_delta = forced_exit
            realized_pnl += realized_delta
            executions.append(execution)
            _update_guard_state(guard_state, execution)
            entry_equity_mark_price = None

        equity_valuation_price = entry_equity_mark_price if position != 0.0 and entry_equity_mark_price is not None else close
        equity_semantics = _ENTRY_EXECUTION_EQUITY_SEMANTICS if equity_valuation_price != close else _CANDLE_CLOSE_EQUITY_SEMANTICS
        equity = cash + (position * equity_valuation_price)
        liquidation_diagnostic = _short_liquidation_diagnostic(
            cfg,
            timestamp,
            candle,
            cash,
            position,
            avg_entry,
        )
        if liquidation_diagnostic is not None:
            buffer_ratio = liquidation_diagnostic.get("buffer_ratio")
            if buffer_ratio is not None:
                ratio = float(buffer_ratio)
                minimum_short_liquidation_buffer_ratio = (
                    ratio
                    if minimum_short_liquidation_buffer_ratio is None
                    else min(minimum_short_liquidation_buffer_ratio, ratio)
                )
            if liquidation_diagnostic.get("would_liquidate"):
                short_liquidation_events.append(liquidation_diagnostic)
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
                short_carrying_cost_cumulative=total_short_carrying_cost,
                short_would_liquidate=(
                    bool(liquidation_diagnostic["would_liquidate"])
                    if liquidation_diagnostic is not None
                    else False
                ),
                short_liquidation_buffer_ratio=(
                    float(liquidation_diagnostic["buffer_ratio"])
                    if liquidation_diagnostic is not None
                    and liquidation_diagnostic.get("buffer_ratio") is not None
                    else None
                ),
            )
        )
        previous_timestamp = timestamp

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
    total_notional = sum(e.notional for e in executions)
    gross_pnl_total = sum(e.gross_pnl for e in executions if e.gross_pnl is not None)
    net_pnl_total = gross_pnl_total - total_cost - total_short_carrying_cost
    win_count = len([e for e in closing_execs if (e.net_pnl or 0.0) > 0])
    loss_count = len([e for e in closing_execs if (e.net_pnl or 0.0) < 0])
    short_closing_execs = [e for e in closing_execs if e.position_side == "SHORT"]
    skipped_action_count = len([a for a in actions if a.action_type == StrategyActionType.SKIP])
    blocked_action_count = len([e for e in executions if e.quantity == 0 and e.reason])
    entry_count = len([e for e in filled_execs if e.action_type in (StrategyActionType.ENTER_LONG.value, StrategyActionType.ENTER_SHORT.value)])
    exit_count = len([e for e in filled_execs if e.gross_pnl is not None])
    partial_exit_count = len([e for e in filled_execs if e.action_type in (StrategyActionType.PARTIAL_EXIT_LONG.value, StrategyActionType.PARTIAL_EXIT_SHORT.value)])
    full_exit_count = len([e for e in filled_execs if e.action_type in (StrategyActionType.EXIT_LONG.value, StrategyActionType.EXIT_SHORT.value)])

    zero_cost = _zero_transaction_cost_assumption(cfg)
    pattern_run = _actions_include_pattern(actions)
    zero_cost_warning = _zero_cost_warning(cfg, pattern_run)
    summary_metadata = {
        "gross_pnl": gross_pnl_total,
        "net_pnl": net_pnl_total,
        "transaction_cost": {
            "maker_fee_bps": cfg.transaction_cost_config.maker_fee_bps if cfg.transaction_cost_config else 0.0,
            "taker_fee_bps": cfg.transaction_cost_config.taker_fee_bps if cfg.transaction_cost_config else 0.0,
            "spread_bps": cfg.transaction_cost_config.spread_bps if cfg.transaction_cost_config else 0.0,
            "slippage_bps": cfg.transaction_cost_config.slippage_bps if cfg.transaction_cost_config else 0.0,
            "minimum_slippage_bps": cfg.transaction_cost_config.minimum_slippage_bps if cfg.transaction_cost_config else 0.0,
            "volatility_slippage_multiplier": cfg.transaction_cost_config.volatility_slippage_multiplier if cfg.transaction_cost_config else 0.0,
            "default_liquidity_role": cfg.default_liquidity_role.value,
            "zero_transaction_cost_assumption": zero_cost,
            "volatility_slippage_source": "candle high-low range divided by close, in basis points",
        },
        "cost_profile": transaction_cost_profile_metadata(cfg.transaction_cost_config),
        "cost_summary": {
            "total_fee_cost": total_fee_cost,
            "total_spread_cost": total_spread_cost,
            "total_slippage_cost": total_slippage_cost,
            "total_cost": total_cost,
            "gross_pnl": gross_pnl_total,
            "net_pnl": net_pnl_total,
            "short_carrying_cost": total_short_carrying_cost,
            "cost_to_gross_pnl_ratio": None if gross_pnl_total == 0 else total_cost / abs(gross_pnl_total),
            "zero_transaction_cost_assumption": zero_cost,
            "zero_cost_warning": zero_cost_warning,
            "diagnostic_severity": "HIGH" if zero_cost_warning else None,
            "volatility_slippage_source": "candle high-low range divided by close, in basis points",
        },
        "limitations": _short_economics_limitations(cfg),
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
                "borrow_fees": bool(cfg.short_economics.enabled),
                "futures_funding": bool(cfg.short_economics.enabled),
                "maintenance_margin": bool(cfg.short_economics.enabled),
                "liquidation": bool(cfg.short_economics.enabled),
                "initial_margin": cfg.short_exposure_mode is ShortExposureMode.SIMULATED_MARGIN and cfg.simulated_margin.enabled,
            },
            "unsupported_economics": _short_economics_unsupported_items(cfg),
        },
        "short_economics": _short_economics_summary(
            cfg,
            total_borrow_cost=total_short_borrow_cost,
            total_funding_cost=total_short_funding_cost,
            total_carrying_cost=total_short_carrying_cost,
            funding_event_count=short_funding_event_count,
            liquidation_events=short_liquidation_events,
            minimum_buffer_ratio=minimum_short_liquidation_buffer_ratio,
        ),
        "simulated_margin": cfg.simulated_margin.to_metadata(),
        "guardrails": cfg.guardrails.to_metadata(),
        "pattern_regime_thresholds": (
            cfg.pattern_regime_thresholds.to_metadata()
            if cfg.pattern_regime_thresholds is not None
            else {"schema_version": "pattern_regime_thresholds_v1", "enabled": False}
        ),
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
            "short_carrying_cost": total_short_carrying_cost,
            "max_drawdown": min([p.drawdown for p in equity_points], default=0.0),
        },
        "performance_metrics": calculate_performance_metrics(
            equity_points,
            interval=cfg.interval,
            risk_free_rate=cfg.risk_free_rate,
        ).to_metadata(),
        "trade_attribution": calculate_trade_attribution_metrics(executions, equity_points),
    }
    if cfg.include_cost_sensitivity_report:
        summary_metadata["cost_sensitivity_report"] = _cost_sensitivity_report(
            gross_pnl_total,
            total_notional,
        )
    summary_metadata["timing_diagnostics"] = calculate_trade_timing_diagnostics(
        executions,
        frame,
    )
    summary_metadata["risk_exit_audit"] = calculate_risk_exit_audit(
        executions,
        summary_metadata,
    )
    summary_metadata["score_calibration"] = calculate_score_calibration_diagnostics(
        executions,
        summary_metadata,
    )
    summary_metadata["performance_diagnostics"] = calculate_backtest_performance_diagnostics(
        summary_metadata,
        executions,
        equity_points,
    )

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
        metadata=summary_metadata,
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
        regime_decision = (
            action.metadata.get("pattern_regime_thresholds")
            if isinstance(action.metadata, dict)
            else None
        )
        if isinstance(regime_decision, dict) and regime_decision.get("blocked"):
            side = execution_side_for_action(action_type) or "BUY"
            position_side = position_side_for_action(action_type)
            reason = str(regime_decision.get("block_reason") or "REGIME_ENTRY_BLOCKED")
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
                account_state=_account_state(cash, position, close, avg_entry, cfg),
            )
            return cash, position, avg_entry, execution, 0.0
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
        return _open_position(
            cash,
            close,
            qty,
            action,
            cfg,
            explicit_price=explicit_price,
            sizing_metadata=sizing_metadata,
            volatility_bps=volatility_bps,
            account_equity=account_equity,
        )

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
    threshold_config: PatternRegimeThresholdConfig | None = None,
) -> StrategyAction:
    if not regime_context and threshold_config is None:
        return action
    metadata = dict(action.metadata) if isinstance(action.metadata, dict) else {}
    clean_context = (
        {key: value for key, value in regime_context.items() if value is not None}
        if regime_context
        else {}
    )
    for key in (
        "market_regime",
        "volatility_regime",
        "liquidity_regime",
        "spread_regime",
        "trend_regime",
        "mean_reversion_regime",
        "session_tag",
        "weekday_tag",
        "trading_value_percentile",
        "liquidity_zscore",
        "range_spread_proxy_percentile",
        "wick_dominance_proxy",
    ):
        if key in clean_context:
            metadata.setdefault(key, clean_context[key])
    if "session_tag" in clean_context:
        metadata.setdefault("session", clean_context["session_tag"])
        metadata.setdefault("market_session", clean_context["session_tag"])
    if clean_context:
        metadata.setdefault("market_regime_context", clean_context)
    decision = evaluate_pattern_regime_thresholds(
        metadata,
        clean_context,
        threshold_config,
    )
    if decision["enabled"]:
        metadata["pattern_regime_thresholds"] = decision
    return replace(action, metadata=metadata)


def _open_position(cash, close, qty, action, cfg, *, explicit_price=None, sizing_metadata=None, volatility_bps=None, account_equity=None):
    is_short = action.action_type == StrategyActionType.ENTER_SHORT
    side = "SELL" if is_short else "BUY"
    requested_qty = qty
    raw_price = explicit_price if explicit_price is not None else close
    cost = _cost(raw_price, qty, side, cfg, volatility_bps=volatility_bps)
    effective_price = cost.effective_price
    notional = raw_price * qty
    reason = None
    extra_metadata = dict(sizing_metadata or {})
    extra_metadata["requested_quantity"] = requested_qty
    qty, cost, exposure_reason, exposure_metadata = _apply_entry_exposure_caps(
        qty,
        raw_price,
        side,
        cfg,
        account_equity=account_equity if account_equity is not None else cash,
        volatility_bps=volatility_bps,
    )
    extra_metadata.update(exposure_metadata)
    if exposure_reason is not None:
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
            reason=exposure_reason,
            extra_metadata=extra_metadata,
            account_state=account_state,
        )
        return cash, 0.0, 0.0, execution, 0.0
    notional = raw_price * qty
    if not is_short:
        qty, cost, reason, affordability_metadata = _apply_entry_affordability(
            cash,
            raw_price,
            qty,
            side,
            cfg,
            required_cash=notional + cost.total_cost,
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
            required_cash=notional + cost.total_cost,
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
            required_cash=required_margin + cost.total_cost,
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
    notional = raw_price * qty
    signed_qty = -qty if is_short else qty
    extra_metadata["filled_quantity"] = qty
    if requested_qty != qty:
        extra_metadata["quantity_was_resized"] = True

    cash_after = cash + notional - cost.total_cost if is_short else cash - notional - cost.total_cost
    position_after = signed_qty
    avg_entry_after = raw_price
    equity_after = cash_after + (position_after * close)
    execution_equity_after = cash_after + (position_after * raw_price)
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
        extra_metadata=extra_metadata | _cost_metadata(cost, cfg, raw_price=raw_price, quantity=qty),
        account_state=_account_state(cash_after, position_after, close, avg_entry_after, cfg),
        execution_equity_after=execution_equity_after,
    )
    return cash_after, position_after, avg_entry_after, execution, -float(cost.total_cost)


def _close_position(cash, position, avg_entry, close, qty, action, cfg, *, explicit_price=None, quantity_metadata=None, volatility_bps=None):
    close_qty = min(abs(position), qty)
    is_short = position < 0
    side = "BUY" if is_short else "SELL"
    raw_price = explicit_price if explicit_price is not None else close
    cost = _cost(raw_price, close_qty, side, cfg, volatility_bps=volatility_bps)
    effective_price = cost.effective_price
    notional = raw_price * close_qty
    cash_after = cash - notional - cost.total_cost if is_short else cash + notional - cost.total_cost
    if is_short:
        gross = (avg_entry - raw_price) * close_qty
        position_after = position + close_qty
    else:
        gross = (raw_price - avg_entry) * close_qty
        position_after = position - close_qty
    net = gross - cost.total_cost
    avg_entry_after = 0.0 if position_after == 0 else avg_entry
    equity_after = cash_after + (position_after * close)
    execution_equity_after = cash_after + (position_after * raw_price)
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
        extra_metadata=dict(quantity_metadata or {}) | _cost_metadata(cost, cfg, raw_price=raw_price, quantity=close_qty),
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
            "sizing_risk_source": SizingRiskSource.ACTION_OVERRIDE.value,
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
        risk_per_unit, risk_metadata, risk_block_reason = _resolve_sizing_risk(action, cfg)
        metadata = {
            "position_sizing_source": "ENGINE_CONFIG",
            "position_sizing_mode": sizing.mode.value,
            "position_sizing_value": sizing.value,
            "risk_per_unit": risk_per_unit,
            "account_equity_for_risk_sizing": account_equity if account_equity is not None else cash,
            **risk_metadata,
        }
        if risk_block_reason is not None:
            metadata["block_reason"] = risk_block_reason
            return 0.0, metadata
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


def _resolve_sizing_risk(
    action: StrategyAction,
    cfg: StrategyEngineConfig,
) -> tuple[float | None, dict[str, object], str | None]:
    metadata = action.metadata if isinstance(action.metadata, dict) else {}
    risk_per_unit = _metadata_float(metadata.get("risk_per_unit"))
    fill_adjusted = _metadata_float(metadata.get("fill_adjusted_risk_per_unit"))
    original = _metadata_float(metadata.get("original_risk_per_unit"))
    pattern_entry = _is_pattern_entry_action(action)

    if not pattern_entry:
        source = (
            SizingRiskSource.ACTION_OVERRIDE.value
            if risk_per_unit is not None and risk_per_unit > 0
            else SizingRiskSource.MISSING.value
        )
        return risk_per_unit, {"sizing_risk_source": source}, None

    base_metadata: dict[str, object] = {
        "strict_fill_adjusted_risk_sizing": cfg.strict_fill_adjusted_risk_sizing,
    }
    if fill_adjusted is not None:
        base_metadata["fill_adjusted_risk_per_unit"] = fill_adjusted
    if original is not None:
        base_metadata["original_risk_per_unit"] = original

    if risk_per_unit is None:
        base_metadata["sizing_risk_source"] = SizingRiskSource.MISSING.value
        return None, base_metadata, "MISSING_RISK_PER_UNIT_FOR_RISK_SIZING"
    if risk_per_unit <= 0:
        base_metadata["sizing_risk_source"] = SizingRiskSource.MISSING.value
        return risk_per_unit, base_metadata, "INVALID_RISK_PER_UNIT_FOR_RISK_SIZING"

    if fill_adjusted is not None and fill_adjusted > 0:
        if not _numbers_equal(risk_per_unit, fill_adjusted):
            base_metadata["sizing_risk_source"] = SizingRiskSource.ORIGINAL_REFERENCE.value
            base_metadata["stale_risk_per_unit"] = risk_per_unit
            return risk_per_unit, base_metadata, "STALE_RISK_PER_UNIT_FOR_RISK_SIZING"
        base_metadata["sizing_risk_source"] = SizingRiskSource.FILL_ADJUSTED.value
        return risk_per_unit, base_metadata, None

    if original is not None or metadata.get("sizing_risk_source") == SizingRiskSource.ORIGINAL_REFERENCE.value:
        base_metadata["sizing_risk_source"] = SizingRiskSource.ORIGINAL_REFERENCE.value
        if cfg.strict_fill_adjusted_risk_sizing:
            return risk_per_unit, base_metadata, "STALE_RISK_PER_UNIT_FOR_RISK_SIZING"
        return risk_per_unit, base_metadata, None

    base_metadata["sizing_risk_source"] = SizingRiskSource.MISSING.value
    return risk_per_unit, base_metadata, "MISSING_FILL_ADJUSTED_RISK_FOR_PATTERN_SIZING"


def _metadata_float(raw: object) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not isfinite(value):
        return None
    return value


def _is_pattern_entry_action(action: StrategyAction) -> bool:
    if action.action_type not in (StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT):
        return False
    if not isinstance(action.metadata, dict):
        return False
    metadata = action.metadata
    return bool(
        metadata.get("canonical_pattern_action")
        or metadata.get("pattern_entry_policy") is not None
        or metadata.get("pattern_type") is not None
        or metadata.get("pattern_event_id") is not None
    )


def _numbers_equal(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) < 1e-12


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


def _apply_forced_guardrail_exit(
    cash: float,
    position: float,
    avg_entry: float,
    close: float,
    timestamp: Any,
    cfg: StrategyEngineConfig,
    peak_equity: float,
    guard_state: dict[str, object],
    *,
    volatility_bps: float | None = None,
):
    if not cfg.guardrails.close_open_position_on_breach or position == 0:
        return None
    equity = cash + (position * close)
    current_drawdown = 0.0 if peak_equity == 0 else (equity - peak_equity) / peak_equity
    reason, guard_metadata = _entry_guardrail_decision(cfg, guard_state, current_drawdown)
    if reason is None:
        return None
    action_type = StrategyActionType.EXIT_LONG if position > 0 else StrategyActionType.EXIT_SHORT
    action = StrategyAction(
        action_type=action_type,
        timestamp=timestamp,
        quantity=abs(position),
        reason=reason,
        requested_price=close,
        metadata={
            **guard_metadata,
            "exit_reason": "GUARDRAIL_FORCED_EXIT",
            "guardrail_forced_exit": True,
            "guardrail_breach_reason": reason,
            "forced_exit_price_source": "CURRENT_CANDLE_CLOSE",
            "forced_exit_generated_by": "BACKTEST_GUARDRAIL",
            "strategy_exit": False,
            "guardrail_scope": "backtest_only",
        },
    )
    return _close_position(
        cash,
        position,
        avg_entry,
        close,
        abs(position),
        action,
        cfg,
        explicit_price=close,
        volatility_bps=volatility_bps,
    )


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
        metadata["required_initial_margin"] = cfg.simulated_margin.required_initial_margin(raw_price * resized_qty)
    return resized_qty, resized_cost, None, metadata


def _apply_entry_exposure_caps(
    qty: float,
    raw_price: float,
    side: str,
    cfg: StrategyEngineConfig,
    *,
    account_equity: float,
    volatility_bps: float | None = None,
):
    cost = _cost(raw_price, qty, side, cfg, volatility_bps=volatility_bps)
    notional = raw_price * qty
    guardrails = cfg.guardrails
    caps: list[tuple[float, str, str]] = []
    if guardrails.max_position_notional is not None:
        caps.append((float(guardrails.max_position_notional), "RISK_GUARD_MAX_POSITION_NOTIONAL", "max_position_notional"))
    if guardrails.max_symbol_notional is not None:
        caps.append((float(guardrails.max_symbol_notional), "RISK_GUARD_MAX_SYMBOL_NOTIONAL", "max_symbol_notional"))
    if guardrails.max_leverage_simulated is not None:
        leverage_cap = max(0.0, float(account_equity)) * float(guardrails.max_leverage_simulated)
        caps.append((leverage_cap, "RISK_GUARD_MAX_LEVERAGE_SIMULATED", "max_leverage_simulated_notional"))
    if not caps:
        return qty, cost, None, {"entry_exposure_cap_applied": False}

    cap_value, reason, cap_name = min(caps, key=lambda item: item[0])
    metadata: dict[str, object] = {
        "entry_exposure_cap_applied": notional > cap_value,
        "entry_exposure_cap_policy": cfg.position_sizing.insufficient_funds_policy.value,
        "entry_exposure_requested_notional": notional,
        "entry_exposure_cap_notional": cap_value,
        "entry_exposure_cap_name": cap_name,
    }
    if notional <= cap_value:
        return qty, cost, None, metadata

    if cfg.position_sizing.insufficient_funds_policy is InsufficientFundsPolicy.BLOCK:
        metadata["block_reason"] = reason
        return qty, cost, reason, metadata

    resized_qty = cap_value / raw_price if raw_price > 0 else 0.0
    if resized_qty <= 0:
        metadata["block_reason"] = reason
        return qty, cost, reason, metadata
    resized_cost = _cost(raw_price, resized_qty, side, cfg, volatility_bps=volatility_bps)
    metadata.update(
        {
            "resize_reason": reason,
            "requested_quantity_before_exposure_cap": qty,
            "filled_quantity_after_exposure_cap": resized_qty,
            "resized_notional_after_exposure_cap": raw_price * resized_qty,
        }
    )
    return resized_qty, resized_cost, None, metadata


def _cost(raw_price, qty, side, cfg, *, volatility_bps=None):
    if cfg.transaction_cost_config is None:
        class _C: pass
        c = _C(); c.gross_notional = raw_price * qty; c.fee_cost = 0.0; c.spread_cost = 0.0; c.slippage_cost = 0.0; c.total_cost = 0.0; c.effective_price = raw_price; c.effective_slippage_bps = 0.0; c.volatility_bps = volatility_bps
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


def _short_carrying_cost(
    cfg: StrategyEngineConfig,
    position: float,
    mark_price: float,
    elapsed_days: float,
) -> dict[str, float]:
    economics = cfg.short_economics
    if not economics.enabled or position >= 0 or elapsed_days <= 0 or mark_price <= 0:
        return {"borrow_cost": 0.0, "funding_cost": 0.0, "total_cost": 0.0}
    notional = abs(position) * mark_price
    borrow_cost = notional * (float(economics.borrow_fee_bps_per_day) / 10_000.0) * elapsed_days
    funding_cost = notional * (float(economics.funding_bps_per_interval) / 10_000.0)
    return {
        "borrow_cost": borrow_cost,
        "funding_cost": funding_cost,
        "total_cost": borrow_cost + funding_cost,
    }


def _elapsed_days(previous_timestamp: Any, timestamp: Any, interval: str) -> float:
    if isinstance(previous_timestamp, (int, float)) and isinstance(timestamp, (int, float)):
        return _interval_days(interval)
    try:
        elapsed = (pd.Timestamp(timestamp) - pd.Timestamp(previous_timestamp)).total_seconds() / 86_400.0
    except (TypeError, ValueError):
        return _interval_days(interval)
    return elapsed if elapsed > 0 else _interval_days(interval)


def _interval_days(interval: str) -> float:
    text = str(interval).strip().lower()
    if not text:
        return 1.0 / 1440.0
    unit = text[-1]
    try:
        amount = float(text[:-1])
    except ValueError:
        amount = 1.0
    if amount <= 0:
        amount = 1.0
    if unit == "m":
        return amount / 1440.0
    if unit == "h":
        return amount / 24.0
    if unit == "d":
        return amount
    return 1.0 / 1440.0


def _short_liquidation_diagnostic(
    cfg: StrategyEngineConfig,
    timestamp: Any,
    candle: pd.Series,
    cash: float,
    position: float,
    avg_entry: float,
) -> dict[str, object] | None:
    economics = cfg.short_economics
    if not economics.enabled or position >= 0 or avg_entry <= 0:
        return None
    try:
        high = float(candle["high"])
        close = float(candle["close"])
    except (KeyError, TypeError, ValueError):
        return None
    qty = abs(position)
    maintenance_rate = float(economics.maintenance_margin_rate)
    buffer_rate = float(economics.liquidation_buffer_rate)
    threshold_multiplier = maintenance_rate * (1.0 + buffer_rate)
    equity_at_high = cash + (position * high)
    equity_at_close = cash + (position * close)
    threshold_at_high = qty * high * threshold_multiplier
    threshold_at_close = qty * close * threshold_multiplier
    estimated_liquidation_price = None
    denominator = qty * (1.0 + threshold_multiplier)
    if denominator > 0:
        estimated_liquidation_price = cash / denominator
    would_liquidate = equity_at_high <= threshold_at_high
    buffer_ratio = None
    if threshold_at_close > 0:
        buffer_ratio = (equity_at_close - threshold_at_close) / threshold_at_close
    return {
        "schema_version": "short_liquidation_diagnostic_v1",
        "timestamp": str(timestamp),
        "position_quantity": position,
        "avg_entry": avg_entry,
        "mark_close": close,
        "adverse_high": high,
        "cash_balance": cash,
        "maintenance_margin_rate": maintenance_rate,
        "liquidation_buffer_rate": buffer_rate,
        "maintenance_requirement_at_close": threshold_at_close,
        "equity_at_close": equity_at_close,
        "equity_at_adverse_high": equity_at_high,
        "estimated_liquidation_price": estimated_liquidation_price,
        "buffer_ratio": buffer_ratio,
        "would_liquidate": would_liquidate,
        "diagnostic_only": True,
    }


def _short_economics_limitations(cfg: StrategyEngineConfig) -> list[str]:
    if not cfg.short_economics.enabled:
        return [
            "No borrow fees modeled",
            "No futures funding modeled",
            "No maintenance margin or liquidation model",
        ]
    return [
        "Short economics are research-only estimates and not real spot, margin, or futures execution.",
        "Liquidation diagnostics do not auto-close positions or submit exchange orders.",
    ]


def _short_economics_unsupported_items(cfg: StrategyEngineConfig) -> list[str]:
    if not cfg.short_economics.enabled:
        return [
            "No borrow fees modeled",
            "No futures funding modeled",
            "No maintenance margin or liquidation model",
        ]
    return [
        "No exchange fee tier lookup",
        "No order-book margin call or liquidation execution",
        "No live borrow availability or funding-rate feed",
    ]


def _short_economics_summary(
    cfg: StrategyEngineConfig,
    *,
    total_borrow_cost: float,
    total_funding_cost: float,
    total_carrying_cost: float,
    funding_event_count: int,
    liquidation_events: list[dict[str, object]],
    minimum_buffer_ratio: float | None,
) -> dict[str, object]:
    economics = cfg.short_economics
    metadata = economics.to_metadata()
    enabled = bool(economics.enabled)
    metadata.update(
        {
            "scope": "backtest_only_research" if enabled else "backtest_only_simulation",
            "cash_bounded_short": cfg.short_exposure_mode is ShortExposureMode.CASH_BOUNDED,
            "simulated_margin": cfg.short_exposure_mode is ShortExposureMode.SIMULATED_MARGIN and cfg.simulated_margin.enabled,
            "borrow_fees_modeled": enabled,
            "futures_funding_modeled": enabled,
            "maintenance_margin_modeled": enabled,
            "liquidation_modeled": enabled,
            "total_borrow_cost": total_borrow_cost,
            "total_funding_cost": total_funding_cost,
            "total_carrying_cost": total_carrying_cost,
            "funding_event_count": funding_event_count,
            "liquidation_diagnostics": {
                "schema_version": "short_liquidation_diagnostics_v1",
                "enabled": enabled,
                "diagnostic_only": True,
                "would_liquidate": bool(liquidation_events),
                "event_count": len(liquidation_events),
                "events": tuple(liquidation_events),
                "minimum_buffer_ratio": minimum_buffer_ratio,
            },
            "warning": (
                "Short economics are research-only estimates; no live margin/futures execution or forced liquidation is enabled."
                if enabled
                else "Short results are simulation-only and exclude borrow fees, futures funding, maintenance margin, and liquidation."
            ),
        }
    )
    return metadata


def _zero_transaction_cost_assumption(cfg: StrategyEngineConfig) -> bool:
    return is_zero_transaction_cost_config(cfg.transaction_cost_config)


def _validate_cost_failsafe(
    cfg: StrategyEngineConfig, actions: list[StrategyAction]
) -> None:
    if (
        cfg.strict_zero_cost_1m_pattern_runs
        and cfg.interval == "1m"
        and _zero_transaction_cost_assumption(cfg)
        and _actions_include_pattern(actions)
    ):
        raise ValueError("strict cost mode blocks zero-cost 1m pattern runs")


def _actions_include_pattern(actions: list[StrategyAction]) -> bool:
    return any(
        bool(getattr(action, "metadata", None))
        and (
            action.metadata.get("pattern_type") is not None
            or action.metadata.get("event_id") is not None
            or action.metadata.get("canonical_pattern_action") is True
        )
        for action in actions
    )


def _zero_cost_warning(cfg: StrategyEngineConfig, pattern_run: bool) -> str | None:
    if _zero_transaction_cost_assumption(cfg) and cfg.interval == "1m" and pattern_run:
        return "HIGH: zero fees, spread, and slippage on a 1m pattern run can materially overstate edge."
    if _zero_transaction_cost_assumption(cfg):
        return "Zero fees, spread, and slippage are enabled; treat as debugging baseline only."
    return None


def _cost_sensitivity_report(gross_pnl: float, total_notional: float) -> dict[str, object]:
    profiles = ("zero", "binance_spot_taker_baseline", "conservative_crypto_1m", "high_slippage_stress")
    rows = []
    for key in profiles:
        profile = COST_PROFILES[key]
        cfg = profile.config
        static_bps = cfg.taker_fee_bps + cfg.spread_bps + max(cfg.slippage_bps, cfg.minimum_slippage_bps)
        estimated_cost = total_notional * (static_bps / 10_000.0)
        rows.append(
            {
                "profile_key": key,
                "static_cost_bps": static_bps,
                "estimated_total_cost": estimated_cost,
                "estimated_net_pnl": gross_pnl - estimated_cost,
                "cost_to_gross_pnl_ratio": None if gross_pnl == 0 else estimated_cost / abs(gross_pnl),
            }
        )
    return {
        "schema_version": "transaction_cost_sensitivity_report_v1",
        "profiles": tuple(rows),
        "break_even_cost_bps": break_even_cost_bps(gross_pnl, total_notional),
    }


def _cost_metadata(cost, cfg: StrategyEngineConfig, *, raw_price: float, quantity: float) -> dict[str, object]:
    config = cfg.transaction_cost_config or TransactionCostConfig()
    fee_bps = config.maker_fee_bps if cfg.default_liquidity_role is LiquidityRole.MAKER else config.taker_fee_bps
    volatility_bps = getattr(cost, "volatility_bps", None)
    effective_slippage = getattr(cost, "effective_slippage_bps", 0.0)
    cost_breakdown = {
        "schema_version": "execution_cost_breakdown_v1",
        "price_semantics": "raw_fill_price",
        "effective_price_semantics": "spread_slippage_adjusted_diagnostic_price",
        "raw_price": float(raw_price),
        "effective_price": float(getattr(cost, "effective_price", raw_price)),
        "gross_notional": float(raw_price) * float(quantity),
        "fee_cost": float(getattr(cost, "fee_cost", 0.0)),
        "spread_cost": float(getattr(cost, "spread_cost", 0.0)),
        "slippage_cost": float(getattr(cost, "slippage_cost", 0.0)),
        "total_cost": float(getattr(cost, "total_cost", 0.0)),
        "fee_bps": float(fee_bps),
        "spread_bps": float(config.spread_bps),
        "slippage_bps": float(effective_slippage),
        "configured_slippage_bps": float(config.slippage_bps),
        "effective_slippage_bps": float(effective_slippage),
        "volatility_bps": volatility_bps,
        "cost_profile_name": _cost_profile_name(config),
        "cost_currency": "quote",
        "liquidity_role": cfg.default_liquidity_role.value,
    }
    return {
        "price_semantics": "raw_fill_price",
        "effective_price_semantics": "spread_slippage_adjusted_diagnostic_price",
        "cost_breakdown": cost_breakdown,
    }


def _cost_profile_name(config: TransactionCostConfig | None) -> str:
    if is_zero_transaction_cost_config(config):
        return "zero"
    for key, profile in COST_PROFILES.items():
        if profile.config == config:
            return key
    return "manual"


def _execution_record(action, side, position_side, raw_price, effective_price, qty, cash_after, position_after, equity_after, reason=None, gross=None, net=None, cost=None, extra_metadata=None, account_state=None, execution_equity_after=None):
    metadata = dict(action.metadata) if isinstance(action.metadata, dict) else {}
    metadata.setdefault("price_semantics", "raw_fill_price")
    metadata.setdefault("effective_price_semantics", "spread_slippage_adjusted_diagnostic_price")
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
        price=raw_price,
        raw_price=raw_price,
        effective_price=effective_price,
        quantity=qty,
        notional=raw_price * qty,
        cash_after=cash_after,
        cash_balance_after=cash_after,
        position_after=position_after,
        equity_after=equity_after,
        execution_equity_after=execution_equity_after if execution_equity_after is not None else cash_after + (position_after * raw_price),
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
