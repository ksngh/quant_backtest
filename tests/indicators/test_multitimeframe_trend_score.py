from __future__ import annotations

import inspect

import pandas as pd
import pytest

from quant_bitcoin.backtesting.multitimeframe_candles import align_completed_higher_timeframe_candles
from quant_bitcoin.indicators.ema import EmaTrendConfig
from quant_bitcoin.indicators import multitimeframe_trend_score
from quant_bitcoin.indicators.multitimeframe_trend_score import (
    TREND_SCORE_SCHEMA_VERSION,
    MultiTimeframeTrendScoreConfig,
    calculate_multitimeframe_trend_score,
    multitimeframe_trend_score_timing_metadata,
)


def _base_candles(closes: list[float]) -> pd.DataFrame:
    rows = []
    for index, close in enumerate(closes):
        rows.append(
            {
                "symbol": "BTCUSDT",
                "timestamp": pd.Timestamp("2026-05-27T00:00:00Z") + pd.Timedelta(minutes=index),
                "open": close - 0.25,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 100 + index,
            }
        )
    return pd.DataFrame(rows)


def _higher(closes: list[float], interval_minutes: int) -> pd.DataFrame:
    rows = []
    for index, close in enumerate(closes):
        open_time = pd.Timestamp("2026-05-27T00:00:00Z") + pd.Timedelta(minutes=index * interval_minutes)
        rows.append(
            {
                "symbol": "BTCUSDT",
                "open_time": open_time,
                "close_time": open_time + pd.Timedelta(minutes=interval_minutes),
                "close": close,
            }
        )
    return pd.DataFrame(rows)


def _config(weights: dict[str, float] | None = None) -> MultiTimeframeTrendScoreConfig:
    return MultiTimeframeTrendScoreConfig(
        weights=weights or {"1m": 0.2, "5m": 0.3, "15m": 0.5},
        ema_config=EmaTrendConfig(fast_period=2, slow_period=3, slope_lookback=1),
    )


def test_multitimeframe_trend_score_bullish_components() -> None:
    result = calculate_multitimeframe_trend_score(
        _base_candles([100 + index for index in range(50)]),
        higher_timeframe_candles={
            "5m": _higher([100, 102, 104], 5),
            "15m": _higher([100, 103, 106], 15),
        },
        config=_config(),
    )

    last = result.iloc[-1]

    assert last["trend_score"] > 0
    assert last["trend_direction"] == "BULLISH"
    metadata = last["trend_score_metadata"]
    assert metadata["schema_version"] == TREND_SCORE_SCHEMA_VERSION
    assert metadata["components"]["1m"]["direction"] == "BULLISH"
    assert metadata["components"]["5m"]["direction"] == "BULLISH"
    assert metadata["components"]["15m"]["direction"] == "BULLISH"


def test_multitimeframe_trend_score_bearish_components() -> None:
    result = calculate_multitimeframe_trend_score(
        _base_candles([150 - index for index in range(50)]),
        higher_timeframe_candles={
            "5m": _higher([106, 104, 102], 5),
            "15m": _higher([109, 106, 103], 15),
        },
        config=_config(),
    )

    last = result.iloc[-1]

    assert last["trend_score"] < 0
    assert last["trend_direction"] == "BEARISH"
    assert last["trend_score_metadata"]["components"]["1m"]["direction"] == "BEARISH"


def test_multitimeframe_trend_score_neutral_flat_components() -> None:
    result = calculate_multitimeframe_trend_score(
        _base_candles([100 for _ in range(50)]),
        higher_timeframe_candles={
            "5m": _higher([100, 100, 100], 5),
            "15m": _higher([100, 100, 100], 15),
        },
        config=_config(),
    )

    last = result.iloc[-1]

    assert last["trend_score"] == 0
    assert last["trend_direction"] == "NEUTRAL"


def test_missing_higher_timeframe_context_is_explicit_not_false_neutral() -> None:
    result = calculate_multitimeframe_trend_score(
        _base_candles([100, 101, 102, 103]),
        config=_config(),
    )

    last = result.iloc[-1]

    assert last["available_weight"] == 0.2
    assert last["missing_timeframes"] == ("5m", "15m")
    assert last["trend_score_metadata"]["components"]["5m"]["missing_reason"] == "MISSING_TIMEFRAME_CONTEXT"
    assert last["trend_score_metadata"]["components"]["15m"]["direction"] == "UNAVAILABLE"
    assert last["trend_direction"] == "BULLISH"


def test_mixed_timeframe_score_can_be_weighted_bearish() -> None:
    result = calculate_multitimeframe_trend_score(
        _base_candles([100 + index for index in range(50)]),
        higher_timeframe_candles={
            "5m": _higher([100, 101, 102], 5),
            "15m": _higher([110, 107, 104], 15),
        },
        config=_config({"1m": 0.2, "5m": 0.2, "15m": 0.6}),
    )

    last = result.iloc[-1]

    assert last["trend_score"] < 0
    assert last["trend_direction"] == "BEARISH"
    assert last["trend_score_metadata"]["components"]["15m"]["direction"] == "BEARISH"


def test_trend_score_rejects_bad_weights() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        MultiTimeframeTrendScoreConfig(weights={"1m": -1, "5m": 0, "15m": 0})
    with pytest.raises(ValueError, match="at least one"):
        MultiTimeframeTrendScoreConfig(weights={"1m": 0, "5m": 0, "15m": 0})


def test_task_226_alignment_integration_preserves_no_lookahead_for_15m() -> None:
    candles = _base_candles([100 + index for index in range(46)])
    alignment = align_completed_higher_timeframe_candles(
        candles,
        source_interval="1m",
        target_intervals=("5m", "15m"),
    )

    result = calculate_multitimeframe_trend_score(
        alignment.candles,
        higher_timeframe_candles=alignment.higher_timeframe_candles,
        config=_config(),
    )

    before_15m_close = result.iloc[44]["trend_score_metadata"]["components"]["15m"]
    at_15m_close = result.iloc[45]["trend_score_metadata"]["components"]["15m"]

    assert before_15m_close["is_available"] is False
    assert before_15m_close["missing_reason"] == "WARMUP"
    assert at_15m_close["is_available"] is True
    assert at_15m_close["feature_timestamp"] == "2026-05-27T00:45:00Z"


def test_trend_score_timing_metadata_documents_diagnostic_default() -> None:
    metadata = multitimeframe_trend_score_timing_metadata(_config())

    assert metadata["schema_version"] == "indicator_timing_metadata_v1"
    assert metadata["current_candle_included"] is True
    assert metadata["requires_closed_candle"] is True
    assert "higher-timeframe components are unavailable" in metadata["higher_timeframe_availability_caveat"]
    assert metadata["safe_usage"] == "diagnostic-only after candle close; not an auto-trading signal"


def test_multitimeframe_trend_score_module_has_no_exchange_or_network_coupling() -> None:
    source = inspect.getsource(multitimeframe_trend_score)

    assert "binance" not in source.lower()
    assert "requests" not in source
    assert "urllib" not in source
    assert "exchange" not in source.lower()
    assert "signed" not in source.lower()
