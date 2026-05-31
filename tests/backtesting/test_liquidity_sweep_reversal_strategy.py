from __future__ import annotations

from dataclasses import replace
import json

import pandas as pd

from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.pattern_action_builder import (
    CostAwareEntryFilterConfig,
    build_pattern_trade_actions,
)
from quant_bitcoin.backtesting import strategy_postgres_runner_cli
from quant_bitcoin.backtesting.strategy_postgres_runner_core import (
    _build_actions,
    build_parser,
)
from quant_bitcoin.indicators import AtrConfig, VolumeRatioBaselineMode, VolumeRatioConfig
from quant_bitcoin.indicators.displacement_candle import DisplacementCandleConfig
from quant_bitcoin.patterns import (
    LiquiditySweepReversalConfig,
    LiquiditySweepReversalRiskExitConfig,
    create_liquidity_sweep_reversal_risk_exit_plan,
    detect_liquidity_sweep_reversals,
)
from quant_bitcoin.patterns.entry_simulation import PatternEntryMode
from quant_bitcoin.strategies.actions import StrategyActionType
from quant_bitcoin.strategies.patterns import strategy_for_pattern


class _FakeProvider:
    def __init__(self, candles: pd.DataFrame) -> None:
        self._candles = candles

    def load(self) -> pd.DataFrame:
        return self._candles


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


def _candles() -> pd.DataFrame:
    vals = [
        (100.0, 101.0, 99.6, 100.0, 100.0),
        (100.0, 100.5, 99.0, 99.8, 100.0),
        (99.8, 100.4, 99.4, 100.0, 100.0),
        (100.0, 100.2, 99.5, 99.9, 100.0),
        (99.9, 100.0, 99.4, 99.6, 100.0),
        (99.6, 100.2, 98.7, 99.5, 100.0),
        (100.8, 105.0, 100.8, 104.5, 500.0),
        (104.5, 105.2, 99.0, 101.5, 120.0),
        (101.5, 103.0, 100.5, 102.5, 100.0),
    ]
    rows = []
    for index, (open_, high, low, close, volume) in enumerate(vals):
        rows.append(
            {
                "symbol": "BTCUSDT",
                "timestamp": pd.Timestamp("2026-05-20T00:00:00Z")
                + pd.Timedelta(minutes=index),
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
    return pd.DataFrame(rows)


def test_strategy_for_pattern_returns_liquidity_sweep_strategy() -> None:
    strategy = strategy_for_pattern("LIQUIDITY_SWEEP_REVERSAL")

    assert strategy.strategy_key == "LIQUIDITY_SWEEP_REVERSAL"


def test_build_actions_expands_liquidity_sweep_retest_entry() -> None:
    _, actions = _build_actions(
        _candles(),
        "LIQUIDITY_SWEEP_REVERSAL",
        pattern_entry_mode=PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
        liquidity_sweep_config=_config(),
        liquidity_sweep_risk_exit_config=LiquiditySweepReversalRiskExitConfig(
            stop_buffer_atr_multiplier=0.1,
            target_r_multiple=2.0,
            min_gross_rr=1.0,
        ),
    )

    assert any(action.action_type == StrategyActionType.ENTER_LONG for action in actions)
    assert any(action.action_type == StrategyActionType.EXIT_LONG for action in actions)
    entry = next(action for action in actions if action.action_type == StrategyActionType.ENTER_LONG)
    assert entry.metadata["liquidity_sweep_reversal"]["sweep_extreme_price"] == 98.7
    assert entry.metadata["pattern_entry_policy"]["entry_mode"] == "LIMIT_AT_ENTRY_REFERENCE"


def test_liquidity_sweep_cost_aware_rejection_uses_specific_reason() -> None:
    _, actions = _build_actions(
        _candles(),
        "LIQUIDITY_SWEEP_REVERSAL",
        pattern_entry_mode=PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
        liquidity_sweep_config=_config(),
        liquidity_sweep_risk_exit_config=LiquiditySweepReversalRiskExitConfig(
            stop_buffer_atr_multiplier=0.1,
            target_r_multiple=2.0,
            min_gross_rr=1.0,
        ),
        cost_aware_entry_filter_config=CostAwareEntryFilterConfig(
            enabled=True,
            min_net_reward_bps=20.0,
            min_net_rr=0.9,
            transaction_cost_config=TransactionCostConfig(
                taker_fee_bps=200.0,
                spread_bps=200.0,
                slippage_bps=200.0,
            ),
            liquidity_role=LiquidityRole.TAKER,
        ),
    )

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "LIQUIDITY_SWEEP_COST_AWARE_RR_REJECTED"
    assert actions[0].metadata["cost_aware_entry_filter"]["blocked"] is True


def test_liquidity_sweep_invalid_stop_uses_specific_reason() -> None:
    event = detect_liquidity_sweep_reversals(
        _candles().iloc[:7],
        symbol="BTCUSDT",
        timeframe="1m",
        config=_config(),
    )[0]
    invalid_event = replace(event, entry_reference=98.0)
    invalid_plan = create_liquidity_sweep_reversal_risk_exit_plan(invalid_event).risk_plan

    actions = build_pattern_trade_actions(
        invalid_event,
        invalid_plan,
        _candles().iloc[7:],
        entry_action_timestamp=invalid_event.timestamp,
        confirmation_candle=_candles().iloc[6],
        position_side="LONG",
        entry_mode=PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
    )

    assert len(actions) == 1
    assert actions[0].action_type == StrategyActionType.SKIP
    assert actions[0].reason == "LIQUIDITY_SWEEP_STOP_INVALID"


def test_cli_parser_accepts_liquidity_sweep_flags_and_defaults() -> None:
    args = build_parser("x").parse_args(
        [
            "--pattern",
            "LIQUIDITY_SWEEP_REVERSAL",
            "--lsr-entry-mode",
            "limit_at_fvg_midpoint",
            "--lsr-min-net-rr",
            "1.1",
            "--no-persist",
        ]
    )

    assert args.pattern == "LIQUIDITY_SWEEP_REVERSAL"
    assert args.cost_profile == "conservative_crypto_1m"
    assert args.enable_market_regime is True
    assert args.lsr_entry_mode == "limit_at_fvg_midpoint"
    assert args.lsr_min_net_rr == 1.1


def test_strategy_cli_outputs_liquidity_sweep_metadata(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        strategy_postgres_runner_cli.PostgresCandleDataProvider,
        "from_database_url",
        lambda *args, **kwargs: _FakeProvider(_candles()),
    )

    assert strategy_postgres_runner_cli.main(
        [
            "--pattern",
            "LIQUIDITY_SWEEP_REVERSAL",
            "--lsr-liquidity-lookback-bars",
            "5",
            "--lsr-min-liquidity-pool-age-bars",
            "2",
            "--lsr-min-gross-rr",
            "1.0",
            "--cost-profile",
            "zero",
            "--no-persist",
        ]
    ) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["strategy"]["pattern"] == "LIQUIDITY_SWEEP_REVERSAL"
    assert output["summary"]["metadata"]["liquidity_sweep_reversal"]["liquidity_pool_lookback_bars"] == 5
    assert "portfolio" in output
