from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from quant_bitcoin.indicators import AtrConfig, PivotConfig, VolumeRatioConfig
from quant_bitcoin.patterns import (
    AdamAndEveConfig,
    AdamAndEveStatus,
    detect_adam_and_eve_patterns,
    filter_new_events,
)
from quant_bitcoin.patterns.adam_and_eve import _prior_downtrend_metadata


def _config(**overrides: object) -> AdamAndEveConfig:
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
        "minimum_pattern_duration": 6,
        "maximum_pattern_duration": 20,
        "adam_left_window": 1,
        "adam_right_window": 1,
        "maximum_adam_bottom_duration": 3,
        "minimum_eve_bottom_duration": 5,
        "minimum_eve_bottom_zone_duration": 3,
        "bottom_zone_atr_multiplier": 1.0,
        "minimum_adam_range_atr": 0.5,
        "minimum_eve_to_adam_duration_ratio": 1.5,
        "minimum_pattern_height_atr": 1.0,
        "maximum_pattern_height_atr": 10.0,
        "require_prior_downtrend": False,
    }
    values.update(overrides)
    return AdamAndEveConfig(**values)


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


def _adam_and_eve_candles(
    *, breakout_close: float = 104.0, breakout_volume: float = 500.0
) -> pd.DataFrame:
    return _candles(
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
            {
                "open": 101.0,
                "high": 106.0,
                "low": 100.0,
                "close": breakout_close,
                "volume": breakout_volume,
            },
        ]
    )


def test_returns_empty_when_no_adam_and_eve_rules_match() -> None:
    candles = _candles(
        [
            {"high": 100.0, "low": 99.0},
            {"high": 101.0, "low": 100.0},
            {"high": 102.0, "low": 101.0},
            {"high": 103.0, "low": 102.0},
        ]
    )

    assert detect_adam_and_eve_patterns(candles, symbol="BTCUSDT", config=_config()) == []


def test_detects_bullish_adam_and_eve_event() -> None:
    events = detect_adam_and_eve_patterns(
        _adam_and_eve_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.pattern_type == "ADAM_AND_EVE_PATTERN"
    assert event.direction == "BULLISH"
    assert event.pattern_status == AdamAndEveStatus.VALID.value
    assert event.symbol == "BTCUSDT"
    assert event.timeframe == "1m"
    assert event.timestamp == "2026-05-16T00:12:00Z"
    assert event.start_index == 2
    assert event.end_index == 12
    assert event.adam_low_index == 2
    assert event.neckline_pivot_index == 4
    assert event.eve_low_index == 7
    assert event.breakout_index == 12
    assert event.adam_low_price == pytest.approx(80.0)
    assert event.neckline == pytest.approx(100.0)
    assert event.eve_low_price == pytest.approx(81.0)
    assert event.bottom_difference_rate == pytest.approx(0.0125)
    assert event.adam_bottom_duration == 3
    assert event.eve_bottom_duration == 8
    assert event.eve_bottom_zone_duration == 4
    assert event.adam_local_range_atr == pytest.approx((92.0 - 80.0) / 8.5)
    assert event.eve_to_adam_duration_ratio == pytest.approx(8 / 3)
    assert event.pattern_height == pytest.approx(20.0)
    assert event.breakout_price == pytest.approx(104.0)
    assert event.breakout_distance == pytest.approx(4.0)
    assert event.breakout_distance_atr > 0.2
    assert event.volume_ratio == pytest.approx(500.0 / 300.0)
    assert event.prior_downtrend_method == "local_lookback_close_decline_lower_low"
    assert event.prior_downtrend_strength >= 0.0
    assert event.prior_lower_low_confirmed is True
    assert event.pattern_score >= 0.7
    assert event.score_components["adam_sharpness"]["source"] == "observed_adam_local_range_atr"
    assert event.score_components["eve_roundness"]["weighted_score"] > 0
    assert event.score_calibration["score_type"] == "heuristic_quality_score"
    assert event.entry_reference == pytest.approx(104.0)
    assert event.stop_reference == pytest.approx(81.0)
    assert event.stop_reference_mode == "EVE_LOW"
    assert event.detector_reference_stop == pytest.approx(80.0)
    assert event.detector_reference_risk_reward == pytest.approx(20.0 / 24.0)
    assert event.target_reference == pytest.approx(124.0)
    assert event.risk_reward == pytest.approx(20.0 / 23.0)
    assert event.reason


def test_candidate_diagnostics_are_opt_in_and_report_guard_hits() -> None:
    default_events = detect_adam_and_eve_patterns(
        _adam_and_eve_candles(),
        symbol="BTCUSDT",
        config=_config(),
    )
    diagnostic_events = detect_adam_and_eve_patterns(
        _adam_and_eve_candles(),
        symbol="BTCUSDT",
        config=_config(enable_candidate_diagnostics=True, max_candidates_per_bar=1),
    )

    assert default_events[0].candidate_diagnostics == {}
    diagnostics = diagnostic_events[0].candidate_diagnostics
    assert diagnostics["schema_version"] == "chart_pattern_candidate_diagnostics_v1"
    assert diagnostics["pattern_type"] == "ADAM_AND_EVE_PATTERN"
    assert diagnostics["candidate_count"] == 1
    assert diagnostics["evaluated_candidate_count"] == 1
    assert diagnostics["selected_rank"] == 1
    assert diagnostics["max_guard_hit"] is True
    assert diagnostics["rejected_by_reason"] == {"max_candidate_guard_hit": 1}
    assert "max_candidate_guard_hit" in diagnostics["overfit_warnings"]


def test_insufficient_pivot_history_returns_empty_list() -> None:
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles().iloc[:5],
            symbol="BTCUSDT",
            config=_config(),
        )
        == []
    )


def test_prior_downtrend_missing_returns_empty_list_when_required() -> None:
    candles = _adam_and_eve_candles()
    candles.loc[0, "close"] = 70.0
    candles.loc[0, "low"] = 69.0

    assert (
        detect_adam_and_eve_patterns(
            candles,
            symbol="BTCUSDT",
            config=_config(require_prior_downtrend=True),
        )
        == []
    )


def test_local_prior_downtrend_is_independent_of_frame_start() -> None:
    config = _config(
        require_prior_downtrend=True,
        prior_downtrend_lookback=1,
        minimum_prior_downtrend_decline_rate=0.05,
    )

    full = detect_adam_and_eve_patterns(
        _adam_and_eve_candles(),
        symbol="BTCUSDT",
        config=config,
    )
    sliced = detect_adam_and_eve_patterns(
        _adam_and_eve_candles().iloc[1:].reset_index(drop=True),
        symbol="BTCUSDT",
        config=config,
    )

    assert len(full) == 1
    assert len(sliced) == 1
    assert full[0].prior_downtrend_method == "local_lookback_close_decline_lower_low"
    assert sliced[0].prior_downtrend_method == "local_lookback_close_decline_lower_low"
    assert full[0].prior_downtrend_strength == pytest.approx(sliced[0].prior_downtrend_strength)


def test_local_prior_downtrend_decline_threshold_and_lower_low_are_configurable() -> None:
    candles = _candles(
        [
            {"close": 100.0, "low": 90.0},
            {"close": 90.0, "low": 79.0},
            {"close": 83.0, "low": 80.0},
        ]
    )

    strict = _prior_downtrend_metadata(
        candles,
        2,
        _config(
            require_prior_downtrend=True,
            prior_downtrend_lookback=1,
            require_prior_lower_low=True,
        ),
    )
    relaxed = _prior_downtrend_metadata(
        candles,
        2,
        _config(
            require_prior_downtrend=True,
            prior_downtrend_lookback=1,
            require_prior_lower_low=False,
        ),
    )

    assert strict["confirmed"] is False
    assert strict["lower_low_confirmed"] is False
    assert relaxed["confirmed"] is True
    assert relaxed["strength"] == pytest.approx((90.0 - 83.0) / 90.0)
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(
                require_prior_downtrend=True,
                prior_downtrend_lookback=1,
                minimum_prior_downtrend_decline_rate=0.2,
            ),
        )
        == []
    )


def test_bottom_mismatch_returns_empty_list() -> None:
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(maximum_bottom_difference_rate=0.005),
        )
        == []
    )


def test_pattern_duration_outside_configured_bounds_returns_empty_list() -> None:
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_pattern_duration=11, maximum_pattern_duration=20),
        )
        == []
    )


def test_adam_not_sharp_or_local_range_too_small_returns_empty_list() -> None:
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(maximum_adam_bottom_duration=2),
        )
        == []
    )
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_adam_range_atr=2.0),
        )
        == []
    )


def test_eve_not_rounded_or_not_wider_than_adam_returns_empty_list() -> None:
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_eve_bottom_zone_duration=5),
        )
        == []
    )
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_eve_to_adam_duration_ratio=3.0),
        )
        == []
    )


def test_pattern_height_below_or_above_configured_bounds_is_deterministic() -> None:
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_pattern_height_atr=5.0),
        )
        == []
    )
    events = detect_adam_and_eve_patterns(
        _adam_and_eve_candles(),
        symbol="BTCUSDT",
        config=_config(maximum_pattern_height_atr=2.0),
    )
    assert len(events) == 1
    assert events[0].pattern_status == AdamAndEveStatus.WEAK.value


def test_breakout_missing_or_without_atr_buffer_returns_empty_list() -> None:
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(breakout_close=101.0),
            symbol="BTCUSDT",
            config=_config(),
        )
        == []
    )


def test_weak_breakout_volume_produces_weak_event() -> None:
    events = detect_adam_and_eve_patterns(
        _adam_and_eve_candles(breakout_volume=250.0),
        symbol="BTCUSDT",
        config=_config(),
    )

    assert len(events) == 1
    assert events[0].pattern_status == AdamAndEveStatus.WEAK.value
    assert events[0].volume_ratio == pytest.approx(250.0 / 175.0)


def test_missing_atr_from_warmup_results_in_no_event() -> None:
    events = detect_adam_and_eve_patterns(
        _adam_and_eve_candles(),
        symbol="BTCUSDT",
        config=_config(atr_config=AtrConfig(period=20)),
    )

    assert events == []


def test_required_displacement_rejects_without_matching_displacement() -> None:
    assert (
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(require_displacement_breakout=True),
        )
        == []
    )


def test_rolling_windows_emit_stable_event_id_and_filter_duplicates() -> None:
    candles = _adam_and_eve_candles()

    assert detect_adam_and_eve_patterns(candles.iloc[:12], symbol="BTCUSDT", config=_config()) == []

    first = detect_adam_and_eve_patterns(
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
                        "timestamp": "2026-05-16T00:13:00Z",
                        "open": 104.0,
                        "high": 107.0,
                        "low": 103.0,
                        "close": 106.0,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    second = detect_adam_and_eve_patterns(
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
    candles = _adam_and_eve_candles().drop(columns=["volume"])

    with pytest.raises(ValueError, match="missing required columns"):
        detect_adam_and_eve_patterns(candles, symbol="BTCUSDT", config=_config())


def test_unsorted_candles_raise_clear_error() -> None:
    candles = _adam_and_eve_candles().iloc[[1, 0, 2, 3, 4]].copy()

    with pytest.raises(ValueError, match="sorted ascending"):
        detect_adam_and_eve_patterns(candles, symbol="BTCUSDT", config=_config())


def test_require_external_filters_without_values_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="liquidity_pass"):
        detect_adam_and_eve_patterns(
            _adam_and_eve_candles(),
            symbol="BTCUSDT",
            config=_config(require_liquidity_pass=True),
        )


def test_pattern_module_does_not_import_exchange_or_execution_dependencies() -> None:
    module = ast.parse(Path("quant_bitcoin/patterns/adam_and_eve.py").read_text())
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
