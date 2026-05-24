from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from quant_bitcoin.indicators import AtrConfig, PivotConfig, VolumeRatioConfig
from quant_bitcoin.patterns import (
    DiamondConfig,
    DiamondStatus,
    detect_diamond_patterns,
    filter_new_events,
)


def _config(**overrides: object) -> DiamondConfig:
    values = {
        "pivot_config": PivotConfig(
            left_window=1,
            right_window=1,
            minimum_distance_between_pivots=1,
        ),
        "atr_config": AtrConfig(period=2),
        "volume_ratio_config": VolumeRatioConfig(
            window=2,
            minimum_volume_ratio_for_confirmation=1.5,
            high_volume_ratio_threshold=2.0,
            require_full_window=False,
        ),
        "minimum_pattern_duration": 7,
        "maximum_pattern_duration": 20,
        "minimum_expansion_range_change_atr": 0.5,
        "minimum_pattern_height_atr": 1.0,
        "maximum_pattern_height_atr": 10.0,
    }
    values.update(overrides)
    return DiamondConfig(**values)


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


def _diamond_candles(*, breakout_close: float = 112.0, breakout_volume: float = 500.0) -> pd.DataFrame:
    return _candles(
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
            {
                "open": 111.0,
                "high": 113.0,
                "low": 110.0,
                "close": breakout_close,
                "volume": breakout_volume,
            },
        ]
    )


def _ten_pivot_diamond_candles(
    *,
    middle_contraction_high: float = 107.0,
    middle_contraction_low: float = 94.0,
) -> pd.DataFrame:
    return _candles(
        [
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            {"open": 104.0, "high": 105.0, "low": 103.0, "close": 104.0},
            {"open": 96.0, "high": 97.0, "low": 95.0, "close": 96.0},
            {"open": 114.0, "high": 115.0, "low": 113.0, "close": 114.0},
            {"open": 86.0, "high": 87.0, "low": 85.0, "close": 86.0},
            {"open": 109.0, "high": 110.0, "low": 108.0, "close": 109.0},
            {"open": 91.0, "high": 92.0, "low": 90.0, "close": 91.0},
            {
                "open": middle_contraction_high - 1.0,
                "high": middle_contraction_high,
                "low": middle_contraction_high - 2.0,
                "close": middle_contraction_high - 1.0,
            },
            {
                "open": middle_contraction_low + 1.0,
                "high": middle_contraction_low + 2.0,
                "low": middle_contraction_low,
                "close": middle_contraction_low + 1.0,
            },
            {"open": 103.0, "high": 104.0, "low": 102.0, "close": 103.0},
            {"open": 99.0, "high": 100.0, "low": 98.0, "close": 99.0},
            {"open": 101.0, "high": 102.0, "low": 100.0, "close": 101.0},
            {"open": 112.0, "high": 114.0, "low": 111.0, "close": 113.0, "volume": 500.0},
        ]
    )


def test_returns_empty_when_no_diamond_rules_match() -> None:
    candles = _candles(
        [
            {"high": 100.0, "low": 99.0},
            {"high": 101.0, "low": 100.0},
            {"high": 102.0, "low": 101.0},
            {"high": 103.0, "low": 102.0},
        ]
    )

    assert detect_diamond_patterns(candles, symbol="BTCUSDT", config=_config()) == []


def test_detects_bullish_diamond_event() -> None:
    events = detect_diamond_patterns(
        _diamond_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.pattern_type == "DIAMOND_PATTERN"
    assert event.direction == "BULLISH"
    assert event.pattern_status == DiamondStatus.VALID.value
    assert event.symbol == "BTCUSDT"
    assert event.timeframe == "1m"
    assert event.timestamp == "2026-05-16T00:10:00Z"
    assert event.start_index == 1
    assert event.end_index == 10
    assert event.expansion_start_index == 1
    assert event.diamond_center_index == 4
    assert event.contraction_end_index == 8
    assert event.breakout_index == 10
    assert event.source_pivot_indices == (1, 2, 3, 4, 5, 6, 7, 8)
    assert event.split_position == 4
    assert event.expansion_pivot_count == 4
    assert event.contraction_pivot_count == 4
    assert event.boundary_touch_count == 4
    assert event.boundary_deviation_atr == pytest.approx(0.0)
    assert event.alternating_pivot_score == pytest.approx(1.0)
    assert event.upper_boundary_slope == pytest.approx(-3.0)
    assert event.upper_boundary_intercept == pytest.approx(125.0)
    assert event.lower_boundary_slope == pytest.approx(3.0)
    assert event.lower_boundary_intercept == pytest.approx(72.0)
    assert event.upper_boundary_value == pytest.approx(95.0)
    assert event.lower_boundary_value == pytest.approx(102.0)
    assert event.expansion_high_slope == pytest.approx(5.0)
    assert event.expansion_low_slope == pytest.approx(-5.0)
    assert event.contraction_high_slope == pytest.approx(-3.0)
    assert event.contraction_low_slope == pytest.approx(3.0)
    assert event.expansion_range_change == pytest.approx(20.0)
    assert event.contraction_range_change == pytest.approx(12.0)
    assert event.contraction_range_change_rate == pytest.approx(0.6)
    assert event.pattern_height == pytest.approx(30.0)
    assert event.breakout_price == pytest.approx(112.0)
    assert event.breakout_distance == pytest.approx(17.0)
    assert event.breakout_distance_atr > 0.2
    assert event.volume_ratio == pytest.approx(500.0 / 300.0)
    assert event.pattern_score >= 0.7
    assert event.score_components["expansion"]["source"] == "observed_expansion_range_change_atr"
    assert event.score_components["boundary_touch"]["source"] == "observed_boundary_deviation_atr"
    assert event.score_components["alternating_pivots"]["source"] == "observed_pivot_sequence"
    assert event.score_components["liquidity"]["is_placeholder"] is True
    assert event.score_calibration["is_calibrated_probability"] is False
    assert event.entry_reference == pytest.approx(112.0)
    assert event.stop_reference == pytest.approx(102.0)
    assert event.target_reference == pytest.approx(142.0)
    assert event.risk_reward == pytest.approx(3.0)
    assert event.reason


def test_candidate_diagnostics_record_counts_and_rejections() -> None:
    default_events = detect_diamond_patterns(
        _diamond_candles(),
        symbol="BTCUSDT",
        config=_config(),
    )
    diagnostic_events = detect_diamond_patterns(
        _diamond_candles(),
        symbol="BTCUSDT",
        config=_config(enable_candidate_diagnostics=True),
    )

    assert default_events[0].candidate_diagnostics == {}
    diagnostics = diagnostic_events[0].candidate_diagnostics
    assert diagnostics["schema_version"] == "chart_pattern_candidate_diagnostics_v1"
    assert diagnostics["pattern_type"] == "DIAMOND_PATTERN"
    assert diagnostics["candidate_count"] == 3
    assert diagnostics["evaluated_candidate_count"] == 1
    assert diagnostics["selected_rank"] == 1
    assert diagnostics["max_guard_hit"] is False
    assert diagnostics["rejected_by_reason"] == {"window_start_before_history": 2}


def test_candidate_diagnostics_report_diamond_guard_overfit_warning() -> None:
    events = detect_diamond_patterns(
        _ten_pivot_diamond_candles(),
        symbol="BTCUSDT",
        config=_config(
            minimum_pivot_count=8,
            maximum_pivot_count=10,
            max_candidate_windows_per_bar=1,
            enable_candidate_diagnostics=True,
        ),
    )

    diagnostics = events[0].candidate_diagnostics
    assert diagnostics["candidate_count"] == 1
    assert diagnostics["evaluated_candidate_count"] == 1
    assert diagnostics["max_guard_hit"] is True
    assert diagnostics["rejected_by_reason"]["max_candidate_guard_hit"] == 1
    assert "max_candidate_guard_hit" in diagnostics["overfit_warnings"]


def test_detects_bearish_diamond_event() -> None:
    events = detect_diamond_patterns(
        _diamond_candles(breakout_close=85.0),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.direction == "BEARISH"
    assert event.pattern_status == DiamondStatus.VALID.value
    assert event.breakout_price == pytest.approx(85.0)
    assert event.breakout_distance == pytest.approx(17.0)
    assert event.entry_reference == pytest.approx(85.0)
    assert event.stop_reference == pytest.approx(95.0)
    assert event.target_reference == pytest.approx(55.0)
    assert event.risk_reward == pytest.approx(3.0)


def test_insufficient_pivot_history_returns_empty_list() -> None:
    assert (
        detect_diamond_patterns(
            _diamond_candles().iloc[:6],
            symbol="BTCUSDT",
            config=_config(),
        )
        == []
    )


@pytest.mark.parametrize("pivot_count", [6, 7])
def test_six_and_seven_pivot_minimums_are_rejected_as_infeasible(pivot_count: int) -> None:
    with pytest.raises(ValueError, match="minimum_pivot_count must be at least 8"):
        _config(minimum_pivot_count=pivot_count, maximum_pivot_count=pivot_count)


def test_missing_enough_pivot_highs_or_lows_returns_empty_list() -> None:
    assert (
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_pivot_count=8, maximum_pivot_count=8),
        )
        != []
    )
    assert (
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_pivot_count=9, maximum_pivot_count=9),
        )
        == []
    )


def test_boundary_deviation_threshold_affects_candidate_acceptance() -> None:
    accepted = detect_diamond_patterns(
        _ten_pivot_diamond_candles(middle_contraction_high=107.0),
        symbol="BTCUSDT",
        config=_config(minimum_pivot_count=10, maximum_pivot_count=10),
    )
    rejected = detect_diamond_patterns(
        _ten_pivot_diamond_candles(
            middle_contraction_high=109.0,
            middle_contraction_low=91.0,
        ),
        symbol="BTCUSDT",
        config=_config(
            minimum_pivot_count=10,
            maximum_pivot_count=10,
            maximum_boundary_touch_deviation_atr=0.05,
            minimum_contraction_range_change_rate=0.69,
        ),
    )

    assert len(accepted) == 1
    assert accepted[0].split_position == 4
    assert accepted[0].expansion_pivot_count == 4
    assert accepted[0].contraction_pivot_count == 6
    assert accepted[0].boundary_touch_count == 6
    assert accepted[0].boundary_deviation_atr == pytest.approx(0.0)
    assert rejected == []


def test_boundary_deviation_within_threshold_lowers_boundary_score() -> None:
    events = detect_diamond_patterns(
        _ten_pivot_diamond_candles(
            middle_contraction_high=109.0,
            middle_contraction_low=91.0,
        ),
        symbol="BTCUSDT",
        config=_config(
            minimum_pivot_count=10,
            maximum_pivot_count=10,
            maximum_boundary_touch_deviation_atr=0.5,
            minimum_contraction_range_change_rate=0.69,
        ),
    )

    assert len(events) == 1
    assert events[0].boundary_deviation_atr > 0
    assert events[0].score_components["boundary_touch"]["raw_score"] < 1.0


def test_require_alternating_pivots_rejects_non_alternating_sequence() -> None:
    candles = _diamond_candles()
    candles.loc[5, "high"] = 108.0
    candles.loc[5, "low"] = 106.0
    candles.loc[6, "high"] = 110.0
    candles.loc[6, "low"] = 108.0

    assert (
        detect_diamond_patterns(
            candles,
            symbol="BTCUSDT",
            config=_config(require_alternating_pivots=True),
        )
        == []
    )


def test_pattern_duration_outside_configured_bounds_returns_empty_list() -> None:
    assert (
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_pattern_duration=9, maximum_pattern_duration=20),
        )
        == []
    )


def test_invalid_expansion_and_contraction_shapes_return_empty_list() -> None:
    no_expansion = _diamond_candles()
    no_expansion.loc[3, "high"] = 104.0
    no_expansion.loc[3, "low"] = 103.0
    no_contraction = _diamond_candles()
    no_contraction.loc[7, "high"] = 112.0
    no_contraction.loc[7, "low"] = 111.0

    assert detect_diamond_patterns(no_expansion, symbol="BTCUSDT", config=_config()) == []
    assert detect_diamond_patterns(no_contraction, symbol="BTCUSDT", config=_config()) == []


def test_insufficient_expansion_or_contraction_range_returns_empty_list() -> None:
    assert (
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_expansion_range_change_atr=10.0),
        )
        == []
    )
    assert (
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_contraction_range_change_rate=0.9),
        )
        == []
    )


def test_pattern_height_outside_configured_bounds_returns_empty_list() -> None:
    assert (
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_pattern_height_atr=5.0),
        )
        == []
    )
    assert (
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(maximum_pattern_height_atr=2.0),
        )
        == []
    )


def test_breakout_missing_or_without_atr_buffer_returns_empty_list() -> None:
    assert (
        detect_diamond_patterns(
            _diamond_candles(breakout_close=96.0),
            symbol="BTCUSDT",
            config=_config(),
        )
        == []
    )


def test_weak_breakout_volume_produces_weak_event() -> None:
    events = detect_diamond_patterns(
        _diamond_candles(breakout_volume=250.0),
        symbol="BTCUSDT",
        config=_config(),
    )

    assert len(events) == 1
    assert events[0].pattern_status == DiamondStatus.WEAK.value
    assert events[0].volume_ratio == pytest.approx(250.0 / 175.0)


def test_missing_atr_from_warmup_results_in_no_event() -> None:
    events = detect_diamond_patterns(
        _diamond_candles(),
        symbol="BTCUSDT",
        config=_config(atr_config=AtrConfig(period=20)),
    )

    assert events == []


def test_required_displacement_rejects_without_matching_displacement() -> None:
    assert (
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(require_displacement_breakout=True),
        )
        == []
    )


def test_rolling_windows_emit_stable_event_id_and_filter_duplicates() -> None:
    candles = _diamond_candles()

    assert detect_diamond_patterns(candles.iloc[:10], symbol="BTCUSDT", config=_config()) == []

    first = detect_diamond_patterns(
        candles,
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )
    extended = pd.concat(
        [
            candles,
            _candles(
                [
                    {
                        "timestamp": "2026-05-16T00:11:00Z",
                        "open": 112.0,
                        "high": 114.0,
                        "low": 111.0,
                        "close": 113.0,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    second = detect_diamond_patterns(
        extended,
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(first) == 1
    assert len(second) >= 1
    assert first[0].event_id == second[0].event_id

    seen: set[str] = set()
    assert filter_new_events(first, seen) == first
    assert filter_new_events(second, seen) == []


def test_missing_required_columns_raise_clear_error() -> None:
    candles = _diamond_candles().drop(columns=["volume"])

    with pytest.raises(ValueError, match="missing required columns"):
        detect_diamond_patterns(candles, symbol="BTCUSDT", config=_config())


def test_unsorted_candles_raise_clear_error() -> None:
    candles = _diamond_candles().iloc[[1, 0, 2, 3, 4]].copy()

    with pytest.raises(ValueError, match="sorted ascending"):
        detect_diamond_patterns(candles, symbol="BTCUSDT", config=_config())


def test_require_external_filters_without_values_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="liquidity_pass"):
        detect_diamond_patterns(
            _diamond_candles(),
            symbol="BTCUSDT",
            config=_config(require_liquidity_pass=True),
        )


def test_pattern_module_does_not_import_exchange_or_execution_dependencies() -> None:
    module = ast.parse(Path("quant_bitcoin/patterns/diamond.py").read_text())
    forbidden_roots = {"binance", "ccxt"}
    forbidden_prefixes = {
        "quant_bitcoin.execution",
        "quant_bitcoin.market_data.binance_downloader",
        "quant_bitcoin.market_data.binance_websocket",
    }
    imports: list[str] = []
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    assert not any(name.split(".")[0] in forbidden_roots for name in imports)
    assert not any(
        name == forbidden or name.startswith(f"{forbidden}.")
        for forbidden in forbidden_prefixes
        for name in imports
    )
