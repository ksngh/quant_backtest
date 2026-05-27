"""Reusable deterministic FVG retest v2 fixtures.

Scenarios cover offline research mechanics only: multi-timeframe visibility,
trend alignment metadata, Fibonacci confluence, retest/reaction entries,
liquidity-target pivots, and stop-mode metadata. No external data, credentials,
or network endpoints are used.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FvgV2Scenario:
    name: str
    direction: str
    candles: pd.DataFrame
    expected: dict[str, object]


def bullish_retest_v2_scenario() -> FvgV2Scenario:
    candles = _base_minutes(46, start=100.0, step=0.4)
    candles.loc[8, ["open", "high", "low", "close", "volume"]] = [98.0, 100.0, 96.0, 99.0, 100.0]
    candles.loc[9, ["open", "high", "low", "close", "volume"]] = [95.0, 108.0, 94.0, 107.0, 500.0]
    candles.loc[10, ["open", "high", "low", "close", "volume"]] = [103.0, 104.0, 102.0, 103.0, 100.0]
    candles.loc[11, ["open", "high", "low", "close"]] = [103.0, 103.5, 100.8, 100.9]
    candles.loc[12, ["open", "high", "low", "close"]] = [101.2, 102.0, 100.7, 100.8]
    candles.loc[15, ["open", "high", "low", "close"]] = [105.0, 113.0, 104.0, 112.0]
    candles.loc[16, ["open", "high", "low", "close"]] = [112.0, 112.5, 106.0, 107.0]
    return FvgV2Scenario(
        name="bullish_retest_v2_aligned_confluent",
        direction="BULLISH",
        candles=candles,
        expected={
            "event_index": 10,
            "zone_mid": 101.0,
            "first_5m_visible_index": 5,
            "first_15m_visible_index": 15,
            "liquidity_target": 113.0,
        },
    )


def bearish_retest_v2_scenario() -> FvgV2Scenario:
    candles = _base_minutes(46, start=130.0, step=-0.35)
    candles.loc[8, ["open", "high", "low", "close", "volume"]] = [103.0, 106.0, 102.0, 105.0, 100.0]
    candles.loc[9, ["open", "high", "low", "close", "volume"]] = [107.0, 108.0, 92.0, 93.0, 500.0]
    candles.loc[10, ["open", "high", "low", "close", "volume"]] = [99.0, 100.0, 96.0, 98.0, 100.0]
    candles.loc[15, ["open", "high", "low", "close"]] = [98.0, 99.0, 88.0, 89.0]
    candles.loc[16, ["open", "high", "low", "close"]] = [89.0, 95.0, 88.5, 94.0]
    return FvgV2Scenario(
        name="bearish_retest_v2_aligned_confluent",
        direction="BEARISH",
        candles=candles,
        expected={
            "event_index": 10,
            "zone_mid": 101.0,
            "first_5m_visible_index": 5,
            "first_15m_visible_index": 15,
            "liquidity_target": 88.0,
        },
    )


def expected_diagnostic_keys() -> set[str]:
    return {
        "fvg_retest_v2",
        "fvg_entry_mode",
        "pattern_entry_mode",
        "summary",
        "metadata",
    }


def _base_minutes(rows: int, *, start: float, step: float) -> pd.DataFrame:
    data = []
    for index in range(rows):
        close = start + index * step
        open_price = close - step / 2
        high = max(open_price, close) + 1.0
        low = min(open_price, close) - 1.0
        data.append(
            {
                "symbol": "BTCUSDT",
                "timestamp": pd.Timestamp("2026-05-27T00:00:00Z") + pd.Timedelta(minutes=index),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": 100.0 + index,
            }
        )
    return pd.DataFrame(data)
