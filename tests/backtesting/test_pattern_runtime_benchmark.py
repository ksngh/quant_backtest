from __future__ import annotations

import time

import pandas as pd
import pytest

from quant_bitcoin.backtesting.fvg_detection_cache import IndicatorCache, PatternEvaluationContext
from quant_bitcoin.strategies.patterns import strategy_for_pattern

_PATTERN_KEYS = (
    "FAIR_VALUE_GAP",
    "ORDER_BLOCK",
    "TRENDLINE_BREAK",
    "CUP_AND_HANDLE",
    "DIAMOND",
    "ADAM_AND_EVE",
)


@pytest.fixture
def candles_400() -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    price = 100.0
    for i in range(400):
        drift = 1.0 if i % 2 == 0 else -0.6
        rows.append(
            {
                "symbol": "BTCUSDT",
                "timestamp": i + 1,
                "open": price,
                "high": price + 2.0 + (i % 3) * 0.1,
                "low": price - 2.0 - (i % 5) * 0.1,
                "close": price + drift,
                "volume": 1000 + i,
            }
        )
        price += 0.2
    return pd.DataFrame(rows)


def _run_pattern(candles: pd.DataFrame, pattern_key: str) -> tuple[int, int, float]:
    strategy = strategy_for_pattern(pattern_key)
    cache = IndicatorCache.for_pattern(candles, getattr(strategy, "detector_config", None))
    actions = 0
    events = 0
    seen: set[str] = set()

    started = time.perf_counter()
    for current_index in range(len(candles)):
        context = PatternEvaluationContext(
            candles=candles,
            current_index=current_index,
            indicator_cache=cache,
            seen_event_ids=seen,
        )
        emitted = strategy.evaluate_at(context)
        actions += len(emitted)
        events = len(seen)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return actions, events, elapsed_ms


@pytest.mark.parametrize("pattern_key", _PATTERN_KEYS)
def test_pattern_paths_emit_actions_without_pathological_growth(candles_400: pd.DataFrame, pattern_key: str) -> None:
    actions, events, _ = _run_pattern(candles_400, pattern_key)
    assert events <= len(candles_400)
    assert actions <= len(candles_400)


@pytest.mark.benchmark
def test_pattern_runtime_benchmark_smoke(candles_400: pd.DataFrame) -> None:
    results = []
    for pattern_key in _PATTERN_KEYS:
        actions, events, elapsed_ms = _run_pattern(candles_400, pattern_key)
        results.append((pattern_key, len(candles_400), elapsed_ms, events, actions))

    for pattern_key, candle_count, elapsed_ms, events, actions in results:
        print(
            f"pattern={pattern_key} candles={candle_count} elapsed_ms={elapsed_ms:.2f} "
            f"events={events} actions={actions}"
        )
