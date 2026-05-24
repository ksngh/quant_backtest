from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from quant_bitcoin.indicators import (
    AtrConfig,
    DisplacementCandleConfig,
    PivotConfig,
    VolumeRatioConfig,
)
from quant_bitcoin.patterns import (
    TrendlineBreakConfig,
    TrendlineBreakStatus,
    TrendlineType,
    detect_trendline_breaks,
    filter_new_events,
)


def _config(**overrides: object) -> TrendlineBreakConfig:
    values = {
        "minimum_trendline_length": 1,
        "pivot_config": PivotConfig(
            left_window=1,
            right_window=1,
            minimum_distance_between_pivots=1,
        ),
        "atr_config": AtrConfig(period=1),
        "volume_ratio_config": VolumeRatioConfig(
            window=2,
            minimum_volume_ratio_for_confirmation=1.3,
            high_volume_ratio_threshold=2.0,
            require_full_window=False,
        ),
        "displacement_config": DisplacementCandleConfig(
            minimum_range_atr_multiplier=0.1,
            minimum_volume_ratio=1.3,
        ),
    }
    values.update(overrides)
    return TrendlineBreakConfig(**values)


def _candles(rows: list[dict]) -> pd.DataFrame:
    base_rows = []
    for index, row in enumerate(rows):
        base = {
            "timestamp": f"2026-05-16T00:{index:02d}:00Z",
            "open": 10.0,
            "high": 11.0,
            "low": 9.0,
            "close": 10.0,
            "volume": 100.0,
        }
        base.update(row)
        base_rows.append(base)
    return pd.DataFrame(base_rows)


def _bullish_break_candles(breakout_volume: float = 500.0) -> pd.DataFrame:
    return _candles(
        [
            {"open": 9.0, "high": 10.0, "low": 8.0, "close": 9.0},
            {"open": 14.0, "high": 15.0, "low": 9.0, "close": 14.0},
            {"open": 11.0, "high": 12.0, "low": 8.0, "close": 11.0},
            {"open": 12.0, "high": 13.0, "low": 9.0, "close": 12.0},
            {"open": 13.0, "high": 14.0, "low": 9.0, "close": 13.0},
            {"open": 11.0, "high": 12.0, "low": 8.0, "close": 12.0},
            {
                "open": 11.0,
                "high": 14.5,
                "low": 11.0,
                "close": 14.2,
                "volume": breakout_volume,
            },
        ]
    )


def _bearish_break_candles() -> pd.DataFrame:
    return _candles(
        [
            {"open": 10.0, "high": 12.0, "low": 8.0, "close": 10.0},
            {"open": 6.0, "high": 11.0, "low": 5.0, "close": 6.0},
            {"open": 9.0, "high": 12.0, "low": 7.0, "close": 9.0},
            {"open": 8.0, "high": 11.0, "low": 7.0, "close": 8.0},
            {"open": 7.0, "high": 10.0, "low": 6.0, "close": 7.0},
            {"open": 8.0, "high": 11.0, "low": 7.0, "close": 8.0},
            {"open": 8.5, "high": 8.5, "low": 5.3, "close": 5.8, "volume": 500.0},
        ]
    )


def test_returns_empty_when_no_trendline_break_rules_match() -> None:
    candles = _candles(
        [
            {"high": 10.0, "low": 8.0},
            {"high": 11.0, "low": 9.0},
            {"high": 12.0, "low": 10.0},
            {"high": 13.0, "low": 11.0},
        ]
    )

    assert detect_trendline_breaks(candles, symbol="BTCUSDT", config=_config()) == []


def test_detects_bullish_trendline_break_event() -> None:
    events = detect_trendline_breaks(
        _bullish_break_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.pattern_type == "TRENDLINE_BREAK"
    assert event.direction == "BULLISH"
    assert event.pattern_status == TrendlineBreakStatus.VALID.value
    assert event.symbol == "BTCUSDT"
    assert event.timeframe == "1m"
    assert event.timestamp == "2026-05-16T00:06:00Z"
    assert event.start_index == 1
    assert event.end_index == 6
    assert event.trendline_type == TrendlineType.DESCENDING_RESISTANCE.value
    assert event.trendline_slope == pytest.approx(-1.0 / 3.0)
    assert event.trendline_intercept == pytest.approx(15.0 + (1.0 / 3.0))
    assert event.touch_count == 2
    assert event.source_pivot_indices == (1, 4)
    assert event.trendline_value == pytest.approx(13.3333333333)
    assert event.break_price == pytest.approx(14.2)
    assert event.break_distance == pytest.approx(14.2 - 13.3333333333)
    assert event.break_distance_atr == pytest.approx((14.2 - 13.3333333333) / 3.5)
    assert event.volume_ratio == pytest.approx(500.0 / 300.0)
    assert event.displacement_confirmed is True
    assert event.pattern_score >= 0.7
    assert event.score_components["trendline_quality"]["weighted_score"] > 0
    assert event.score_components["structure_alignment"]["is_placeholder"] is True
    assert event.score_components["liquidity"]["is_placeholder"] is True
    assert event.score_calibration["is_calibrated_probability"] is False
    assert event.risk_reward == pytest.approx(2.0)
    assert event.reason


def test_detects_bearish_trendline_break_event() -> None:
    events = detect_trendline_breaks(
        _bearish_break_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.direction == "BEARISH"
    assert event.pattern_status == TrendlineBreakStatus.VALID.value
    assert event.trendline_type == TrendlineType.ASCENDING_SUPPORT.value
    assert event.trendline_slope == pytest.approx(1.0 / 3.0)
    assert event.trendline_value == pytest.approx(6.6666666667)
    assert event.break_price == pytest.approx(5.8)
    assert event.break_distance == pytest.approx(6.6666666667 - 5.8)
    assert event.source_pivot_indices == (1, 4)
    assert event.displacement_confirmed is True


def test_insufficient_pivot_history_returns_empty_list() -> None:
    candles = _bullish_break_candles().iloc[:4]

    assert detect_trendline_breaks(candles, symbol="BTCUSDT", config=_config()) == []


def test_flat_trendline_is_rejected() -> None:
    candles = _candles(
        [
            {"high": 10.0, "low": 8.0},
            {"high": 15.0, "low": 9.0, "close": 14.0},
            {"high": 12.0, "low": 8.0},
            {"high": 13.0, "low": 9.0},
            {"high": 15.0, "low": 9.0, "close": 14.0},
            {"high": 12.0, "low": 8.0},
            {"open": 12.0, "high": 16.0, "low": 12.0, "close": 15.8, "volume": 500.0},
        ]
    )

    assert detect_trendline_breaks(candles, symbol="BTCUSDT", config=_config()) == []


def test_break_without_atr_buffer_is_not_emitted_by_default() -> None:
    candles = _bullish_break_candles()
    candles.loc[6, "close"] = 13.6
    candles.loc[6, "high"] = 14.5

    assert detect_trendline_breaks(candles, symbol="BTCUSDT", config=_config()) == []


def test_weak_volume_produces_weak_event() -> None:
    events = detect_trendline_breaks(
        _bullish_break_candles(breakout_volume=250.0),
        symbol="BTCUSDT",
        config=_config(),
    )

    assert len(events) == 1
    assert events[0].pattern_status == TrendlineBreakStatus.WEAK.value
    assert events[0].volume_ratio == pytest.approx(250.0 / 175.0)


def test_missing_atr_from_warmup_results_in_no_event() -> None:
    events = detect_trendline_breaks(
        _bullish_break_candles(),
        symbol="BTCUSDT",
        config=_config(atr_config=AtrConfig(period=20)),
    )

    assert events == []


def test_rolling_windows_emit_event_when_breakout_candle_arrives() -> None:
    candles = _bullish_break_candles()

    assert detect_trendline_breaks(candles.iloc[:6], symbol="BTCUSDT", config=_config()) == []
    events = detect_trendline_breaks(candles.iloc[:7], symbol="BTCUSDT", config=_config())

    assert [event.pattern_type for event in events] == ["TRENDLINE_BREAK"]


def test_event_id_is_stable_across_overlapping_rolling_windows() -> None:
    prefix = _candles([{"timestamp": "2026-05-16T00:00:00Z"}])
    pattern = _bullish_break_candles().assign(
        timestamp=[f"2026-05-16T00:0{index + 1}:00Z" for index in range(7)]
    )
    suffix = _candles(
        [
            {
                "timestamp": "2026-05-16T00:08:00Z",
                "open": 14.0,
                "high": 15.0,
                "low": 13.0,
                "close": 14.5,
            }
        ]
    )
    candles = pd.concat([prefix, pattern, suffix], ignore_index=True)

    first_window_events = detect_trendline_breaks(
        candles.iloc[:8], symbol="BTCUSDT", timeframe="1m", config=_config()
    )
    second_window_events = detect_trendline_breaks(
        candles.iloc[1:9], symbol="BTCUSDT", timeframe="1m", config=_config()
    )

    assert len(first_window_events) == 1
    assert len(second_window_events) == 1
    assert first_window_events[0].event_id == second_window_events[0].event_id


def test_filter_new_events_can_deduplicate_trendline_break_events() -> None:
    events = detect_trendline_breaks(
        _bullish_break_candles(),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )
    seen_event_ids: set[str] = set()

    assert filter_new_events(events, seen_event_ids) == events
    assert filter_new_events(events, seen_event_ids) == []
    assert seen_event_ids == {events[0].event_id}


def test_missing_required_candle_column_raises_clear_error() -> None:
    candles = _bullish_break_candles().drop(columns=["volume"])

    with pytest.raises(ValueError, match="missing required candle columns: volume"):
        detect_trendline_breaks(candles, symbol="BTCUSDT", config=_config())


def test_unsorted_candle_input_is_rejected() -> None:
    candles = _bullish_break_candles().iloc[[1, 0, 2, 3, 4, 5, 6]]

    with pytest.raises(ValueError, match="candles must be sorted ascending by timestamp"):
        detect_trendline_breaks(candles, symbol="BTCUSDT", config=_config())


def test_detector_accepts_standard_schema_without_binance_raw_fields() -> None:
    candles = _bullish_break_candles()

    assert list(candles.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert len(detect_trendline_breaks(candles, symbol="BTCUSDT", config=_config())) == 1


def test_requiring_unavailable_liquidity_or_spread_filters_needs_explicit_values() -> None:
    with pytest.raises(ValueError, match="liquidity_pass must be supplied"):
        detect_trendline_breaks(
            _bullish_break_candles(),
            symbol="BTCUSDT",
            config=_config(require_liquidity_pass=True),
        )

    with pytest.raises(ValueError, match="spread_pass must be supplied"):
        detect_trendline_breaks(
            _bullish_break_candles(),
            symbol="BTCUSDT",
            config=_config(require_spread_pass=True),
        )


def test_trendline_module_does_not_import_exchange_clients_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/trendline_break.py")
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
