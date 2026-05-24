from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.indicators import (
    MARKET_REGIME_OUTPUT_COLUMNS,
    LiquidityRegime,
    MarketRegimeConfig,
    RegimeVolatility,
    TrendRegime,
    calculate_market_regime,
    calculate_market_regime_snapshot,
    classify_liquidity_regime,
    classify_regime_volatility,
    classify_trend_regime,
    classify_utc_session,
    classify_weekday_tag,
)


def _candles(closes: list[object], *, volumes: list[object] | None = None) -> pd.DataFrame:
    rows = []
    volumes = volumes or [1000.0] * len(closes)
    for index, close in enumerate(closes):
        numeric_close = float(close) if isinstance(close, (int, float)) else close
        rows.append(
            {
                "symbol": "BTCUSDT",
                "timestamp": f"2026-05-24T00:{index:02d}:00Z",
                "open": numeric_close,
                "high": (numeric_close * 1.002) if isinstance(numeric_close, float) else numeric_close,
                "low": (numeric_close * 0.998) if isinstance(numeric_close, float) else numeric_close,
                "close": close,
                "volume": volumes[index],
            }
        )
    return pd.DataFrame(rows)


def _config() -> MarketRegimeConfig:
    return MarketRegimeConfig(
        volatility_window=2,
        trend_window=2,
        liquidity_window=2,
        mean_reversion_window=2,
        minimum_average_trading_value=100.0,
        low_spread_threshold=0.003,
        high_spread_threshold=0.02,
        trend_strength_threshold=0.01,
    )


def test_calculates_market_regime_schema_and_tags() -> None:
    rows = calculate_market_regime(_candles([100.0, 101.0, 103.0, 106.0]), _config())
    latest = rows.iloc[-1]

    assert list(rows.columns) == list(MARKET_REGIME_OUTPUT_COLUMNS)
    assert latest["is_valid"] == True
    assert latest["liquidity_regime"] == LiquidityRegime.HIGH.value
    assert latest["trading_value_percentile"] == pytest.approx(1.0)
    assert latest["liquidity_zscore"] == pytest.approx(1.0)
    assert latest["trend_regime"] == TrendRegime.UPTREND.value
    assert latest["volatility_regime"] == RegimeVolatility.LOW.value
    assert latest["spread_regime"] == "NORMAL"
    assert latest["range_spread_proxy_percentile"] == pytest.approx(1.0)
    assert latest["wick_dominance_proxy"] == pytest.approx(1.0)
    assert latest["session_tag"] == "ASIA"
    assert latest["weekday_tag"] == "WEEKEND"
    assert latest["mean_reversion_regime"] == "OVERBOUGHT"
    assert latest["market_regime"] == "LOW_VOL_UPTREND"


def test_marks_warmup_rows_unknown_without_lookahead() -> None:
    rows = calculate_market_regime(_candles([100.0, 101.0]), _config())

    assert rows.iloc[0]["is_valid"] == False
    assert rows.iloc[0]["market_regime"] == "UNKNOWN"
    assert rows.iloc[0]["reason"] == "warmup"
    assert rows.iloc[1]["is_valid"] == False
    assert rows.iloc[1]["volatility_regime"] == RegimeVolatility.UNKNOWN.value


def test_missing_and_invalid_inputs_are_invalid_or_rejected() -> None:
    missing = _candles([100.0, None, 101.0])
    rows = calculate_market_regime(missing, _config())
    assert rows.iloc[1]["is_valid"] == False
    assert rows.iloc[1]["reason"] == "missing_ohlcv"

    invalid = _candles([100.0, 101.0, 102.0])
    invalid.loc[1, "high"] = 90.0
    invalid.loc[1, "low"] = 110.0
    rows = calculate_market_regime(invalid, _config())
    assert rows.iloc[1]["reason"] == "invalid_high_low"

    with pytest.raises(ValueError, match="missing required Market Regime columns: volume"):
        calculate_market_regime(_candles([100.0]).drop(columns=["volume"]))
    with pytest.raises(ValueError):
        calculate_market_regime(_candles(["not-a-number"]))
    with pytest.raises(ValueError, match="volatility_window must be at least 1"):
        MarketRegimeConfig(volatility_window=0)


def test_uses_quote_volume_when_available() -> None:
    candles = _candles([100.0, 101.0, 102.0])
    candles["quote_volume"] = [1000.0, 2000.0, 3000.0]

    rows = calculate_market_regime(candles, _config())

    assert rows.iloc[-1]["trading_value"] == 3000.0
    assert rows.iloc[-1]["average_trading_value"] == 2500.0


def test_no_lookahead_regime_labels_match_rolling_prefixes() -> None:
    candles = _candles([100.0, 101.0, 103.0, 106.0, 107.0, 108.0])
    full = calculate_market_regime(candles, _config())

    for position in range(len(candles)):
        prefix = calculate_market_regime(candles.iloc[: position + 1], _config())
        assert prefix.iloc[-1]["market_regime"] == full.iloc[position]["market_regime"]
        assert prefix.iloc[-1]["trend_regime"] == full.iloc[position]["trend_regime"]
        assert prefix.iloc[-1]["mean_reversion_regime"] == full.iloc[position]["mean_reversion_regime"]


def test_snapshot_and_classifiers_are_stable() -> None:
    snapshot = calculate_market_regime_snapshot(_candles([100.0, 101.0, 103.0]), _config())

    assert snapshot["symbol"] == "BTCUSDT"
    assert snapshot["timestamp"] == "2026-05-24T00:02:00Z"
    assert classify_regime_volatility(None, _config()) == RegimeVolatility.UNKNOWN.value
    assert classify_liquidity_regime(0.0, _config()) == LiquidityRegime.UNTRADABLE.value
    assert classify_trend_regime(-0.02, _config()) == TrendRegime.DOWNTREND.value


def test_utc_session_and_weekday_tags_are_deterministic() -> None:
    assert classify_utc_session("2026-05-22T01:00:00Z") == "ASIA"
    assert classify_utc_session("2026-05-22T09:00:00Z") == "EU"
    assert classify_utc_session("2026-05-22T13:00:00Z") == "EU_US_OVERLAP"
    assert classify_utc_session("2026-05-22T18:00:00Z") == "US"
    assert classify_utc_session("2026-05-22T22:00:00Z") == "OFF_HOURS"
    assert classify_weekday_tag("2026-05-22T18:00:00Z") == "WEEKDAY"
    assert classify_weekday_tag("2026-05-24T18:00:00Z") == "WEEKEND"
