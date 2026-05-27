from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd
import pytest

from quant_bitcoin.indicators import (
    AtrConfig,
    DisplacementCandleConfig,
    PivotConfig,
    SupportResistanceZoneConfig,
    VolumeInputMode,
    VolumeRatioBaselineMode,
    VolumeRatioConfig,
)
from quant_bitcoin.patterns import (
    FairValueGapConfig,
    PatternStatus,
    PatternType,
    detect_fair_value_gaps_at_index,
    detect_patterns,
    filter_new_events,
)


def _config(**overrides: object) -> FairValueGapConfig:
    values = {
        "atr_config": AtrConfig(period=1),
        "volume_ratio_config": VolumeRatioConfig(
            window=2,
            minimum_volume_ratio_for_confirmation=1.3,
            high_volume_ratio_threshold=2.0,
            require_full_window=False,
        ),
        "displacement_config": DisplacementCandleConfig(
            minimum_range_atr_multiplier=1.0,
            minimum_volume_ratio=1.3,
        ),
    }
    values.update(overrides)
    return FairValueGapConfig(**values)


def _candles(rows: list[dict]) -> pd.DataFrame:
    base_rows = []
    for index, row in enumerate(rows):
        base = {
            "timestamp": f"2026-05-16T00:0{index}:00Z",
            "open": 99.0,
            "high": 101.0,
            "low": 98.0,
            "close": 100.0,
            "volume": 100.0,
        }
        base.update(row)
        base_rows.append(base)
    return pd.DataFrame(base_rows)


def _valid_bullish_fvg_candles() -> pd.DataFrame:
    return _candles(
        [
            {"open": 98.0, "high": 100.0, "low": 96.0, "close": 99.0, "volume": 100.0},
            {"open": 95.0, "high": 108.0, "low": 94.0, "close": 107.0, "volume": 500.0},
            {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0, "volume": 100.0},
        ]
    )


def _valid_bearish_fvg_candles() -> pd.DataFrame:
    return _candles(
        [
            {"open": 104.0, "high": 106.0, "low": 104.0, "close": 105.0, "volume": 100.0},
            {"open": 107.0, "high": 108.0, "low": 92.0, "close": 93.0, "volume": 500.0},
            {"open": 101.0, "high": 102.0, "low": 98.0, "close": 100.0, "volume": 100.0},
        ]
    )


def _fib_bearish_fvg_candles() -> pd.DataFrame:
    return _candles(
        [
            {"open": 103.0, "high": 106.0, "low": 102.0, "close": 105.0, "volume": 100.0},
            {"open": 107.0, "high": 108.0, "low": 92.0, "close": 93.0, "volume": 500.0},
            {"open": 99.0, "high": 100.0, "low": 96.0, "close": 98.0, "volume": 100.0},
        ]
    )


def _trend_rows(score: float | None, direction: str, timestamp: str = "2026-05-16T00:02:00Z") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "trend_score": score,
                "trend_direction": direction,
                "available_weight": 1.0 if score is not None else 0.0,
                "trend_score_metadata": {
                    "schema_version": "multitimeframe_trend_score_v1",
                    "timestamp": timestamp,
                    "components": {
                        "1m": {
                            "score": score,
                            "direction": direction,
                            "is_available": score is not None,
                        }
                    },
                    "missing_timeframes": [] if score is not None else ["1m"],
                    "diagnostic_only": True,
                },
            }
        ]
    )


def test_returns_empty_when_no_fair_value_gap_rules_match() -> None:
    candles = _candles(
        [
            {"high": 101.0, "low": 98.0},
            {"open": 99.0, "high": 102.0, "low": 98.0, "close": 101.0, "volume": 500.0},
            {"high": 101.5, "low": 99.0},
        ]
    )

    assert detect_patterns(candles, symbol="BTCUSDT", timeframe="1m", config=_config()) == []


def test_detects_one_bullish_fair_value_gap_event() -> None:
    events = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.pattern_type == PatternType.FAIR_VALUE_GAP.value
    assert event.direction == "BULLISH"
    assert event.pattern_status == PatternStatus.WEAK.value
    assert event.symbol == "BTCUSDT"
    assert event.timeframe == "1m"
    assert event.timestamp == "2026-05-16T00:02:00Z"
    assert event.candle_1_index == 0
    assert event.candle_2_index == 1
    assert event.candle_3_index == 2
    assert event.zone_low == pytest.approx(100.0)
    assert event.zone_high == pytest.approx(102.0)
    assert event.zone_mid == pytest.approx(101.0)
    assert event.gap_size == pytest.approx(2.0)
    assert event.gap_size_atr == pytest.approx(0.4)
    assert event.fill_ratio == pytest.approx(0.0)
    assert event.fvg_state == "FRESH"
    assert event.displacement_confirmed is True
    assert event.displacement_direction == "BULLISH"
    assert event.volume_ratio == pytest.approx(500.0 / 300.0)
    assert event.pattern_score == pytest.approx(event.executable_pattern_score)
    assert event.pattern_score < event.diagnostic_pattern_score
    assert event.diagnostic_pattern_score >= 0.7
    assert event.score_components["gap_quality"]["weighted_score"] > 0
    assert event.score_components["liquidity"]["is_placeholder"] is True
    assert event.score_components["liquidity"]["included_in_executable_score"] is False
    assert event.score_component_sources["structure_alignment"] == "missing_context"
    assert event.score_components["structure_alignment"]["raw_score"] == 0.0
    assert event.score_components["structure_alignment"]["is_placeholder"] is False
    assert event.score_components["support_resistance_context"]["source"] == "missing_context"
    assert event.score_calibration["is_calibrated_probability"] is False
    assert event.entry_reference == pytest.approx(101.0)
    assert event.stop_reference == pytest.approx(99.0)
    assert event.target_reference == pytest.approx(105.0)
    assert event.risk_reward == pytest.approx(2.0)
    assert event.reason


def test_fvg_trend_score_diagnostic_mode_records_bullish_alignment_without_score_change() -> None:
    baseline = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )[0]

    event = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(use_multitimeframe_trend_score=True, trend_score_rows=_trend_rows(0.45, "BULLISH")),
    )[0]

    assert event.mtf_trend_score == pytest.approx(0.45)
    assert event.mtf_trend_direction == "BULLISH"
    assert event.mtf_trend_aligned is True
    assert event.pattern_score == pytest.approx(baseline.pattern_score)
    assert "mtf_trend_alignment" in event.score_components
    assert event.score_components["mtf_trend_alignment"]["source"] == "observed_multitimeframe_ema_trend_score"
    assert event.score_components["mtf_trend_alignment"]["metadata"]["signed_score"] == pytest.approx(0.45)


def test_fvg_trend_filter_rejects_bullish_gap_in_bearish_context() -> None:
    events = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(
            use_multitimeframe_trend_score=True,
            require_trend_alignment=True,
            trend_score_rows=_trend_rows(-0.35, "BEARISH"),
        ),
    )

    assert events == []


def test_fvg_trend_filter_accepts_bearish_gap_in_bearish_context() -> None:
    events = detect_patterns(
        _valid_bearish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(
            use_multitimeframe_trend_score=True,
            require_trend_alignment=True,
            trend_score_rows=_trend_rows(-0.35, "BEARISH"),
        ),
    )

    assert len(events) == 1
    assert events[0].direction == "BEARISH"
    assert events[0].mtf_trend_aligned is True
    assert events[0].mtf_trend_score == pytest.approx(-0.35)


def test_fvg_trend_filter_rejects_bearish_gap_in_bullish_context() -> None:
    events = detect_patterns(
        _valid_bearish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(
            use_multitimeframe_trend_score=True,
            require_trend_alignment=True,
            trend_score_rows=_trend_rows(0.35, "BULLISH"),
        ),
    )

    assert events == []


def test_required_fvg_trend_filter_rejects_missing_context() -> None:
    events = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(use_multitimeframe_trend_score=True, require_trend_alignment=True),
    )

    assert events == []


def test_fvg_trend_missing_context_is_explicit_in_diagnostic_mode() -> None:
    event = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(use_multitimeframe_trend_score=True, trend_score_rows=_trend_rows(None, "UNAVAILABLE")),
    )[0]

    component = event.score_components["mtf_trend_alignment"]
    assert event.mtf_trend_score is None
    assert event.mtf_trend_aligned is False
    assert component["is_placeholder"] is True
    assert component["metadata"]["missing_context_reason"] == "UNAVAILABLE_TREND_SCORE"
    assert "mtf_trend_alignment uses placeholder context" in " ".join(event.score_limitations)


def test_default_fvg_config_does_not_emit_trend_metadata() -> None:
    event = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )[0]

    assert event.mtf_trend_score is None
    assert event.mtf_trend_direction is None
    assert event.mtf_trend_aligned is None
    assert event.mtf_trend_metadata == {}
    assert "mtf_trend_alignment" not in event.score_components


def test_fvg_trend_metadata_is_json_serializable() -> None:
    event = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(use_multitimeframe_trend_score=True, trend_score_rows=_trend_rows(0.45, "BULLISH")),
    )[0]

    json.dumps(event.mtf_trend_metadata)
    json.dumps(event.score_components["mtf_trend_alignment"])


def test_fvg_fibonacci_confluence_diagnostic_mode_records_pass_without_score_change() -> None:
    baseline = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )[0]

    event = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(use_fibonacci_confluence=True),
    )[0]

    assert event.fib_confluence_pass is True
    assert event.fib_retracement_level == pytest.approx(0.5)
    assert event.fib_metadata["anchor_method"] == "DISPLACEMENT_CANDLE_RANGE"
    assert event.pattern_score == pytest.approx(baseline.pattern_score)
    assert "fibonacci_confluence" in event.score_components
    assert event.score_components["fibonacci_confluence"]["source"] == "observed_displacement_candle_range"


def test_fvg_fibonacci_hard_filter_rejects_non_confluent_bullish_gap() -> None:
    events = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(
            use_fibonacci_confluence=True,
            require_fibonacci_confluence=True,
            fib_min_level=0.7,
            fib_max_level=0.8,
        ),
    )

    assert events == []


def test_fvg_fibonacci_hard_filter_accepts_bearish_confluent_gap() -> None:
    events = detect_patterns(
        _fib_bearish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(use_fibonacci_confluence=True, require_fibonacci_confluence=True),
    )

    assert len(events) == 1
    assert events[0].direction == "BEARISH"
    assert events[0].fib_confluence_pass is True
    assert events[0].fib_retracement_level == pytest.approx(0.5625)


def test_default_fvg_config_does_not_emit_fibonacci_metadata() -> None:
    event = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )[0]

    assert event.fib_confluence_pass is None
    assert event.fib_retracement_level is None
    assert event.fib_metadata == {}
    assert "fibonacci_confluence" not in event.score_components


def test_fvg_fibonacci_metadata_is_json_serializable() -> None:
    event = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(use_fibonacci_confluence=True),
    )[0]

    json.dumps(event.fib_metadata)
    json.dumps(event.score_components["fibonacci_confluence"])


def test_fvg_event_records_atr_timing_metadata_and_warmup_blocks_early_event() -> None:
    event = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(atr_config=AtrConfig(period=1, smoothing_method="SMA")),
    )[0]

    assert event.atr_metadata["period"] == 1
    assert event.atr_metadata["smoothing_method"] == "SMA"
    assert event.atr_metadata["current_candle_included"] is True
    assert event.atr_metadata["first_valid_index"] == 0
    assert (
        detect_patterns(
            _valid_bullish_fvg_candles(),
            symbol="BTCUSDT",
            timeframe="1m",
            config=_config(atr_config=AtrConfig(period=4)),
        )
        == []
    )


def test_fvg_volume_confirmation_accepts_prior_only_volume_config() -> None:
    events = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(
            volume_ratio_config=VolumeRatioConfig(
                window=1,
                baseline_mode=VolumeRatioBaselineMode.PRIOR_ONLY,
                minimum_volume_ratio_for_confirmation=1.3,
                high_volume_ratio_threshold=2.0,
            )
        ),
    )

    assert len(events) == 1
    assert events[0].volume_ratio == pytest.approx(5.0)
    assert events[0].displacement_confirmed is True


def test_fvg_volume_confirmation_can_use_quote_volume_when_available() -> None:
    candles = _valid_bullish_fvg_candles()
    candles["volume"] = [1.0, 1.0, 1.0]
    candles["quote_volume"] = [1_000.0, 5_000.0, 1_000.0]

    events = detect_patterns(
        candles,
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(
            volume_ratio_config=VolumeRatioConfig(
                window=2,
                require_full_window=False,
                volume_input_mode=VolumeInputMode.QUOTE_VOLUME_IF_AVAILABLE,
                minimum_volume_ratio_for_confirmation=1.3,
                high_volume_ratio_threshold=2.0,
            )
        ),
    )

    assert len(events) == 1
    assert events[0].volume_ratio == pytest.approx(5_000.0 / 3_000.0)
    assert events[0].displacement_confirmed is True


def test_insufficient_candle_history_returns_empty_list() -> None:
    candles = _candles([{}, {}])

    assert detect_patterns(candles, symbol="BTCUSDT", config=_config()) == []


def test_rolling_windows_emit_event_when_completed_candle_arrives() -> None:
    candles = _valid_bullish_fvg_candles()

    assert detect_patterns(candles.iloc[:1], symbol="BTCUSDT", config=_config()) == []
    assert detect_patterns(candles.iloc[:2], symbol="BTCUSDT", config=_config()) == []
    events = detect_patterns(candles.iloc[:3], symbol="BTCUSDT", config=_config())

    assert [event.pattern_type for event in events] == [PatternType.FAIR_VALUE_GAP.value]


def test_event_id_is_stable_across_overlapping_rolling_windows() -> None:
    candles = pd.concat(
        [
            _candles([{"timestamp": "2026-05-16T00:00:00Z"}]),
            _valid_bullish_fvg_candles().assign(
                timestamp=[
                    "2026-05-16T00:01:00Z",
                    "2026-05-16T00:02:00Z",
                    "2026-05-16T00:03:00Z",
                ]
            ),
            _candles(
                [
                    {
                        "timestamp": "2026-05-16T00:04:00Z",
                        "open": 106.0,
                        "high": 110.0,
                        "low": 105.0,
                        "close": 109.0,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    first_window_events = detect_patterns(
        candles.iloc[:4], symbol="BTCUSDT", timeframe="1m", config=_config()
    )
    second_window_events = detect_patterns(
        candles.iloc[1:5], symbol="BTCUSDT", timeframe="1m", config=_config()
    )

    assert len(first_window_events) == 1
    assert len(second_window_events) == 1
    assert first_window_events[0].event_id == second_window_events[0].event_id


def test_filter_new_events_documents_seen_event_id_duplicate_prevention() -> None:
    events = detect_patterns(
        _valid_bullish_fvg_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )
    seen_event_ids: set[str] = set()

    assert filter_new_events(events, seen_event_ids) == events
    assert filter_new_events(events, seen_event_ids) == []
    assert seen_event_ids == {events[0].event_id}


def test_missing_required_candle_column_raises_clear_error() -> None:
    candles = _valid_bullish_fvg_candles().drop(columns=["volume"])

    with pytest.raises(ValueError, match="missing required candle columns: volume"):
        detect_patterns(candles, symbol="BTCUSDT", config=_config())


def test_unsorted_candle_input_is_rejected() -> None:
    candles = _valid_bullish_fvg_candles().iloc[[1, 0, 2]]

    with pytest.raises(ValueError, match="candles must be sorted ascending by timestamp"):
        detect_patterns(candles, symbol="BTCUSDT", config=_config())


def test_detector_accepts_standard_schema_without_binance_raw_fields() -> None:
    candles = _valid_bullish_fvg_candles()

    assert list(candles.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert len(detect_patterns(candles, symbol="BTCUSDT", config=_config())) == 1


def test_bullish_fvg_near_confirmed_support_gets_observed_context_score() -> None:
    candles = _candles(
        [
            {"open": 104.0, "high": 105.0, "low": 99.0, "close": 104.0},
            {"open": 101.0, "high": 103.0, "low": 95.0, "close": 102.0},
            {"open": 103.0, "high": 104.0, "low": 99.0, "close": 103.0},
            {"open": 101.0, "high": 103.0, "low": 95.2, "close": 102.0},
            {"open": 102.0, "high": 104.0, "low": 99.0, "close": 103.0},
            {"open": 98.0, "high": 100.0, "low": 96.0, "close": 99.0},
            {"open": 95.0, "high": 108.0, "low": 94.0, "close": 107.0, "volume": 500.0},
            {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0},
        ]
    )

    events = detect_fair_value_gaps_at_index(
        candles,
        7,
        symbol="BTCUSDT",
        config=_config(
            minimum_pattern_score=0.0,
            pivot_config=PivotConfig(
                left_window=1,
                right_window=1,
                minimum_distance_between_pivots=1,
            ),
            support_resistance_config=SupportResistanceZoneConfig(
                minimum_touch_count=2,
                zone_width_atr_multiplier=1.5,
                maximum_zone_width_rate=0.2,
                merge_overlapping_zones=False,
            ),
        ),
    )

    assert len(events) == 1
    component = events[0].score_components["support_resistance_context"]
    assert component["source"] == "observed_support_resistance_proximity"
    assert component["raw_score"] > 0
    assert component["is_placeholder"] is False
    assert component["metadata"]["context"] == "NEAR_SUPPORT"
    assert component["metadata"]["latest_confirmed_index"] <= 7


def test_fvg_at_index_score_context_is_unchanged_by_future_candles() -> None:
    candles = _candles(
        [
            {"open": 104.0, "high": 105.0, "low": 99.0, "close": 104.0},
            {"open": 101.0, "high": 103.0, "low": 95.0, "close": 102.0},
            {"open": 103.0, "high": 104.0, "low": 99.0, "close": 103.0},
            {"open": 101.0, "high": 103.0, "low": 95.2, "close": 102.0},
            {"open": 102.0, "high": 104.0, "low": 99.0, "close": 103.0},
            {"open": 98.0, "high": 100.0, "low": 96.0, "close": 99.0},
            {"open": 95.0, "high": 108.0, "low": 94.0, "close": 107.0, "volume": 500.0},
            {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0},
        ]
    )
    future = pd.DataFrame(
        [
            {
                "timestamp": "2026-05-16T00:08:00Z",
                "open": 150.0,
                "high": 160.0,
                "low": 149.0,
                "close": 155.0,
                "volume": 100.0,
            },
            {
                "timestamp": "2026-05-16T00:09:00Z",
                "open": 120.0,
                "high": 121.0,
                "low": 118.0,
                "close": 119.0,
                "volume": 100.0,
            },
            {
                "timestamp": "2026-05-16T00:10:00Z",
                "open": 150.0,
                "high": 160.0,
                "low": 149.0,
                "close": 155.0,
                "volume": 100.0,
            },
        ]
    )
    config = _config(
        minimum_pattern_score=0.0,
        pivot_config=PivotConfig(
            left_window=1,
            right_window=1,
            minimum_distance_between_pivots=1,
        ),
        support_resistance_config=SupportResistanceZoneConfig(
            minimum_touch_count=2,
            zone_width_atr_multiplier=1.5,
            maximum_zone_width_rate=0.2,
            merge_overlapping_zones=False,
        ),
    )

    prefix_event = detect_fair_value_gaps_at_index(
        candles, 7, symbol="BTCUSDT", config=config
    )[0]
    extended_event = detect_fair_value_gaps_at_index(
        pd.concat([candles, future], ignore_index=True),
        7,
        symbol="BTCUSDT",
        config=config,
    )[0]

    assert prefix_event.score_components["support_resistance_context"] == (
        extended_event.score_components["support_resistance_context"]
    )


def test_requiring_unavailable_liquidity_or_spread_filters_needs_explicit_values() -> None:
    with pytest.raises(ValueError, match="liquidity_pass must be supplied"):
        detect_patterns(
            _valid_bullish_fvg_candles(),
            symbol="BTCUSDT",
            config=FairValueGapConfig(
                require_liquidity_pass=True,
                atr_config=AtrConfig(period=1),
            ),
        )

    with pytest.raises(ValueError, match="spread_pass must be supplied"):
        detect_patterns(
            _valid_bullish_fvg_candles(),
            symbol="BTCUSDT",
            config=FairValueGapConfig(
                require_spread_pass=True,
                atr_config=AtrConfig(period=1),
            ),
        )


def test_pattern_module_does_not_import_exchange_clients_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/fair_value_gap.py")
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
