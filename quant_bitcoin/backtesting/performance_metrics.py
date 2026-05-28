from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite, sqrt
from statistics import median
from typing import Any, Sequence

from quant_bitcoin.backtesting.strategy_models import StrategyEquityPoint, StrategyExecution

MINUTES_PER_YEAR = 365 * 24 * 60
INTERVAL_MINUTES: dict[str, int] = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
}


@dataclass(frozen=True)
class PerformanceMetrics:
    schema_version: str
    interval: str
    risk_free_rate: float
    period_count: int
    annualization_factor: float | None
    annualized_return: float | None
    annualized_volatility: float | None
    downside_deviation: float | None
    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None
    max_drawdown: float
    max_drawdown_duration_periods: int
    current_drawdown_duration_periods: int
    max_recovery_duration_periods: int | None
    total_return: float | None
    warnings: tuple[str, ...] = ()

    def to_metadata(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TradeLifecycleOutcome:
    entry_timestamp: Any | None
    exit_timestamp: Any | None
    position_side: str
    pattern_type: str
    pattern_direction: str
    exit_reason: str
    timeframe: str
    session: str
    market_regime: str
    liquidity_regime: str
    spread_regime: str
    weekday_tag: str
    gross_pnl: float
    net_pnl: float
    realized_r_multiple: float | None
    exit_execution_count: int
    partial_exit_execution_count: int
    duration_seconds: float | None


@dataclass(frozen=True)
class TradeMetricSummary:
    completed_trade_count: int
    closing_execution_count: int
    partial_exit_execution_count: int
    win_count: int
    loss_count: int
    breakeven_count: int
    hit_ratio: float | None
    average_win: float | None
    average_loss: float | None
    payoff_ratio: float | None
    expectancy: float | None
    gross_profit: float
    gross_loss: float
    profit_factor: float | None
    profit_factor_is_infinite: bool
    average_r: float | None
    median_r: float | None
    max_consecutive_losses: int
    average_trade_duration_seconds: float | None
    median_trade_duration_seconds: float | None


def calculate_trade_attribution_metrics(
    executions: Sequence[StrategyExecution],
    equity_points: Sequence[StrategyEquityPoint] = (),
) -> dict[str, object]:
    """Build additive trade-level analytics from completed execution lifecycles."""

    filled = [execution for execution in executions if float(execution.quantity) > 0]
    closing_executions = [execution for execution in filled if execution.net_pnl is not None]
    outcomes = _completed_trade_lifecycles(filled)
    summary = _trade_metric_summary(outcomes, len(closing_executions))
    exposure = _exposure_fraction(equity_points)
    turnover = _turnover_metrics(filled, equity_points)

    warnings: list[str] = []
    if not outcomes:
        warnings.append("no completed trade lifecycles")
    if summary.profit_factor_is_infinite:
        warnings.append("profit factor is undefined for zero gross loss and positive gross profit")

    return {
        "schema_version": "trade_attribution_metrics_v1",
        "aggregation_policy": {
            "trade_outcome_unit": "entry_to_final_exit_lifecycle",
            "partial_exit_policy": "partial exits contribute realized pnl to the open lifecycle and do not increment completed_trade_count until final exit",
            "missing_group_key": "UNKNOWN",
            "profit_factor_zero_loss_policy": "null with profit_factor_is_infinite=true when gross loss is zero and gross profit is positive",
            "exposure_policy": "point_fraction_with_nonzero_position",
            "turnover_policy": "sum_filled_notional_divided_by_initial_equity",
        },
        "trade_metrics": asdict(summary),
        "exposure": exposure,
        "turnover": turnover,
        "attribution": {
            "by_pattern_type": _grouped_attribution(outcomes, "pattern_type"),
            "by_pattern_direction": _grouped_attribution(outcomes, "pattern_direction"),
            "by_position_side": _grouped_attribution(outcomes, "position_side"),
            "by_exit_reason": _grouped_attribution(outcomes, "exit_reason"),
            "by_timeframe": _grouped_attribution(outcomes, "timeframe"),
            "by_session": _grouped_attribution(outcomes, "session"),
            "by_market_regime": _grouped_attribution(outcomes, "market_regime"),
            "by_liquidity_regime": _grouped_attribution(outcomes, "liquidity_regime"),
            "by_spread_regime": _grouped_attribution(outcomes, "spread_regime"),
            "by_weekday_tag": _grouped_attribution(outcomes, "weekday_tag"),
        },
        "warnings": tuple(warnings),
    }


def annualization_factor_for_interval(interval: str) -> float:
    if interval not in INTERVAL_MINUTES:
        supported = ", ".join(sorted(INTERVAL_MINUTES))
        raise ValueError(f"unsupported performance metric interval: {interval}; supported: {supported}")
    return MINUTES_PER_YEAR / INTERVAL_MINUTES[interval]


def period_returns_from_equity(
    equity_points: Sequence[StrategyEquityPoint],
) -> tuple[float, ...]:
    returns: list[float] = []
    ordered = list(equity_points)
    for previous, current in zip(ordered, ordered[1:], strict=False):
        previous_equity = float(previous.equity)
        current_equity = float(current.equity)
        if previous_equity == 0:
            returns.append(0.0)
            continue
        returns.append((current_equity - previous_equity) / previous_equity)
    return tuple(returns)


def calculate_performance_metrics(
    equity_points: Sequence[StrategyEquityPoint],
    *,
    interval: str = "1m",
    risk_free_rate: float = 0.0,
) -> PerformanceMetrics:
    if not isfinite(risk_free_rate):
        raise ValueError("risk_free_rate must be finite")

    warnings: list[str] = []
    try:
        annualization_factor = annualization_factor_for_interval(interval)
    except ValueError:
        annualization_factor = None
        warnings.append(f"unsupported interval for annualization: {interval}")

    points = list(equity_points)
    max_drawdown = min((float(point.drawdown) for point in points), default=0.0)
    drawdown_duration = _drawdown_duration_metrics(points)
    if len(points) < 2:
        warnings.append("insufficient equity points")
        return PerformanceMetrics(
            schema_version="performance_metrics_v1",
            interval=interval,
            risk_free_rate=float(risk_free_rate),
            period_count=0,
            annualization_factor=annualization_factor,
            annualized_return=None,
            annualized_volatility=None,
            downside_deviation=None,
            sharpe_ratio=None,
            sortino_ratio=None,
            calmar_ratio=None,
            max_drawdown=max_drawdown,
            max_drawdown_duration_periods=drawdown_duration["max_drawdown_duration_periods"],
            current_drawdown_duration_periods=drawdown_duration["current_drawdown_duration_periods"],
            max_recovery_duration_periods=drawdown_duration["max_recovery_duration_periods"],
            total_return=None,
            warnings=tuple(warnings),
        )

    returns = period_returns_from_equity(points)
    total_return = _total_return(points)
    if annualization_factor is None:
        return PerformanceMetrics(
            schema_version="performance_metrics_v1",
            interval=interval,
            risk_free_rate=float(risk_free_rate),
            period_count=len(returns),
            annualization_factor=None,
            annualized_return=None,
            annualized_volatility=None,
            downside_deviation=None,
            sharpe_ratio=None,
            sortino_ratio=None,
            calmar_ratio=None,
            max_drawdown=max_drawdown,
            max_drawdown_duration_periods=drawdown_duration["max_drawdown_duration_periods"],
            current_drawdown_duration_periods=drawdown_duration["current_drawdown_duration_periods"],
            max_recovery_duration_periods=drawdown_duration["max_recovery_duration_periods"],
            total_return=total_return,
            warnings=tuple(warnings),
        )

    annualized_return = _annualized_return(points, annualization_factor, len(returns))
    period_risk_free_rate = risk_free_rate / annualization_factor
    excess_returns = tuple(value - period_risk_free_rate for value in returns)
    volatility = _population_std(returns) * sqrt(annualization_factor)
    downside_period = _downside_deviation_period(excess_returns)
    downside_deviation = (
        downside_period * sqrt(annualization_factor)
        if downside_period is not None
        else None
    )
    mean_excess = _mean(excess_returns)

    return PerformanceMetrics(
        schema_version="performance_metrics_v1",
        interval=interval,
        risk_free_rate=float(risk_free_rate),
        period_count=len(returns),
        annualization_factor=annualization_factor,
        annualized_return=annualized_return,
        annualized_volatility=volatility,
        downside_deviation=downside_deviation,
        sharpe_ratio=(mean_excess / _population_std(excess_returns) * sqrt(annualization_factor))
        if _population_std(excess_returns) > 0
        else None,
        sortino_ratio=(mean_excess / downside_period * sqrt(annualization_factor))
        if downside_period and downside_period > 0
        else None,
        calmar_ratio=(annualized_return / abs(max_drawdown))
        if annualized_return is not None and max_drawdown < 0
        else None,
        max_drawdown=max_drawdown,
        max_drawdown_duration_periods=drawdown_duration["max_drawdown_duration_periods"],
        current_drawdown_duration_periods=drawdown_duration["current_drawdown_duration_periods"],
        max_recovery_duration_periods=drawdown_duration["max_recovery_duration_periods"],
        total_return=total_return,
        warnings=tuple(warnings),
    )


def _completed_trade_lifecycles(
    executions: Sequence[StrategyExecution],
) -> tuple[TradeLifecycleOutcome, ...]:
    open_trades: dict[str, dict[str, Any]] = {}
    completed: list[TradeLifecycleOutcome] = []
    unmatched_index = 0

    for execution in executions:
        action_type = str(execution.action_type)
        side = _known(execution.position_side)
        if action_type in ("ENTER_LONG", "ENTER_SHORT"):
            open_trades[side] = _new_open_trade(execution, side)
            continue
        if execution.net_pnl is None and execution.gross_pnl is None:
            continue
        trade = open_trades.get(side)
        if trade is None:
            unmatched_index += 1
            side = _known(execution.position_side, fallback=f"UNMATCHED_{unmatched_index}")
            trade = _new_open_trade(execution, side)
            open_trades[side] = trade
        _apply_exit_to_trade(trade, execution)
        if action_type in ("EXIT_LONG", "EXIT_SHORT") or abs(float(execution.position_after)) == 0:
            completed.append(_finalize_trade(trade))
            open_trades.pop(side, None)

    return tuple(completed)


def _new_open_trade(execution: StrategyExecution, side: str) -> dict[str, Any]:
    metadata = execution.metadata or {}
    return {
        "entry_timestamp": execution.timestamp,
        "exit_timestamp": None,
        "position_side": _known(execution.position_side, fallback=side),
        "pattern_type": _metadata_key(metadata, "pattern_type"),
        "pattern_direction": _metadata_key(metadata, "pattern_direction"),
        "timeframe": _metadata_key(metadata, "timeframe", "interval"),
        "session": _metadata_key(metadata, "session", "market_session", "session_tag"),
        "market_regime": _metadata_key(metadata, "market_regime", "regime"),
        "liquidity_regime": _metadata_key(metadata, "liquidity_regime"),
        "spread_regime": _metadata_key(metadata, "spread_regime"),
        "weekday_tag": _metadata_key(metadata, "weekday_tag"),
        "gross_pnl": 0.0,
        "net_pnl": -float(execution.total_cost or 0.0),
        "r_values": [],
        "exit_reasons": [],
        "exit_execution_count": 0,
        "partial_exit_execution_count": 0,
    }


def _apply_exit_to_trade(trade: dict[str, Any], execution: StrategyExecution) -> None:
    trade["exit_timestamp"] = execution.timestamp
    trade["gross_pnl"] += float(execution.gross_pnl or 0.0)
    trade["net_pnl"] += float(execution.net_pnl or 0.0)
    trade["exit_execution_count"] += 1
    if str(execution.action_type).startswith("PARTIAL_EXIT"):
        trade["partial_exit_execution_count"] += 1
    if execution.realized_r_multiple is not None:
        trade["r_values"].append(float(execution.realized_r_multiple))
    reason = _known(execution.exit_reason or execution.reason)
    if reason != "UNKNOWN":
        trade["exit_reasons"].append(reason)
    metadata = execution.metadata or {}
    for target, keys in (
        ("pattern_type", ("pattern_type",)),
        ("pattern_direction", ("pattern_direction",)),
        ("timeframe", ("timeframe", "interval")),
        ("session", ("session", "market_session", "session_tag")),
        ("market_regime", ("market_regime", "regime")),
        ("liquidity_regime", ("liquidity_regime",)),
        ("spread_regime", ("spread_regime",)),
        ("weekday_tag", ("weekday_tag",)),
    ):
        if trade[target] == "UNKNOWN":
            trade[target] = _metadata_key(metadata, *keys)


def _finalize_trade(trade: dict[str, Any]) -> TradeLifecycleOutcome:
    r_values = trade["r_values"]
    return TradeLifecycleOutcome(
        entry_timestamp=trade["entry_timestamp"],
        exit_timestamp=trade["exit_timestamp"],
        position_side=trade["position_side"],
        pattern_type=trade["pattern_type"],
        pattern_direction=trade["pattern_direction"],
        exit_reason=_combined_exit_reason(trade["exit_reasons"]),
        timeframe=trade["timeframe"],
        session=trade["session"],
        market_regime=trade["market_regime"],
        liquidity_regime=trade["liquidity_regime"],
        spread_regime=trade["spread_regime"],
        weekday_tag=trade["weekday_tag"],
        gross_pnl=float(trade["gross_pnl"]),
        net_pnl=float(trade["net_pnl"]),
        realized_r_multiple=(sum(r_values) / len(r_values)) if r_values else None,
        exit_execution_count=int(trade["exit_execution_count"]),
        partial_exit_execution_count=int(trade["partial_exit_execution_count"]),
        duration_seconds=_duration_seconds(trade["entry_timestamp"], trade["exit_timestamp"]),
    )


def _trade_metric_summary(
    outcomes: Sequence[TradeLifecycleOutcome],
    closing_execution_count: int,
) -> TradeMetricSummary:
    pnl_values = [float(outcome.net_pnl) for outcome in outcomes]
    wins = [value for value in pnl_values if value > 0]
    losses = [value for value in pnl_values if value < 0]
    breakeven_count = len([value for value in pnl_values if value == 0])
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    r_values = [outcome.realized_r_multiple for outcome in outcomes if outcome.realized_r_multiple is not None]
    durations = [outcome.duration_seconds for outcome in outcomes if outcome.duration_seconds is not None]
    profit_factor_is_infinite = gross_profit > 0 and gross_loss == 0
    return TradeMetricSummary(
        completed_trade_count=len(outcomes),
        closing_execution_count=closing_execution_count,
        partial_exit_execution_count=sum(outcome.partial_exit_execution_count for outcome in outcomes),
        win_count=len(wins),
        loss_count=len(losses),
        breakeven_count=breakeven_count,
        hit_ratio=(len(wins) / len(outcomes)) if outcomes else None,
        average_win=(sum(wins) / len(wins)) if wins else None,
        average_loss=(sum(losses) / len(losses)) if losses else None,
        payoff_ratio=((sum(wins) / len(wins)) / abs(sum(losses) / len(losses))) if wins and losses else None,
        expectancy=(sum(pnl_values) / len(pnl_values)) if pnl_values else None,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=(gross_profit / abs(gross_loss)) if gross_loss < 0 else None,
        profit_factor_is_infinite=profit_factor_is_infinite,
        average_r=(sum(r_values) / len(r_values)) if r_values else None,
        median_r=float(median(r_values)) if r_values else None,
        max_consecutive_losses=_max_consecutive_losses(pnl_values),
        average_trade_duration_seconds=(sum(durations) / len(durations)) if durations else None,
        median_trade_duration_seconds=float(median(durations)) if durations else None,
    )


def _grouped_attribution(
    outcomes: Sequence[TradeLifecycleOutcome],
    key: str,
) -> dict[str, dict[str, object]]:
    groups: dict[str, list[TradeLifecycleOutcome]] = {}
    for outcome in outcomes:
        groups.setdefault(_known(getattr(outcome, key)), []).append(outcome)
    return {
        group_key: _compact_group_metrics(group_outcomes)
        for group_key, group_outcomes in sorted(groups.items(), key=lambda item: item[0])
    }


def _compact_group_metrics(outcomes: Sequence[TradeLifecycleOutcome]) -> dict[str, object]:
    summary = _trade_metric_summary(outcomes, sum(outcome.exit_execution_count for outcome in outcomes))
    return {
        "completed_trade_count": summary.completed_trade_count,
        "net_pnl": sum(outcome.net_pnl for outcome in outcomes),
        "gross_pnl": sum(outcome.gross_pnl for outcome in outcomes),
        "hit_ratio": summary.hit_ratio,
        "expectancy": summary.expectancy,
        "profit_factor": summary.profit_factor,
        "profit_factor_is_infinite": summary.profit_factor_is_infinite,
        "payoff_ratio": summary.payoff_ratio,
        "average_r": summary.average_r,
        "partial_exit_execution_count": summary.partial_exit_execution_count,
    }


def _exposure_fraction(equity_points: Sequence[StrategyEquityPoint]) -> dict[str, object]:
    points = list(equity_points)
    if not points:
        return {"exposure_fraction": None, "exposed_point_count": 0, "total_point_count": 0}
    exposed = len([point for point in points if float(point.position_quantity) != 0.0])
    return {
        "exposure_fraction": exposed / len(points),
        "exposed_point_count": exposed,
        "total_point_count": len(points),
    }


def _turnover_metrics(
    executions: Sequence[StrategyExecution],
    equity_points: Sequence[StrategyEquityPoint],
) -> dict[str, object]:
    total_notional = sum(float(execution.notional) for execution in executions if float(execution.quantity) > 0)
    initial_equity = float(equity_points[0].equity) if equity_points else None
    return {
        "total_filled_notional": total_notional,
        "turnover_ratio": (total_notional / initial_equity) if initial_equity and initial_equity != 0 else None,
    }


def _max_consecutive_losses(values: Sequence[float]) -> int:
    current = 0
    maximum = 0
    for value in values:
        if value < 0:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0
    return maximum


def _metadata_key(metadata: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return _known(value)
    return "UNKNOWN"


def _known(value: Any, *, fallback: str = "UNKNOWN") -> str:
    if value in (None, ""):
        return fallback
    return str(value)


def _combined_exit_reason(reasons: Sequence[str]) -> str:
    unique = tuple(dict.fromkeys(reason for reason in reasons if reason and reason != "UNKNOWN"))
    if not unique:
        return "UNKNOWN"
    if len(unique) == 1:
        return unique[0]
    return "+".join(unique)


def _duration_seconds(start: Any | None, end: Any | None) -> float | None:
    if start is None or end is None:
        return None
    try:
        delta = end - start
    except TypeError:
        return None
    if hasattr(delta, "total_seconds"):
        return float(delta.total_seconds())
    if isinstance(delta, (int, float)):
        return float(delta)
    return None


def _drawdown_duration_metrics(points: Sequence[StrategyEquityPoint]) -> dict[str, int | None]:
    current = 0
    maximum = 0
    completed_recoveries: list[int] = []
    for point in points:
        if float(point.drawdown) < 0:
            current += 1
            maximum = max(maximum, current)
            continue
        if current > 0:
            completed_recoveries.append(current)
        current = 0
    return {
        "max_drawdown_duration_periods": maximum,
        "current_drawdown_duration_periods": current,
        "max_recovery_duration_periods": max(completed_recoveries) if completed_recoveries else None,
    }


def _total_return(points: Sequence[StrategyEquityPoint]) -> float | None:
    start = float(points[0].equity)
    end = float(points[-1].equity)
    if start == 0:
        return None
    return (end - start) / start


def _annualized_return(
    points: Sequence[StrategyEquityPoint],
    annualization_factor: float,
    period_count: int,
) -> float | None:
    start = float(points[0].equity)
    end = float(points[-1].equity)
    if start <= 0 or end <= 0 or period_count <= 0:
        return None
    try:
        return (end / start) ** (annualization_factor / period_count) - 1.0
    except OverflowError:
        return None


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _population_std(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = _mean(values)
    return sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _downside_deviation_period(values: Sequence[float]) -> float | None:
    downside = [min(value, 0.0) for value in values if value < 0]
    if not downside:
        return None
    return sqrt(sum(value**2 for value in downside) / len(values))
