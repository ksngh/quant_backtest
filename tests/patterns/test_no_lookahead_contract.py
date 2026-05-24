from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import pytest

from quant_bitcoin.indicators import (
    AtrConfig,
    DisplacementCandleConfig,
    PivotConfig,
    VolumeRatioConfig,
)
from quant_bitcoin.patterns import (
    AdamAndEveConfig,
    CupAndHandleConfig,
    DiamondConfig,
    FairValueGapConfig,
    OrderBlockConfig,
    TrendlineBreakConfig,
    detect_adam_and_eve_patterns,
    detect_adam_and_eve_patterns_at_index,
    detect_cup_and_handle_patterns,
    detect_cup_and_handle_patterns_at_index,
    detect_diamond_patterns,
    detect_diamond_patterns_at_index,
    detect_fair_value_gaps,
    detect_fair_value_gaps_at_index,
    detect_order_blocks,
    detect_order_blocks_at_index,
    detect_trendline_breaks,
    detect_trendline_breaks_at_index,
)


def _rows(rows: list[dict], *, base_price: float = 100.0) -> pd.DataFrame:
    normalized = []
    for index, row in enumerate(rows):
        base = {
            "timestamp": f"2026-05-16T00:{index:02d}:00Z",
            "open": base_price,
            "high": base_price + 1,
            "low": base_price - 1,
            "close": base_price,
            "volume": 100.0,
        }
        base.update(row)
        normalized.append(base)
    return pd.DataFrame(normalized)


def _volume_config(minimum: float = 1.3) -> VolumeRatioConfig:
    return VolumeRatioConfig(
        window=2,
        minimum_volume_ratio_for_confirmation=minimum,
        high_volume_ratio_threshold=2.0,
        require_full_window=False,
    )


def _pivot_config() -> PivotConfig:
    return PivotConfig(left_window=1, right_window=1, minimum_distance_between_pivots=1)


def _fvg_case() -> tuple[pd.DataFrame, FairValueGapConfig, int, Callable, Callable]:
    candles = _rows(
        [
            {"open": 98.0, "high": 100.0, "low": 96.0, "close": 99.0},
            {"open": 95.0, "high": 108.0, "low": 94.0, "close": 107.0, "volume": 500.0},
            {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0},
        ]
    )
    config = FairValueGapConfig(
        atr_config=AtrConfig(period=1),
        volume_ratio_config=_volume_config(),
        displacement_config=DisplacementCandleConfig(
            minimum_range_atr_multiplier=1.0,
            minimum_volume_ratio=1.3,
        ),
    )
    return candles, config, 2, detect_fair_value_gaps, detect_fair_value_gaps_at_index


def _order_block_case() -> tuple[pd.DataFrame, OrderBlockConfig, int, Callable, Callable]:
    candles = _rows(
        [
            {"open": 100.0, "high": 100.0, "low": 99.0, "close": 99.2},
            {"open": 99.2, "high": 110.0, "low": 98.0, "close": 109.5, "volume": 500.0},
        ]
    )
    return candles, OrderBlockConfig(atr_config=AtrConfig(period=2), volume_ratio_config=_volume_config()), 1, detect_order_blocks, detect_order_blocks_at_index


def _trendline_case() -> tuple[pd.DataFrame, TrendlineBreakConfig, int, Callable, Callable]:
    candles = _rows(
        [
            {"open": 9.0, "high": 10.0, "low": 8.0, "close": 9.0},
            {"open": 14.0, "high": 15.0, "low": 9.0, "close": 14.0},
            {"open": 11.0, "high": 12.0, "low": 8.0, "close": 11.0},
            {"open": 12.0, "high": 13.0, "low": 9.0, "close": 12.0},
            {"open": 13.0, "high": 14.0, "low": 9.0, "close": 13.0},
            {"open": 11.0, "high": 12.0, "low": 8.0, "close": 12.0},
            {"open": 11.0, "high": 14.5, "low": 11.0, "close": 14.2, "volume": 500.0},
        ],
        base_price=10.0,
    )
    config = TrendlineBreakConfig(
        minimum_trendline_length=1,
        pivot_config=_pivot_config(),
        atr_config=AtrConfig(period=1),
        volume_ratio_config=_volume_config(),
        displacement_config=DisplacementCandleConfig(
            minimum_range_atr_multiplier=0.1,
            minimum_volume_ratio=1.3,
        ),
    )
    return candles, config, 6, detect_trendline_breaks, detect_trendline_breaks_at_index


def _cup_case() -> tuple[pd.DataFrame, CupAndHandleConfig, int, Callable, Callable]:
    candles = _rows(
        [
            {"open": 90.0, "high": 92.0, "low": 89.0, "close": 91.0},
            {"open": 96.0, "high": 100.0, "low": 95.0, "close": 99.0},
            {"open": 92.0, "high": 93.0, "low": 88.0, "close": 89.0},
            {"open": 82.0, "high": 83.0, "low": 80.0, "close": 81.0},
            {"open": 81.0, "high": 82.0, "low": 79.0, "close": 81.0},
            {"open": 81.0, "high": 82.0, "low": 80.0, "close": 81.0},
            {"open": 88.0, "high": 90.0, "low": 86.0, "close": 89.0},
            {"open": 96.0, "high": 99.0, "low": 95.0, "close": 98.0},
            {"open": 95.0, "high": 98.0, "low": 95.0, "close": 97.0},
            {"open": 96.0, "high": 97.0, "low": 94.0, "close": 95.0},
            {"open": 96.0, "high": 99.0, "low": 95.0, "close": 98.0},
            {"open": 99.0, "high": 104.0, "low": 98.0, "close": 103.0, "volume": 500.0},
        ]
    )
    config = CupAndHandleConfig(
        pivot_config=_pivot_config(),
        atr_config=AtrConfig(period=2),
        volume_ratio_config=_volume_config(1.5),
        minimum_cup_duration=4,
        maximum_cup_duration=12,
        minimum_handle_duration=2,
        maximum_handle_duration=5,
        minimum_bottom_zone_duration=2,
        bottom_zone_atr_multiplier=1.0,
        require_prior_uptrend=False,
    )
    return candles, config, 11, detect_cup_and_handle_patterns, detect_cup_and_handle_patterns_at_index


def _diamond_case() -> tuple[pd.DataFrame, DiamondConfig, int, Callable, Callable]:
    candles = _rows(
        [
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"open": 104.0, "high": 105.0, "low": 103.0, "close": 104.0},
            {"open": 96.0, "high": 97.0, "low": 95.0, "close": 96.0},
            {"open": 114.0, "high": 115.0, "low": 113.0, "close": 114.0},
            {"open": 86.0, "high": 87.0, "low": 85.0, "close": 86.0},
            {"open": 109.0, "high": 110.0, "low": 108.0, "close": 109.0},
            {"open": 91.0, "high": 92.0, "low": 90.0, "close": 91.0},
            {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0},
            {"open": 97.0, "high": 98.0, "low": 96.0, "close": 97.0},
            {"open": 98.0, "high": 100.0, "low": 97.0, "close": 98.0},
            {"open": 111.0, "high": 113.0, "low": 110.0, "close": 112.0, "volume": 500.0},
        ]
    )
    config = DiamondConfig(
        pivot_config=_pivot_config(),
        atr_config=AtrConfig(period=2),
        volume_ratio_config=_volume_config(1.5),
        minimum_pattern_duration=7,
        maximum_pattern_duration=20,
        minimum_expansion_range_change_atr=0.5,
        minimum_pattern_height_atr=1.0,
        maximum_pattern_height_atr=10.0,
    )
    return candles, config, 10, detect_diamond_patterns, detect_diamond_patterns_at_index


def _adam_case() -> tuple[pd.DataFrame, AdamAndEveConfig, int, Callable, Callable]:
    candles = _rows(
        [
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"open": 90.0, "high": 92.0, "low": 88.0, "close": 89.0},
            {"open": 82.0, "high": 90.0, "low": 80.0, "close": 83.0},
            {"open": 88.0, "high": 92.0, "low": 86.0, "close": 90.0},
            {"open": 96.0, "high": 100.0, "low": 95.0, "close": 99.0},
            {"open": 90.0, "high": 93.0, "low": 86.0, "close": 88.0},
            {"open": 84.0, "high": 88.0, "low": 82.0, "close": 85.0},
            {"open": 83.0, "high": 87.0, "low": 81.0, "close": 84.0},
            {"open": 84.0, "high": 86.0, "low": 82.0, "close": 84.0},
            {"open": 84.0, "high": 87.0, "low": 83.0, "close": 85.0},
            {"open": 86.0, "high": 90.0, "low": 84.0, "close": 88.0},
            {"open": 90.0, "high": 95.0, "low": 89.0, "close": 94.0},
            {"open": 101.0, "high": 106.0, "low": 100.0, "close": 104.0, "volume": 500.0},
        ]
    )
    config = AdamAndEveConfig(
        pivot_config=_pivot_config(),
        atr_config=AtrConfig(period=2),
        volume_ratio_config=_volume_config(1.5),
        minimum_pattern_duration=6,
        maximum_pattern_duration=20,
        adam_left_window=1,
        adam_right_window=1,
        maximum_adam_bottom_duration=3,
        minimum_eve_bottom_duration=5,
        minimum_eve_bottom_zone_duration=3,
        bottom_zone_atr_multiplier=1.0,
        minimum_adam_range_atr=0.5,
        minimum_eve_to_adam_duration_ratio=1.5,
        minimum_pattern_height_atr=1.0,
        maximum_pattern_height_atr=10.0,
        require_prior_downtrend=False,
    )
    return candles, config, 12, detect_adam_and_eve_patterns, detect_adam_and_eve_patterns_at_index


@pytest.mark.parametrize(
    "case_factory",
    [_fvg_case, _order_block_case, _trendline_case, _cup_case, _diamond_case, _adam_case],
)
def test_at_index_detection_matches_rolling_prefix_end_index(case_factory: Callable) -> None:
    candles, config, current_index, detect_all, detect_at_index = case_factory()

    prefix_events = detect_all(
        candles.iloc[: current_index + 1],
        symbol="BTCUSDT",
        timeframe="1m",
        config=config,
    )
    expected = [event for event in prefix_events if event.end_index == current_index]
    actual = detect_at_index(
        candles,
        current_index,
        symbol="BTCUSDT",
        timeframe="1m",
        config=config,
    )

    assert [event.event_id for event in actual] == [event.event_id for event in expected]
    assert actual


def test_fvg_default_detection_ignores_future_lifecycle_break() -> None:
    candles, config, _, _, _ = _fvg_case()
    future_break = _rows([{"open": 101.0, "high": 102.0, "low": 98.0, "close": 98.5}])
    future_break["timestamp"] = ["2026-05-16T00:03:00Z"]
    full = pd.concat([candles, future_break], ignore_index=True)

    events = detect_fair_value_gaps(full, symbol="BTCUSDT", timeframe="1m", config=config)
    retrospective = detect_fair_value_gaps(
        full,
        symbol="BTCUSDT",
        timeframe="1m",
        config=FairValueGapConfig(**{**config.__dict__, "retrospective_lifecycle": True}),
    )

    assert len(events) == 1
    assert events[0].fvg_state == "FRESH"
    assert retrospective == []


def test_order_block_default_detection_ignores_future_lifecycle_break() -> None:
    candles, config, _, _, _ = _order_block_case()
    future_break = _rows([{"open": 101.0, "high": 102.0, "low": 97.0, "close": 97.5}])
    future_break["timestamp"] = ["2026-05-16T00:02:00Z"]
    full = pd.concat([candles, future_break], ignore_index=True)

    events = detect_order_blocks(full, symbol="BTCUSDT", timeframe="1m", config=config)
    retrospective = detect_order_blocks(
        full,
        symbol="BTCUSDT",
        timeframe="1m",
        config=OrderBlockConfig(**{**config.__dict__, "retrospective_lifecycle": True}),
    )

    assert len(events) == 1
    assert events[0].order_block_state == "FRESH"
    assert retrospective == []
