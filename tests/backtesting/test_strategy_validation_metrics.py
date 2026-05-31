from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from quant_bitcoin.backtesting.strategy_validation_metrics import (
    endpoint_exclusion_window,
    exposure_metrics,
    relative_parameter_neighborhood,
    trade_contribution_metrics,
)


def _point(minute: int, position: float) -> SimpleNamespace:
    return SimpleNamespace(
        candle_open_time=datetime(2026, 5, 20, 0, minute, tzinfo=timezone.utc),
        position=position,
    )


def test_trade_contribution_metrics_handles_one_trade_and_negative_net() -> None:
    one = trade_contribution_metrics([100.0])
    negative = trade_contribution_metrics([100.0, -150.0])

    assert one.largest_winner_contribution == 1.0
    assert one.net_without_best_winner == 0.0
    assert negative.net_profit == -50.0
    assert negative.largest_winner_contribution is None
    assert negative.net_without_best_winner == -150.0


def test_trade_contribution_metrics_reports_top_three_winner_concentration() -> None:
    metrics = trade_contribution_metrics([60.0, 30.0, 10.0, -20.0])

    assert metrics.trade_count == 4
    assert metrics.net_profit == 80.0
    assert metrics.largest_winner_contribution == pytest.approx(0.75)
    assert metrics.top_three_winner_contribution == pytest.approx(1.25)


def test_exposure_metrics_separates_long_short_and_flat_time() -> None:
    metrics = exposure_metrics([
        _point(0, 0.0),
        _point(1, 1.0),
        _point(2, 1.0),
        _point(3, -1.0),
        _point(4, 0.0),
    ])

    assert metrics.total_seconds == 240.0
    assert metrics.flat_fraction == pytest.approx(0.25)
    assert metrics.long_fraction == pytest.approx(0.50)
    assert metrics.short_fraction == pytest.approx(0.25)
    assert metrics.max_continuous_position_fraction == pytest.approx(0.50)


def test_endpoint_exclusion_window_removes_first_and_last_minutes() -> None:
    start = datetime(2026, 5, 20, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 20, 4, 0, tzinfo=timezone.utc)

    trimmed_start, trimmed_end = endpoint_exclusion_window(start, end, minutes=60)

    assert trimmed_start == datetime(2026, 5, 20, 1, 0, tzinfo=timezone.utc)
    assert trimmed_end == datetime(2026, 5, 20, 3, 0, tzinfo=timezone.utc)


def test_relative_parameter_neighborhood_is_deterministic_and_bounded() -> None:
    assert relative_parameter_neighborhood(10.0, relative=0.2) == (8.0, 10.0, 12.0)
    assert relative_parameter_neighborhood(0.0, relative=0.2) == (0.0, 0.0, 0.0)

    with pytest.raises(ValueError, match="non-negative"):
        relative_parameter_neighborhood(-1.0)
