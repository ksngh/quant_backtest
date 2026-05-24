from __future__ import annotations

import pandas as pd

from quant_bitcoin.backtesting.fvg_detection_cache import (
    IndicatorCache,
    PatternIndicatorCache,
    PatternEvaluationContext,
    detect_adam_and_eve_at_index,
    detect_cup_and_handle_at_index,
    detect_diamond_at_index,
    detect_fair_value_gap_at_index,
    detect_order_block_at_index,
    detect_trendline_break_at_index,
)
from quant_bitcoin.patterns import (
    AdamAndEveConfig,
    CupAndHandleConfig,
    DiamondConfig,
    FairValueGapConfig,
    OrderBlockConfig,
    TrendlineBreakConfig,
    detect_adam_and_eve_patterns,
    detect_cup_and_handle_patterns,
    detect_diamond_patterns,
    detect_fair_value_gaps,
    detect_order_blocks,
    detect_trendline_breaks,
)
from quant_bitcoin.strategies.patterns import FairValueGapStrategy, OrderBlockStrategy, strategy_for_pattern
from quant_bitcoin.indicators.atr import AtrConfig
from quant_bitcoin.indicators.pivots import PivotConfig
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
    assert "confirmed_index" in cache.pivot_rows.columns
    assert cache.calculation_counts == {
        "atr": 1,
        "volume_ratio": 1,
        "displacement_rows": 1,
        "pivot_rows": 1,
        "market_regime_rows": 0,
    }


def test_indicator_cache_for_fvg_alias_still_returns_general_cache() -> None:
    cache = IndicatorCache.for_fvg(_candles(), FairValueGapConfig())
    assert isinstance(cache, PatternIndicatorCache)


def test_indicator_cache_visible_pivots_respect_confirmed_index() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": 1, "open": 10, "high": 10, "low": 9, "close": 10, "volume": 100},
            {"timestamp": 2, "open": 11, "high": 15, "low": 10, "close": 12, "volume": 100},
            {"timestamp": 3, "open": 10, "high": 11, "low": 8, "close": 9, "volume": 100},
            {"timestamp": 4, "open": 11, "high": 14, "low": 10, "close": 13, "volume": 100},
            {"timestamp": 5, "open": 9, "high": 10, "low": 7, "close": 8, "volume": 100},
        ]
    )
    config = TrendlineBreakConfig(
        pivot_config=PivotConfig(left_window=1, right_window=1, minimum_distance_between_pivots=1)
    )
    cache = IndicatorCache.for_pattern(candles, config)

    visible = cache.visible_pivot_rows(2)

    assert not cache.pivot_rows.empty
    assert not visible.empty
    assert visible["confirmed_index"].max() <= 2


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


def test_strategy_for_pattern_uses_shared_context_for_each_pattern() -> None:
    candles = _candles()
    for pattern_key in (
        "FAIR_VALUE_GAP",
        "ORDER_BLOCK",
        "TRENDLINE_BREAK",
        "CUP_AND_HANDLE",
        "DIAMOND",
        "ADAM_AND_EVE",
    ):
        strategy = strategy_for_pattern(pattern_key)
        cache = IndicatorCache.for_pattern(candles, strategy.detector_config)
        seen: set[str] = set()
        actions = []

        for current_index in range(len(candles)):
            context = PatternEvaluationContext(
                candles=candles,
                current_index=current_index,
                indicator_cache=cache,
                seen_event_ids=seen,
            )
            actions.extend(strategy.evaluate_at(context))

        assert len(actions) <= len(candles)
        assert cache.calculation_counts["atr"] == 1
        assert cache.calculation_counts["volume_ratio"] == 1
        assert cache.calculation_counts["pivot_rows"] == 1


def test_cached_at_index_helpers_match_rolling_prefix_for_each_pattern() -> None:
    candles = _candles()
    cases = [
        (FairValueGapConfig(), detect_fair_value_gap_at_index, detect_fair_value_gaps),
        (OrderBlockConfig(), detect_order_block_at_index, detect_order_blocks),
        (TrendlineBreakConfig(), detect_trendline_break_at_index, detect_trendline_breaks),
        (CupAndHandleConfig(), detect_cup_and_handle_at_index, detect_cup_and_handle_patterns),
        (DiamondConfig(), detect_diamond_at_index, detect_diamond_patterns),
        (AdamAndEveConfig(), detect_adam_and_eve_at_index, detect_adam_and_eve_patterns),
    ]

    for config, cached_detect, detect_all in cases:
        cache = IndicatorCache.for_pattern(candles, config)
        for current_index in range(len(candles)):
            context = PatternEvaluationContext(
                candles=candles,
                current_index=current_index,
                indicator_cache=cache,
                seen_event_ids=set(),
            )
            cached_events = cached_detect(context, config=config)
            prefix_events = detect_all(candles.iloc[: current_index + 1], config=config)
            expected = [event for event in prefix_events if event.end_index == current_index]
            assert [event.event_id for event in cached_events] == [event.event_id for event in expected]


def test_cached_at_index_helpers_ignore_appended_future_candles() -> None:
    candles = _candles()
    future = pd.DataFrame(
        [
            {"timestamp": 41, "open": 90, "high": 130, "low": 80, "close": 125, "volume": 10000},
            {"timestamp": 42, "open": 125, "high": 126, "low": 70, "close": 75, "volume": 12000},
        ]
    )
    appended = pd.concat([candles, future], ignore_index=True)
    current_index = 20
    cases = [
        (FairValueGapConfig(), detect_fair_value_gap_at_index),
        (OrderBlockConfig(), detect_order_block_at_index),
        (TrendlineBreakConfig(), detect_trendline_break_at_index),
        (CupAndHandleConfig(), detect_cup_and_handle_at_index),
        (DiamondConfig(), detect_diamond_at_index),
        (AdamAndEveConfig(), detect_adam_and_eve_at_index),
    ]

    for config, cached_detect in cases:
        prefix_cache = IndicatorCache.for_pattern(candles, config)
        prefix_context = PatternEvaluationContext(
            candles=candles,
            current_index=current_index,
            indicator_cache=prefix_cache,
        )
        prefix_events = cached_detect(prefix_context, config=config)

        appended_cache = IndicatorCache.for_pattern(appended, config)
        appended_context = PatternEvaluationContext(
            candles=appended,
            current_index=current_index,
            indicator_cache=appended_cache,
        )
        appended_events = cached_detect(appended_context, config=config)

        assert [event.event_id for event in appended_events] == [
            event.event_id for event in prefix_events
        ]
