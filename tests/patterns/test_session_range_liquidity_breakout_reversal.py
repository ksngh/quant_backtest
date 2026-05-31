from __future__ import annotations

import pandas as pd
import pytest

from quant_bitcoin.indicators import AtrConfig, VolumeRatioBaselineMode, VolumeRatioConfig
from quant_bitcoin.patterns import (
    SessionRangeLiquidityBreakoutReversalConfig,
    create_session_range_liquidity_breakout_reversal_risk_exit_plan,
    detect_session_range_liquidity_breakout_reversals,
)
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus


def _config(**overrides: object) -> SessionRangeLiquidityBreakoutReversalConfig:
    values = {
        "range_lookback_bars": 4,
        "minimum_range_bps": 1.0,
        "minimum_volume_ratio": 0.5,
        "minimum_body_ratio": 0.2,
        "minimum_pattern_score": 0.0,
        "target_r_multiple": 2.0,
        "stop_atr_buffer_multiplier": 0.0,
        "atr_config": AtrConfig(period=2, require_full_window=False),
        "volume_ratio_config": VolumeRatioConfig(
            window=2,
            minimum_volume_ratio_for_confirmation=0.5,
            high_volume_ratio_threshold=2.0,
            require_full_window=True,
            baseline_mode=VolumeRatioBaselineMode.PRIOR_ONLY,
        ),
    }
    values.update(overrides)
    return SessionRangeLiquidityBreakoutReversalConfig(**values)


def _candles(rows: list[dict]) -> pd.DataFrame:
    candles = []
    for index, row in enumerate(rows):
        base = {
            "timestamp": pd.Timestamp("2026-05-20T00:00:00Z") + pd.Timedelta(minutes=index),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 100.0,
        }
        base.update(row)
        candles.append(base)
    return pd.DataFrame(candles)


def _failed_upside_rows() -> list[dict]:
    return [
        {"open": 100.0, "high": 100.8, "low": 99.0, "close": 100.1},
        {"open": 100.1, "high": 101.0, "low": 99.5, "close": 100.6},
        {"open": 100.6, "high": 100.9, "low": 99.8, "close": 100.4},
        {"open": 100.4, "high": 100.7, "low": 99.4, "close": 100.2},
        {"open": 101.6, "high": 102.2, "low": 100.1, "close": 100.5, "volume": 350.0},
    ]


def test_detects_failed_upside_session_range_short_event() -> None:
    events = detect_session_range_liquidity_breakout_reversals(
        _candles(_failed_upside_rows()),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(direction_mode="SHORT_ONLY"),
    )

    assert len(events) == 1
    event = events[0]
    assert event.pattern_type == "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL"
    assert event.direction == "BEARISH"
    assert event.breakout_side == "UPSIDE_FAILURE"
    assert event.entry_reference == pytest.approx(100.5)
    assert event.stop_reference > event.entry_reference
    assert event.target_reference < event.entry_reference
    assert event.score_calibration["is_calibrated_probability"] is False


def test_risk_exit_plan_uses_event_side_stop_and_target() -> None:
    event = detect_session_range_liquidity_breakout_reversals(
        _candles(_failed_upside_rows()),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(direction_mode="SHORT_ONLY"),
    )[0]

    plan = create_session_range_liquidity_breakout_reversal_risk_exit_plan(
        event,
        config=_config(direction_mode="SHORT_ONLY"),
    )

    assert plan.status == RiskExitPlanStatus.VALID
    assert plan.direction.value == "SHORT"
    assert plan.stop_price and plan.stop_price > event.entry_reference
    assert plan.targets[0].price < event.entry_reference


def test_future_candles_do_not_change_confirmed_event_identity() -> None:
    candles = _candles(_failed_upside_rows())
    base = detect_session_range_liquidity_breakout_reversals(
        candles,
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(direction_mode="SHORT_ONLY"),
    )[0]
    extended = detect_session_range_liquidity_breakout_reversals(
        pd.concat(
            [
                candles,
                _candles([{"open": 100.0, "high": 100.2, "low": 98.0, "close": 98.5}]).assign(
                    timestamp=[pd.Timestamp("2026-05-20T00:05:00Z")]
                ),
            ],
            ignore_index=True,
        ),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(direction_mode="SHORT_ONLY"),
    )[0]

    assert extended.event_id == base.event_id
    assert extended.entry_reference == pytest.approx(base.entry_reference)
