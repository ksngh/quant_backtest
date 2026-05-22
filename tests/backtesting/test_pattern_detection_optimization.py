from __future__ import annotations

import pandas as pd

from quant_bitcoin.backtesting.pattern_detection_cache import IndicatorCache, PatternEvaluationContext
from quant_bitcoin.patterns.fair_value_gap import detect_fair_value_gaps
from quant_bitcoin.strategies.patterns import FairValueGapStrategy


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
