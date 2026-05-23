from __future__ import annotations

import pandas as pd

from quant_bitcoin.backtesting.fvg_detection_cache import (
    IndicatorCache,
    PatternEvaluationContext,
    detect_fair_value_gap_at_index,
    detect_order_block_at_index,
)
from quant_bitcoin.patterns.fair_value_gap import FairValueGapConfig, detect_fair_value_gaps
from quant_bitcoin.patterns.order_block import OrderBlockConfig, detect_order_blocks
from quant_bitcoin.strategies.patterns import FairValueGapStrategy, OrderBlockStrategy
from quant_bitcoin.indicators.atr import AtrConfig
from quant_bitcoin.indicators.volume_ratio import VolumeRatioConfig


def _candles() -> pd.DataFrame:
    rows = []
    price = 100.0
    for i in range(40):
        rows.append({"timestamp": i + 1, "open": price, "high": price + 2, "low": price - 2, "close": price + 1, "volume": 100 + i})
        price += 0.5
    return pd.DataFrame(rows)


def test_fvg_optimized_strategy_actions_match_prefix_path() -> None:
    candles = _candles()
    strategy = FairValueGapStrategy()

    prefix_actions = []
    for i in range(1, len(candles) + 1):
        prefix_actions.extend(strategy.evaluate(candles.iloc[:i]))

    cache = IndicatorCache.for_fvg(candles, strategy.detector_config)
    optimized_actions = []
    seen: set[str] = set()
    for i in range(1, len(candles) + 1):
        context = PatternEvaluationContext(candles=candles, current_index=i - 1, indicator_cache=cache, seen_event_ids=seen)
        optimized_actions.extend(strategy.evaluate_at(context))

    assert [(a.action_type.value, a.timestamp) for a in optimized_actions] == [
        (a.action_type.value, a.timestamp) for a in prefix_actions
    ]


def test_fvg_cache_builds_indicators_once() -> None:
    candles = _candles()
    strategy = FairValueGapStrategy()
    cache = IndicatorCache.for_fvg(candles, strategy.detector_config)
    assert len(cache.candles) == len(candles)
    assert "atr" in cache.candles.columns
    assert "volume_ratio" in cache.candles.columns


def test_detect_fair_value_gaps_prefix_consistency_sanity() -> None:
    candles = _candles()
    full = detect_fair_value_gaps(candles)
    rebuilt = []
    for i in range(3, len(candles) + 1):
        rebuilt.extend([e for e in detect_fair_value_gaps(candles.iloc[:i]) if e.end_index == i - 1])
    assert [e.event_id for e in rebuilt] == [e.event_id for e in full]


def test_fvg_optimized_detection_not_affected_by_future_fill_or_break() -> None:
    base = pd.DataFrame(
        [
            {"timestamp": 1, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 100},
            {"timestamp": 2, "open": 101, "high": 104, "low": 100, "close": 103, "volume": 160},
            {"timestamp": 3, "open": 106, "high": 108, "low": 106, "close": 107, "volume": 180},
        ]
    )
    appended = pd.concat(
        [
            base,
            pd.DataFrame(
                [
                    {"timestamp": 4, "open": 107, "high": 108, "low": 100, "close": 101, "volume": 200},
                    {"timestamp": 5, "open": 101, "high": 102, "low": 98, "close": 99, "volume": 210},
                ]
            ),
        ],
        ignore_index=True,
    )
    config = FairValueGapConfig(
        require_displacement_candle=False,
        minimum_volume_ratio=0.0,
        minimum_pattern_score=0.0,
        atr_config=AtrConfig(period=2),
        volume_ratio_config=VolumeRatioConfig(window=2),
    )

    prefix_cache = IndicatorCache.for_fvg(base, config)
    prefix_context = PatternEvaluationContext(
        candles=base,
        current_index=2,
        indicator_cache=prefix_cache,
    )
    prefix_events = detect_fair_value_gap_at_index(prefix_context, config=config)

    full_cache = IndicatorCache.for_fvg(appended, config)
    full_context = PatternEvaluationContext(
        candles=appended,
        current_index=2,
        indicator_cache=full_cache,
    )
    full_events = detect_fair_value_gap_at_index(full_context, config=config)

    assert len(prefix_events) == 1
    assert len(full_events) == 1
    assert full_events[0].event_id == prefix_events[0].event_id
    assert full_events[0].direction == prefix_events[0].direction
    assert full_events[0].pattern_status == prefix_events[0].pattern_status
    assert full_events[0].entry_reference == prefix_events[0].entry_reference
    assert full_events[0].stop_reference == prefix_events[0].stop_reference
    assert full_events[0].target_reference == prefix_events[0].target_reference


def test_fvg_optimized_cache_matches_rolling_prefix_detection() -> None:
    candles = _candles()
    strategy = FairValueGapStrategy()
    config = strategy.detector_config
    cache = IndicatorCache.for_fvg(candles, config)
    seen: set[str] = set()

    for current_index in range(2, len(candles)):
        context = PatternEvaluationContext(
            candles=candles,
            current_index=current_index,
            indicator_cache=cache,
            seen_event_ids=seen.copy(),
        )
        optimized = detect_fair_value_gap_at_index(context, config=config)
        prefix_events = detect_fair_value_gaps(candles.iloc[: current_index + 1], config=config)
        expected = [event for event in prefix_events if event.end_index == current_index]
        assert [event.event_id for event in optimized] == [event.event_id for event in expected]


def test_order_block_optimized_cache_matches_rolling_prefix_detection() -> None:
    candles = _candles()
    strategy = OrderBlockStrategy()
    config = OrderBlockConfig(
        minimum_displacement_atr_multiplier=0.0,
        minimum_volume_ratio=0.0,
        weak_volume_ratio=0.0,
        minimum_pattern_score=0.0,
        weak_pattern_score=0.0,
    )
    cache = IndicatorCache.for_pattern(candles, config)
    seen: set[str] = set()

    for current_index in range(1, len(candles)):
        context = PatternEvaluationContext(
            candles=candles,
            current_index=current_index,
            indicator_cache=cache,
            seen_event_ids=seen.copy(),
        )
        optimized = detect_order_block_at_index(context, config=config)
        prefix_events = detect_order_blocks(candles.iloc[: current_index + 1], config=config)
        expected = [event for event in prefix_events if event.end_index == current_index]
        assert [event.event_id for event in optimized] == [event.event_id for event in expected]
