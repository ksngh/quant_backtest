from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.backtesting.pattern_event_study import (
    extract_fair_value_gap_event_study_records,
)
from quant_bitcoin.indicators import AtrConfig, VolumeRatioConfig
from quant_bitcoin.patterns import FairValueGapConfig


def _base_columns() -> list[str]:
    return ["timestamp", "open", "high", "low", "close", "volume"]


def test_extract_fvg_event_study_records_empty_returns_empty_dataset() -> None:
    candles = pd.DataFrame(columns=_base_columns())

    dataset = extract_fair_value_gap_event_study_records(
        candles,
        symbol="BTCUSDT",
        timeframe="1m",
        config=FairValueGapConfig(require_displacement_candle=False, minimum_volume_ratio=0.0, minimum_pattern_score=0.0, atr_config=AtrConfig(period=2), volume_ratio_config=VolumeRatioConfig(window=2)),
    )

    assert dataset.records == ()


def test_extract_fvg_event_study_records_insufficient_returns_empty_dataset() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"timestamp": "2024-01-01T00:01:00Z", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 11},
        ]
    )

    dataset = extract_fair_value_gap_event_study_records(candles)

    assert dataset.records == ()


def test_extract_fvg_event_study_records_detects_bullish_and_bearish() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 100},
            {"timestamp": "2024-01-01T00:01:00Z", "open": 100.5, "high": 102, "low": 100, "close": 101.5, "volume": 180},
            {"timestamp": "2024-01-01T00:02:00Z", "open": 103, "high": 104, "low": 102.5, "close": 103.5, "volume": 260},
            {"timestamp": "2024-01-01T00:03:00Z", "open": 102, "high": 102.2, "low": 101.2, "close": 101.5, "volume": 140},
            {"timestamp": "2024-01-01T00:04:00Z", "open": 98.8, "high": 99, "low": 98.2, "close": 98.5, "volume": 260},
        ]
    )

    dataset = extract_fair_value_gap_event_study_records(
        candles,
        symbol="BTCUSDT",
        timeframe="1m",
        config=FairValueGapConfig(require_displacement_candle=False, minimum_volume_ratio=0.0, minimum_pattern_score=0.0, atr_config=AtrConfig(period=2), volume_ratio_config=VolumeRatioConfig(window=2)),
    )

    assert len(dataset.records) >= 2
    directions = {record.direction for record in dataset.records}
    assert "BULLISH" in directions
    assert "BEARISH" in directions
    assert len({record.event_id for record in dataset.records}) == len(dataset.records)


def test_extract_fvg_event_study_records_no_lookahead_confirmation_index() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99.5, "close": 100.5, "volume": 100},
            {"timestamp": "2024-01-01T00:01:00Z", "open": 100.6, "high": 102.0, "low": 100.4, "close": 101.9, "volume": 190},
            {"timestamp": "2024-01-01T00:02:00Z", "open": 103.0, "high": 104.0, "low": 102.7, "close": 103.6, "volume": 280},
        ]
    )

    dataset = extract_fair_value_gap_event_study_records(candles, symbol="BTCUSDT", timeframe="1m", config=FairValueGapConfig(require_displacement_candle=False, minimum_volume_ratio=0.0, minimum_pattern_score=0.0, atr_config=AtrConfig(period=2), volume_ratio_config=VolumeRatioConfig(window=2)))

    assert len(dataset.records) == 1
    assert dataset.records[0].end_index == 2


def test_extract_fvg_event_study_records_missing_columns_error() -> None:
    candles = pd.DataFrame([{"timestamp": "2024-01-01T00:00:00Z", "open": 1, "high": 2, "low": 0, "close": 1}])

    with pytest.raises(ValueError, match="missing required candle columns"):
        extract_fair_value_gap_event_study_records(candles)


def test_extract_fvg_event_study_records_unsorted_timestamps_error() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:01:00Z", "open": 1, "high": 2, "low": 0, "close": 1, "volume": 1},
            {"timestamp": "2024-01-01T00:00:00Z", "open": 1, "high": 2, "low": 0, "close": 1, "volume": 1},
            {"timestamp": "2024-01-01T00:02:00Z", "open": 1, "high": 2, "low": 0, "close": 1, "volume": 1},
        ]
    )

    with pytest.raises(ValueError, match="sorted by ascending timestamp"):
        extract_fair_value_gap_event_study_records(candles)


def test_extract_fvg_event_study_records_does_not_mutate_input() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "open": "100", "high": "101", "low": "99", "close": "100", "volume": "10"},
            {"timestamp": "2024-01-01T00:01:00Z", "open": "100", "high": "102", "low": "100", "close": "101", "volume": "20"},
            {"timestamp": "2024-01-01T00:02:00Z", "open": "103", "high": "104", "low": "102.5", "close": "103.5", "volume": "30"},
        ]
    )
    original = candles.copy(deep=True)

    _ = extract_fair_value_gap_event_study_records(candles)

    pd.testing.assert_frame_equal(candles, original)
