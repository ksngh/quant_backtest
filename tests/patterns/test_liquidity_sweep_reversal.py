from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from quant_bitcoin.indicators import AtrConfig, VolumeRatioBaselineMode, VolumeRatioConfig
from quant_bitcoin.indicators.displacement_candle import DisplacementCandleConfig
from quant_bitcoin.patterns import (
    LiquiditySweepReversalConfig,
    LiquiditySweepStatus,
    detect_liquidity_sweep_reversals,
)


def _config(**overrides: object) -> LiquiditySweepReversalConfig:
    values = {
        "atr_config": AtrConfig(period=2, require_full_window=False),
        "volume_ratio_config": VolumeRatioConfig(
            window=2,
            minimum_volume_ratio_for_confirmation=1.5,
            high_volume_ratio_threshold=2.0,
            require_full_window=True,
            baseline_mode=VolumeRatioBaselineMode.PRIOR_ONLY,
        ),
        "displacement_config": DisplacementCandleConfig(
            minimum_body_ratio=0.5,
            minimum_range_atr_multiplier=0.5,
            minimum_volume_ratio=1.5,
            minimum_close_position_ratio=0.6,
        ),
        "min_liquidity_pool_age_bars": 2,
        "liquidity_pool_lookback_bars": 5,
        "min_gross_rr": 1.0,
    }
    values.update(overrides)
    return LiquiditySweepReversalConfig(**values)


def _candles(rows: list[dict]) -> pd.DataFrame:
    base_rows = []
    for index, row in enumerate(rows):
        candle = {
            "timestamp": pd.Timestamp("2026-05-20T00:00:00Z") + pd.Timedelta(minutes=index),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 100.0,
        }
        candle.update(row)
        base_rows.append(candle)
    return pd.DataFrame(base_rows)


def _bullish_sweep_rows() -> list[dict]:
    return [
        {"open": 100.0, "high": 101.0, "low": 99.6, "close": 100.0},
        {"open": 100.0, "high": 100.5, "low": 99.0, "close": 99.8},
        {"open": 99.8, "high": 100.4, "low": 99.4, "close": 100.0},
        {"open": 100.0, "high": 100.2, "low": 99.5, "close": 99.9},
        {"open": 99.9, "high": 100.0, "low": 99.4, "close": 99.6},
        {"open": 99.6, "high": 100.2, "low": 98.7, "close": 99.5},
        {"open": 100.8, "high": 105.0, "low": 100.8, "close": 104.5, "volume": 500.0},
    ]


def _bearish_sweep_rows() -> list[dict]:
    return [
        {"open": 100.0, "high": 100.4, "low": 99.4, "close": 100.0},
        {"open": 100.0, "high": 101.0, "low": 99.8, "close": 100.5},
        {"open": 100.5, "high": 100.8, "low": 99.9, "close": 100.2},
        {"open": 100.2, "high": 100.7, "low": 99.8, "close": 100.1},
        {"open": 100.1, "high": 100.5, "low": 99.4, "close": 100.0},
        {"open": 100.2, "high": 101.5, "low": 100.0, "close": 100.6},
        {"open": 98.8, "high": 98.8, "low": 94.0, "close": 95.0, "volume": 500.0},
    ]


def test_detects_bullish_liquidity_sweep_reversal_event() -> None:
    events = detect_liquidity_sweep_reversals(
        _candles(_bullish_sweep_rows()),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.pattern_type == "LIQUIDITY_SWEEP_REVERSAL"
    assert event.direction == "BULLISH"
    assert event.pattern_status == LiquiditySweepStatus.VALID.value
    assert event.timestamp == pd.Timestamp("2026-05-20T00:06:00Z")
    assert event.liquidity_pool_price == pytest.approx(99.0)
    assert event.sweep_extreme_price == pytest.approx(98.7)
    assert event.reclaim_lag_bars == 0
    assert event.displacement_direction == "BULLISH"
    assert event.volume_ratio == pytest.approx(5.0)
    assert event.fvg_confluence_pass is True
    assert event.order_block_confluence_pass is True
    assert event.risk_reward and event.risk_reward >= 1.0
    assert event.score_calibration["is_calibrated_probability"] is False
    assert event.score_components["sweep_quality"]["weighted_score"] > 0


def test_detects_bearish_liquidity_sweep_reversal_event() -> None:
    events = detect_liquidity_sweep_reversals(
        _candles(_bearish_sweep_rows()),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert len(events) == 1
    event = events[0]
    assert event.direction == "BEARISH"
    assert event.liquidity_pool_price == pytest.approx(101.0)
    assert event.sweep_extreme_price == pytest.approx(101.5)
    assert event.displacement_direction == "BEARISH"
    assert event.fvg_confluence_pass is True
    assert event.order_block_confluence_pass is True
    assert event.stop_reference > event.entry_reference
    assert event.target_reference < event.entry_reference


def test_wick_sweep_without_reclaim_returns_no_event() -> None:
    rows = _bullish_sweep_rows()
    rows[5] = {**rows[5], "close": 98.9}
    rows[6] = {**rows[6], "open": 98.9, "high": 99.2, "low": 98.0, "close": 98.8}

    events = detect_liquidity_sweep_reversals(
        _candles(rows),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert events == []


def test_no_sweep_returns_no_event() -> None:
    rows = _bullish_sweep_rows()
    rows[5] = {**rows[5], "low": 99.05, "close": 99.5}

    events = detect_liquidity_sweep_reversals(
        _candles(rows),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert events == []


def test_reclaim_without_displacement_returns_no_event() -> None:
    rows = _bullish_sweep_rows()
    rows[6] = {**rows[6], "open": 99.1, "high": 99.5, "low": 98.9, "close": 99.25, "volume": 500.0}

    events = detect_liquidity_sweep_reversals(
        _candles(rows),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert events == []


def test_insufficient_prior_only_volume_returns_no_event() -> None:
    rows = _bullish_sweep_rows()
    rows[6] = {**rows[6], "volume": 120.0}

    events = detect_liquidity_sweep_reversals(
        _candles(rows),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )

    assert events == []


def test_score_component_weights_and_limitations_are_documented() -> None:
    event = detect_liquidity_sweep_reversals(
        _candles(_bullish_sweep_rows()),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )[0]

    total_weight = sum(component["weight"] for component in event.score_components.values())
    assert total_weight == pytest.approx(1.0)
    assert "heuristic_score_not_calibrated_probability" in event.score_limitations
    assert event.score_calibration["promotion_blocked_without_oos_validation"] is True


def test_future_candles_do_not_change_confirmed_event_id() -> None:
    candles = _candles(_bullish_sweep_rows())
    base = detect_liquidity_sweep_reversals(candles, symbol="BTCUSDT", timeframe="1m", config=_config())[0]
    extended = detect_liquidity_sweep_reversals(
        pd.concat(
            [
                candles,
                _candles([{"open": 104.5, "high": 106.0, "low": 103.0, "close": 105.0}]).assign(
                    timestamp=[pd.Timestamp("2026-05-20T00:07:00Z")]
                ),
            ],
            ignore_index=True,
        ),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )[0]

    assert extended.event_id == base.event_id
    assert extended.entry_reference == pytest.approx(base.entry_reference)
    assert extended.target_reference == pytest.approx(base.target_reference)


def test_missing_required_columns_raise_value_error() -> None:
    with pytest.raises(ValueError, match="missing required candle columns"):
        detect_liquidity_sweep_reversals(
            _candles(_bullish_sweep_rows()).drop(columns=["volume"]),
            config=_config(),
        )


def test_unsorted_input_raises_value_error() -> None:
    candles = _candles(_bullish_sweep_rows()).sort_values("timestamp", ascending=False)

    with pytest.raises(ValueError, match="sorted ascending"):
        detect_liquidity_sweep_reversals(candles, config=_config())


def test_same_input_produces_stable_event_id() -> None:
    candles = _candles(_bullish_sweep_rows())

    first = detect_liquidity_sweep_reversals(candles, symbol="BTCUSDT", timeframe="1m", config=_config())[0]
    second = detect_liquidity_sweep_reversals(candles, symbol="BTCUSDT", timeframe="1m", config=_config())[0]

    assert first.event_id == second.event_id
    assert replace(first, event_id=second.event_id) == second
