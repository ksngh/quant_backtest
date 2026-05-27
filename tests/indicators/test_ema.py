from __future__ import annotations

import inspect

import pandas as pd
import pytest

from quant_bitcoin.indicators import ema
from quant_bitcoin.indicators.ema import EmaTrendConfig, calculate_ema_trend_features, ema_timing_metadata


def _candles(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": "BTCUSDT",
            "timestamp": pd.date_range("2026-05-27T00:00:00Z", periods=len(closes), freq="min"),
            "close": closes,
        }
    )


def test_calculate_ema_trend_features_matches_pandas_ewm() -> None:
    candles = _candles([100, 102, 104, 106, 108])
    config = EmaTrendConfig(fast_period=2, slow_period=3, slope_lookback=1)

    result = calculate_ema_trend_features(candles, config)

    expected_fast = candles["close"].ewm(span=2, adjust=False).mean()
    expected_slow = candles["close"].ewm(span=3, adjust=False).mean()
    assert result["ema_fast"].round(8).tolist() == expected_fast.round(8).tolist()
    assert result["ema_slow"].round(8).tolist() == expected_slow.round(8).tolist()
    assert bool(result.loc[2, "is_valid"])
    assert result.loc[2, "ema_fast_slope"] > 0
    assert result.loc[2, "ema_slow_slope"] > 0
    assert result.loc[2, "close_vs_ema_slow"] > 0
    assert result.loc[2, "fast_vs_slow"] > 0


def test_ema_warmup_marks_early_rows_invalid() -> None:
    config = EmaTrendConfig(fast_period=2, slow_period=4, slope_lookback=2)

    result = calculate_ema_trend_features(_candles([100, 101, 102, 103]), config)

    assert result["is_valid"].tolist() == [False, False, False, True]
    assert result.loc[0, "reason"] == "WARMUP"
    assert result.loc[3, "reason"] is None


def test_ema_detects_bearish_slope() -> None:
    config = EmaTrendConfig(fast_period=2, slow_period=3, slope_lookback=1)

    result = calculate_ema_trend_features(_candles([108, 106, 104, 102]), config)

    assert bool(result.loc[3, "is_valid"])
    assert result.loc[3, "ema_fast_slope"] < 0
    assert result.loc[3, "ema_slow_slope"] < 0
    assert result.loc[3, "close_vs_ema_slow"] < 0
    assert result.loc[3, "fast_vs_slow"] < 0


def test_ema_rejects_invalid_periods_and_inputs() -> None:
    with pytest.raises(ValueError, match="fast_period must be at least 1"):
        EmaTrendConfig(fast_period=0)
    with pytest.raises(ValueError, match="fast_period must be less than slow_period"):
        EmaTrendConfig(fast_period=5, slow_period=5)
    with pytest.raises(ValueError, match="slope_lookback must be at least 1"):
        EmaTrendConfig(slope_lookback=0)

    unsorted = _candles([100, 101, 102]).iloc[[0, 2, 1]].reset_index(drop=True)
    with pytest.raises(ValueError, match="sorted ascending"):
        calculate_ema_trend_features(unsorted, EmaTrendConfig(fast_period=2, slow_period=3))


def test_ema_timing_metadata_documents_closed_current_candle_use() -> None:
    config = EmaTrendConfig(fast_period=2, slow_period=3, slope_lookback=1)

    metadata = ema_timing_metadata(config)

    assert metadata["schema_version"] == "indicator_timing_metadata_v1"
    assert metadata["current_candle_included"] is True
    assert metadata["requires_closed_candle"] is True
    assert metadata["warmup_period"] == 3
    assert metadata["confirmation_delay"] == 0


def test_ema_module_has_no_exchange_or_network_coupling() -> None:
    source = inspect.getsource(ema)

    assert "binance" not in source.lower()
    assert "requests" not in source
    assert "urllib" not in source
    assert "signed" not in source.lower()
