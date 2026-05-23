from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite, sqrt
from typing import Sequence

from quant_bitcoin.backtesting.strategy_models import StrategyEquityPoint

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
    total_return: float | None
    warnings: tuple[str, ...] = ()

    def to_metadata(self) -> dict[str, object]:
        return asdict(self)


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
        total_return=total_return,
        warnings=tuple(warnings),
    )


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
