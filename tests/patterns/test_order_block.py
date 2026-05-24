from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from quant_bitcoin.indicators import (
    AtrConfig,
    PivotConfig,
    SupportResistanceZoneConfig,
    VolumeRatioConfig,
)
from quant_bitcoin.patterns import (
    OrderBlockConfig,
    OrderBlockState,
    OrderBlockStatus,
    OrderBlockZoneDefinition,
    detect_order_blocks,
    filter_new_events,
)


def _config(**overrides: object) -> OrderBlockConfig:
    values = {
        "atr_config": AtrConfig(period=2),
        "volume_ratio_config": VolumeRatioConfig(
            window=2,
            minimum_volume_ratio_for_confirmation=1.3,
            high_volume_ratio_threshold=2.0,
            require_full_window=False,
        ),
    }
    values.update(overrides)
    return OrderBlockConfig(**values)


def _candles(rows: list[dict]) -> pd.DataFrame:
    base_rows = []
    for index, row in enumerate(rows):
        base = {
            "timestamp": f"2026-05-16T00:{index:02d}:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 100.0,
        }
        base.update(row)
        base_rows.append(base)
    return pd.DataFrame(base_rows)


def _bullish_order_block_candles(
    *,
    displacement_volume: float = 500.0,
    later: list[dict] | None = None,
) -> pd.DataFrame:
    rows = [
        {"open": 100.0, "high": 100.0, "low": 99.0, "close": 99.2, "volume": 100.0},
        {
            "open": 99.2,
            "high": 110.0,
            "low": 98.0,
            "close": 109.5,
            "volume": displacement_volume,
        },
    ]
    rows.extend(later or [])
    return _candles(rows)


def _bearish_order_block_candles() -> pd.DataFrame:
    return _candles(
        [
            {"open": 99.0, "high": 100.0, "low": 99.0, "close": 99.8, "volume": 100.0},
            {"open": 99.8, "high": 101.0, "low": 89.0, "close": 89.5, "volume": 500.0},
        ]
    )


def test_returns_empty_when_no_order_block_rules_match() -> None:
    candles = _candles(
        [
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
        ]
    )

    assert detect_order_blocks(candles, symbol="BTCUSDT", config=_config()) == []


def test_detects_bullish_order_block_event() -> None:
    events = detect_order_blocks(
        _bullish_order_block_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.pattern_type == "ORDER_BLOCK"
    assert event.direction == "BULLISH"
    assert event.pattern_status == OrderBlockStatus.WEAK.value
    assert event.order_block_state == OrderBlockState.FRESH.value
    assert event.symbol == "BTCUSDT"
    assert event.timeframe == "1m"
    assert event.timestamp == "2026-05-16T00:01:00Z"
    assert event.source_candle_index == 0
    assert event.displacement_candle_index == 1
    assert event.zone_low == pytest.approx(99.0)
    assert event.zone_high == pytest.approx(100.0)
    assert event.zone_mid == pytest.approx(99.5)
    assert event.zone_size == pytest.approx(1.0)
    assert event.zone_size_atr == pytest.approx(1.0 / 6.5)
    assert event.source_mode == "SINGLE_CANDLE"
    assert event.source_cluster_size == 1
    assert event.detector_input_type == "OHLCV_HEURISTIC"
    assert event.retest_entry_eligible is False
    assert event.zone_definition == OrderBlockZoneDefinition.FULL_RANGE.value
    assert event.displacement_direction == "BULLISH"
    assert event.displacement_range_atr == pytest.approx(12.0 / 6.5)
    assert event.body_ratio == pytest.approx(10.3 / 12.0)
    assert event.volume_ratio == pytest.approx(500.0 / 300.0)
    assert event.mitigation_depth == pytest.approx(0.0)
    assert event.pattern_score == pytest.approx(event.executable_pattern_score)
    assert event.pattern_score < event.diagnostic_pattern_score
    assert event.diagnostic_pattern_score >= 0.6
    assert event.score_components["zone_quality"]["source"] == "observed_zone_size_atr"
    assert event.score_components["structure_confirmation"]["source"] == "missing_context"
    assert event.score_components["structure_confirmation"]["raw_score"] == 0.0
    assert event.score_components["structure_confirmation"]["is_placeholder"] is False
    assert event.score_components["liquidity"]["is_placeholder"] is True
    assert event.score_components["liquidity"]["included_in_executable_score"] is False
    assert event.score_calibration["score_type"] == "heuristic_quality_score"
    assert event.entry_reference == pytest.approx(99.5)
    assert event.stop_reference == pytest.approx(99.0 - 0.2 * 6.5)
    assert event.risk_reward == pytest.approx(2.0)
    assert event.reason


def test_bullish_multi_candle_cluster_is_opt_in_and_deterministic() -> None:
    candles = _candles(
        [
            {"open": 100.0, "high": 101.0, "low": 98.0, "close": 99.0, "volume": 100.0},
            {"open": 99.0, "high": 100.0, "low": 97.0, "close": 98.0, "volume": 120.0},
            {"open": 98.0, "high": 110.0, "low": 97.0, "close": 109.5, "volume": 600.0},
        ]
    )

    single = detect_order_blocks(candles, symbol="BTCUSDT", config=_config(maximum_zone_size_atr_multiplier=2.0))
    cluster = detect_order_blocks(
        candles,
        symbol="BTCUSDT",
        config=_config(
            allow_multi_candle_order_block=True,
            maximum_source_cluster_size=2,
            maximum_zone_size_atr_multiplier=2.0,
        ),
    )

    assert single[0].source_mode == "SINGLE_CANDLE"
    assert single[0].source_cluster_start_index == 1
    assert cluster[0].source_mode == "MULTI_CANDLE_CLUSTER"
    assert cluster[0].source_cluster_start_index == 0
    assert cluster[0].source_cluster_end_index == 1
    assert cluster[0].source_cluster_size == 2
    assert cluster[0].zone_low == pytest.approx(97.0)
    assert cluster[0].zone_high == pytest.approx(101.0)


def test_bearish_multi_candle_cluster_is_symmetric() -> None:
    candles = _candles(
        [
            {"open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0, "volume": 100.0},
            {"open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0, "volume": 120.0},
            {"open": 102.0, "high": 103.0, "low": 90.0, "close": 90.5, "volume": 600.0},
        ]
    )

    events = detect_order_blocks(
        candles,
        symbol="BTCUSDT",
        config=_config(
            allow_multi_candle_order_block=True,
            maximum_source_cluster_size=2,
            maximum_zone_size_atr_multiplier=2.0,
        ),
    )

    assert len(events) == 1
    assert events[0].direction == "BEARISH"
    assert events[0].source_mode == "MULTI_CANDLE_CLUSTER"
    assert events[0].source_cluster_size == 2
    assert events[0].zone_low == pytest.approx(99.0)
    assert events[0].zone_high == pytest.approx(103.0)


def test_detects_bearish_order_block_event() -> None:
    events = detect_order_blocks(
        _bearish_order_block_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.direction == "BEARISH"
    assert event.pattern_status == OrderBlockStatus.WEAK.value
    assert event.order_block_state == OrderBlockState.FRESH.value
    assert event.zone_low == pytest.approx(99.0)
    assert event.zone_high == pytest.approx(100.0)
    assert event.displacement_direction == "BEARISH"
    assert event.displacement_range_atr == pytest.approx(12.0 / 6.5)
    assert event.volume_ratio == pytest.approx(500.0 / 300.0)
    assert event.risk_reward == pytest.approx(2.0)


def test_insufficient_candle_history_returns_empty_list() -> None:
    candles = _bullish_order_block_candles().iloc[:1]

    assert detect_order_blocks(candles, symbol="BTCUSDT", config=_config()) == []


def test_source_candle_not_found_returns_empty_list() -> None:
    candles = _candles(
        [
            {"open": 99.0, "high": 100.0, "low": 99.0, "close": 99.8, "volume": 100.0},
            {"open": 99.8, "high": 110.0, "low": 98.0, "close": 109.5, "volume": 500.0},
        ]
    )

    assert detect_order_blocks(candles, symbol="BTCUSDT", config=_config()) == []


def test_zone_size_too_small_or_too_large_returns_empty_list() -> None:
    candles = _bullish_order_block_candles()

    assert (
        detect_order_blocks(
            candles,
            symbol="BTCUSDT",
            config=_config(minimum_zone_size_atr_multiplier=0.2),
        )
        == []
    )
    assert (
        detect_order_blocks(
            candles,
            symbol="BTCUSDT",
            config=_config(maximum_zone_size_atr_multiplier=0.1),
        )
        == []
    )


def test_weak_displacement_volume_produces_weak_event() -> None:
    events = detect_order_blocks(
        _bullish_order_block_candles(displacement_volume=250.0),
        symbol="BTCUSDT",
        config=_config(),
    )

    assert len(events) == 1
    assert events[0].pattern_status == OrderBlockStatus.WEAK.value
    assert events[0].volume_ratio == pytest.approx(250.0 / 175.0)


def test_missing_atr_or_volume_ratio_from_warmup_results_in_no_event() -> None:
    candles = _bullish_order_block_candles()

    assert (
        detect_order_blocks(
            candles,
            symbol="BTCUSDT",
            config=_config(atr_config=AtrConfig(period=20)),
        )
        == []
    )
    assert (
        detect_order_blocks(
            candles,
            symbol="BTCUSDT",
            config=_config(
                volume_ratio_config=VolumeRatioConfig(
                    window=20,
                    minimum_volume_ratio_for_confirmation=1.3,
                    high_volume_ratio_threshold=2.0,
                    require_full_window=True,
                )
            ),
        )
        == []
    )


@pytest.mark.parametrize(
    "later_candle, expected_state, expected_depth",
    [
        ({"open": 102.0, "high": 103.0, "low": 102.0, "close": 102.5}, "FRESH", 0.0),
        ({"open": 101.0, "high": 102.0, "low": 99.8, "close": 101.0}, "TOUCHED", 0.2),
        ({"open": 101.0, "high": 102.0, "low": 99.5, "close": 101.0}, "MITIGATED", 0.5),
    ],
)
def test_order_block_state_classification(
    later_candle: dict, expected_state: str, expected_depth: float
) -> None:
    events = detect_order_blocks(
        _bullish_order_block_candles(later=[later_candle]),
        symbol="BTCUSDT",
        config=_config(retrospective_lifecycle=True, weak_pattern_score=0.0),
    )

    assert len(events) == 1
    assert events[0].order_block_state == expected_state
    assert events[0].mitigation_depth == pytest.approx(expected_depth)


def test_retest_event_emission_uses_visible_post_displacement_candles() -> None:
    events = detect_order_blocks(
        _bullish_order_block_candles(
            later=[{"open": 101.0, "high": 102.0, "low": 99.5, "close": 101.0}]
        ),
        symbol="BTCUSDT",
        config=_config(emit_retest_events=True, retest_entry_max_wait_bars=2, weak_pattern_score=0.0),
    )

    assert len(events) == 1
    assert events[0].order_block_state == OrderBlockState.MITIGATED.value
    assert events[0].end_index == 2
    assert events[0].retest_entry_eligible is True
    assert events[0].retest_wait_bars == 1


def test_retest_event_skips_when_no_touch_within_wait_window() -> None:
    events = detect_order_blocks(
        _bullish_order_block_candles(
            later=[{"open": 102.0, "high": 103.0, "low": 102.0, "close": 102.5}]
        ),
        symbol="BTCUSDT",
        config=_config(emit_retest_events=True, retest_entry_max_wait_bars=1),
    )

    assert events == []


def test_broken_zone_is_not_emitted_as_valid_reference() -> None:
    events = detect_order_blocks(
        _bullish_order_block_candles(
            later=[{"open": 101.0, "high": 102.0, "low": 97.0, "close": 97.5}]
        ),
        symbol="BTCUSDT",
        config=_config(retrospective_lifecycle=True),
    )

    assert events == []


def test_rolling_windows_emit_event_when_displacement_candle_arrives() -> None:
    candles = _bullish_order_block_candles()

    assert detect_order_blocks(candles.iloc[:1], symbol="BTCUSDT", config=_config()) == []
    events = detect_order_blocks(candles.iloc[:2], symbol="BTCUSDT", config=_config())

    assert [event.pattern_type for event in events] == ["ORDER_BLOCK"]


def test_event_id_is_stable_across_overlapping_rolling_windows() -> None:
    prefix = _candles(
        [
            {
                "timestamp": "2026-05-16T00:00:00Z",
                "open": 99.5,
                "high": 100.0,
                "low": 99.0,
                "close": 99.5,
            }
        ]
    )
    pattern = _bullish_order_block_candles().assign(
        timestamp=["2026-05-16T00:01:00Z", "2026-05-16T00:02:00Z"]
    )
    suffix = _candles(
        [
            {
                "timestamp": "2026-05-16T00:03:00Z",
                "open": 103.0,
                "high": 104.0,
                "low": 102.0,
                "close": 103.5,
            }
        ]
    )
    candles = pd.concat([prefix, pattern, suffix], ignore_index=True)

    first_window_events = detect_order_blocks(
        candles.iloc[:3], symbol="BTCUSDT", timeframe="1m", config=_config()
    )
    second_window_events = detect_order_blocks(
        candles.iloc[1:4], symbol="BTCUSDT", timeframe="1m", config=_config()
    )

    assert len(first_window_events) == 1
    assert len(second_window_events) == 1
    assert first_window_events[0].event_id == second_window_events[0].event_id


def test_filter_new_events_can_deduplicate_order_block_events() -> None:
    events = detect_order_blocks(
        _bullish_order_block_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )
    seen_event_ids: set[str] = set()

    assert filter_new_events(events, seen_event_ids) == events
    assert filter_new_events(events, seen_event_ids) == []
    assert seen_event_ids == {events[0].event_id}


def test_missing_required_candle_column_raises_clear_error() -> None:
    candles = _bullish_order_block_candles().drop(columns=["volume"])

    with pytest.raises(ValueError, match="missing required candle columns: volume"):
        detect_order_blocks(candles, symbol="BTCUSDT", config=_config())


def test_unsorted_candle_input_is_rejected() -> None:
    candles = _bullish_order_block_candles().iloc[[1, 0]]

    with pytest.raises(ValueError, match="candles must be sorted ascending by timestamp"):
        detect_order_blocks(candles, symbol="BTCUSDT", config=_config())


def test_detector_accepts_standard_schema_without_binance_raw_fields() -> None:
    candles = _bullish_order_block_candles()

    assert list(candles.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert len(detect_order_blocks(candles, symbol="BTCUSDT", config=_config())) == 1


def test_bearish_order_block_near_confirmed_resistance_gets_observed_context_score() -> None:
    candles = _candles(
        [
            {"open": 100.0, "high": 104.0, "low": 94.0, "close": 98.0},
            {"open": 106.0, "high": 110.0, "low": 100.0, "close": 105.0},
            {"open": 100.0, "high": 104.0, "low": 94.0, "close": 98.0},
            {"open": 106.0, "high": 109.8, "low": 100.0, "close": 105.0},
            {"open": 100.0, "high": 104.0, "low": 94.0, "close": 98.0},
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0},
            {"open": 101.0, "high": 101.5, "low": 89.0, "close": 90.0, "volume": 500.0},
        ]
    )

    events = detect_order_blocks(
        candles,
        symbol="BTCUSDT",
        config=_config(
            minimum_displacement_atr_multiplier=0.8,
            minimum_pattern_score=0.0,
            weak_pattern_score=0.0,
            maximum_zone_size_atr_multiplier=1.0,
            pivot_config=PivotConfig(
                left_window=1,
                right_window=1,
                minimum_distance_between_pivots=1,
            ),
            support_resistance_config=SupportResistanceZoneConfig(
                minimum_touch_count=2,
                zone_width_atr_multiplier=1.5,
                maximum_zone_width_rate=0.3,
                merge_overlapping_zones=False,
            ),
        ),
    )

    assert len(events) == 1
    component = events[0].score_components["support_resistance_context"]
    assert events[0].direction == "BEARISH"
    assert component["source"] == "observed_support_resistance_proximity"
    assert component["is_placeholder"] is False
    assert component["metadata"]["context"] == "NEAR_RESISTANCE"
    assert component["metadata"]["expected_zone_type"] == "RESISTANCE"


def test_requiring_unavailable_liquidity_or_spread_filters_needs_explicit_values() -> None:
    with pytest.raises(ValueError, match="liquidity_pass must be supplied"):
        detect_order_blocks(
            _bullish_order_block_candles(),
            symbol="BTCUSDT",
            config=_config(require_liquidity_pass=True),
        )

    with pytest.raises(ValueError, match="spread_pass must be supplied"):
        detect_order_blocks(
            _bullish_order_block_candles(),
            symbol="BTCUSDT",
            config=_config(require_spread_pass=True),
        )


def test_order_block_module_does_not_import_exchange_clients_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/order_block.py")
    tree = ast.parse(source_path.read_text())
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)

    assert not any(module.startswith("quant_bitcoin.market_data") for module in imported_modules)
    assert not any(module.startswith("quant_bitcoin.execution") for module in imported_modules)
    assert not any("binance" in module.lower() for module in imported_modules)
