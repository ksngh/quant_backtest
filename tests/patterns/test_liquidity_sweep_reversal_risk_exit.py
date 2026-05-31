from __future__ import annotations

from dataclasses import replace

import pandas as pd

from quant_bitcoin.indicators import AtrConfig, VolumeRatioBaselineMode, VolumeRatioConfig
from quant_bitcoin.indicators.displacement_candle import DisplacementCandleConfig
from quant_bitcoin.patterns import (
    LiquiditySweepReversalConfig,
    LiquiditySweepReversalRiskExitConfig,
    create_liquidity_sweep_reversal_risk_exit_plan,
    detect_liquidity_sweep_reversals,
)
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus


def _config() -> LiquiditySweepReversalConfig:
    return LiquiditySweepReversalConfig(
        atr_config=AtrConfig(period=2, require_full_window=False),
        volume_ratio_config=VolumeRatioConfig(
            window=2,
            minimum_volume_ratio_for_confirmation=1.5,
            high_volume_ratio_threshold=2.0,
            require_full_window=True,
            baseline_mode=VolumeRatioBaselineMode.PRIOR_ONLY,
        ),
        displacement_config=DisplacementCandleConfig(
            minimum_body_ratio=0.5,
            minimum_range_atr_multiplier=0.5,
            minimum_volume_ratio=1.5,
            minimum_close_position_ratio=0.6,
        ),
        min_liquidity_pool_age_bars=2,
        liquidity_pool_lookback_bars=5,
        min_gross_rr=1.0,
    )


def _event():
    rows = []
    vals = [
        (100.0, 101.0, 99.6, 100.0, 100.0),
        (100.0, 100.5, 99.0, 99.8, 100.0),
        (99.8, 100.4, 99.4, 100.0, 100.0),
        (100.0, 100.2, 99.5, 99.9, 100.0),
        (99.9, 100.0, 99.4, 99.6, 100.0),
        (99.6, 100.2, 98.7, 99.5, 100.0),
        (100.8, 105.0, 100.8, 104.5, 500.0),
    ]
    for index, (open_, high, low, close, volume) in enumerate(vals):
        rows.append(
            {
                "timestamp": pd.Timestamp("2026-05-20T00:00:00Z")
                + pd.Timedelta(minutes=index),
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
    return detect_liquidity_sweep_reversals(
        pd.DataFrame(rows),
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )[0]


def test_risk_exit_plan_uses_sweep_extreme_stop_with_atr_buffer() -> None:
    event = _event()
    wrapped = create_liquidity_sweep_reversal_risk_exit_plan(
        event,
        config=LiquiditySweepReversalRiskExitConfig(
            stop_buffer_atr_multiplier=0.1,
            target_r_multiple=2.0,
            min_gross_rr=1.0,
        ),
    )

    plan = wrapped.risk_plan
    assert plan.status == RiskExitPlanStatus.VALID
    assert plan.structural_stop == event.stop_reference
    assert plan.stop_price is not None and plan.stop_price < event.sweep_extreme_price
    assert plan.targets
    assert wrapped.structural_stop_source == "SWEEP_EXTREME_ATR_BUFFER"
    assert wrapped.target_reference == event.target_reference


def test_invalid_stop_side_returns_invalid_plan() -> None:
    event = replace(_event(), entry_reference=98.0)

    wrapped = create_liquidity_sweep_reversal_risk_exit_plan(event)

    assert wrapped.risk_plan.status == RiskExitPlanStatus.INVALID
    assert wrapped.risk_plan.reasons
