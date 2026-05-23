from __future__ import annotations

import pytest

from quant_bitcoin.backtesting.performance_metrics import (
    annualization_factor_for_interval,
    calculate_performance_metrics,
    period_returns_from_equity,
)
from quant_bitcoin.backtesting.strategy_models import StrategyEquityPoint


def _point(index: int, equity: float, drawdown: float = 0.0) -> StrategyEquityPoint:
    return StrategyEquityPoint(
        timestamp=index,
        cash=equity,
        position_quantity=0.0,
        mark_price=0.0,
        equity=equity,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        drawdown=drawdown,
    )


def test_period_returns_from_equity_points() -> None:
    assert period_returns_from_equity([_point(1, 100), _point(2, 110), _point(3, 99)]) == (
        0.1,
        -0.1,
    )


@pytest.mark.parametrize(
    ("interval", "expected"),
    [("1m", 525600), ("5m", 105120), ("15m", 35040)],
)
def test_annualization_factor_for_supported_minute_intervals(interval, expected) -> None:
    assert annualization_factor_for_interval(interval) == expected


def test_sharpe_ratio_uses_excess_equity_returns() -> None:
    metrics = calculate_performance_metrics(
        [_point(1, 100), _point(2, 110), _point(3, 104.5)],
        interval="30m",
        risk_free_rate=0.0,
    )

    assert metrics.period_count == 2
    assert metrics.annualized_volatility is not None
    assert metrics.sharpe_ratio is not None
    assert metrics.sharpe_ratio > 0


def test_sortino_ratio_uses_downside_returns_only() -> None:
    metrics = calculate_performance_metrics(
        [_point(1, 100), _point(2, 110), _point(3, 104.5)],
        interval="30m",
    )

    assert metrics.downside_deviation is not None
    assert metrics.sortino_ratio is not None


def test_sortino_ratio_without_downside_returns_is_none() -> None:
    metrics = calculate_performance_metrics(
        [_point(1, 100), _point(2, 101), _point(3, 102)],
        interval="15m",
    )

    assert metrics.downside_deviation is None
    assert metrics.sortino_ratio is None


def test_calmar_ratio_uses_absolute_max_drawdown() -> None:
    metrics = calculate_performance_metrics(
        [_point(1, 100, 0.0), _point(2, 99, -0.01), _point(3, 100.01, 0.0)],
        interval="30m",
    )

    assert metrics.max_drawdown == -0.01
    assert metrics.calmar_ratio is not None
    assert metrics.calmar_ratio > 0


def test_flat_equity_curve_is_deterministic() -> None:
    metrics = calculate_performance_metrics([_point(1, 100), _point(2, 100)])

    assert metrics.total_return == 0.0
    assert metrics.annualized_volatility == 0.0
    assert metrics.sharpe_ratio is None
    assert metrics.sortino_ratio is None


def test_empty_equity_curve_is_safe() -> None:
    metrics = calculate_performance_metrics([], interval="1m")

    assert metrics.period_count == 0
    assert metrics.total_return is None
    assert "insufficient equity points" in metrics.warnings


def test_unsupported_interval_returns_explicit_warning() -> None:
    metrics = calculate_performance_metrics([_point(1, 100), _point(2, 101)], interval="2h")

    assert metrics.annualization_factor is None
    assert metrics.annualized_return is None
    assert "unsupported interval for annualization: 2h" in metrics.warnings
