from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from quant_bitcoin.indicators import AtrConfig, PivotConfig, VolumeRatioConfig
from quant_bitcoin.patterns import (
    CupAndHandleConfig,
    CupAndHandleStatus,
    detect_cup_and_handle_patterns,
    filter_new_events,
)


def _config(**overrides: object) -> CupAndHandleConfig:
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
        "minimum_cup_duration": 4,
        "maximum_cup_duration": 12,
        "minimum_handle_duration": 2,
        "maximum_handle_duration": 5,
        "minimum_bottom_zone_duration": 2,
        "bottom_zone_atr_multiplier": 1.0,
        "require_prior_uptrend": False,
    }
    values.update(overrides)
    return CupAndHandleConfig(**values)


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


def _valid_cup_and_handle_candles(*, breakout_volume: float = 500.0) -> pd.DataFrame:
    return _candles(
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
            {
                "open": 99.0,
                "high": 104.0,
                "low": 98.0,
                "close": 103.0,
                "volume": breakout_volume,
            },
        ]
    )


def test_returns_empty_when_no_cup_and_handle_rules_match() -> None:
    candles = _candles(
        [
            {"high": 100.0, "low": 99.0},
            {"high": 101.0, "low": 100.0},
            {"high": 102.0, "low": 101.0},
            {"high": 103.0, "low": 102.0},
        ]
    )

    assert detect_cup_and_handle_patterns(candles, symbol="BTCUSDT", config=_config()) == []


def test_detects_bullish_cup_and_handle_event() -> None:
    events = detect_cup_and_handle_patterns(
        _valid_cup_and_handle_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.pattern_type == "CUP_AND_HANDLE"
    assert event.direction == "BULLISH"
    assert event.pattern_status == CupAndHandleStatus.VALID.value
    assert event.symbol == "BTCUSDT"
    assert event.timeframe == "1m"
    assert event.timestamp == "2026-05-16T00:11:00Z"
    assert event.start_index == 1
    assert event.end_index == 11
    assert event.left_rim_index == 1
    assert event.cup_bottom_index == 4
    assert event.right_rim_index == 7
    assert event.handle_low_index == 9
    assert event.breakout_index == 11
    assert event.left_rim_price == pytest.approx(100.0)
    assert event.cup_bottom_price == pytest.approx(79.0)
    assert event.right_rim_price == pytest.approx(99.0)
    assert event.handle_low_price == pytest.approx(94.0)
    assert event.neckline == pytest.approx(100.0)
    assert event.cup_depth == pytest.approx(20.0)
    assert event.cup_depth_rate == pytest.approx(20.0 / 99.0)
    assert event.cup_duration == 6
    assert event.bottom_zone_duration == 3
    assert event.duration_ratio == pytest.approx(1.0)
    assert event.handle_depth == pytest.approx(6.0)
    assert event.handle_depth_ratio == pytest.approx(0.3)
    assert event.handle_duration == 4
    assert event.breakout_price == pytest.approx(103.0)
    assert event.breakout_distance == pytest.approx(3.0)
    assert event.breakout_distance_atr > 0.2
    assert event.volume_ratio == pytest.approx(500.0 / 300.0)
    assert event.prior_uptrend_method == "LOCAL"
    assert event.neckline_retest_status == "NOT_REQUESTED"
    assert event.handle_quality["handle_depth_ratio"] == pytest.approx(0.3)
    assert "detector target_reference" in event.detector_target_reference_semantics
    assert event.pattern_score >= 0.7
    assert event.score_components["roundness"]["source"] == "observed_bottom_duration"
    assert event.score_components["breakout_strength"]["weighted_score"] > 0
    assert event.score_calibration["score_bucket"] in {"MEDIUM", "HIGH"}
    assert event.entry_reference == pytest.approx(103.0)
    assert event.stop_reference == pytest.approx(94.0)
    assert event.target_reference == pytest.approx(123.0)
    assert event.risk_reward == pytest.approx(20.0 / 9.0)
    assert event.reason


def test_candidate_diagnostics_are_opt_in_and_report_guard_hits() -> None:
    default_events = detect_cup_and_handle_patterns(
        _valid_cup_and_handle_candles(),
        symbol="BTCUSDT",
        config=_config(),
    )
    diagnostic_events = detect_cup_and_handle_patterns(
        _valid_cup_and_handle_candles(),
        symbol="BTCUSDT",
        config=_config(enable_candidate_diagnostics=True, max_candidates_per_bar=1),
    )

    assert default_events[0].candidate_diagnostics == {}
    diagnostics = diagnostic_events[0].candidate_diagnostics
    assert diagnostics["schema_version"] == "chart_pattern_candidate_diagnostics_v1"
    assert diagnostics["pattern_type"] == "CUP_AND_HANDLE"
    assert diagnostics["candidate_count"] == 1
    assert diagnostics["evaluated_candidate_count"] == 1
    assert diagnostics["selected_rank"] == 1
    assert diagnostics["max_guard_hit"] is True
    assert diagnostics["rejected_by_reason"] == {"max_candidate_guard_hit": 1}
    assert "max_candidate_guard_hit" in diagnostics["overfit_warnings"]


def test_local_prior_uptrend_detected_over_fixed_lookback() -> None:
    events = detect_cup_and_handle_patterns(
        _valid_cup_and_handle_candles(),
        symbol="BTCUSDT",
        config=_config(require_prior_uptrend=True, local_uptrend_lookback=1, local_uptrend_minimum_return_rate=0.05),
    )

    assert len(events) == 1
    assert events[0].prior_uptrend_method == "LOCAL"
    assert events[0].prior_uptrend_strength is not None
    assert events[0].prior_uptrend_strength >= 0.05


def test_local_prior_uptrend_absent_rejects_candidate() -> None:
    events = detect_cup_and_handle_patterns(
        _valid_cup_and_handle_candles(),
        symbol="BTCUSDT",
        config=_config(require_prior_uptrend=True, local_uptrend_lookback=1, local_uptrend_minimum_return_rate=0.20),
    )

    assert events == []


def test_neckline_retest_status_records_fill_and_failure_cases() -> None:
    retest = pd.concat(
        [
            _valid_cup_and_handle_candles(),
            _candles([{"timestamp": "2026-05-16T00:12:00Z", "open": 102.0, "high": 103.0, "low": 100.0, "close": 102.0}]),
        ],
        ignore_index=True,
    )
    failed = pd.concat(
        [
            _valid_cup_and_handle_candles(),
            _candles([{"timestamp": "2026-05-16T00:12:00Z", "open": 102.0, "high": 103.0, "low": 98.0, "close": 99.0}]),
        ],
        ignore_index=True,
    )

    retest_events = detect_cup_and_handle_patterns(retest, symbol="BTCUSDT", config=_config(neckline_retest_max_wait_bars=2))
    failed_events = detect_cup_and_handle_patterns(failed, symbol="BTCUSDT", config=_config(neckline_retest_max_wait_bars=2))

    assert retest_events[0].neckline_retest_status == "RETESTED"
    assert retest_events[0].neckline_retest_wait_bars == 1
    assert failed_events[0].neckline_retest_status == "FAILED_BELOW_NECKLINE"


def test_insufficient_pivot_history_returns_empty_list() -> None:
    assert (
        detect_cup_and_handle_patterns(
            _valid_cup_and_handle_candles().iloc[:4],
            symbol="BTCUSDT",
            config=_config(),
        )
        == []
    )


def test_rim_price_mismatch_returns_empty_list() -> None:
    assert (
        detect_cup_and_handle_patterns(
            _valid_cup_and_handle_candles(),
            symbol="BTCUSDT",
            config=_config(maximum_rim_difference_rate=0.005),
        )
        == []
    )


def test_cup_too_shallow_and_too_deep_return_empty_list() -> None:
    assert (
        detect_cup_and_handle_patterns(
            _valid_cup_and_handle_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_cup_depth_rate=0.25),
        )
        == []
    )
    assert (
        detect_cup_and_handle_patterns(
            _valid_cup_and_handle_candles(),
            symbol="BTCUSDT",
            config=_config(maximum_cup_depth_rate=0.15),
        )
        == []
    )


def test_cup_duration_outside_configured_bounds_returns_empty_list() -> None:
    assert (
        detect_cup_and_handle_patterns(
            _valid_cup_and_handle_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_cup_duration=7, maximum_cup_duration=12),
        )
        == []
    )


def test_insufficient_bottom_zone_duration_returns_empty_list() -> None:
    assert (
        detect_cup_and_handle_patterns(
            _valid_cup_and_handle_candles(),
            symbol="BTCUSDT",
            config=_config(minimum_bottom_zone_duration=4),
        )
        == []
    )


def test_handle_missing_too_deep_and_below_midpoint_return_empty_list() -> None:
    missing_handle = _valid_cup_and_handle_candles()
    missing_handle.loc[8, "low"] = 96.0
    missing_handle.loc[9, "low"] = 96.0
    missing_handle.loc[10, "low"] = 96.0
    too_deep = _valid_cup_and_handle_candles()
    too_deep.loc[9, "low"] = 90.0
    below_midpoint = _valid_cup_and_handle_candles()
    below_midpoint.loc[9, "low"] = 85.0

    assert detect_cup_and_handle_patterns(missing_handle, symbol="BTCUSDT", config=_config()) == []
    assert detect_cup_and_handle_patterns(too_deep, symbol="BTCUSDT", config=_config()) == []
    assert (
        detect_cup_and_handle_patterns(
            below_midpoint,
            symbol="BTCUSDT",
            config=_config(maximum_handle_depth_ratio=1.0),
        )
        == []
    )


def test_breakout_missing_or_without_atr_buffer_returns_empty_list() -> None:
    no_breakout = _valid_cup_and_handle_candles()
    no_breakout.loc[11, "close"] = 100.5

    assert detect_cup_and_handle_patterns(no_breakout, symbol="BTCUSDT", config=_config()) == []


def test_weak_breakout_volume_produces_weak_event() -> None:
    events = detect_cup_and_handle_patterns(
        _valid_cup_and_handle_candles(breakout_volume=250.0),
        symbol="BTCUSDT",
        config=_config(),
    )

    assert len(events) == 1
    assert events[0].pattern_status == CupAndHandleStatus.WEAK.value
    assert events[0].volume_ratio == pytest.approx(250.0 / 175.0)


def test_missing_atr_from_warmup_results_in_no_event() -> None:
    events = detect_cup_and_handle_patterns(
        _valid_cup_and_handle_candles(),
        symbol="BTCUSDT",
        config=_config(atr_config=AtrConfig(period=20)),
    )

    assert events == []


def test_rolling_windows_emit_stable_event_id_and_filter_duplicates() -> None:
    candles = _valid_cup_and_handle_candles()

    assert detect_cup_and_handle_patterns(candles.iloc[:11], symbol="BTCUSDT", config=_config()) == []

    first = detect_cup_and_handle_patterns(
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
                        "timestamp": "2026-05-16T00:12:00Z",
                        "open": 103.0,
                        "high": 105.0,
                        "low": 102.0,
                        "close": 104.0,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    second = detect_cup_and_handle_patterns(
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
    candles = _valid_cup_and_handle_candles().drop(columns=["volume"])

    with pytest.raises(ValueError, match="missing required columns"):
        detect_cup_and_handle_patterns(candles, symbol="BTCUSDT", config=_config())


def test_unsorted_candles_raise_clear_error() -> None:
    candles = _valid_cup_and_handle_candles().iloc[[1, 0, 2, 3, 4]].copy()

    with pytest.raises(ValueError, match="sorted ascending"):
        detect_cup_and_handle_patterns(candles, symbol="BTCUSDT", config=_config())


def test_require_external_filters_without_values_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="liquidity_pass"):
        detect_cup_and_handle_patterns(
            _valid_cup_and_handle_candles(),
            symbol="BTCUSDT",
            config=_config(require_liquidity_pass=True),
        )


def test_pattern_module_does_not_import_exchange_or_execution_dependencies() -> None:
    module = ast.parse(Path("quant_bitcoin/patterns/cup_and_handle.py").read_text())
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
