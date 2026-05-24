from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from quant_bitcoin.backtesting.performance_metrics import (
    annualization_factor_for_interval,
    calculate_trade_attribution_metrics,
    calculate_performance_metrics,
    period_returns_from_equity,
)
from quant_bitcoin.backtesting.strategy_models import StrategyEquityPoint, StrategyExecution


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


def _execution(
    *,
    timestamp,
    action_type: str,
    quantity: float = 1.0,
    position_after: float = 0.0,
    position_side: str = "LONG",
    net_pnl: float | None = None,
    gross_pnl: float | None = None,
    realized_r_multiple: float | None = None,
    exit_reason: str | None = None,
    metadata: dict[str, object] | None = None,
) -> StrategyExecution:
    side = "BUY" if action_type in ("ENTER_LONG", "EXIT_SHORT", "PARTIAL_EXIT_SHORT") else "SELL"
    return StrategyExecution(
        timestamp=timestamp,
        side=side,
        action_type=action_type,
        price=100.0,
        quantity=quantity,
        notional=100.0 * quantity,
        cash_after=10000.0,
        position_after=position_after,
        equity_after=10000.0 + float(net_pnl or 0.0),
        position_side=position_side,
        exit_reason=exit_reason,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        realized_r_multiple=realized_r_multiple,
        metadata=metadata or {},
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


def test_drawdown_duration_and_recovery_duration_are_reported() -> None:
    metrics = calculate_performance_metrics(
        [
            _point(1, 100, 0.0),
            _point(2, 95, -0.05),
            _point(3, 96, -0.04),
            _point(4, 101, 0.0),
            _point(5, 97, -0.04),
        ],
        interval="30m",
    )

    assert metrics.max_drawdown_duration_periods == 2
    assert metrics.max_recovery_duration_periods == 2
    assert metrics.current_drawdown_duration_periods == 1


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


def test_trade_attribution_handles_no_losses_without_infinite_json_value() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    metadata = {
        "pattern_type": "FAIR_VALUE_GAP",
        "pattern_direction": "BULLISH",
        "regime": "TRENDING",
        "session_tag": "EU_US_OVERLAP",
        "liquidity_regime": "LOW",
        "spread_regime": "WIDE",
        "weekday_tag": "WEEKDAY",
    }
    metrics = calculate_trade_attribution_metrics(
        [
            _execution(timestamp=start, action_type="ENTER_LONG", position_after=1.0, metadata=metadata),
            _execution(
                timestamp=start + timedelta(minutes=5),
                action_type="EXIT_LONG",
                position_after=0.0,
                net_pnl=25.0,
                gross_pnl=25.0,
                realized_r_multiple=1.5,
                exit_reason="TAKE_PROFIT",
                metadata=metadata,
            ),
        ],
        [_point(1, 10000), _point(2, 10025)],
    )

    trade_metrics = metrics["trade_metrics"]
    assert trade_metrics["completed_trade_count"] == 1
    assert trade_metrics["hit_ratio"] == 1.0
    assert trade_metrics["profit_factor"] is None
    assert trade_metrics["profit_factor_is_infinite"] is True
    assert metrics["attribution"]["by_pattern_type"]["FAIR_VALUE_GAP"]["net_pnl"] == 25.0
    assert metrics["attribution"]["by_market_regime"]["TRENDING"]["completed_trade_count"] == 1
    assert metrics["attribution"]["by_session"]["EU_US_OVERLAP"]["completed_trade_count"] == 1
    assert metrics["attribution"]["by_liquidity_regime"]["LOW"]["completed_trade_count"] == 1
    assert metrics["attribution"]["by_spread_regime"]["WIDE"]["completed_trade_count"] == 1
    assert metrics["attribution"]["by_weekday_tag"]["WEEKDAY"]["completed_trade_count"] == 1


def test_trade_attribution_handles_no_wins_and_max_consecutive_losses() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    metrics = calculate_trade_attribution_metrics(
        [
            _execution(timestamp=start, action_type="ENTER_LONG", position_after=1.0),
            _execution(timestamp=start + timedelta(minutes=1), action_type="EXIT_LONG", position_after=0.0, net_pnl=-4.0, gross_pnl=-4.0),
            _execution(timestamp=start + timedelta(minutes=2), action_type="ENTER_SHORT", position_after=-1.0, position_side="SHORT"),
            _execution(timestamp=start + timedelta(minutes=3), action_type="EXIT_SHORT", position_after=0.0, position_side="SHORT", net_pnl=-6.0, gross_pnl=-6.0),
        ],
        [_point(1, 10000), _point(2, 9996), _point(3, 9990)],
    )

    trade_metrics = metrics["trade_metrics"]
    assert trade_metrics["completed_trade_count"] == 2
    assert trade_metrics["win_count"] == 0
    assert trade_metrics["loss_count"] == 2
    assert trade_metrics["hit_ratio"] == 0.0
    assert trade_metrics["profit_factor"] == 0.0
    assert trade_metrics["max_consecutive_losses"] == 2
    assert metrics["attribution"]["by_position_side"]["LONG"]["completed_trade_count"] == 1
    assert metrics["attribution"]["by_position_side"]["SHORT"]["completed_trade_count"] == 1


def test_trade_attribution_handles_no_completed_trades() -> None:
    metrics = calculate_trade_attribution_metrics(
        [_execution(timestamp=1, action_type="ENTER_LONG", position_after=1.0)],
        [_point(1, 10000)],
    )

    assert metrics["trade_metrics"]["completed_trade_count"] == 0
    assert metrics["trade_metrics"]["expectancy"] is None
    assert metrics["attribution"]["by_pattern_type"] == {}
    assert "no completed trade lifecycles" in metrics["warnings"]


def test_trade_attribution_aggregates_partial_exits_into_one_lifecycle() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    metadata = {"pattern_type": "CUP_AND_HANDLE", "pattern_direction": "BULLISH", "timeframe": "5m"}
    metrics = calculate_trade_attribution_metrics(
        [
            _execution(timestamp=start, action_type="ENTER_LONG", position_after=1.0, metadata=metadata),
            _execution(
                timestamp=start + timedelta(minutes=5),
                action_type="PARTIAL_EXIT_LONG",
                quantity=0.4,
                position_after=0.6,
                net_pnl=4.0,
                gross_pnl=4.0,
                realized_r_multiple=0.4,
                exit_reason="TARGET_1",
                metadata=metadata,
            ),
            _execution(
                timestamp=start + timedelta(minutes=10),
                action_type="EXIT_LONG",
                quantity=0.6,
                position_after=0.0,
                net_pnl=6.0,
                gross_pnl=6.0,
                realized_r_multiple=0.6,
                exit_reason="TIME_STOP",
                metadata=metadata,
            ),
        ],
        [_point(1, 10000), _point(2, 10004), _point(3, 10010)],
    )

    trade_metrics = metrics["trade_metrics"]
    assert trade_metrics["completed_trade_count"] == 1
    assert trade_metrics["closing_execution_count"] == 2
    assert trade_metrics["partial_exit_execution_count"] == 1
    assert trade_metrics["expectancy"] == 10.0
    assert trade_metrics["average_r"] == pytest.approx(0.5)
    assert trade_metrics["average_trade_duration_seconds"] == 600.0
    assert metrics["turnover"]["turnover_ratio"] == pytest.approx(0.02)
    assert metrics["exposure"]["exposure_fraction"] == 0.0
    assert metrics["attribution"]["by_exit_reason"]["TARGET_1+TIME_STOP"]["completed_trade_count"] == 1
    assert metrics["attribution"]["by_timeframe"]["5m"]["net_pnl"] == 10.0
