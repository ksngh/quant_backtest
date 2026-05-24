from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from quant_bitcoin.indicators import AtrConfig, DisplacementCandleConfig, VolumeRatioConfig
from quant_bitcoin.patterns import (
    FairValueGapConfig,
    PatternStatus,
    PatternType,
    detect_patterns,
    filter_new_events,
)


def _config() -> FairValueGapConfig:
    return FairValueGapConfig(
        atr_config=AtrConfig(period=1),
        volume_ratio_config=VolumeRatioConfig(
            window=2,
            minimum_volume_ratio_for_confirmation=1.3,
            high_volume_ratio_threshold=2.0,
            require_full_window=False,
        ),
        displacement_config=DisplacementCandleConfig(
            minimum_range_atr_multiplier=1.0,
            minimum_volume_ratio=1.3,
        ),
    )


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
    assert event.pattern_status == PatternStatus.VALID.value
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
    assert event.pattern_score >= 0.7
    assert event.score_components["gap_quality"]["weighted_score"] > 0
    assert event.score_components["liquidity"]["is_placeholder"] is True
    assert event.score_component_sources["structure_alignment"] == "placeholder_constant"
    assert event.score_calibration["is_calibrated_probability"] is False
    assert event.entry_reference == pytest.approx(101.0)
    assert event.stop_reference == pytest.approx(99.0)
    assert event.target_reference == pytest.approx(105.0)
    assert event.risk_reward == pytest.approx(2.0)
    assert event.reason


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
