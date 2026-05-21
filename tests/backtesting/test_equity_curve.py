from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.backtesting.basic import BacktestTrade
from quant_bitcoin.backtesting.equity_curve import (
    EquityCurveConfig,
    build_equity_curve_from_trades,
    calculate_drawdown_series,
)
from quant_bitcoin.strategies import Signal


def _candles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2024-01-01T00:00:00Z",
                    "2024-01-01T00:01:00Z",
                    "2024-01-01T00:02:00Z",
                ],
                utc=True,
            ),
            "open": [100.0, 100.0, 110.0],
            "high": [101.0, 111.0, 111.0],
            "low": [99.0, 99.0, 109.0],
            "close": [100.0, 110.0, 105.0],
            "volume": [1.0, 1.0, 1.0],
        }
    )


def test_build_equity_curve_no_trades() -> None:
    result = build_equity_curve_from_trades(_candles(), [], starting_cash=1000.0)

    assert len(result.points) == 3
    assert all(point.cash == 1000.0 for point in result.points)
    assert all(point.position_quantity == 0.0 for point in result.points)
    assert all(point.equity == 1000.0 for point in result.points)
    assert all(point.drawdown == 0.0 for point in result.points)


def test_build_equity_curve_long_mark_to_market_and_close() -> None:
    trades = [
        BacktestTrade(
            timestamp=pd.Timestamp("2024-01-01T00:00:00Z"),
            signal=Signal.BUY,
            price=100.0,
            quantity=1.0,
            cash_after=900.0,
            position_after=1.0,
        ),
        BacktestTrade(
            timestamp=pd.Timestamp("2024-01-01T00:02:00Z"),
            signal=Signal.SELL,
            price=105.0,
            quantity=1.0,
            cash_after=1005.0,
            position_after=0.0,
        ),
    ]

    result = build_equity_curve_from_trades(_candles(), trades, starting_cash=1000.0)

    assert result.points[0].equity == pytest.approx(1000.0)
    assert result.points[1].position_market_value == pytest.approx(110.0)
    assert result.points[1].equity == pytest.approx(1010.0)
    assert result.points[2].position_quantity == pytest.approx(0.0)
    assert result.points[2].cash == pytest.approx(1005.0)
    assert result.points[2].trade_marker == "SELL"


def test_drawdown_series_deterministic() -> None:
    result = build_equity_curve_from_trades(
        _candles(),
        [{"timestamp": "2024-01-01T00:00:00Z", "side": "BUY", "price": 100.0, "quantity": 1.0}],
        starting_cash=1000.0,
    )

    drawdowns = [point.drawdown for point in result.points]
    assert drawdowns[0] == pytest.approx(0.0)
    assert drawdowns[1] == pytest.approx(0.0)
    assert drawdowns[2] == pytest.approx((1005.0 - 1010.0) / 1010.0)


def test_calculate_drawdown_series_on_points() -> None:
    result = build_equity_curve_from_trades(_candles(), [], starting_cash=1000.0)
    recalculated = calculate_drawdown_series(result.points)
    assert [p.drawdown for p in recalculated] == [0.0, 0.0, 0.0]


def test_missing_columns_validation() -> None:
    candles = _candles().drop(columns=["close"])
    with pytest.raises(ValueError, match="missing required columns"):
        build_equity_curve_from_trades(candles, [], starting_cash=1000.0)


def test_unsorted_timestamp_validation() -> None:
    candles = _candles().iloc[[1, 0, 2]].reset_index(drop=True)
    with pytest.raises(ValueError, match="sorted ascending"):
        build_equity_curve_from_trades(candles, [], starting_cash=1000.0)


def test_allow_empty_candles_by_config() -> None:
    empty = _candles().iloc[0:0]
    result = build_equity_curve_from_trades(
        empty,
        [],
        starting_cash=1000.0,
        config=EquityCurveConfig(allow_empty_candles=True),
    )
    assert result.points == ()


def test_inputs_not_mutated() -> None:
    candles = _candles()
    candles_original = candles.copy(deep=True)
    trades = [{"timestamp": "2024-01-01T00:00:00Z", "side": "BUY", "price": 100.0, "quantity": 1.0}]
    trades_original = [dict(trade) for trade in trades]

    _ = build_equity_curve_from_trades(candles, trades, starting_cash=1000.0)

    pd.testing.assert_frame_equal(candles, candles_original)
    assert trades == trades_original
