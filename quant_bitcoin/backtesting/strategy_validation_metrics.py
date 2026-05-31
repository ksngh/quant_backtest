"""Small pure helpers for Task 279 strategy validation diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Sequence


@dataclass(frozen=True)
class TradeContributionMetrics:
    trade_count: int
    net_profit: float
    largest_winner_contribution: float | None
    top_three_winner_contribution: float | None
    net_without_best_winner: float


@dataclass(frozen=True)
class ExposureMetrics:
    total_seconds: float
    long_seconds: float
    short_seconds: float
    flat_seconds: float
    long_fraction: float
    short_fraction: float
    flat_fraction: float
    max_continuous_position_fraction: float


def trade_contribution_metrics(net_pnls: Sequence[float]) -> TradeContributionMetrics:
    """Return concentration diagnostics for realized closed-trade PnL."""

    values = [float(value) for value in net_pnls]
    net_profit = sum(values)
    winners = sorted((value for value in values if value > 0), reverse=True)
    if net_profit > 0 and winners:
        largest = winners[0]
        top_three = sum(winners[:3])
        largest_contribution = largest / net_profit
        top_three_contribution = top_three / net_profit
        net_without_best = net_profit - largest
    else:
        largest_contribution = None
        top_three_contribution = None
        net_without_best = net_profit - (winners[0] if winners else 0.0)
    return TradeContributionMetrics(
        trade_count=len(values),
        net_profit=net_profit,
        largest_winner_contribution=largest_contribution,
        top_three_winner_contribution=top_three_contribution,
        net_without_best_winner=net_without_best,
    )


def exposure_metrics(points: Sequence[Any]) -> ExposureMetrics:
    """Measure long/short/flat time from ordered equity graph points."""

    if len(points) < 2:
        return ExposureMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    long_seconds = short_seconds = flat_seconds = 0.0
    max_continuous = 0.0
    current_side: str | None = None
    current_run = 0.0

    for left, right in zip(points, points[1:]):
        left_time = _timestamp(left)
        right_time = _timestamp(right)
        seconds = max((right_time - left_time).total_seconds(), 0.0)
        side = _position_side(_position(left))
        if side == "LONG":
            long_seconds += seconds
        elif side == "SHORT":
            short_seconds += seconds
        else:
            flat_seconds += seconds

        if side == current_side:
            current_run += seconds
        else:
            if current_side in {"LONG", "SHORT"}:
                max_continuous = max(max_continuous, current_run)
            current_side = side
            current_run = seconds

    if current_side in {"LONG", "SHORT"}:
        max_continuous = max(max_continuous, current_run)
    total = long_seconds + short_seconds + flat_seconds
    if total <= 0:
        return ExposureMetrics(0.0, long_seconds, short_seconds, flat_seconds, 0.0, 0.0, 0.0, 0.0)
    return ExposureMetrics(
        total_seconds=total,
        long_seconds=long_seconds,
        short_seconds=short_seconds,
        flat_seconds=flat_seconds,
        long_fraction=long_seconds / total,
        short_fraction=short_seconds / total,
        flat_fraction=flat_seconds / total,
        max_continuous_position_fraction=max_continuous / total,
    )


def endpoint_exclusion_window(
    start: datetime,
    end: datetime,
    *,
    minutes: int = 60,
) -> tuple[datetime, datetime]:
    """Return a deterministic first/last endpoint-excluded window."""

    if end <= start:
        raise ValueError("end must be after start")
    if minutes < 0:
        raise ValueError("minutes must be non-negative")
    delta = timedelta(minutes=minutes)
    trimmed_start = start + delta
    trimmed_end = end - delta
    if trimmed_end <= trimmed_start:
        raise ValueError("endpoint exclusion removes the full window")
    return trimmed_start, trimmed_end


def relative_parameter_neighborhood(value: float, *, relative: float = 0.20) -> tuple[float, float, float]:
    """Return a bounded low/base/high parameter neighborhood."""

    if value < 0:
        raise ValueError("value must be non-negative")
    if relative < 0:
        raise ValueError("relative must be non-negative")
    base = float(value)
    return (max(0.0, base * (1.0 - relative)), base, base * (1.0 + relative))


def _timestamp(point: Any) -> datetime:
    value = getattr(point, "candle_open_time", None) or getattr(point, "timestamp", None)
    if not isinstance(value, datetime):
        raise ValueError("point timestamp must be a datetime")
    return value


def _position(point: Any) -> float:
    value = getattr(point, "position", None)
    if value is None:
        value = getattr(point, "position_quantity", None)
    return float(value or 0.0)


def _position_side(position: float) -> str:
    if position > 0:
        return "LONG"
    if position < 0:
        return "SHORT"
    return "FLAT"
