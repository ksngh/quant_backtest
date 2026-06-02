from __future__ import annotations

import argparse
import cProfile
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
import pstats
import sys
import time
from collections.abc import Sequence
from math import isfinite
from urllib.parse import urlsplit, urlunsplit

import pandas as pd

from quant_bitcoin.backtesting.json_metadata import json_ready, metadata_hash as json_metadata_hash
from quant_bitcoin.backtesting.pattern_action_builder import (
    CloseVolumeEntryFilterConfig,
    CostAwareEntryFilterConfig,
    FvgOrderBlockConfluenceConfig,
    OrderBlockEntryVolumeFilterConfig,
    OrderBlockMtfFilterConfig,
    OrderBlockRiskExitConfig,
    build_fvg_channel_trade_actions,
    build_pattern_trade_actions,
)
from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES, break_even_cost_bps, cost_profile, manual_cost_overrides_present
from quant_bitcoin.backtesting.performance_metrics import calculate_performance_metrics
from quant_bitcoin.backtesting.pattern_invalidation import soft_invalidation_for_event
from quant_bitcoin.backtesting.retest_opportunity import build_fvg_ob_retest_opportunity_report
from quant_bitcoin.backtesting.trendline_forensics import build_trendline_false_breakout_forensics
from quant_bitcoin.backtesting.fvg_detection_cache import (
    IndicatorCache,
    PatternEvaluationContext,
)
from quant_bitcoin.patterns.entry_simulation import PatternEntryConfig, PatternEntryMode, PatternEntryStatus, PatternEntryTrigger
from quant_bitcoin.patterns.fvg_channel import FvgChannelConfig
from quant_bitcoin.patterns.liquidity_sweep_reversal import (
    LiquiditySweepEntryMode,
    LiquiditySweepReversalConfig,
)
from quant_bitcoin.patterns.liquidity_sweep_reversal_risk_exit import (
    LiquiditySweepReversalRiskExitConfig,
)
from quant_bitcoin.patterns.order_block import OrderBlockConfig
from quant_bitcoin.patterns.session_range_liquidity_breakout_reversal import (
    SessionRangeLiquidityBreakoutReversalConfig,
)
from quant_bitcoin.backtesting.strategy_engine import (
    StrategyEngineConfig,
    run_strategy_backtest_engine,
)
from quant_bitcoin.backtesting.sizing import (
    BacktestGuardrailConfig,
    InsufficientFundsPolicy,
    PositionSizingConfig,
    PositionSizingMode,
    ShortExposureMode,
    SimulatedMarginConfig,
)
from quant_bitcoin.indicators.market_regime import (
    MarketRegimeConfig,
    PatternRegimeThresholdConfig,
    PatternRegimeThresholdOverride,
    calculate_market_regime,
)
from quant_bitcoin.backtesting.strategy_persistence_adapter import (
    build_strategy_engine_persistence_payload,
)
from quant_bitcoin.market_data import PostgresCandleDataProvider
from quant_bitcoin.persistence import (
    BACKTEST_ENGINE_NAME,
    BACKTEST_ENGINE_VERSION,
    PostgresBacktestResultRepository,
)
from quant_bitcoin.risk.exit_plan import (
    RiskExitDirection,
    RiskExitPlan,
    RiskExitPlanStatus,
    RiskExitTarget,
    RiskExitTargetSource,
    target_semantics_metadata,
)
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType
from quant_bitcoin.strategies.lookback_return_momentum import (
    STRATEGY_KEY as LOOKBACK_RETURN_MOMENTUM_KEY,
    LookbackReturnMomentumCostAwareConfig,
    LookbackReturnMomentumConfig,
    LookbackReturnMomentumStrategy,
    build_lookback_return_momentum_actions,
    config_for_timeframe as lookback_return_momentum_config_for_timeframe,
)
from quant_bitcoin.strategies.pattern_execution_policy import policy_for_pattern, validate_pattern_entry_mode
from quant_bitcoin.strategies.pattern_explanations import build_pattern_strategy_explanation
from quant_bitcoin.strategies.patterns import PatternEntryFilterConfig, strategy_for_pattern

DEFAULT_DATABASE_URL = "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
DEFAULT_SOURCE = "binance_spot"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"
DEFAULT_STRATEGY = "FAIR_VALUE_GAP"
OWNER_FVG_V2_CHANNEL_DEFAULT_PROFILE_KEY = "owner_fvg_v2_channel_default_v1"
OWNER_ORDER_BLOCK_DEFAULT_PROFILE_KEY = "owner_order_block_default_v1"
OWNER_LIQUIDITY_SWEEP_DEFAULT_PROFILE_KEY = "owner_liquidity_sweep_reversal_default_v1"


class StrategyBacktestArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None):
        raw_args = list(sys.argv[1:] if args is None else args)
        parsed = super().parse_args(raw_args, namespace)
        parsed._raw_args = tuple(raw_args)
        return _apply_owner_fvg_v2_channel_defaults(parsed, raw_args)


def build_parser(prog: str, include_strategy: bool = True) -> argparse.ArgumentParser:
    parser = StrategyBacktestArgumentParser(
        prog=prog,
        description="Run strategy-level backtest from stored 1m candles.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
    )
    parser.add_argument("--source", default=os.environ.get("CANDLE_SOURCE", DEFAULT_SOURCE))
    parser.add_argument("--symbol", default=os.environ.get("SYMBOL", DEFAULT_SYMBOL))
    parser.add_argument("--interval", default=os.environ.get("INTERVAL", DEFAULT_INTERVAL))
    if include_strategy:
        parser.add_argument("--strategy", default=DEFAULT_STRATEGY)
    parser.add_argument("--pattern", default=None)
    parser.add_argument("--research-task-id", default=None)
    parser.add_argument("--research-variant-id", default=None)
    parser.add_argument("--research-window-id", default=None)
    parser.add_argument("--research-run-group", default=None)
    parser.add_argument("--allow-weak-pattern-events", action="store_true")
    parser.add_argument("--allowed-pattern-statuses", default=None)
    parser.add_argument("--min-pattern-score", type=float, default=None)
    parser.add_argument("--min-risk-reward", type=float, default=None)
    parser.add_argument("--pattern-quantity-override", type=float, default=None)
    parser.add_argument(
        "--pattern-entry-mode",
        choices=[mode.value.lower() for mode in PatternEntryMode],
        default=None,
        help="Pattern-specific entry mode. Unsupported pattern/mode combinations fail before backtest execution.",
    )
    parser.add_argument(
        "--fvg-entry-mode",
        choices=[mode.value.lower() for mode in PatternEntryMode],
        default=PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE.value.lower(),
        help="FVG-only historical entry mode. Default preserves market-on-confirmation behavior.",
    )
    parser.add_argument("--fvg-entry-custom-price", type=_positive_finite_float, default=None)
    parser.add_argument("--pattern-entry-custom-price", type=_positive_finite_float, default=None)
    parser.add_argument("--fvg-entry-max-wait-bars", type=int, default=None)
    parser.add_argument(
        "--fvg-entry-trigger",
        choices=[trigger.value.lower() for trigger in PatternEntryTrigger],
        default=PatternEntryTrigger.TOUCH.value.lower(),
        help="FVG limit-entry trigger. Default TOUCH preserves historical limit-touch fill behavior.",
    )
    parser.add_argument(
        "--fvg-entry-expire-status",
        choices=[PatternEntryStatus.NOT_FILLED.value.lower(), PatternEntryStatus.CANCELLED.value.lower()],
        default=PatternEntryStatus.NOT_FILLED.value.lower(),
        help="FVG limit-entry expiry behavior after --fvg-entry-max-wait-bars.",
    )
    parser.add_argument(
        "--compare-fvg-entry-modes",
        action="store_true",
        help="Run read-only FVG entry-mode comparison diagnostics in the JSON output without changing persistence behavior.",
    )
    parser.add_argument(
        "--compare-pattern-entry-modes",
        action="store_true",
        help="Run read-only pattern entry-mode comparison diagnostics for the selected pattern.",
    )
    parser.set_defaults(enable_fvg_v2=False)
    parser.add_argument("--enable-fvg-v2", dest="enable_fvg_v2", action="store_true", help="Enable experimental FVG retest v2 diagnostics metadata.")
    parser.add_argument("--disable-fvg-v2", dest="enable_fvg_v2", action="store_false", help="Disable the default FVG v2 diagnostics profile for FAIR_VALUE_GAP runs.")
    parser.set_defaults(fvg_use_trend_score=False)
    parser.add_argument("--fvg-use-trend-score", dest="fvg_use_trend_score", action="store_true", help="Record FVG v2 trend-score research setting.")
    parser.add_argument("--disable-fvg-trend-score", dest="fvg_use_trend_score", action="store_false", help="Disable the default FVG v2 trend-score research setting.")
    parser.add_argument("--fvg-trend-fast-period", type=int, default=9)
    parser.add_argument("--fvg-trend-slow-period", type=int, default=21)
    parser.add_argument("--fvg-trend-weight-1m", type=float, default=0.20)
    parser.add_argument("--fvg-trend-weight-5m", type=float, default=0.30)
    parser.add_argument("--fvg-trend-weight-15m", type=float, default=0.50)
    parser.add_argument("--fvg-min-bullish-trend-score", type=float, default=0.10)
    parser.set_defaults(fvg_use_fibonacci_confluence=False)
    parser.add_argument("--fvg-use-fibonacci-confluence", dest="fvg_use_fibonacci_confluence", action="store_true")
    parser.add_argument("--disable-fvg-fibonacci-confluence", dest="fvg_use_fibonacci_confluence", action="store_false")
    parser.add_argument("--fvg-require-liquidity-target", action="store_true")
    parser.add_argument("--fvg-stop-mode", default="fvg_boundary_atr_buffer")
    parser.add_argument(
        "--fvg-inverse-direction",
        action="store_true",
        help="Research-only: reverse FVG trade direction so bullish FVG enters short and bearish FVG enters long.",
    )
    parser.set_defaults(enable_fvg_v2_channel=False)
    parser.add_argument("--enable-fvg-v2-channel", dest="enable_fvg_v2_channel", action="store_true", help="Enable experimental FVG v2 parallel-channel retest entries and line-boundary exits.")
    parser.add_argument("--disable-fvg-v2-channel", dest="enable_fvg_v2_channel", action="store_false", help="Disable the default FVG v2 parallel-channel profile for FAIR_VALUE_GAP runs.")
    parser.add_argument("--fvg-channel-window", type=int, default=20)
    parser.add_argument("--fvg-channel-tolerance", type=_non_negative_finite_float, default=1e-8)
    parser.add_argument("--fvg-channel-max-wait-bars", type=int, default=None)
    parser.add_argument("--fvg-channel-allow-same-candle-exit", action="store_true")
    parser.add_argument(
        "--fvg-channel-standalone-scan",
        dest="fvg_channel_standalone_scan",
        action="store_true",
        help="Enable rolling visible-prefix FVG channel scans in addition to real FVG event expansion.",
    )
    parser.add_argument(
        "--disable-fvg-channel-standalone-scan",
        dest="fvg_channel_standalone_scan",
        action="store_false",
        help="Disable default standalone FVG channel visible-prefix scans.",
    )
    parser.set_defaults(fvg_channel_standalone_scan=False)
    parser.set_defaults(enable_fvg_close_volume_filter=False)
    parser.add_argument("--enable-fvg-close-volume-filter", dest="enable_fvg_close_volume_filter", action="store_true")
    parser.add_argument("--disable-fvg-close-volume-filter", dest="enable_fvg_close_volume_filter", action="store_false")
    parser.add_argument("--fvg-close-volume-window", type=int, default=20)
    parser.add_argument("--fvg-min-close-volume-ratio", type=_non_negative_finite_float, default=2.0)
    parser.add_argument(
        "--fvg-close-volume-input-mode",
        choices=["base_volume", "quote_volume_if_available", "trading_value"],
        default="base_volume",
    )
    parser.add_argument(
        "--fvg-close-volume-baseline-mode",
        choices=["prior_only", "current_inclusive"],
        default="prior_only",
    )
    parser.add_argument(
        "--fvg-require-order-block-confluence",
        action="store_true",
        help="Require same-direction Order Block confluence before entering FVG candidates.",
    )
    parser.add_argument("--fvg-order-block-confluence-lookback-bars", type=int, default=100)
    parser.add_argument(
        "--fvg-order-block-confluence-mode",
        choices=["zone_overlap", "entry_price_inside_ob", "fvg_midpoint_inside_ob"],
        default="zone_overlap",
    )
    parser.add_argument(
        "--fvg-order-block-confluence-source",
        choices=["local_entry_candles", "historical_detector"],
        default="local_entry_candles",
    )
    parser.add_argument(
        "--fvg-local-order-block-break-mode",
        choices=["break_previous_range", "break_previous_body"],
        default="break_previous_range",
    )
    parser.add_argument("--fvg-order-block-require-fresh", action="store_true")
    parser.add_argument("--ob-min-volume-ratio", type=_non_negative_finite_float, default=None)
    parser.add_argument("--ob-weak-volume-ratio", type=_non_negative_finite_float, default=None)
    parser.set_defaults(enable_ob_entry_volume_filter=False)
    parser.add_argument("--enable-ob-entry-volume-filter", dest="enable_ob_entry_volume_filter", action="store_true")
    parser.add_argument("--disable-ob-entry-volume-filter", dest="enable_ob_entry_volume_filter", action="store_false")
    parser.add_argument("--ob-entry-volume-window", type=int, default=20)
    parser.add_argument("--ob-min-entry-volume-ratio", type=_non_negative_finite_float, default=1.0)
    parser.set_defaults(enable_ob_mtf_filter=False)
    parser.add_argument("--enable-ob-mtf-filter", dest="enable_ob_mtf_filter", action="store_true")
    parser.add_argument("--disable-ob-mtf-filter", dest="enable_ob_mtf_filter", action="store_false")
    parser.add_argument("--ob-mtf-timeframes", default="15m,1h")
    parser.add_argument(
        "--ob-risk-exit-mode",
        choices=["previous_candle_1r", "zone_structural_2r"],
        default="previous_candle_1r",
        help="Order Block stop/target mode. previous_candle_1r uses previous high/low stop and symmetric 1R target.",
    )
    parser.add_argument("--lsr-liquidity-lookback-bars", type=int, default=80)
    parser.add_argument("--lsr-min-liquidity-pool-age-bars", type=int, default=5)
    parser.add_argument("--lsr-min-sweep-atr-multiplier", type=_non_negative_finite_float, default=0.05)
    parser.add_argument("--lsr-min-sweep-bps", type=_non_negative_finite_float, default=2.0)
    parser.add_argument("--lsr-reclaim-max-bars", type=int, default=2)
    parser.add_argument("--lsr-displacement-max-bars-after-sweep", type=int, default=3)
    parser.add_argument("--lsr-min-displacement-body-ratio", type=_score_threshold, default=0.55)
    parser.add_argument("--lsr-min-displacement-atr-multiplier", type=_non_negative_finite_float, default=0.8)
    parser.add_argument("--lsr-min-volume-ratio", type=_non_negative_finite_float, default=1.5)
    parser.add_argument("--lsr-require-fvg-confluence", action="store_true")
    parser.add_argument("--lsr-require-order-block-confluence", action="store_true")
    parser.add_argument("--lsr-require-both-fvg-and-ob", action="store_true")
    parser.add_argument(
        "--lsr-entry-mode",
        choices=[
            "market_on_reclaim_close",
            "market_on_displacement_close",
            "limit_at_fvg_midpoint",
            "limit_at_ob_618",
            "best_net_rr_between_fvg_midpoint_and_ob_618",
        ],
        default="best_net_rr_between_fvg_midpoint_and_ob_618",
    )
    parser.add_argument("--lsr-entry-max-wait-bars", type=int, default=20)
    parser.add_argument("--lsr-target-r-multiple", type=_positive_finite_float, default=2.0)
    parser.add_argument("--lsr-min-gross-rr", type=_non_negative_finite_float, default=1.2)
    parser.add_argument("--lsr-min-net-rr", type=_non_negative_finite_float, default=1.0)
    parser.add_argument("--lsr-min-net-reward-bps", type=_non_negative_finite_float, default=8.0)
    parser.add_argument("--lsr-enable-tradability-gates", action="store_true")
    parser.add_argument("--lsr-enable-mtf-confirmation", action="store_true")
    parser.add_argument("--lsr-mtf-timeframes", default="15m")
    parser.add_argument("--srlbr-range-lookback-bars", type=int, default=120)
    parser.add_argument("--srlbr-breakout-buffer-bps", type=_non_negative_finite_float, default=0.0)
    parser.add_argument("--srlbr-minimum-range-bps", type=_non_negative_finite_float, default=10.0)
    parser.add_argument("--srlbr-minimum-volume-ratio", type=_non_negative_finite_float, default=0.8)
    parser.add_argument("--srlbr-minimum-body-ratio", type=_score_threshold, default=0.25)
    parser.add_argument(
        "--srlbr-signal-mode",
        choices=["failed_breakout_reversal", "breakdown_continuation", "short_mix"],
        default="failed_breakout_reversal",
    )
    parser.add_argument(
        "--srlbr-direction-mode",
        choices=["both", "long_only", "short_only"],
        default="both",
    )
    parser.add_argument("--srlbr-minimum-pattern-score", type=_score_threshold, default=0.40)
    parser.add_argument("--srlbr-target-r-multiple", type=_positive_finite_float, default=4.0)
    parser.add_argument("--srlbr-stop-atr-buffer-multiplier", type=_non_negative_finite_float, default=0.20)
    parser.add_argument("--srlbr-max-bars-in-trade", type=int, default=240)
    parser.add_argument("--lookback-bars", type=int, default=None)
    parser.add_argument("--entry-threshold", type=_positive_finite_float, default=None)
    parser.add_argument("--holding-bars", type=int, default=None)
    parser.add_argument("--risk-distance-mode", choices=["atr", "fixed_pct"], default=None)
    parser.add_argument("--atr-period", type=int, default=None)
    parser.add_argument("--atr-smoothing", choices=["RMA", "SMA", "EMA"], default=None)
    parser.add_argument("--stop-loss-atr-multiple", type=_positive_finite_float, default=None)
    parser.add_argument("--take-profit-atr-multiple", type=_positive_finite_float, default=None)
    parser.add_argument("--minimum-atr-bps", type=_non_negative_finite_float, default=None)
    parser.add_argument("--risk-distance-pct", type=_positive_finite_float, default=None)
    parser.add_argument("--stop-loss-r", type=_positive_finite_float, default=None)
    parser.add_argument("--take-profit-r", type=_positive_finite_float, default=None)
    parser.add_argument("--start-time", type=_optional_timestamp, default=None)
    parser.add_argument("--end-time", type=_optional_timestamp, default=None)
    parser.add_argument("--starting-cash", type=float, default=10000.0)
    parser.add_argument(
        "--starting-cash-currency",
        default="KRW",
        help="Currency denomination of --starting-cash. BTCUSDT engine accounting remains in quote cash.",
    )
    parser.add_argument(
        "--quote-currency",
        default=None,
        help="Quote-currency cash used by the engine. Defaults to the symbol quote, for example USDT for BTCUSDT.",
    )
    parser.add_argument(
        "--krw-per-usdt",
        type=_positive_finite_float,
        default=1500.0,
        help="Manual KRW per USDT rate used only when --starting-cash-currency KRW and --quote-currency USDT.",
    )
    parser.add_argument("--trade-quantity", type=float, default=1.0)
    parser.add_argument(
        "--position-sizing-mode",
        choices=["fixed_quantity", "cash_fraction", "target_notional", "equity_risk_fraction"],
        default="fixed_quantity",
        help="Backtest sizing mode. fixed_quantity uses --trade-quantity unless an action has quantity.",
    )
    parser.add_argument("--position-sizing-value", type=_positive_finite_float, default=None)
    parser.add_argument(
        "--insufficient-funds-policy",
        choices=["resize", "block"],
        default="resize",
        help="Resize or block entries when cash/buying power is insufficient.",
    )
    parser.add_argument(
        "--short-exposure-mode",
        choices=["cash_bounded", "simulated_margin"],
        default="cash_bounded",
        help="Backtest-only short exposure mode. simulated_margin is opt-in and not real exchange margin.",
    )
    parser.add_argument("--simulated-margin-leverage", type=_positive_finite_float, default=None)
    parser.add_argument(
        "--insufficient-margin-policy",
        choices=["block", "resize"],
        default="block",
    )
    parser.add_argument("--maker-fee-bps", type=_non_negative_finite_float, default=0.0)
    parser.add_argument("--taker-fee-bps", type=_non_negative_finite_float, default=0.0)
    parser.add_argument("--spread-bps", type=_non_negative_finite_float, default=0.0)
    parser.add_argument("--slippage-bps", type=_non_negative_finite_float, default=0.0)
    parser.add_argument("--minimum-slippage-bps", type=_non_negative_finite_float, default=0.0)
    parser.add_argument("--volatility-slippage-multiplier", type=_non_negative_finite_float, default=0.0)
    parser.add_argument("--cost-profile", choices=sorted(COST_PROFILES), default=None)
    parser.add_argument("--allow-cost-profile-overrides", action="store_true")
    parser.add_argument("--enable-cost-aware-entry-filter", action="store_true")
    parser.add_argument("--min-net-reward-bps", type=_non_negative_finite_float, default=20.0)
    parser.add_argument("--min-net-rr", type=_positive_finite_float, default=1.5)
    parser.add_argument("--strict-cost-mode", action="store_true")
    parser.add_argument("--cost-sensitivity-report", action="store_true")
    parser.add_argument("--liquidity-role", type=_liquidity_role, default=LiquidityRole.TAKER.value)
    parser.add_argument("--risk-free-rate", type=_finite_float, default=0.0)
    parser.set_defaults(enforce_candle_continuity=False)
    parser.add_argument("--enforce-candle-continuity", dest="enforce_candle_continuity", action="store_true")
    parser.add_argument("--no-enforce-candle-continuity", dest="enforce_candle_continuity", action="store_false")
    parser.set_defaults(enable_market_regime=False)
    parser.add_argument("--enable-market-regime", dest="enable_market_regime", action="store_true")
    parser.add_argument("--disable-market-regime", dest="enable_market_regime", action="store_false")
    parser.add_argument("--market-regime-window", type=int, default=20)
    parser.add_argument("--market-regime-min-trading-value", type=_non_negative_finite_float, default=1_000_000.0)
    parser.add_argument("--enable-pattern-regime-thresholds", action="store_true")
    parser.add_argument("--regime-min-volume-ratio", type=_non_negative_finite_float, default=None)
    parser.add_argument("--regime-breakout-atr-multiplier", type=_non_negative_finite_float, default=None)
    parser.add_argument("--regime-min-pattern-score", type=_score_threshold, default=None)
    parser.add_argument("--high-vol-breakout-atr-multiplier", type=_non_negative_finite_float, default=None)
    parser.add_argument("--block-low-liquidity-pattern-entries", action="store_true")
    parser.add_argument("--block-wide-spread-pattern-entries", action="store_true")
    parser.add_argument("--max-account-drawdown", type=_positive_finite_float, default=None)
    parser.add_argument("--max-consecutive-losses", type=int, default=None)
    parser.add_argument("--max-daily-loss", type=_positive_finite_float, default=None)
    parser.add_argument("--no-persist", action="store_true")
    parser.add_argument("--profile", action="store_true")
    return parser


_OWNER_FVG_DEFAULT_FLAGS: dict[str, tuple[str, ...]] = {
    "cost_profile": ("--cost-profile",),
    "enable_fvg_v2": ("--enable-fvg-v2", "--disable-fvg-v2"),
    "enable_fvg_v2_channel": ("--enable-fvg-v2-channel", "--disable-fvg-v2-channel"),
    "fvg_channel_standalone_scan": ("--fvg-channel-standalone-scan", "--disable-fvg-channel-standalone-scan"),
    "fvg_channel_window": ("--fvg-channel-window",),
    "fvg_channel_max_wait_bars": ("--fvg-channel-max-wait-bars",),
    "enable_fvg_close_volume_filter": ("--enable-fvg-close-volume-filter", "--disable-fvg-close-volume-filter"),
    "fvg_close_volume_window": ("--fvg-close-volume-window",),
    "fvg_min_close_volume_ratio": ("--fvg-min-close-volume-ratio",),
    "fvg_close_volume_input_mode": ("--fvg-close-volume-input-mode",),
    "fvg_close_volume_baseline_mode": ("--fvg-close-volume-baseline-mode",),
    "fvg_use_trend_score": ("--fvg-use-trend-score", "--disable-fvg-trend-score"),
    "fvg_use_fibonacci_confluence": ("--fvg-use-fibonacci-confluence", "--disable-fvg-fibonacci-confluence"),
    "fvg_stop_mode": ("--fvg-stop-mode",),
    "enforce_candle_continuity": ("--enforce-candle-continuity", "--no-enforce-candle-continuity"),
    "enable_market_regime": ("--enable-market-regime", "--disable-market-regime"),
    "starting_cash": ("--starting-cash",),
    "starting_cash_currency": ("--starting-cash-currency",),
    "quote_currency": ("--quote-currency",),
    "krw_per_usdt": ("--krw-per-usdt",),
    "position_sizing_mode": ("--position-sizing-mode",),
    "position_sizing_value": ("--position-sizing-value",),
}
_MANUAL_COST_FLAGS = (
    "--maker-fee-bps",
    "--taker-fee-bps",
    "--spread-bps",
    "--slippage-bps",
    "--minimum-slippage-bps",
    "--volatility-slippage-multiplier",
)
_OWNER_FVG_DEFAULT_VALUES: dict[str, object] = {
    "cost_profile": "conservative_crypto_1m",
    "enable_fvg_v2": True,
    "enable_fvg_v2_channel": True,
    "fvg_channel_standalone_scan": True,
    "fvg_channel_window": 20,
    "fvg_channel_max_wait_bars": 5,
    "enable_fvg_close_volume_filter": True,
    "fvg_close_volume_window": 20,
    "fvg_min_close_volume_ratio": 2.0,
    "fvg_close_volume_input_mode": "base_volume",
    "fvg_close_volume_baseline_mode": "prior_only",
    "fvg_use_trend_score": True,
    "fvg_use_fibonacci_confluence": True,
    "fvg_stop_mode": "wider_of_fvg_and_swing",
    "enforce_candle_continuity": True,
    "enable_market_regime": True,
    "starting_cash": 1_000_000.0,
    "starting_cash_currency": "KRW",
    "krw_per_usdt": 1500.0,
    "position_sizing_mode": "cash_fraction",
    "position_sizing_value": 0.10,
}
_OWNER_ORDER_BLOCK_DEFAULT_VALUES: dict[str, object] = {
    "cost_profile": "conservative_crypto_1m",
    "ob_risk_exit_mode": "previous_candle_1r",
}
_OWNER_ORDER_BLOCK_DEFAULT_FLAGS: dict[str, tuple[str, ...]] = {
    "cost_profile": ("--cost-profile",),
    "ob_risk_exit_mode": ("--ob-risk-exit-mode",),
}
_OWNER_LIQUIDITY_SWEEP_DEFAULT_VALUES: dict[str, object] = {
    "cost_profile": "conservative_crypto_1m",
    "enforce_candle_continuity": True,
    "enable_market_regime": True,
    "position_sizing_mode": "cash_fraction",
    "position_sizing_value": 0.10,
}
_OWNER_LIQUIDITY_SWEEP_DEFAULT_FLAGS: dict[str, tuple[str, ...]] = {
    "cost_profile": ("--cost-profile",),
    "enforce_candle_continuity": ("--enforce-candle-continuity", "--no-enforce-candle-continuity"),
    "enable_market_regime": ("--enable-market-regime", "--disable-market-regime"),
    "position_sizing_mode": ("--position-sizing-mode",),
    "position_sizing_value": ("--position-sizing-value",),
}


def _raw_args_include_flag(raw_args: Sequence[str], flags: Sequence[str]) -> bool:
    flag_set = set(flags)
    return any(str(token).split("=", 1)[0] in flag_set for token in raw_args)


def _apply_owner_fvg_v2_channel_defaults(args: argparse.Namespace, raw_args: Sequence[str]) -> argparse.Namespace:
    strategy_key = _select_strategy_key(args)
    profile_enabled = strategy_key == "FAIR_VALUE_GAP"
    defaulted_fields: list[str] = []
    explicit_fields: list[str] = []
    skipped_fields: list[str] = []

    def has_field_flag(field: str) -> bool:
        return _raw_args_include_flag(raw_args, _OWNER_FVG_DEFAULT_FLAGS[field])

    def apply_field(field: str, value: object) -> None:
        if has_field_flag(field):
            explicit_fields.append(field)
            return
        setattr(args, field, value)
        defaulted_fields.append(field)

    if profile_enabled:
        if has_field_flag("cost_profile"):
            explicit_fields.append("cost_profile")
        elif _raw_args_include_flag(raw_args, _MANUAL_COST_FLAGS):
            skipped_fields.append("cost_profile")
        else:
            args.cost_profile = _OWNER_FVG_DEFAULT_VALUES["cost_profile"]
            defaulted_fields.append("cost_profile")

        for field in (
            "enable_fvg_v2",
            "enable_fvg_v2_channel",
            "fvg_channel_standalone_scan",
            "fvg_channel_window",
            "fvg_channel_max_wait_bars",
            "enable_fvg_close_volume_filter",
            "fvg_close_volume_window",
            "fvg_min_close_volume_ratio",
            "fvg_close_volume_input_mode",
            "fvg_close_volume_baseline_mode",
            "fvg_use_trend_score",
            "fvg_use_fibonacci_confluence",
            "fvg_stop_mode",
            "enforce_candle_continuity",
            "enable_market_regime",
            "starting_cash",
            "starting_cash_currency",
            "krw_per_usdt",
        ):
            apply_field(field, _OWNER_FVG_DEFAULT_VALUES[field])

        mode_is_explicit = has_field_flag("position_sizing_mode")
        value_is_explicit = has_field_flag("position_sizing_value")
        if mode_is_explicit:
            explicit_fields.append("position_sizing_mode")
        else:
            args.position_sizing_mode = _OWNER_FVG_DEFAULT_VALUES["position_sizing_mode"]
            defaulted_fields.append("position_sizing_mode")
        if value_is_explicit:
            explicit_fields.append("position_sizing_value")
        elif not mode_is_explicit:
            args.position_sizing_value = _OWNER_FVG_DEFAULT_VALUES["position_sizing_value"]
            defaulted_fields.append("position_sizing_value")
        else:
            skipped_fields.append("position_sizing_value")

    args.owner_fvg_v2_channel_default_profile = {
        "schema_version": "owner_fvg_v2_channel_default_profile_v1",
        "profile_key": OWNER_FVG_V2_CHANNEL_DEFAULT_PROFILE_KEY,
        "enabled": profile_enabled,
        "applies_to_pattern": "FAIR_VALUE_GAP",
        "selected_pattern": strategy_key,
        "defaulted_fields": sorted(defaulted_fields),
        "explicit_fields": sorted(set(explicit_fields)),
        "skipped_fields": sorted(skipped_fields),
        "start_time_defaulted": False,
        "applied_values": {
            field: getattr(args, field)
            for field in sorted(_OWNER_FVG_DEFAULT_VALUES)
            if hasattr(args, field)
        },
        "scope": "offline_backtest_research_only",
    }
    ob_defaulted_fields: list[str] = []
    ob_explicit_fields: list[str] = []
    ob_skipped_fields: list[str] = []
    ob_profile_enabled = strategy_key == "ORDER_BLOCK"
    if ob_profile_enabled:
        if _raw_args_include_flag(raw_args, _OWNER_ORDER_BLOCK_DEFAULT_FLAGS["cost_profile"]):
            ob_explicit_fields.append("cost_profile")
        elif _raw_args_include_flag(raw_args, _MANUAL_COST_FLAGS):
            ob_skipped_fields.append("cost_profile")
        else:
            args.cost_profile = _OWNER_ORDER_BLOCK_DEFAULT_VALUES["cost_profile"]
            ob_defaulted_fields.append("cost_profile")
        if _raw_args_include_flag(raw_args, _OWNER_ORDER_BLOCK_DEFAULT_FLAGS["ob_risk_exit_mode"]):
            ob_explicit_fields.append("ob_risk_exit_mode")
        else:
            args.ob_risk_exit_mode = _OWNER_ORDER_BLOCK_DEFAULT_VALUES["ob_risk_exit_mode"]
            ob_defaulted_fields.append("ob_risk_exit_mode")
    args.owner_order_block_default_profile = {
        "schema_version": "owner_order_block_default_profile_v1",
        "profile_key": OWNER_ORDER_BLOCK_DEFAULT_PROFILE_KEY,
        "enabled": ob_profile_enabled,
        "applies_to_pattern": "ORDER_BLOCK",
        "selected_pattern": strategy_key,
        "defaulted_fields": sorted(ob_defaulted_fields),
        "explicit_fields": sorted(ob_explicit_fields),
        "skipped_fields": sorted(ob_skipped_fields),
        "applied_values": {
            field: getattr(args, field)
            for field in sorted(_OWNER_ORDER_BLOCK_DEFAULT_VALUES)
            if hasattr(args, field)
        },
        "scope": "offline_backtest_research_only",
    }
    lsr_defaulted_fields: list[str] = []
    lsr_explicit_fields: list[str] = []
    lsr_skipped_fields: list[str] = []
    lsr_profile_enabled = strategy_key == "LIQUIDITY_SWEEP_REVERSAL"
    if lsr_profile_enabled:
        if _raw_args_include_flag(raw_args, _OWNER_LIQUIDITY_SWEEP_DEFAULT_FLAGS["cost_profile"]):
            lsr_explicit_fields.append("cost_profile")
        elif _raw_args_include_flag(raw_args, _MANUAL_COST_FLAGS):
            lsr_skipped_fields.append("cost_profile")
        else:
            args.cost_profile = _OWNER_LIQUIDITY_SWEEP_DEFAULT_VALUES["cost_profile"]
            lsr_defaulted_fields.append("cost_profile")
        for field in (
            "enforce_candle_continuity",
            "enable_market_regime",
            "position_sizing_mode",
            "position_sizing_value",
        ):
            if _raw_args_include_flag(raw_args, _OWNER_LIQUIDITY_SWEEP_DEFAULT_FLAGS[field]):
                lsr_explicit_fields.append(field)
            else:
                setattr(args, field, _OWNER_LIQUIDITY_SWEEP_DEFAULT_VALUES[field])
                lsr_defaulted_fields.append(field)
    args.owner_liquidity_sweep_reversal_default_profile = {
        "schema_version": "owner_liquidity_sweep_reversal_default_profile_v1",
        "profile_key": OWNER_LIQUIDITY_SWEEP_DEFAULT_PROFILE_KEY,
        "enabled": lsr_profile_enabled,
        "applies_to_pattern": "LIQUIDITY_SWEEP_REVERSAL",
        "selected_pattern": strategy_key,
        "defaulted_fields": sorted(lsr_defaulted_fields),
        "explicit_fields": sorted(lsr_explicit_fields),
        "skipped_fields": sorted(lsr_skipped_fields),
        "applied_values": {
            field: getattr(args, field)
            for field in sorted(_OWNER_LIQUIDITY_SWEEP_DEFAULT_VALUES)
            if hasattr(args, field)
        },
        "scope": "offline_backtest_research_only",
    }
    return args


def _ms(start: float, end: float) -> float:
    return round((end - start) * 1000.0, 3)


def _build_runtime_metadata(
    strategy_key: str,
    candle_count: int,
    pattern_profile: dict[str, object],
    timings: dict[str, float],
) -> dict[str, object]:
    return {
        "runtime": {
            "runtime_schema_version": "v1",
            "strategy_key": strategy_key,
            "created_by": "quant-bitcoin-strategy-backtest",
            "candle_count": candle_count,
            "total_elapsed_ms": timings.get("total_elapsed_ms", 0.0),
            "candle_load_elapsed_ms": timings.get("load_candles_ms", 0.0),
            "action_build_elapsed_ms": timings.get("build_actions_ms", 0.0),
            "engine_elapsed_ms": timings.get("run_engine_ms", 0.0),
            "persistence_elapsed_ms": timings.get("persist_ms", 0.0),
            "json_output_elapsed_ms": timings.get("json_output_ms", 0.0),
            "pattern_timings": [pattern_profile],
        }
    }


def _build_strategy_parameters(
    *,
    strategy_key: str,
    entry_filter_config: PatternEntryFilterConfig,
    transaction_cost_config: TransactionCostConfig,
    default_liquidity_role: LiquidityRole,
    position_sizing: PositionSizingConfig,
    policy_metadata: dict[str, object],
    simulated_margin: SimulatedMarginConfig,
    risk_free_rate: float,
    fvg_entry_metadata: dict[str, object] | None = None,
    fvg_direction_metadata: dict[str, object] | None = None,
    fvg_v2_metadata: dict[str, object] | None = None,
    fvg_order_block_confluence_config: FvgOrderBlockConfluenceConfig | None = None,
    pattern_execution_policy: dict[str, object] | None = None,
    workflow_settings: dict[str, object] | None = None,
    cost_profile_metadata: dict[str, object] | None = None,
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
    order_block_config: OrderBlockConfig | None = None,
    order_block_entry_volume_filter_config: OrderBlockEntryVolumeFilterConfig | None = None,
    order_block_mtf_filter_config: OrderBlockMtfFilterConfig | None = None,
    order_block_risk_exit_config: OrderBlockRiskExitConfig | None = None,
    liquidity_sweep_config: LiquiditySweepReversalConfig | None = None,
    liquidity_sweep_risk_exit_config: LiquiditySweepReversalRiskExitConfig | None = None,
    session_range_liquidity_breakout_reversal_config: SessionRangeLiquidityBreakoutReversalConfig | None = None,
    pattern_regime_thresholds: PatternRegimeThresholdConfig | None = None,
    cash_denomination_metadata: dict[str, object] | None = None,
    research_metadata: dict[str, object] | None = None,
    lookback_return_momentum_config: LookbackReturnMomentumConfig | None = None,
) -> dict[str, object]:
    return {
        "pattern": strategy_key,
        "research": research_metadata
        or {"schema_version": "research_run_metadata_v1", "enabled": False},
        "pattern_entry_filter": {
            "allowed_statuses": list(entry_filter_config.allowed_statuses),
            "minimum_pattern_score": entry_filter_config.minimum_pattern_score,
            "minimum_risk_reward": entry_filter_config.minimum_risk_reward,
            "quantity_override": entry_filter_config.quantity_override,
        },
        "transaction_cost": {
            "maker_fee_bps": transaction_cost_config.maker_fee_bps,
            "taker_fee_bps": transaction_cost_config.taker_fee_bps,
            "spread_bps": transaction_cost_config.spread_bps,
            "slippage_bps": transaction_cost_config.slippage_bps,
            "minimum_slippage_bps": transaction_cost_config.minimum_slippage_bps,
            "volatility_slippage_multiplier": transaction_cost_config.volatility_slippage_multiplier,
            "liquidity_role": default_liquidity_role.value,
        },
        "cash_denomination": cash_denomination_metadata,
        "lookback_return_momentum": (
            lookback_return_momentum_config.to_metadata()
            if lookback_return_momentum_config is not None
            else {
                "schema_version": "lookback_return_momentum_config_v1",
                "enabled": False,
            }
        ),
        "cost_profile": cost_profile_metadata,
        "cost_aware_entry_filter": _cost_aware_entry_filter_metadata(cost_aware_entry_filter_config),
        "position_sizing": position_sizing.to_metadata(),
        "fvg_entry": fvg_entry_metadata or _build_fvg_entry_metadata(
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            PatternEntryConfig(),
            None,
        ),
        "fvg_direction": fvg_direction_metadata or _build_fvg_direction_metadata(False),
        "fvg_v2": fvg_v2_metadata,
        "fvg_order_block_confluence": _fvg_order_block_confluence_metadata(fvg_order_block_confluence_config),
        "order_block": _order_block_config_metadata(order_block_config),
        "order_block_entry_volume_filter": (
            order_block_entry_volume_filter_config.to_metadata()
            if order_block_entry_volume_filter_config is not None
            else OrderBlockEntryVolumeFilterConfig(enabled=False).to_metadata()
        ),
        "order_block_mtf_filter": (
            order_block_mtf_filter_config.to_metadata()
            if order_block_mtf_filter_config is not None
            else OrderBlockMtfFilterConfig(enabled=False).to_metadata()
        ),
        "order_block_risk_exit": (
            order_block_risk_exit_config.to_metadata()
            if order_block_risk_exit_config is not None
            else OrderBlockRiskExitConfig(mode="ZONE_STRUCTURAL_2R").to_metadata()
        ),
        "liquidity_sweep_reversal": (
            liquidity_sweep_config.to_metadata()
            if liquidity_sweep_config is not None
            else {"schema_version": "liquidity_sweep_reversal_config_v1", "enabled": False}
        ),
        "liquidity_sweep_reversal_risk_exit": (
            liquidity_sweep_risk_exit_config.to_metadata()
            if liquidity_sweep_risk_exit_config is not None
            else {
                "schema_version": "liquidity_sweep_reversal_risk_exit_config_v1",
                "enabled": False,
            }
        ),
        "session_range_liquidity_breakout_reversal": (
            session_range_liquidity_breakout_reversal_config.to_metadata()
            if session_range_liquidity_breakout_reversal_config is not None
            else {
                "schema_version": "session_range_liquidity_breakout_reversal_config_v1",
                "enabled": False,
            }
        ),
        "pattern_execution_policy": pattern_execution_policy,
        "pattern_regime_thresholds": (
            pattern_regime_thresholds.to_metadata()
            if pattern_regime_thresholds is not None
            else {"schema_version": "pattern_regime_thresholds_v1", "enabled": False}
        ),
        "workflow_settings": workflow_settings,
        "short_exposure_policy": policy_metadata["short_exposure_policy"],
        "simulated_margin": simulated_margin.to_metadata(),
        "risk_free_rate": risk_free_rate,
    }


def _build_research_metadata(args: argparse.Namespace) -> dict[str, object]:
    task_id = getattr(args, "research_task_id", None)
    variant_id = getattr(args, "research_variant_id", None)
    window_id = getattr(args, "research_window_id", None)
    run_group = getattr(args, "research_run_group", None)
    enabled = any(value for value in (task_id, variant_id, window_id, run_group))
    return {
        "schema_version": "research_run_metadata_v1",
        "enabled": bool(enabled),
        "task_id": task_id,
        "variant_id": variant_id,
        "window_id": window_id,
        "run_group": run_group,
        "scope": "offline_backtest_research_only",
    }


def _cost_aware_entry_filter_metadata(config: CostAwareEntryFilterConfig | None) -> dict[str, object]:
    if config is None:
        return {
            "schema_version": "cost_aware_entry_filter_config_v1",
            "enabled": False,
        }
    return {
        "schema_version": "cost_aware_entry_filter_config_v1",
        "enabled": config.enabled,
        "min_net_reward_bps": config.min_net_reward_bps,
        "min_net_rr": config.min_net_rr,
        "cost_profile_name": config.cost_profile_name,
        "liquidity_role": config.liquidity_role.value,
    }


def _fvg_order_block_confluence_metadata(config: FvgOrderBlockConfluenceConfig | None) -> dict[str, object]:
    if config is None:
        return {
            "schema_version": "fvg_order_block_confluence_config_v1",
            "enabled": False,
            "default_behavior_preserved": True,
        }
    return config.to_metadata()


def _build_reproducibility_metadata(
    *,
    args: argparse.Namespace,
    candles: pd.DataFrame,
    strategy_key: str,
    strategy_name: str,
    strategy_version: str,
    strategy_parameters: dict[str, object],
    engine_name: str,
    engine_version: str,
) -> dict[str, object]:
    dataset = _build_dataset_identity(args, candles)
    config = {
        "strategy_parameters": strategy_parameters,
        "engine": {
            "name": engine_name,
            "version": engine_version,
            "starting_cash": getattr(args, "effective_starting_cash", args.starting_cash),
            "source_starting_cash": args.starting_cash,
            "cash_denomination": getattr(args, "cash_denomination_metadata", None),
            "trade_quantity": args.trade_quantity,
        },
    }
    return {
        "schema_version": "backtest_reproducibility_v1",
        "created_by": "quant-bitcoin-strategy-backtest",
        "dataset": dataset,
        "strategy": {
            "key": strategy_key,
            "name": strategy_name,
            "version": strategy_version,
            "parameters_hash": _metadata_hash(strategy_parameters),
        },
        "engine": config["engine"],
        "config_hashes": {
            "dataset": _metadata_hash(dataset),
            "strategy_parameters": _metadata_hash(strategy_parameters),
            "engine": _metadata_hash(config["engine"]),
            "full_config": _metadata_hash(config),
        },
        "random_seeds": {
            "walk_forward": None,
            "monte_carlo": None,
        },
        "environment": {
            "database_url": _redact_sensitive_value(args.database_url),
            "profile_enabled": bool(args.profile),
        },
        "sensitive_values_redacted": True,
    }


def _build_dataset_identity(args: argparse.Namespace, candles: pd.DataFrame) -> dict[str, object]:
    return {
        "source": args.source,
        "symbol": args.symbol,
        "interval": args.interval,
        "requested_start_time": _json_safe(args.start_time),
        "requested_end_time": _json_safe(args.end_time),
        "actual_start_time": _iso_timestamp(candles.iloc[0]["timestamp"]) if not candles.empty else None,
        "actual_end_time": _iso_timestamp(candles.iloc[-1]["timestamp"]) if not candles.empty else None,
        "candle_count": int(len(candles)),
        "candle_content_hash": _candle_content_hash(candles),
        "quality": _candle_quality_summary(candles, args.interval),
    }


def _candle_content_hash(candles: pd.DataFrame) -> str:
    rows = []
    for row in candles.loc[:, ["timestamp", "open", "high", "low", "close", "volume"]].itertuples(index=False):
        rows.append(
            {
                "timestamp": _iso_timestamp(row.timestamp),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
        )
    return _metadata_hash({"candles": rows})


def _candle_quality_summary(candles: pd.DataFrame, interval: str) -> dict[str, object]:
    timestamp_count = int(len(candles))
    duplicate_count = (
        int(pd.to_datetime(candles["timestamp"], utc=True).duplicated().sum())
        if "timestamp" in candles
        else 0
    )
    gap_count = 0
    expected_delta = _interval_delta(interval)
    if expected_delta is not None and timestamp_count > 1 and "timestamp" in candles:
        timestamps = pd.to_datetime(candles["timestamp"], utc=True)
        gap_count = int((timestamps.diff().iloc[1:] != expected_delta).sum())
    return {
        "schema_version": "candle_quality_summary_v1",
        "row_count": timestamp_count,
        "duplicate_timestamp_count": duplicate_count,
        "interval_gap_count": gap_count,
        "continuity_checked": expected_delta is not None,
    }


def _interval_delta(interval: str) -> pd.Timedelta | None:
    unit = str(interval)
    try:
        if unit.endswith("m"):
            return pd.Timedelta(minutes=int(unit[:-1]))
        if unit.endswith("h"):
            return pd.Timedelta(hours=int(unit[:-1]))
        if unit.endswith("d"):
            return pd.Timedelta(days=int(unit[:-1]))
    except ValueError:
        return None
    return None


def _metadata_hash(value: object) -> str:
    return json_metadata_hash(value)


def _redact_sensitive_value(value: object) -> object:
    if value is None:
        return None
    text = str(value)
    if "://" in text:
        return _redact_url(text)
    lowered = text.lower()
    if any(token in lowered for token in ("password", "secret", "token", "api_key", "apikey")):
        return "<redacted>"
    return text


def _redact_url(value: str) -> str:
    parts = urlsplit(value)
    if "@" not in parts.netloc:
        return value
    host = parts.hostname or ""
    if parts.port is not None:
        host = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, f"***:***@{host}", parts.path, parts.query, parts.fragment))


def _optional_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _non_negative_finite_float(value: str) -> float:
    parsed = float(value)
    if not isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative finite float")
    return parsed


def _positive_finite_float(value: str) -> float:
    parsed = float(value)
    if not isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive finite float")
    return parsed


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not isfinite(parsed):
        raise argparse.ArgumentTypeError("value must be finite")
    return parsed


def _score_threshold(value: str) -> float:
    parsed = _non_negative_finite_float(value)
    if parsed > 1:
        raise argparse.ArgumentTypeError("score threshold must be between 0 and 1")
    return parsed


def _liquidity_role(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in {LiquidityRole.MAKER.value, LiquidityRole.TAKER.value}:
        raise argparse.ArgumentTypeError("liquidity-role must be MAKER or TAKER")
    return normalized


def _build_cash_denomination_metadata(args: argparse.Namespace) -> dict[str, object]:
    source_amount = float(args.starting_cash)
    if not isfinite(source_amount) or source_amount < 0:
        raise ValueError("--starting-cash must be a non-negative finite number")

    quote_currency = _cash_currency(getattr(args, "quote_currency", None)) or _infer_quote_currency(args.symbol)
    source_currency = _cash_currency(getattr(args, "starting_cash_currency", None)) or quote_currency
    if source_currency in {"QUOTE", "QUOTE_CURRENCY"}:
        source_currency = quote_currency

    raw_args = tuple(getattr(args, "_raw_args", ()) or ())
    currency_was_explicit = _raw_args_include_flag(raw_args, ("--starting-cash-currency",))
    quote_was_explicit = _raw_args_include_flag(raw_args, ("--quote-currency",))
    starting_cash_was_explicit = _raw_args_include_flag(raw_args, ("--starting-cash",))

    converted = False
    conversion_rate = None
    conversion_pair = None
    conversion_source = None
    if source_currency == quote_currency:
        effective_quote_cash = source_amount
    elif source_currency == "KRW" and quote_currency == "USDT":
        rate = getattr(args, "krw_per_usdt", None)
        if rate is None:
            raise ValueError("--starting-cash-currency KRW requires --krw-per-usdt for BTCUSDT quote-cash conversion")
        conversion_rate = float(rate)
        effective_quote_cash = source_amount / conversion_rate
        converted = True
        conversion_pair = "KRW/USDT"
        conversion_source = "manual_cli_krw_per_usdt"
    else:
        raise ValueError(
            f"unsupported starting cash conversion: {source_currency} to {quote_currency}; "
            "supported conversion in this task is KRW to USDT with --krw-per-usdt"
        )

    metadata = {
        "schema_version": "backtest_cash_denomination_v1",
        "source_starting_cash": source_amount,
        "source_currency": source_currency,
        "quote_currency": quote_currency,
        "effective_quote_starting_cash": effective_quote_cash,
        "engine_starting_cash": effective_quote_cash,
        "converted": converted,
        "conversion_rate": conversion_rate,
        "conversion_pair": conversion_pair,
        "conversion_source": conversion_source,
        "starting_cash_currency_was_explicit": currency_was_explicit,
        "starting_cash_was_explicit": starting_cash_was_explicit,
        "quote_currency_was_explicit": quote_was_explicit,
        "engine_accounting_currency": quote_currency,
        "quote_cash_semantics": "strategy engine cash, costs, PnL, and equity are denominated in the symbol quote currency",
        "live_fx_lookup_used": False,
        "scope": "offline_backtest_research_only",
    }
    if starting_cash_was_explicit and not currency_was_explicit:
        metadata["assumption_warning"] = (
            f"--starting-cash-currency was not provided; treating --starting-cash as {quote_currency} quote cash"
        )
    return metadata


def _cash_currency(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return normalized or None


def _infer_quote_currency(symbol: object) -> str:
    normalized = str(symbol or "").strip().upper()
    for suffix in ("USDT", "USDC", "BUSD", "USD", "KRW", "BTC", "ETH"):
        if normalized.endswith(suffix) and len(normalized) > len(suffix):
            return suffix
    return "USDT"


def _build_transaction_cost_config(args: argparse.Namespace) -> tuple[TransactionCostConfig, LiquidityRole]:
    manual_values = {
        "maker_fee_bps": args.maker_fee_bps,
        "taker_fee_bps": args.taker_fee_bps,
        "spread_bps": args.spread_bps,
        "slippage_bps": args.slippage_bps,
        "minimum_slippage_bps": args.minimum_slippage_bps,
        "volatility_slippage_multiplier": args.volatility_slippage_multiplier,
    }
    selected_profile = cost_profile(args.cost_profile) if args.cost_profile else None
    if selected_profile is not None and manual_cost_overrides_present(manual_values) and not args.allow_cost_profile_overrides:
        raise ValueError("--cost-profile cannot be combined with manual bps values unless --allow-cost-profile-overrides is set")
    if selected_profile is not None and not args.allow_cost_profile_overrides:
        config = selected_profile.config
    else:
        config = TransactionCostConfig(
            maker_fee_bps=args.maker_fee_bps if selected_profile is None else args.maker_fee_bps or selected_profile.config.maker_fee_bps,
            taker_fee_bps=args.taker_fee_bps if selected_profile is None else args.taker_fee_bps or selected_profile.config.taker_fee_bps,
            spread_bps=args.spread_bps if selected_profile is None else args.spread_bps or selected_profile.config.spread_bps,
            slippage_bps=args.slippage_bps if selected_profile is None else args.slippage_bps or selected_profile.config.slippage_bps,
            minimum_slippage_bps=args.minimum_slippage_bps if selected_profile is None else args.minimum_slippage_bps or selected_profile.config.minimum_slippage_bps,
            volatility_slippage_multiplier=args.volatility_slippage_multiplier if selected_profile is None else args.volatility_slippage_multiplier or selected_profile.config.volatility_slippage_multiplier,
        )
    return (
        config,
        LiquidityRole(args.liquidity_role),
    )


def _build_cost_aware_entry_filter_config(
    args: argparse.Namespace,
    transaction_cost_config: TransactionCostConfig,
    default_liquidity_role: LiquidityRole,
) -> CostAwareEntryFilterConfig:
    return CostAwareEntryFilterConfig(
        enabled=bool(args.enable_cost_aware_entry_filter),
        min_net_reward_bps=float(args.min_net_reward_bps),
        min_net_rr=float(args.min_net_rr),
        transaction_cost_config=transaction_cost_config,
        liquidity_role=default_liquidity_role,
        cost_profile_name=args.cost_profile,
    )


def _cost_profile_metadata(args: argparse.Namespace, config: TransactionCostConfig, result=None) -> dict[str, object]:
    profile = cost_profile(args.cost_profile) if args.cost_profile else ("manual" if any([
        config.maker_fee_bps,
        config.taker_fee_bps,
        config.spread_bps,
        config.slippage_bps,
        config.minimum_slippage_bps,
        config.volatility_slippage_multiplier,
    ]) else "zero")
    if isinstance(profile, str):
        metadata = {
            "schema_version": "transaction_cost_profile_v1",
            "profile_key": profile,
            "description": "Manual bps values" if profile == "manual" else "No fees, spread, or slippage; useful only as a debugging baseline.",
            "source": "manual_cli_values" if profile == "manual" else "implicit_zero_default",
            "zero_cost_profile": profile == "zero",
        }
    else:
        metadata = profile.to_metadata()
    metadata.update(
        {
            "maker_fee_bps": config.maker_fee_bps,
            "taker_fee_bps": config.taker_fee_bps,
            "spread_bps": config.spread_bps,
            "slippage_bps": config.slippage_bps,
            "minimum_slippage_bps": config.minimum_slippage_bps,
            "volatility_slippage_multiplier": config.volatility_slippage_multiplier,
            "overrides_allowed": bool(args.allow_cost_profile_overrides),
        }
    )
    if result is not None:
        summary = result.summary
        total_notional = sum(getattr(execution, "notional", 0.0) for execution in result.executions)
        total_cost = summary.gross_pnl - summary.net_pnl
        metadata["cost_sensitivity"] = {
            "cost_to_gross_pnl_ratio": None if summary.gross_pnl == 0 else total_cost / abs(summary.gross_pnl),
            "break_even_cost_bps": break_even_cost_bps(summary.gross_pnl, total_notional),
        }
    return metadata


def _build_position_sizing_config(args: argparse.Namespace) -> PositionSizingConfig:
    mode = PositionSizingMode(args.position_sizing_mode.upper())
    policy = InsufficientFundsPolicy(args.insufficient_funds_policy.upper())
    if mode in (PositionSizingMode.CASH_FRACTION, PositionSizingMode.TARGET_NOTIONAL, PositionSizingMode.EQUITY_RISK_FRACTION) and args.position_sizing_value is None:
        raise ValueError(f"{mode.value} requires --position-sizing-value")
    if mode in (PositionSizingMode.CASH_FRACTION, PositionSizingMode.EQUITY_RISK_FRACTION) and args.position_sizing_value is not None and args.position_sizing_value > 1.0:
        raise ValueError(f"{mode.value} --position-sizing-value must be <= 1.0")
    return PositionSizingConfig(
        mode=mode,
        value=args.position_sizing_value,
        insufficient_funds_policy=policy,
    )


def _build_simulated_margin_config(args: argparse.Namespace) -> tuple[ShortExposureMode, SimulatedMarginConfig]:
    short_mode = ShortExposureMode(args.short_exposure_mode.upper())
    margin_policy = InsufficientFundsPolicy(args.insufficient_margin_policy.upper())
    if short_mode is ShortExposureMode.SIMULATED_MARGIN:
        if args.simulated_margin_leverage is None:
            raise ValueError("simulated_margin short exposure requires --simulated-margin-leverage")
        return short_mode, SimulatedMarginConfig(
            enabled=True,
            leverage=args.simulated_margin_leverage,
            insufficient_margin_policy=margin_policy,
        )
    if args.simulated_margin_leverage is not None:
        raise ValueError("--simulated-margin-leverage requires --short-exposure-mode simulated_margin")
    return short_mode, SimulatedMarginConfig(enabled=False, insufficient_margin_policy=margin_policy)


def _build_guardrail_config(args: argparse.Namespace) -> BacktestGuardrailConfig:
    return BacktestGuardrailConfig(
        max_account_drawdown=args.max_account_drawdown,
        max_consecutive_losses=args.max_consecutive_losses,
        max_daily_loss=args.max_daily_loss,
    )


def _build_market_regime_config(args: argparse.Namespace) -> MarketRegimeConfig:
    window = args.market_regime_window
    if window < 1:
        raise ValueError("market_regime_window must be at least 1")
    return MarketRegimeConfig(
        volatility_window=window,
        trend_window=window,
        liquidity_window=window,
        mean_reversion_window=window,
        minimum_average_trading_value=args.market_regime_min_trading_value,
    )


def _market_regime_by_timestamp(candles: pd.DataFrame, args: argparse.Namespace) -> dict[object, dict[str, object]] | None:
    if not args.enable_market_regime and not _build_pattern_regime_threshold_config(args).enabled:
        return None
    frame = candles.copy(deep=True)
    if "symbol" not in frame.columns:
        frame["symbol"] = args.symbol
    rows = calculate_market_regime(frame, _build_market_regime_config(args))
    return {
        row["timestamp"]: {
            "market_regime": row["market_regime"],
            "volatility_regime": row["volatility_regime"],
            "liquidity_regime": row["liquidity_regime"],
            "spread_regime": row["spread_regime"],
            "trend_regime": row["trend_regime"],
            "mean_reversion_regime": row["mean_reversion_regime"],
            "trading_value_percentile": row["trading_value_percentile"],
            "liquidity_zscore": row["liquidity_zscore"],
            "range_spread_proxy_percentile": row["range_spread_proxy_percentile"],
            "wick_dominance_proxy": row["wick_dominance_proxy"],
            "session_tag": row["session_tag"],
            "weekday_tag": row["weekday_tag"],
            "market_regime_is_valid": bool(row["is_valid"]),
            "market_regime_reason": row["reason"],
            "tradability_proxy_caveat": "OHLCV-derived liquidity/spread/session proxies; not true bid-ask or order-book data.",
        }
        for _, row in rows.iterrows()
    }


def _workflow_settings_metadata(args: argparse.Namespace, guardrails: BacktestGuardrailConfig) -> dict[str, object]:
    regime_thresholds = _build_pattern_regime_threshold_config(args)
    return {
        "schema_version": "canonical_cli_workflow_settings_v1",
        "enforce_candle_continuity": bool(args.enforce_candle_continuity),
        "market_regime_enabled": bool(args.enable_market_regime),
        "market_regime": {
            "enabled": bool(args.enable_market_regime),
            "window": args.market_regime_window,
            "minimum_average_trading_value": args.market_regime_min_trading_value,
        },
        "pattern_regime_thresholds": regime_thresholds.to_metadata(),
        "cost_aware_entry_filter": {
            "schema_version": "cost_aware_entry_filter_config_v1",
            "enabled": bool(args.enable_cost_aware_entry_filter),
            "min_net_reward_bps": args.min_net_reward_bps,
            "min_net_rr": args.min_net_rr,
        },
        "fvg_order_block_confluence": _build_fvg_order_block_confluence_config(args).to_metadata(),
        "order_block_risk_exit": _build_order_block_risk_exit_config(args).to_metadata(),
        "guardrails": guardrails.to_metadata(),
        "cash_denomination": getattr(args, "cash_denomination_metadata", None),
        "owner_default_profile": getattr(
            args,
            "owner_fvg_v2_channel_default_profile",
            {
                "schema_version": "owner_fvg_v2_channel_default_profile_v1",
                "profile_key": OWNER_FVG_V2_CHANNEL_DEFAULT_PROFILE_KEY,
                "enabled": False,
            },
        ),
        "owner_order_block_default_profile": getattr(
            args,
            "owner_order_block_default_profile",
            {
                "schema_version": "owner_order_block_default_profile_v1",
                "profile_key": OWNER_ORDER_BLOCK_DEFAULT_PROFILE_KEY,
                "enabled": False,
            },
        ),
    }


def _select_strategy_key(args: argparse.Namespace) -> str:
    return (args.pattern or getattr(args, "strategy", None) or DEFAULT_STRATEGY).upper()


def _is_lookback_return_momentum_strategy(strategy_key: str) -> bool:
    return str(strategy_key).upper() == LOOKBACK_RETURN_MOMENTUM_KEY


def _build_lookback_return_momentum_config(
    args: argparse.Namespace,
) -> LookbackReturnMomentumConfig:
    return lookback_return_momentum_config_for_timeframe(
        args.interval,
        lookback_bars=getattr(args, "lookback_bars", None),
        entry_threshold=getattr(args, "entry_threshold", None),
        holding_bars=getattr(args, "holding_bars", None),
        risk_distance_mode=getattr(args, "risk_distance_mode", None),
        atr_period=getattr(args, "atr_period", None),
        atr_smoothing=getattr(args, "atr_smoothing", None),
        stop_loss_atr_multiple=getattr(args, "stop_loss_atr_multiple", None),
        take_profit_atr_multiple=getattr(args, "take_profit_atr_multiple", None),
        minimum_atr_bps=getattr(args, "minimum_atr_bps", None),
        risk_distance_pct=getattr(args, "risk_distance_pct", None),
        stop_loss_r=getattr(args, "stop_loss_r", None),
        take_profit_r=getattr(args, "take_profit_r", None),
    )


def _build_lookback_return_momentum_cost_aware_config(
    config: CostAwareEntryFilterConfig | None,
) -> LookbackReturnMomentumCostAwareConfig | None:
    if config is None:
        return None
    cost_config = config.transaction_cost_config or TransactionCostConfig()
    fee_bps = (
        cost_config.maker_fee_bps
        if config.liquidity_role is LiquidityRole.MAKER
        else cost_config.taker_fee_bps
    )
    return LookbackReturnMomentumCostAwareConfig(
        enabled=config.enabled,
        min_net_reward_bps=config.min_net_reward_bps,
        min_net_rr=config.min_net_rr,
        fee_bps=fee_bps,
        spread_bps=cost_config.spread_bps,
        slippage_bps=cost_config.slippage_bps,
        minimum_slippage_bps=cost_config.minimum_slippage_bps,
        volatility_slippage_multiplier=cost_config.volatility_slippage_multiplier,
        liquidity_role=config.liquidity_role.value,
        cost_profile_name=config.cost_profile_name,
    )


def _build_pattern_entry_filter_config(args: argparse.Namespace) -> PatternEntryFilterConfig:
    statuses = {"VALID"}
    if args.allowed_pattern_statuses:
        statuses = {v.strip().upper() for v in args.allowed_pattern_statuses.split(",") if v.strip()}
    if args.allow_weak_pattern_events:
        statuses.add("WEAK")
    return PatternEntryFilterConfig(
        allowed_statuses=tuple(sorted(statuses)),
        minimum_pattern_score=args.min_pattern_score,
        minimum_risk_reward=args.min_risk_reward,
        quantity_override=args.pattern_quantity_override,
        regime_threshold_config=_build_pattern_regime_threshold_config(args),
    )


def _build_pattern_regime_threshold_config(
    args: argparse.Namespace,
) -> PatternRegimeThresholdConfig:
    enabled = bool(args.enable_pattern_regime_thresholds)
    default_thresholds = PatternRegimeThresholdOverride(
        minimum_volume_ratio=args.regime_min_volume_ratio,
        breakout_atr_multiplier=args.regime_breakout_atr_multiplier,
        minimum_pattern_score=args.regime_min_pattern_score,
    )
    volatility_overrides = None
    if args.high_vol_breakout_atr_multiplier is not None:
        volatility_overrides = {
            "HIGH": PatternRegimeThresholdOverride(
                breakout_atr_multiplier=args.high_vol_breakout_atr_multiplier
            )
        }
        enabled = True
    liquidity_overrides = None
    if args.block_low_liquidity_pattern_entries:
        liquidity_overrides = {
            "LOW": PatternRegimeThresholdOverride(
                block_entry=True,
                block_reason="LOW_LIQUIDITY_REGIME_BLOCK",
            ),
            "UNTRADABLE": PatternRegimeThresholdOverride(
                block_entry=True,
                block_reason="UNTRADABLE_LIQUIDITY_REGIME_BLOCK",
            ),
        }
        enabled = True
    spread_overrides = None
    if args.block_wide_spread_pattern_entries:
        spread_overrides = {
            "WIDE": PatternRegimeThresholdOverride(
                block_entry=True,
                block_reason="WIDE_SPREAD_REGIME_BLOCK",
            )
        }
        enabled = True
    return PatternRegimeThresholdConfig(
        enabled=enabled,
        default_thresholds=default_thresholds,
        volatility_regime_overrides=volatility_overrides,
        liquidity_regime_overrides=liquidity_overrides,
        spread_regime_overrides=spread_overrides,
    )


def _selected_fvg_entry_mode(args: argparse.Namespace) -> PatternEntryMode:
    mode = PatternEntryMode(str(args.fvg_entry_mode).upper())
    custom_price = _selected_entry_custom_price(args)
    if mode is PatternEntryMode.LIMIT_AT_CUSTOM_PRICE and custom_price is None:
        raise ValueError("limit_at_custom_price requires --fvg-entry-custom-price")
    if mode is not PatternEntryMode.LIMIT_AT_CUSTOM_PRICE and custom_price is not None:
        raise ValueError("--fvg-entry-custom-price requires --fvg-entry-mode limit_at_custom_price")
    return mode


def _selected_pattern_entry_mode(args: argparse.Namespace, strategy_key: str) -> PatternEntryMode:
    if args.pattern_entry_mode is not None:
        mode = PatternEntryMode(str(args.pattern_entry_mode).upper())
    elif strategy_key == "FAIR_VALUE_GAP":
        mode = _selected_fvg_entry_mode(args)
    elif strategy_key == "LIQUIDITY_SWEEP_REVERSAL":
        mode = _selected_liquidity_sweep_entry_mode(args)
    else:
        mode = policy_for_pattern(strategy_key).default_entry_mode
    custom_price = _selected_entry_custom_price(args)
    if mode is PatternEntryMode.LIMIT_AT_CUSTOM_PRICE and custom_price is None:
        raise ValueError("limit_at_custom_price requires --fvg-entry-custom-price")
    if mode is not PatternEntryMode.LIMIT_AT_CUSTOM_PRICE and custom_price is not None:
        raise ValueError("--fvg-entry-custom-price requires --pattern-entry-mode limit_at_custom_price")
    validate_pattern_entry_mode(strategy_key, mode)
    return mode


def _selected_liquidity_sweep_entry_mode(args: argparse.Namespace) -> PatternEntryMode:
    mode = str(getattr(args, "lsr_entry_mode", "best_net_rr_between_fvg_midpoint_and_ob_618")).upper()
    if mode in {"MARKET_ON_RECLAIM_CLOSE", "MARKET_ON_DISPLACEMENT_CLOSE"}:
        return PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE
    if mode in {
        "LIMIT_AT_FVG_MIDPOINT",
        "LIMIT_AT_OB_618",
        "BEST_NET_RR_BETWEEN_FVG_MIDPOINT_AND_OB_618",
    }:
        return PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE
    raise ValueError(f"unsupported --lsr-entry-mode: {getattr(args, 'lsr_entry_mode', None)}")


def _selected_entry_custom_price(args: argparse.Namespace) -> float | None:
    pattern_custom_price = getattr(args, "pattern_entry_custom_price", None)
    fvg_custom_price = getattr(args, "fvg_entry_custom_price", None)
    if pattern_custom_price is not None and fvg_custom_price is not None and pattern_custom_price != fvg_custom_price:
        raise ValueError("--pattern-entry-custom-price and --fvg-entry-custom-price cannot disagree")
    return pattern_custom_price if pattern_custom_price is not None else fvg_custom_price


def _selected_fvg_entry_config(args: argparse.Namespace) -> PatternEntryConfig:
    expire_status = PatternEntryStatus(str(args.fvg_entry_expire_status).upper())
    entry_trigger = PatternEntryTrigger(str(args.fvg_entry_trigger).upper())
    return PatternEntryConfig(
        max_wait_bars=args.fvg_entry_max_wait_bars,
        expire_status=expire_status,
        entry_trigger=entry_trigger,
    )


def _selected_liquidity_sweep_entry_config(args: argparse.Namespace) -> PatternEntryConfig:
    max_wait = int(getattr(args, "lsr_entry_max_wait_bars", 20))
    if max_wait < 1:
        raise ValueError("--lsr-entry-max-wait-bars must be at least 1")
    return PatternEntryConfig(
        max_wait_bars=max_wait,
        expire_status=PatternEntryStatus.NOT_FILLED,
        entry_trigger=PatternEntryTrigger.TOUCH,
    )


def _build_fvg_entry_metadata(
    mode: PatternEntryMode,
    config: PatternEntryConfig,
    custom_price: float | None,
) -> dict[str, object]:
    return {
        "schema_version": "fvg_entry_mode_config_v1",
        "mode": mode.value,
        "max_wait_bars": config.max_wait_bars,
        "expire_status": config.expire_status.value,
        "entry_trigger": config.entry_trigger.value if hasattr(config.entry_trigger, "value") else str(config.entry_trigger),
        "custom_price": custom_price,
        "economic_interpretation": _fvg_entry_economic_interpretation(mode),
        "default_behavior_preserved": mode is PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        "scope": "backtest_research_only",
    }


def _build_fvg_direction_metadata(inverse_enabled: bool) -> dict[str, object]:
    return {
        "schema_version": "fvg_direction_mode_config_v1",
        "mode": "INVERSE_CONTRARIAN" if inverse_enabled else "NORMAL",
        "inverse_direction_enabled": bool(inverse_enabled),
        "scope": "backtest_research_only",
        "default_behavior_preserved": not inverse_enabled,
        "hypothesis": (
            "reverse FVG direction: bullish FVG enters short and bearish FVG enters long"
            if inverse_enabled
            else "normal FVG direction: bullish FVG enters long and bearish FVG enters short"
        ),
    }


def _build_fvg_v2_metadata(args: argparse.Namespace) -> dict[str, object]:
    enabled = bool(
        getattr(args, "enable_fvg_v2", False)
        or getattr(args, "fvg_use_trend_score", False)
        or getattr(args, "fvg_use_fibonacci_confluence", False)
        or getattr(args, "fvg_require_liquidity_target", False)
        or getattr(args, "enable_fvg_v2_channel", False)
        or getattr(args, "enable_fvg_close_volume_filter", False)
        or getattr(args, "fvg_require_order_block_confluence", False)
        or str(getattr(args, "fvg_stop_mode", "fvg_boundary_atr_buffer")).upper() != "FVG_BOUNDARY_ATR_BUFFER"
        or str(getattr(args, "fvg_entry_trigger", "touch")).upper() != "TOUCH"
    )
    return {
        "schema_version": "fvg_retest_v2_settings_v1",
        "enabled": enabled,
        "experimental_scope": "offline_research_only",
        "trend_score": {
            "enabled": bool(getattr(args, "fvg_use_trend_score", False)),
            "fast_period": int(getattr(args, "fvg_trend_fast_period", 9)),
            "slow_period": int(getattr(args, "fvg_trend_slow_period", 21)),
            "weights": {
                "1m": float(getattr(args, "fvg_trend_weight_1m", 0.20)),
                "5m": float(getattr(args, "fvg_trend_weight_5m", 0.30)),
                "15m": float(getattr(args, "fvg_trend_weight_15m", 0.50)),
            },
            "minimum_bullish_trend_score": float(getattr(args, "fvg_min_bullish_trend_score", 0.10)),
        },
        "fibonacci_confluence": {
            "enabled": bool(getattr(args, "fvg_use_fibonacci_confluence", False)),
        },
        "liquidity_targets": {
            "require_liquidity_target": bool(getattr(args, "fvg_require_liquidity_target", False)),
        },
        "stop_mode": str(getattr(args, "fvg_stop_mode", "fvg_boundary_atr_buffer")).upper(),
        "entry_trigger": str(getattr(args, "fvg_entry_trigger", "touch")).upper(),
        "direction": _build_fvg_direction_metadata(bool(getattr(args, "fvg_inverse_direction", False))),
        "parallel_channel": _build_fvg_channel_config(args).to_metadata(),
        "close_volume_entry_filter": _build_close_volume_entry_filter_config(args).to_metadata(),
        "order_block_confluence": _build_fvg_order_block_confluence_config(args).to_metadata(),
        "default_behavior_preserved": not enabled,
    }


def _build_fvg_order_block_confluence_config(args: argparse.Namespace) -> FvgOrderBlockConfluenceConfig:
    lookback = getattr(args, "fvg_order_block_confluence_lookback_bars", 100)
    if lookback is not None and int(lookback) < 1:
        raise ValueError("--fvg-order-block-confluence-lookback-bars must be at least 1")
    return FvgOrderBlockConfluenceConfig(
        enabled=bool(getattr(args, "fvg_require_order_block_confluence", False)),
        source=str(getattr(args, "fvg_order_block_confluence_source", "local_entry_candles")).upper(),
        local_break_mode=str(getattr(args, "fvg_local_order_block_break_mode", "break_previous_range")).upper(),
        lookback_bars=None if lookback is None else int(lookback),
        mode=str(getattr(args, "fvg_order_block_confluence_mode", "zone_overlap")).upper(),
        require_fresh=bool(getattr(args, "fvg_order_block_require_fresh", False)),
    )


def _build_close_volume_entry_filter_config(args: argparse.Namespace) -> CloseVolumeEntryFilterConfig:
    window = int(getattr(args, "fvg_close_volume_window", 20))
    if window < 1:
        raise ValueError("--fvg-close-volume-window must be at least 1")
    return CloseVolumeEntryFilterConfig(
        enabled=bool(getattr(args, "enable_fvg_close_volume_filter", False)),
        window=window,
        minimum_volume_ratio=float(getattr(args, "fvg_min_close_volume_ratio", 2.0)),
        low_volume_ratio_threshold=0.5,
        applies_to_side="ALL",
        baseline_mode=str(getattr(args, "fvg_close_volume_baseline_mode", "prior_only")).upper(),
        volume_input_mode=str(getattr(args, "fvg_close_volume_input_mode", "base_volume")).upper(),
        require_full_window=True,
        fail_closed_on_invalid=True,
    )


def _build_order_block_config(args: argparse.Namespace) -> OrderBlockConfig:
    config = OrderBlockConfig()
    updates: dict[str, object] = {}
    min_volume = getattr(args, "ob_min_volume_ratio", None)
    weak_volume = getattr(args, "ob_weak_volume_ratio", None)
    if min_volume is not None:
        updates["minimum_volume_ratio"] = float(min_volume)
    if weak_volume is not None:
        updates["weak_volume_ratio"] = float(weak_volume)
    if not updates:
        return config
    return replace(config, **updates)


def _order_block_config_metadata(config: OrderBlockConfig | None) -> dict[str, object]:
    resolved = config or OrderBlockConfig()
    return {
        "schema_version": "order_block_detector_config_v1",
        "minimum_volume_ratio": float(resolved.minimum_volume_ratio),
        "weak_volume_ratio": float(resolved.weak_volume_ratio),
        "default_entry_reference": str(resolved.default_entry_reference),
        "default_risk_reward": float(resolved.default_risk_reward),
        "stop_atr_buffer_multiplier": float(resolved.stop_atr_buffer_multiplier),
    }


def _build_order_block_entry_volume_filter_config(args: argparse.Namespace) -> OrderBlockEntryVolumeFilterConfig:
    window = int(getattr(args, "ob_entry_volume_window", 20))
    if window < 1:
        raise ValueError("--ob-entry-volume-window must be at least 1")
    return OrderBlockEntryVolumeFilterConfig(
        enabled=bool(getattr(args, "enable_ob_entry_volume_filter", False)),
        window=window,
        minimum_volume_ratio=float(getattr(args, "ob_min_entry_volume_ratio", 1.0)),
        baseline_mode="PRIOR_ONLY",
        volume_input_mode="BASE_VOLUME",
        require_full_window=True,
        fail_closed_on_invalid=True,
    )


def _build_order_block_mtf_filter_config(args: argparse.Namespace) -> OrderBlockMtfFilterConfig:
    raw_timeframes = str(getattr(args, "ob_mtf_timeframes", "15m,1h"))
    timeframes = tuple(value.strip() for value in raw_timeframes.split(",") if value.strip())
    return OrderBlockMtfFilterConfig(
        enabled=bool(getattr(args, "enable_ob_mtf_filter", False)),
        timeframes=timeframes or ("15m", "1h"),
        require_all_timeframes=True,
        fail_closed_on_missing=True,
        order_block_config=_build_order_block_config(args),
    )


def _build_order_block_risk_exit_config(args: argparse.Namespace) -> OrderBlockRiskExitConfig:
    return OrderBlockRiskExitConfig(
        mode=str(getattr(args, "ob_risk_exit_mode", "previous_candle_1r")).upper(),
        fallback_on_unsupported_entry_mode=True,
    )


def _build_liquidity_sweep_config(args: argparse.Namespace) -> LiquiditySweepReversalConfig:
    lookback = int(getattr(args, "lsr_liquidity_lookback_bars", 80))
    pool_age = int(getattr(args, "lsr_min_liquidity_pool_age_bars", 5))
    reclaim = int(getattr(args, "lsr_reclaim_max_bars", 2))
    displacement_wait = int(getattr(args, "lsr_displacement_max_bars_after_sweep", 3))
    entry_mode = str(getattr(args, "lsr_entry_mode", "best_net_rr_between_fvg_midpoint_and_ob_618")).upper()
    timeframes = tuple(
        value.strip()
        for value in str(getattr(args, "lsr_mtf_timeframes", "15m")).split(",")
        if value.strip()
    )
    return LiquiditySweepReversalConfig(
        liquidity_pool_lookback_bars=lookback,
        min_liquidity_pool_age_bars=pool_age,
        min_sweep_atr_multiplier=float(getattr(args, "lsr_min_sweep_atr_multiplier", 0.05)),
        min_sweep_bps=float(getattr(args, "lsr_min_sweep_bps", 2.0)),
        reclaim_max_bars=reclaim,
        displacement_max_bars_after_sweep=displacement_wait,
        minimum_displacement_body_ratio=float(getattr(args, "lsr_min_displacement_body_ratio", 0.55)),
        minimum_displacement_atr_multiplier=float(getattr(args, "lsr_min_displacement_atr_multiplier", 0.8)),
        minimum_volume_ratio=float(getattr(args, "lsr_min_volume_ratio", 1.5)),
        require_fvg_confluence=bool(getattr(args, "lsr_require_fvg_confluence", False)),
        require_order_block_confluence=bool(getattr(args, "lsr_require_order_block_confluence", False)),
        require_both_fvg_and_ob=bool(getattr(args, "lsr_require_both_fvg_and_ob", False)),
        entry_mode=entry_mode,
        target_r_multiple=float(getattr(args, "lsr_target_r_multiple", 2.0)),
        min_gross_rr=float(getattr(args, "lsr_min_gross_rr", 1.2)),
        min_net_rr=float(getattr(args, "lsr_min_net_rr", 1.0)),
        min_net_reward_bps=float(getattr(args, "lsr_min_net_reward_bps", 8.0)),
        enable_tradability_gates=bool(getattr(args, "lsr_enable_tradability_gates", False)),
        enable_mtf_confirmation=bool(getattr(args, "lsr_enable_mtf_confirmation", False)),
        mtf_timeframes=timeframes or ("15m",),
    )


def _build_liquidity_sweep_risk_exit_config(args: argparse.Namespace) -> LiquiditySweepReversalRiskExitConfig:
    return LiquiditySweepReversalRiskExitConfig(
        stop_buffer_atr_multiplier=0.10,
        target_r_multiple=float(getattr(args, "lsr_target_r_multiple", 2.0)),
        min_gross_rr=float(getattr(args, "lsr_min_gross_rr", 1.2)),
    )


def _build_session_range_liquidity_breakout_reversal_config(
    args: argparse.Namespace,
) -> SessionRangeLiquidityBreakoutReversalConfig:
    lookback = int(getattr(args, "srlbr_range_lookback_bars", 120))
    max_bars = int(getattr(args, "srlbr_max_bars_in_trade", 240))
    if lookback < 2:
        raise ValueError("--srlbr-range-lookback-bars must be at least 2")
    if max_bars < 1:
        raise ValueError("--srlbr-max-bars-in-trade must be at least 1")
    return SessionRangeLiquidityBreakoutReversalConfig(
        range_lookback_bars=lookback,
        breakout_buffer_bps=float(getattr(args, "srlbr_breakout_buffer_bps", 0.0)),
        minimum_range_bps=float(getattr(args, "srlbr_minimum_range_bps", 10.0)),
        minimum_volume_ratio=float(getattr(args, "srlbr_minimum_volume_ratio", 0.8)),
        minimum_body_ratio=float(getattr(args, "srlbr_minimum_body_ratio", 0.25)),
        signal_mode=str(getattr(args, "srlbr_signal_mode", "failed_breakout_reversal")).upper(),
        direction_mode=str(getattr(args, "srlbr_direction_mode", "both")).upper(),
        minimum_pattern_score=float(getattr(args, "srlbr_minimum_pattern_score", 0.40)),
        target_r_multiple=float(getattr(args, "srlbr_target_r_multiple", 4.0)),
        stop_atr_buffer_multiplier=float(getattr(args, "srlbr_stop_atr_buffer_multiplier", 0.20)),
        max_bars_in_trade=max_bars,
    )


def _build_fvg_channel_config(args: argparse.Namespace) -> FvgChannelConfig:
    window = int(getattr(args, "fvg_channel_window", 20))
    if window < 3:
        raise ValueError("--fvg-channel-window must be at least 3")
    max_wait = getattr(args, "fvg_channel_max_wait_bars", None)
    if max_wait is not None and int(max_wait) < 1:
        raise ValueError("--fvg-channel-max-wait-bars must be at least 1")
    return FvgChannelConfig(
        enabled=bool(getattr(args, "enable_fvg_v2_channel", False)),
        window=window,
        tolerance=float(getattr(args, "fvg_channel_tolerance", 1e-8)),
        max_wait_bars=None if max_wait is None else int(max_wait),
        allow_same_candle_exit=bool(getattr(args, "fvg_channel_allow_same_candle_exit", False)),
        standalone_scan_enabled=bool(getattr(args, "fvg_channel_standalone_scan", False)),
    )


def _fvg_entry_economic_interpretation(mode: PatternEntryMode) -> str:
    if mode in (PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, PatternEntryMode.MARKET_ON_NEXT_OPEN):
        return "chase_momentum_after_confirmation"
    if mode in (
        PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
        PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT,
        PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY,
        PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY,
        PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY,
        PatternEntryMode.LIMIT_AT_CUSTOM_PRICE,
    ):
        return "imbalance_retest_or_rebalancing_entry"
    if mode == PatternEntryMode.LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT:
        return "order_block_618_retracement_retest"
    return "unknown"


def _build_actions(
    candles: pd.DataFrame,
    strategy_key: str,
    entry_filter_config: PatternEntryFilterConfig | None = None,
    *,
    lookback_return_momentum_config: LookbackReturnMomentumConfig | None = None,
    fvg_entry_mode: PatternEntryMode | None = None,
    pattern_entry_mode: PatternEntryMode | None = None,
    fvg_entry_config: PatternEntryConfig | None = None,
    fvg_entry_custom_price: float | None = None,
    pattern_policy_metadata: dict[str, object] | None = None,
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
    fvg_channel_config: FvgChannelConfig | None = None,
    close_volume_entry_filter_config: CloseVolumeEntryFilterConfig | None = None,
    fvg_order_block_confluence_config: FvgOrderBlockConfluenceConfig | None = None,
    order_block_config: OrderBlockConfig | None = None,
    order_block_entry_volume_filter_config: OrderBlockEntryVolumeFilterConfig | None = None,
    order_block_mtf_filter_config: OrderBlockMtfFilterConfig | None = None,
    order_block_risk_exit_config: OrderBlockRiskExitConfig | None = None,
    liquidity_sweep_config: LiquiditySweepReversalConfig | None = None,
    liquidity_sweep_risk_exit_config: LiquiditySweepReversalRiskExitConfig | None = None,
    session_range_liquidity_breakout_reversal_config: SessionRangeLiquidityBreakoutReversalConfig | None = None,
    fvg_inverse_direction: bool = False,
):
    if _is_lookback_return_momentum_strategy(strategy_key):
        config = lookback_return_momentum_config or LookbackReturnMomentumConfig()
        cost_config = _build_lookback_return_momentum_cost_aware_config(cost_aware_entry_filter_config)
        strategy = LookbackReturnMomentumStrategy(config=config, cost_aware_config=cost_config)
        return strategy, build_lookback_return_momentum_actions(
            candles,
            config=config,
            cost_aware_config=cost_config,
        )

    strategy = strategy_for_pattern(strategy_key, entry_filter_config=entry_filter_config)
    if strategy.strategy_key == "ORDER_BLOCK" and order_block_config is not None:
        object.__setattr__(strategy, "detector_config", order_block_config)
    if strategy.strategy_key == "LIQUIDITY_SWEEP_REVERSAL":
        if liquidity_sweep_config is not None:
            object.__setattr__(strategy, "detector_config", liquidity_sweep_config)
        if liquidity_sweep_risk_exit_config is not None:
            object.__setattr__(strategy, "risk_config", liquidity_sweep_risk_exit_config)
    if strategy.strategy_key == "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL" and session_range_liquidity_breakout_reversal_config is not None:
        object.__setattr__(
            strategy,
            "detector_config",
            session_range_liquidity_breakout_reversal_config,
        )
    actions: list[StrategyAction] = []
    use_cached_context = hasattr(strategy, "detector_config") and hasattr(strategy, "evaluate_at")
    cache = (
        IndicatorCache.for_pattern(candles, strategy.detector_config)
        if use_cached_context
        else None
    )
    seen_event_ids = set()
    seen_fvg_channel_ids: set[str] = set()
    reported_fvg_channel_duplicate_ids: set[str] = set()

    for index in range(1, len(candles) + 1):
        raw_actions = (
            strategy.evaluate_at(
                PatternEvaluationContext(
                    candles=candles,
                    current_index=index - 1,
                    indicator_cache=cache,
                    seen_event_ids=seen_event_ids,
                )
            )
            if use_cached_context
            else strategy.evaluate(candles.iloc[:index])
        )
        expanded_actions = _expand_raw_actions(
            raw_actions,
            candles,
            index,
            pattern_entry_mode=pattern_entry_mode
            or (fvg_entry_mode if strategy.strategy_key == "FAIR_VALUE_GAP" else None)
            or _default_entry_mode_for_strategy(strategy.strategy_key),
            fvg_entry_config=fvg_entry_config,
            fvg_entry_custom_price=fvg_entry_custom_price,
            pattern_policy_metadata=pattern_policy_metadata,
            cost_aware_entry_filter_config=cost_aware_entry_filter_config,
            fvg_channel_config=fvg_channel_config if strategy.strategy_key == "FAIR_VALUE_GAP" else None,
            close_volume_entry_filter_config=close_volume_entry_filter_config if strategy.strategy_key == "FAIR_VALUE_GAP" else None,
            fvg_order_block_confluence_config=fvg_order_block_confluence_config if strategy.strategy_key == "FAIR_VALUE_GAP" else None,
            order_block_entry_volume_filter_config=(
                order_block_entry_volume_filter_config if strategy.strategy_key == "ORDER_BLOCK" else None
            ),
            order_block_mtf_filter_config=(
                order_block_mtf_filter_config if strategy.strategy_key == "ORDER_BLOCK" else None
            ),
            order_block_risk_exit_config=(
                order_block_risk_exit_config if strategy.strategy_key == "ORDER_BLOCK" else None
            ),
            seen_fvg_channel_ids=seen_fvg_channel_ids,
            fvg_inverse_direction=fvg_inverse_direction if strategy.strategy_key == "FAIR_VALUE_GAP" else False,
        )
        actions.extend(_dedupe_channel_duplicate_skips(expanded_actions, reported_fvg_channel_duplicate_ids))
        if (
            strategy.strategy_key == "FAIR_VALUE_GAP"
            and fvg_channel_config is not None
            and fvg_channel_config.enabled
            and fvg_channel_config.standalone_scan_enabled
        ):
            standalone_actions = _actions_with_policy_metadata(
                _build_standalone_fvg_channel_actions(
                    candles,
                    index,
                    fvg_channel_config,
                    seen_fvg_channel_ids,
                    cost_aware_entry_filter_config,
                    close_volume_entry_filter_config,
                    fvg_order_block_confluence_config,
                ),
                pattern_policy_metadata,
            )
            actions.extend(_dedupe_channel_duplicate_skips(standalone_actions, reported_fvg_channel_duplicate_ids))

    return strategy, actions


def _summarize_profiler(profiler: cProfile.Profile, limit: int = 10) -> list[dict[str, object]]:
    stats = pstats.Stats(profiler)
    entries: list[dict[str, object]] = []
    for (filename, line_no, func_name), (cc, nc, tt, ct, callers) in sorted(
        stats.stats.items(),
        key=lambda item: item[1][3],
        reverse=True,
    )[:limit]:
        entries.append(
            {
                "function": func_name,
                "file": filename,
                "line": line_no,
                "primitive_calls": cc,
                "total_calls": nc,
                "total_time_s": round(tt, 6),
                "cumulative_time_s": round(ct, 6),
            }
        )
    return entries


def _expand_raw_actions(
    raw_actions: Sequence[StrategyAction],
    candles: pd.DataFrame,
    index: int,
    *,
    pattern_entry_mode: PatternEntryMode | None = None,
    fvg_entry_config: PatternEntryConfig | None = None,
    fvg_entry_custom_price: float | None = None,
    pattern_policy_metadata: dict[str, object] | None = None,
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
    fvg_channel_config: FvgChannelConfig | None = None,
    close_volume_entry_filter_config: CloseVolumeEntryFilterConfig | None = None,
    fvg_order_block_confluence_config: FvgOrderBlockConfluenceConfig | None = None,
    order_block_entry_volume_filter_config: OrderBlockEntryVolumeFilterConfig | None = None,
    order_block_mtf_filter_config: OrderBlockMtfFilterConfig | None = None,
    order_block_risk_exit_config: OrderBlockRiskExitConfig | None = None,
    seen_fvg_channel_ids: set[str] | None = None,
    fvg_inverse_direction: bool = False,
) -> list[StrategyAction]:
    expanded: list[StrategyAction] = []
    for action in raw_actions:
        metadata = action.metadata or {}
        if _is_invalid_risk_skip(action):
            expanded.append(action)
            continue
        if action.action_type not in {
            StrategyActionType.ENTER_LONG,
            StrategyActionType.ENTER_SHORT,
        }:
            expanded.append(action)
            continue

        risk_plan = metadata.get("risk_plan")
        side = metadata.get("position_side")
        if risk_plan is None or side not in {"LONG", "SHORT"}:
            expanded.append(_risk_plan_invalid_skip(action, metadata))
            continue
        if getattr(risk_plan, "status", None) != RiskExitPlanStatus.VALID:
            expanded.append(_risk_plan_invalid_skip(action, metadata))
            continue

        original_side = str(side).upper()
        effective_side = _opposite_position_side(original_side) if fvg_inverse_direction else original_side
        effective_risk_plan = _inverse_fvg_risk_plan(risk_plan) if fvg_inverse_direction else risk_plan
        direction_metadata = _fvg_action_direction_metadata(
            inverse_enabled=fvg_inverse_direction,
            original_side=original_side,
            effective_side=effective_side,
        )
        event_metadata = {**metadata, **direction_metadata, "position_side": effective_side}
        event = type("PatternEventProxy", (), event_metadata)()
        if fvg_channel_config is not None and fvg_channel_config.enabled:
            if fvg_inverse_direction:
                expanded.append(
                    StrategyAction(
                        StrategyActionType.SKIP,
                        timestamp=action.timestamp,
                        quantity=0.0,
                        reason="FVG_INVERSE_DIRECTION_CHANNEL_UNSUPPORTED",
                        metadata={
                            **event_metadata,
                            "risk_plan": effective_risk_plan,
                            "risk_plan_status": _status_value(getattr(effective_risk_plan, "status", None)),
                            "risk_plan_reasons": tuple(getattr(effective_risk_plan, "reasons", ()) or ()),
                            "fvg_channel_mode_enabled": True,
                            "skip_reason": "inverse FVG direction is supported for baseline FVG action expansion only; channel boundary inversion requires a separate rule contract",
                        },
                    )
                )
                continue
            built_actions = build_fvg_channel_trade_actions(
                event,
                effective_risk_plan,
                candles.iloc[:index],
                candles.iloc[index:],
                entry_action_timestamp=action.timestamp,
                position_side=effective_side,
                entry_quantity=action.quantity,
                channel_config=fvg_channel_config,
                seen_channel_ids=seen_fvg_channel_ids,
                channel_candidate_source="fvg_event_expansion",
                cost_aware_entry_filter_config=cost_aware_entry_filter_config,
                close_volume_entry_filter_config=close_volume_entry_filter_config,
                fvg_order_block_confluence_config=fvg_order_block_confluence_config,
            )
            expanded.extend(_actions_with_policy_metadata(built_actions, pattern_policy_metadata))
            continue
        built_actions = build_pattern_trade_actions(
            event,
            effective_risk_plan,
            candles.iloc[index:],
            entry_action_timestamp=action.timestamp,
            confirmation_candle=candles.iloc[index - 1],
            position_side=effective_side,
            entry_quantity=action.quantity,
            soft_invalidation=soft_invalidation_for_event(event, effective_risk_plan),
            entry_mode=pattern_entry_mode or PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            entry_config=fvg_entry_config,
            entry_custom_price=fvg_entry_custom_price,
            cost_aware_entry_filter_config=cost_aware_entry_filter_config,
            fvg_order_block_confluence_config=fvg_order_block_confluence_config,
            order_block_entry_volume_filter_config=order_block_entry_volume_filter_config,
            order_block_mtf_filter_config=order_block_mtf_filter_config,
            order_block_risk_exit_config=order_block_risk_exit_config,
            context_candles=candles.iloc[:index],
        )
        expanded.extend(_actions_with_policy_metadata(built_actions, pattern_policy_metadata))
    return expanded


def _default_entry_mode_for_strategy(strategy_key: str) -> PatternEntryMode:
    try:
        return policy_for_pattern(strategy_key).default_entry_mode
    except ValueError:
        return PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE


def _fvg_action_direction_metadata(
    *,
    inverse_enabled: bool,
    original_side: str,
    effective_side: str,
) -> dict[str, object]:
    return {
        "fvg_direction_mode": "INVERSE_CONTRARIAN" if inverse_enabled else "NORMAL",
        "fvg_inverse_direction_enabled": bool(inverse_enabled),
        "original_position_side": original_side,
        "effective_position_side": effective_side,
        "direction_inversion_reason": (
            "owner_requested_research_mode_reverse_fvg_buy_sell_direction"
            if inverse_enabled
            else None
        ),
    }


def _opposite_position_side(side: str) -> str:
    normalized = str(side).upper()
    if normalized == "LONG":
        return "SHORT"
    if normalized == "SHORT":
        return "LONG"
    raise ValueError("position side must be LONG or SHORT")


def _inverse_fvg_risk_plan(risk_plan: RiskExitPlan) -> RiskExitPlan:
    try:
        original_direction = _coerce_risk_direction(risk_plan.direction)
    except ValueError:
        return _copy_inverse_risk_plan_invalid(
            risk_plan,
            direction=RiskExitDirection.SHORT,
            reasons=("direction must be LONG or SHORT for inverse FVG mode",),
        )
    inverse_direction = (
        RiskExitDirection.SHORT
        if original_direction == RiskExitDirection.LONG
        else RiskExitDirection.LONG
    )
    entry = _positive_number(risk_plan.entry_price)
    risk = _positive_number(risk_plan.risk_per_unit)
    if entry is None or risk is None:
        return _copy_inverse_risk_plan_invalid(
            risk_plan,
            direction=inverse_direction,
            reasons=("entry_price and risk_per_unit are required for inverse FVG mode",),
        )

    stop_price = entry + risk if inverse_direction == RiskExitDirection.SHORT else entry - risk
    if stop_price <= 0 or not isfinite(stop_price):
        return _copy_inverse_risk_plan_invalid(
            risk_plan,
            direction=inverse_direction,
            reasons=("inverse FVG stop_price must be finite and positive",),
        )

    r_multiples = _risk_target_multiples(risk_plan)
    targets = tuple(
        RiskExitTarget(
            name=f"TP{index}",
            price=entry - (risk * multiple) if inverse_direction == RiskExitDirection.SHORT else entry + (risk * multiple),
            source=RiskExitTargetSource.R_MULTIPLE,
            r_multiple=multiple,
            metadata={
                "rule": "inverse_fvg_r_multiple",
                "target_source": RiskExitTargetSource.R_MULTIPLE.value,
                "target_role": "inverse_fvg_r_multiple_target",
                "r_multiple": multiple,
            },
        )
        for index, multiple in enumerate(r_multiples, start=1)
    )
    target_semantics = target_semantics_metadata(
        direction=inverse_direction,
        entry_price=entry,
        risk_per_unit=risk,
        detector_target_reference=None,
        r_multiple_targets=targets,
        structural_targets=(),
        measured_targets=(),
        risk_targets=targets,
    )
    return RiskExitPlan(
        direction=inverse_direction,
        entry_price=entry,
        structural_stop=stop_price,
        atr=0.0,
        atr_buffer_multiplier=0.0,
        atr_buffer=0.0,
        stop_price=stop_price,
        risk_per_unit=risk,
        targets=targets,
        status=RiskExitPlanStatus.VALID,
        reasons=(),
        minimum_first_target_r=risk_plan.minimum_first_target_r,
        time_stop=risk_plan.time_stop,
        break_even=risk_plan.break_even,
        trailing_stop=risk_plan.trailing_stop,
        partial_exits=risk_plan.partial_exits,
        atr_metadata={
            **dict(risk_plan.atr_metadata or {}),
            "fvg_inverse_direction_enabled": True,
            "original_direction": original_direction.value,
            "effective_direction": inverse_direction.value,
            "inverse_stop_source": "symmetric_original_risk_per_unit",
        },
        target_semantics={
            **target_semantics,
            "direction_mode": "INVERSE_CONTRARIAN",
            "original_direction": original_direction.value,
            "effective_direction": inverse_direction.value,
        },
    )


def _copy_inverse_risk_plan_invalid(
    risk_plan: RiskExitPlan,
    *,
    direction: RiskExitDirection,
    reasons: tuple[str, ...],
) -> RiskExitPlan:
    return RiskExitPlan(
        direction=direction,
        entry_price=risk_plan.entry_price,
        structural_stop=None,
        atr=0.0,
        atr_buffer_multiplier=0.0,
        atr_buffer=0.0,
        stop_price=None,
        risk_per_unit=None,
        targets=(),
        status=RiskExitPlanStatus.INVALID,
        reasons=reasons,
        minimum_first_target_r=risk_plan.minimum_first_target_r,
        time_stop=risk_plan.time_stop,
        break_even=risk_plan.break_even,
        trailing_stop=risk_plan.trailing_stop,
        partial_exits=risk_plan.partial_exits,
        atr_metadata={
            **dict(risk_plan.atr_metadata or {}),
            "fvg_inverse_direction_enabled": True,
            "inverse_risk_plan_invalid": True,
        },
        target_semantics={},
    )


def _coerce_risk_direction(value: object) -> RiskExitDirection:
    if isinstance(value, RiskExitDirection):
        return value
    normalized = str(value.value if hasattr(value, "value") else value).upper()
    if normalized == RiskExitDirection.LONG.value:
        return RiskExitDirection.LONG
    if normalized == RiskExitDirection.SHORT.value:
        return RiskExitDirection.SHORT
    raise ValueError("direction must be LONG or SHORT")


def _positive_number(value: object) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if isfinite(parsed) and parsed > 0 else None


def _risk_target_multiples(risk_plan: RiskExitPlan) -> tuple[float, ...]:
    values = [
        float(target.r_multiple)
        for target in risk_plan.targets
        if target.r_multiple is not None and isfinite(float(target.r_multiple)) and float(target.r_multiple) > 0
    ]
    if not values:
        values = [1.0, 2.0, 3.0]
    return tuple(dict.fromkeys(values))


def _status_value(status: object) -> str | None:
    if status is None:
        return None
    return str(status.value if hasattr(status, "value") else status)


def _build_standalone_fvg_channel_actions(
    candles: pd.DataFrame,
    index: int,
    fvg_channel_config: FvgChannelConfig,
    seen_fvg_channel_ids: set[str],
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
    close_volume_entry_filter_config: CloseVolumeEntryFilterConfig | None = None,
    fvg_order_block_confluence_config: FvgOrderBlockConfluenceConfig | None = None,
) -> list[StrategyAction]:
    if index < 3:
        return []
    visible_candle = candles.iloc[index - 1]
    timestamp = visible_candle["timestamp"]
    event = type(
        "FvgChannelScanEventProxy",
        (),
        {
            "event_id": f"fvg-channel-scan-{index - 1}",
            "pattern_type": "FAIR_VALUE_GAP",
            "direction": "CHANNEL",
            "pattern_direction": "CHANNEL",
            "pattern_status": "VALID",
            "timestamp": timestamp,
            "pattern_score": None,
            "executable_pattern_score": None,
            "diagnostic_pattern_score": None,
            "risk_reward": None,
            "entry_reference": None,
            "stop_reference": None,
            "target_reference": None,
            "score_components": {},
            "score_component_sources": {},
            "score_limitations": (),
            "score_calibration": {},
            "channel_scan_source": "rolling_visible_prefix",
        },
    )()
    price = float(visible_candle["close"])
    risk_plan = RiskExitPlan(
        direction="LONG",
        entry_price=price,
        structural_stop=price,
        atr=0.0,
        atr_buffer_multiplier=0.0,
        atr_buffer=0.0,
        stop_price=price,
        risk_per_unit=0.0,
        targets=(),
        status=RiskExitPlanStatus.VALID,
        reasons=(),
    )
    actions = build_fvg_channel_trade_actions(
        event,
        risk_plan,
        candles.iloc[:index],
        candles.iloc[index:],
        entry_action_timestamp=timestamp,
        position_side="LONG",
        channel_config=fvg_channel_config,
        seen_channel_ids=seen_fvg_channel_ids,
        channel_candidate_source="standalone_visible_prefix_scan",
        cost_aware_entry_filter_config=cost_aware_entry_filter_config,
        close_volume_entry_filter_config=close_volume_entry_filter_config,
        fvg_order_block_confluence_config=fvg_order_block_confluence_config,
    )
    return [
        action
        for action in actions
        if action.reason != "FVG_CHANNEL_NOT_FOUND"
    ]


def _dedupe_channel_duplicate_skips(
    actions: Sequence[StrategyAction],
    reported_channel_ids: set[str],
) -> list[StrategyAction]:
    deduped: list[StrategyAction] = []
    for action in actions:
        if action.reason != "FVG_CHANNEL_DUPLICATE":
            deduped.append(action)
            continue
        metadata = action.metadata or {}
        channel_id = metadata.get("channel_id")
        if not isinstance(channel_id, str) or channel_id not in reported_channel_ids:
            deduped.append(action)
        if isinstance(channel_id, str):
            reported_channel_ids.add(channel_id)
    return deduped


def _actions_with_policy_metadata(
    actions: Sequence[StrategyAction],
    policy_metadata: dict[str, object] | None,
) -> list[StrategyAction]:
    if not policy_metadata:
        return list(actions)
    enriched: list[StrategyAction] = []
    for action in actions:
        metadata = dict(action.metadata or {})
        metadata["pattern_execution_policy"] = policy_metadata
        metadata["pattern_execution_policy_key"] = policy_metadata.get("policy_key")
        metadata["pattern_entry_policy_rationale"] = policy_metadata.get("economic_rationale")
        enriched.append(
            StrategyAction(
                action_type=action.action_type,
                timestamp=action.timestamp,
                quantity=action.quantity,
                reason=action.reason,
                metadata=metadata,
                requested_price=action.requested_price,
                quantity_mode=action.quantity_mode,
            )
        )
    return enriched


def _is_invalid_risk_skip(action: StrategyAction) -> bool:
    return action.action_type == StrategyActionType.SKIP and action.reason == "RISK_PLAN_INVALID"


def _risk_plan_invalid_skip(
    action: StrategyAction,
    metadata: dict[str, object],
) -> StrategyAction:
    return StrategyAction(
        StrategyActionType.SKIP,
        timestamp=action.timestamp,
        quantity=0.0,
        reason="RISK_PLAN_INVALID",
        metadata=metadata,
    )


def _empty_output(
    strategy_key: str,
    starting_cash: float,
    *,
    interval: str = DEFAULT_INTERVAL,
    risk_free_rate: float = 0.0,
    policy_metadata: dict[str, object] | None = None,
    strategy_type: str = "single_pattern",
) -> dict[str, object]:
    metadata = {
        "performance_metrics": calculate_performance_metrics(
            [],
            interval=interval,
            risk_free_rate=risk_free_rate,
        ).to_metadata()
    }
    if policy_metadata:
        metadata.update(policy_metadata)
    return {
        "strategy": {
            "name": (
                f"{strategy_key}_PATTERN_STRATEGY"
                if strategy_type == "single_pattern"
                else f"{strategy_key}_RESEARCH_STRATEGY"
            ),
            "strategy_type": strategy_type,
            "strategy_key": strategy_key,
            "pattern": strategy_key,
        },
        "portfolio": {
            "starting_cash": starting_cash,
            "ending_cash": starting_cash,
            "ending_position": 0.0,
            "final_equity": starting_cash,
            "total_return": 0.0,
        },
        "summary": {
            "trade_count": 0,
            "buy_count": 0,
            "sell_count": 0,
            "max_drawdown": 0.0,
            "metadata": metadata,
        },
        "executions": [],
        "events": [],
        "warnings": ["candle_count = 0"],
    }


def _iso_timestamp(value: object) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat().replace("+00:00", "Z")
    return str(value)


def _json_safe(value: object) -> object:
    return json_ready(value)


def _serialize_execution(execution) -> dict[str, object]:
    return {
        "timestamp": _iso_timestamp(execution.timestamp),
        "side": execution.side,
        "execution_side": execution.execution_side,
        "action_type": execution.action_type,
        "position_signal": execution.position_signal,
        "position_side": execution.position_side,
        "price": execution.price,
        "quantity": execution.quantity,
        "notional": execution.notional,
        "cash_after": execution.cash_after,
        "cash_balance_after": execution.cash_balance_after,
        "position_after": execution.position_after,
        "equity_after": execution.equity_after,
        "execution_equity_after": execution.execution_equity_after,
        "mark_to_market_equity_after": execution.mark_to_market_equity_after,
        "free_cash_after": execution.free_cash_after,
        "margin_used_after": execution.margin_used_after,
        "short_proceeds_locked_after": execution.short_proceeds_locked_after,
        "short_collateral_locked_after": execution.short_collateral_locked_after,
        "available_buying_power_after": execution.available_buying_power_after,
        "cash_after_semantics": execution.cash_after_semantics,
        "raw_price": execution.raw_price,
        "effective_price": execution.effective_price,
        "price_semantics": (execution.metadata or {}).get("price_semantics", "raw_fill_price"),
        "effective_price_semantics": (execution.metadata or {}).get(
            "effective_price_semantics",
            "spread_slippage_adjusted_diagnostic_price",
        ),
        "cost_breakdown": (execution.metadata or {}).get("cost_breakdown"),
        "fee_cost": execution.fee_cost,
        "spread_cost": execution.spread_cost,
        "slippage_cost": execution.slippage_cost,
        "total_cost": execution.total_cost,
        "reason": execution.reason,
        "pattern_event_id": execution.pattern_event_id,
        "exit_reason": execution.exit_reason,
        "gross_pnl": execution.gross_pnl,
        "net_pnl": execution.net_pnl,
        "realized_r_multiple": execution.realized_r_multiple,
        "metadata": _json_safe(execution.metadata or {}),
    }


def _serialize_events(executions: Sequence[object]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for execution in executions:
        pattern_event_id = getattr(execution, "pattern_event_id", None)
        if not pattern_event_id:
            continue
        event = {
            "pattern_event_id": pattern_event_id,
            "timestamp": _iso_timestamp(execution.timestamp),
            "action_type": execution.action_type,
            "position_signal": execution.position_signal,
            "position_side": execution.position_side,
            "execution_side": execution.execution_side,
            "reason": execution.reason,
            "exit_reason": execution.exit_reason,
        }
        metadata = getattr(execution, "metadata", {}) or {}
        for key in (
            "pattern_type",
            "pattern_direction",
            "pattern_status",
            "pattern_score",
            "score_components",
            "score_component_sources",
            "score_limitations",
            "score_calibration",
        ):
            if key in metadata:
                event[key] = metadata[key]
        events.append(event)
    return events


def _serialize_output(
    result,
    strategy_key: str,
    strategy_name: str,
    *,
    strategy_type: str = "single_pattern",
) -> dict[str, object]:
    events = _serialize_events(result.executions)
    diagnostics = {
        "pattern_event_count": len(events),
        "execution_count": len(result.executions),
        "event_ids": sorted({e["pattern_event_id"] for e in events}),
    }
    return {
        "strategy": {
            "name": strategy_name,
            "strategy_type": strategy_type,
            "strategy_key": strategy_key,
            "pattern": strategy_key,
        },
        "portfolio": {
            "starting_cash": result.summary.starting_cash,
            "ending_cash": result.summary.ending_cash,
            "ending_position": result.summary.ending_position,
            "final_equity": result.summary.final_equity,
            "total_return": result.summary.total_return,
            "account_state": _json_safe((result.summary.metadata or {}).get("account_state", {})),
        },
        "summary": {
            "trade_count": result.summary.trade_count,
            "buy_count": result.summary.buy_count,
            "sell_count": result.summary.sell_count,
            "max_drawdown": result.summary.max_drawdown,
            "metadata": _json_safe(result.summary.metadata or {}),
        },
        "executions": [_serialize_execution(execution) for execution in result.executions],
        "events": events,
        "diagnostics": diagnostics,
        "warnings": [],
    }


def _build_fvg_entry_mode_diagnostics(
    actions: Sequence[StrategyAction],
    result,
    mode: PatternEntryMode,
    *,
    pattern_key: str = "FAIR_VALUE_GAP",
) -> dict[str, object]:
    entry_actions = [
        action
        for action in actions
        if action.action_type in (StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT)
        and (action.metadata or {}).get("entry_mode")
    ]
    missed_actions = [
        action
        for action in actions
        if action.action_type == StrategyActionType.SKIP
        and getattr(action, "reason", None) == "ENTRY_NOT_FILLED"
    ]
    evaluated_count = len(entry_actions) + len(missed_actions)
    bars_waited_values = [
        float((action.metadata or {}).get("bars_waited"))
        for action in [*entry_actions, *missed_actions]
        if isinstance((action.metadata or {}).get("bars_waited"), (int, float))
    ]
    entry_reference_distances = _numeric_metadata_values([*entry_actions, *missed_actions], "entry_reference_distance")
    zone_mid_distances = _numeric_zone_distances([*entry_actions, *missed_actions], "from_zone_mid")
    trade_metrics = ((result.summary.metadata or {}).get("trade_attribution") or {}).get("trade_metrics", {})
    timing_aggregate = ((result.summary.metadata or {}).get("timing_diagnostics") or {}).get("aggregate", {})
    return {
        "schema_version": "fvg_entry_mode_diagnostics_v1",
        "pattern_key": pattern_key,
        "selected_entry_mode": mode.value,
        "economic_interpretation": _fvg_entry_economic_interpretation(mode),
        "entry_mode_hypothesis": _entry_mode_hypothesis(pattern_key, mode),
        "entry_style": "CHASE_OR_MOMENTUM" if mode in (PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, PatternEntryMode.MARKET_ON_NEXT_OPEN) else "RETEST_LIMIT",
        "candidate_event_count": evaluated_count,
        "filled_entry_count": len(entry_actions),
        "missed_trade_count": len(missed_actions),
        "fill_rate": None if evaluated_count == 0 else len(entry_actions) / evaluated_count,
        "trade_count": result.summary.trade_count,
        "completed_trade_count": trade_metrics.get("completed_trade_count"),
        "hit_rate": trade_metrics.get("hit_ratio"),
        "average_r": trade_metrics.get("average_r"),
        "expectancy": trade_metrics.get("expectancy"),
        "average_mfe_r": timing_aggregate.get("average_mfe_r"),
        "average_mae_r": timing_aggregate.get("average_mae_r"),
        "average_bars_waited": None if not bars_waited_values else sum(bars_waited_values) / len(bars_waited_values),
        "average_entry_reference_distance": _average(entry_reference_distances),
        "average_zone_mid_distance": _average(zone_mid_distances),
        "entry_not_filled_reasons": sorted({str((action.metadata or {}).get("reason")) for action in missed_actions if (action.metadata or {}).get("reason")}),
    }


def _build_lookback_return_momentum_diagnostics(
    actions: Sequence[StrategyAction],
    result,
    config: LookbackReturnMomentumConfig,
) -> dict[str, object]:
    entry_actions = [
        action
        for action in actions
        if action.action_type in (StrategyActionType.ENTER_LONG, StrategyActionType.ENTER_SHORT)
    ]
    exit_actions = [
        action
        for action in actions
        if action.action_type in (StrategyActionType.EXIT_LONG, StrategyActionType.EXIT_SHORT)
    ]
    cost_aware_blocked_actions = [
        action
        for action in actions
        if action.action_type == StrategyActionType.SKIP
        and (((action.metadata or {}).get("cost_aware_entry_filter") or {}).get("blocked") is True)
    ]
    invalid_atr_blocked_actions = [
        action
        for action in actions
        if action.action_type == StrategyActionType.SKIP
        and (action.reason == "INVALID_ATR_RISK_DISTANCE" or (action.metadata or {}).get("skip_reason") == "INVALID_ATR_RISK_DISTANCE")
    ]
    atr_too_small_blocked_actions = [
        action
        for action in actions
        if action.action_type == StrategyActionType.SKIP
        and (action.reason == "ATR_TOO_SMALL_FOR_COST" or (action.metadata or {}).get("skip_reason") == "ATR_TOO_SMALL_FOR_COST")
    ]
    exit_reasons = [
        str((action.metadata or {}).get("exit_reason"))
        for action in exit_actions
        if (action.metadata or {}).get("exit_reason")
    ]
    cost_aware_block_reasons = [
        str(((action.metadata or {}).get("cost_aware_entry_filter") or {}).get("block_reason") or action.reason)
        for action in cost_aware_blocked_actions
        if (((action.metadata or {}).get("cost_aware_entry_filter") or {}).get("block_reason") or action.reason)
    ]
    attempted_entry_count = (
        len(entry_actions)
        + len(cost_aware_blocked_actions)
        + len(invalid_atr_blocked_actions)
        + len(atr_too_small_blocked_actions)
    )
    return {
        "schema_version": "lookback_return_momentum_diagnostics_v1",
        "strategy_key": LOOKBACK_RETURN_MOMENTUM_KEY,
        "config": config.to_metadata(),
        "candidate_entry_count": attempted_entry_count,
        "accepted_entry_count": len(entry_actions),
        "cost_aware_blocked_entry_count": len(cost_aware_blocked_actions),
        "invalid_atr_blocked_entry_count": len(invalid_atr_blocked_actions),
        "atr_too_small_blocked_entry_count": len(atr_too_small_blocked_actions),
        "cost_aware_block_rate": (
            None
            if attempted_entry_count == 0
            else len(cost_aware_blocked_actions) / attempted_entry_count
        ),
        "cost_aware_block_reasons": sorted(set(cost_aware_block_reasons)),
        "exit_count": len(exit_actions),
        "exit_reasons": sorted(set(exit_reasons)),
        "long_entry_count": sum(1 for action in entry_actions if action.action_type == StrategyActionType.ENTER_LONG),
        "short_entry_count": sum(1 for action in entry_actions if action.action_type == StrategyActionType.ENTER_SHORT),
        "blocked_long_entry_count": sum(1 for action in cost_aware_blocked_actions if (action.metadata or {}).get("signal_side") == "LONG"),
        "blocked_short_entry_count": sum(1 for action in cost_aware_blocked_actions if (action.metadata or {}).get("signal_side") == "SHORT"),
        "invalid_atr_long_entry_count": sum(1 for action in invalid_atr_blocked_actions if (action.metadata or {}).get("signal_side") == "LONG"),
        "invalid_atr_short_entry_count": sum(1 for action in invalid_atr_blocked_actions if (action.metadata or {}).get("signal_side") == "SHORT"),
        "atr_too_small_long_entry_count": sum(1 for action in atr_too_small_blocked_actions if (action.metadata or {}).get("signal_side") == "LONG"),
        "atr_too_small_short_entry_count": sum(1 for action in atr_too_small_blocked_actions if (action.metadata or {}).get("signal_side") == "SHORT"),
        "trade_count": result.summary.trade_count,
        "completed_trade_count": (
            ((result.summary.metadata or {}).get("trade_attribution") or {})
            .get("trade_metrics", {})
            .get("completed_trade_count")
        ),
        "average_net_r": result.summary.average_net_r,
        "scope": "offline_backtest_research_only",
    }


def _build_fvg_entry_mode_comparison(
    candles: pd.DataFrame,
    strategy_key: str,
    entry_filter_config: PatternEntryFilterConfig,
    entry_config: PatternEntryConfig,
    custom_price: float | None,
    engine_config: StrategyEngineConfig,
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
    fvg_order_block_confluence_config: FvgOrderBlockConfluenceConfig | None = None,
) -> dict[str, object]:
    if strategy_key != "FAIR_VALUE_GAP":
        return {
            "schema_version": "fvg_entry_mode_comparison_v1",
            "skipped_reason": "comparison is only defined for FAIR_VALUE_GAP",
            "modes": {},
        }

    modes: dict[str, object] = {}
    for mode in (
        PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        PatternEntryMode.MARKET_ON_NEXT_OPEN,
        PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
        PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT,
        PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY,
        PatternEntryMode.LIMIT_AT_PATTERN_NEAR_BOUNDARY,
        PatternEntryMode.LIMIT_AT_PATTERN_FAR_BOUNDARY,
        PatternEntryMode.LIMIT_AT_CUSTOM_PRICE,
    ):
        _, actions = _build_actions(
            candles,
            strategy_key,
            entry_filter_config,
            fvg_entry_mode=mode,
            fvg_entry_config=entry_config,
            fvg_entry_custom_price=custom_price if mode is PatternEntryMode.LIMIT_AT_CUSTOM_PRICE else None,
            cost_aware_entry_filter_config=cost_aware_entry_filter_config,
            fvg_order_block_confluence_config=fvg_order_block_confluence_config,
        )
        result = run_strategy_backtest_engine(candles, actions, config=engine_config)
        modes[mode.value] = _build_fvg_entry_mode_diagnostics(actions, result, mode, pattern_key=strategy_key)
    return {
        "schema_version": "fvg_entry_mode_comparison_v1",
        "comparison_scope": "read_only_backtest_research",
        "modes": modes,
    }


def _build_pattern_entry_mode_comparison(
    candles: pd.DataFrame,
    strategy_key: str,
    entry_filter_config: PatternEntryFilterConfig,
    entry_config: PatternEntryConfig,
    custom_price: float | None,
    engine_config: StrategyEngineConfig,
    cost_aware_entry_filter_config: CostAwareEntryFilterConfig | None = None,
    fvg_order_block_confluence_config: FvgOrderBlockConfluenceConfig | None = None,
    order_block_config: OrderBlockConfig | None = None,
    order_block_entry_volume_filter_config: OrderBlockEntryVolumeFilterConfig | None = None,
    order_block_mtf_filter_config: OrderBlockMtfFilterConfig | None = None,
    order_block_risk_exit_config: OrderBlockRiskExitConfig | None = None,
) -> dict[str, object]:
    policy = policy_for_pattern(strategy_key)
    modes: dict[str, object] = {}
    for mode in policy.allowed_entry_modes:
        _, actions = _build_actions(
            candles,
            strategy_key,
            entry_filter_config,
            pattern_entry_mode=mode,
            fvg_entry_config=entry_config,
            fvg_entry_custom_price=custom_price if mode is PatternEntryMode.LIMIT_AT_CUSTOM_PRICE else None,
            pattern_policy_metadata=policy.to_metadata(selected_entry_mode=mode),
            cost_aware_entry_filter_config=cost_aware_entry_filter_config,
            fvg_order_block_confluence_config=(
                fvg_order_block_confluence_config if strategy_key == "FAIR_VALUE_GAP" else None
            ),
            order_block_config=order_block_config if strategy_key == "ORDER_BLOCK" else None,
            order_block_entry_volume_filter_config=(
                order_block_entry_volume_filter_config if strategy_key == "ORDER_BLOCK" else None
            ),
            order_block_mtf_filter_config=order_block_mtf_filter_config if strategy_key == "ORDER_BLOCK" else None,
            order_block_risk_exit_config=(
                order_block_risk_exit_config if strategy_key == "ORDER_BLOCK" else None
            ),
        )
        result = run_strategy_backtest_engine(candles, actions, config=engine_config)
        modes[mode.value] = _build_fvg_entry_mode_diagnostics(actions, result, mode, pattern_key=strategy_key)
    return {
        "schema_version": "pattern_entry_mode_comparison_v1",
        "comparison_scope": "read_only_backtest_research",
        "pattern_key": strategy_key,
        "modes": modes,
    }


def _numeric_metadata_values(actions: Sequence[StrategyAction], key: str) -> list[float]:
    values: list[float] = []
    for action in actions:
        policy = (action.metadata or {}).get("pattern_entry_policy") or {}
        value = policy.get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def _numeric_zone_distances(actions: Sequence[StrategyAction], key: str) -> list[float]:
    values: list[float] = []
    for action in actions:
        policy = (action.metadata or {}).get("pattern_entry_policy") or {}
        zone_distance = policy.get("zone_distance") or {}
        value = zone_distance.get(key) if isinstance(zone_distance, dict) else None
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def _average(values: Sequence[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _entry_mode_hypothesis(pattern_key: str, mode: PatternEntryMode) -> str:
    try:
        return policy_for_pattern(pattern_key).mode_hypotheses.get(mode, "unspecified")
    except ValueError:
        return "unspecified"


def run(
    argv: Sequence[str] | None = None,
    *,
    prog: str = "quant-bitcoin-strategy-backtest",
    include_strategy: bool = True,
) -> int:
    args = build_parser(prog, include_strategy).parse_args(argv)
    strategy_key = _select_strategy_key(args)
    is_lookback_return_momentum = _is_lookback_return_momentum_strategy(strategy_key)
    lookback_return_momentum_config = (
        _build_lookback_return_momentum_config(args)
        if is_lookback_return_momentum
        else None
    )
    cash_denomination_metadata = _build_cash_denomination_metadata(args)
    effective_starting_cash = float(cash_denomination_metadata["effective_quote_starting_cash"])
    args.effective_starting_cash = effective_starting_cash
    args.cash_denomination_metadata = cash_denomination_metadata
    if getattr(args, "fvg_inverse_direction", False) and strategy_key != "FAIR_VALUE_GAP":
        raise ValueError("--fvg-inverse-direction is only supported with --pattern FAIR_VALUE_GAP")
    pattern_entry_mode = (
        PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE
        if is_lookback_return_momentum
        else _selected_pattern_entry_mode(args, strategy_key)
    )
    pattern_entry_custom_price = _selected_entry_custom_price(args)
    fvg_entry_config = (
        _selected_liquidity_sweep_entry_config(args)
        if strategy_key == "LIQUIDITY_SWEEP_REVERSAL"
        else _selected_fvg_entry_config(args)
    )
    fvg_channel_config = _build_fvg_channel_config(args)
    close_volume_entry_filter_config = _build_close_volume_entry_filter_config(args)
    fvg_order_block_confluence_config = _build_fvg_order_block_confluence_config(args)
    order_block_config = _build_order_block_config(args)
    order_block_entry_volume_filter_config = _build_order_block_entry_volume_filter_config(args)
    order_block_mtf_filter_config = _build_order_block_mtf_filter_config(args)
    order_block_risk_exit_config = _build_order_block_risk_exit_config(args)
    liquidity_sweep_config = _build_liquidity_sweep_config(args)
    liquidity_sweep_risk_exit_config = _build_liquidity_sweep_risk_exit_config(args)
    session_range_liquidity_breakout_reversal_config = (
        _build_session_range_liquidity_breakout_reversal_config(args)
    )
    fvg_entry_metadata = _build_fvg_entry_metadata(
        pattern_entry_mode,
        fvg_entry_config,
        pattern_entry_custom_price,
    )
    fvg_direction_metadata = _build_fvg_direction_metadata(bool(args.fvg_inverse_direction))
    fvg_v2_metadata = _build_fvg_v2_metadata(args)
    pattern_execution_policy = (
        {
            "schema_version": "pattern_execution_policy_v1",
            "enabled": False,
            "skipped_reason": "not_a_pattern_strategy",
            "strategy_key": strategy_key,
            "scope": "offline_backtest_research_only",
        }
        if is_lookback_return_momentum
        else validate_pattern_entry_mode(strategy_key, pattern_entry_mode).to_metadata(
            selected_entry_mode=pattern_entry_mode
        )
    )
    transaction_cost_config, default_liquidity_role = _build_transaction_cost_config(args)
    cost_aware_entry_filter_config = _build_cost_aware_entry_filter_config(
        args,
        transaction_cost_config,
        default_liquidity_role,
    )
    if strategy_key == "LIQUIDITY_SWEEP_REVERSAL" and not args.enable_cost_aware_entry_filter:
        cost_aware_entry_filter_config = replace(
            cost_aware_entry_filter_config,
            enabled=True,
            min_net_reward_bps=float(getattr(args, "lsr_min_net_reward_bps", 8.0)),
            min_net_rr=float(getattr(args, "lsr_min_net_rr", 1.0)),
        )
    position_sizing = _build_position_sizing_config(args)
    short_exposure_mode, simulated_margin = _build_simulated_margin_config(args)
    guardrails = _build_guardrail_config(args)
    workflow_settings = _workflow_settings_metadata(args, guardrails)
    research_metadata = _build_research_metadata(args)
    policy_metadata = {
        "position_sizing": position_sizing.to_metadata(),
        "workflow_settings": workflow_settings,
        "short_exposure_policy": {
            "mode": short_exposure_mode.value,
            "default_policy": "short exposure is bounded by cash unless explicit simulated-margin mode is enabled",
        },
        "simulated_margin": simulated_margin.to_metadata(),
    }
    start_total = time.perf_counter()
    timings: dict[str, float] = {}
    pattern_profile: dict[str, object] = {
        "pattern_key": strategy_key,
        "candle_count": 0,
        "events_detected": 0,
        "actions_emitted": 0,
        "elapsed_ms": 0.0,
    }
    profiler = cProfile.Profile() if args.profile else None

    start_load = time.perf_counter()
    provider = PostgresCandleDataProvider.from_database_url(
        args.database_url,
        source=args.source,
        symbol=args.symbol,
        interval=args.interval,
        start_time=args.start_time,
        end_time=args.end_time,
        enforce_continuity=args.enforce_candle_continuity,
    )
    candles = provider.load()
    timings["load_candles_ms"] = _ms(start_load, time.perf_counter())
    if candles.empty:
        output = _empty_output(
            strategy_key,
            effective_starting_cash,
            interval=args.interval,
            risk_free_rate=args.risk_free_rate,
            policy_metadata=policy_metadata,
            strategy_type=(
                "lookback_return_momentum"
                if is_lookback_return_momentum
                else "single_pattern"
            ),
        )
        if lookback_return_momentum_config is not None:
            output["summary"]["metadata"]["lookback_return_momentum"] = (
                lookback_return_momentum_config.to_metadata()
            )
        output["cash_denomination"] = cash_denomination_metadata
        output["summary"]["metadata"]["cash_denomination"] = cash_denomination_metadata
        output["summary"]["metadata"]["order_block"] = _order_block_config_metadata(order_block_config)
        output["summary"]["metadata"]["order_block_entry_volume_filter"] = (
            order_block_entry_volume_filter_config.to_metadata()
        )
        output["summary"]["metadata"]["order_block_mtf_filter"] = order_block_mtf_filter_config.to_metadata()
        output["summary"]["metadata"]["order_block_risk_exit"] = order_block_risk_exit_config.to_metadata()
        output["summary"]["metadata"]["liquidity_sweep_reversal"] = _build_liquidity_sweep_config(args).to_metadata()
        output["summary"]["metadata"]["liquidity_sweep_reversal_risk_exit"] = (
            _build_liquidity_sweep_risk_exit_config(args).to_metadata()
        )
        output["summary"]["metadata"]["session_range_liquidity_breakout_reversal"] = (
            session_range_liquidity_breakout_reversal_config.to_metadata()
        )
        if cash_denomination_metadata.get("assumption_warning"):
            output["warnings"].append("starting_cash_currency_assumed_quote_currency")
        print(
            json.dumps(
                _json_safe(
                    output
                )
            )
        )
        return 0
    pattern_profile["candle_count"] = int(len(candles))

    start_build = time.perf_counter()
    if profiler is not None:
        profiler.enable()
    entry_filter_config = _build_pattern_entry_filter_config(args)
    pattern_regime_thresholds = _build_pattern_regime_threshold_config(args)
    strategy, actions = _build_actions(
        candles,
        strategy_key,
        entry_filter_config,
        lookback_return_momentum_config=lookback_return_momentum_config,
        pattern_entry_mode=pattern_entry_mode,
        fvg_entry_config=fvg_entry_config,
        fvg_entry_custom_price=pattern_entry_custom_price,
        pattern_policy_metadata=pattern_execution_policy,
        cost_aware_entry_filter_config=cost_aware_entry_filter_config,
        fvg_channel_config=fvg_channel_config,
        close_volume_entry_filter_config=close_volume_entry_filter_config,
        fvg_order_block_confluence_config=fvg_order_block_confluence_config,
        order_block_config=order_block_config,
        order_block_entry_volume_filter_config=order_block_entry_volume_filter_config,
        order_block_mtf_filter_config=order_block_mtf_filter_config,
        order_block_risk_exit_config=order_block_risk_exit_config,
        liquidity_sweep_config=liquidity_sweep_config if strategy_key == "LIQUIDITY_SWEEP_REVERSAL" else None,
        liquidity_sweep_risk_exit_config=(
            liquidity_sweep_risk_exit_config if strategy_key == "LIQUIDITY_SWEEP_REVERSAL" else None
        ),
        session_range_liquidity_breakout_reversal_config=(
            session_range_liquidity_breakout_reversal_config
            if strategy_key == "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL"
            else None
        ),
        fvg_inverse_direction=bool(args.fvg_inverse_direction),
    )
    if profiler is not None:
        profiler.disable()
    timings["build_actions_ms"] = _ms(start_build, time.perf_counter())
    pattern_profile["actions_emitted"] = len(actions)
    pattern_profile["events_detected"] = sum(1 for a in actions if getattr(a, "metadata", None) and a.metadata.get("event_id"))
    strategy_version = getattr(strategy, "strategy_version", "strategy_engine_v1")
    strategy_parameters = _build_strategy_parameters(
        strategy_key=strategy.strategy_key,
        entry_filter_config=entry_filter_config,
        transaction_cost_config=transaction_cost_config,
        default_liquidity_role=default_liquidity_role,
        position_sizing=position_sizing,
        policy_metadata=policy_metadata,
        simulated_margin=simulated_margin,
        risk_free_rate=args.risk_free_rate,
        fvg_entry_metadata=fvg_entry_metadata,
        fvg_direction_metadata=fvg_direction_metadata,
        fvg_v2_metadata=fvg_v2_metadata,
        fvg_order_block_confluence_config=fvg_order_block_confluence_config,
        order_block_config=order_block_config,
        order_block_entry_volume_filter_config=order_block_entry_volume_filter_config,
        order_block_mtf_filter_config=order_block_mtf_filter_config,
        order_block_risk_exit_config=order_block_risk_exit_config,
        liquidity_sweep_config=liquidity_sweep_config if strategy.strategy_key == "LIQUIDITY_SWEEP_REVERSAL" else None,
        liquidity_sweep_risk_exit_config=(
            liquidity_sweep_risk_exit_config if strategy.strategy_key == "LIQUIDITY_SWEEP_REVERSAL" else None
        ),
        session_range_liquidity_breakout_reversal_config=(
            session_range_liquidity_breakout_reversal_config
            if strategy.strategy_key == "SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL"
            else None
        ),
        pattern_execution_policy=pattern_execution_policy,
        workflow_settings=workflow_settings,
        cost_profile_metadata=_cost_profile_metadata(args, transaction_cost_config),
        cost_aware_entry_filter_config=cost_aware_entry_filter_config,
        pattern_regime_thresholds=pattern_regime_thresholds,
        cash_denomination_metadata=cash_denomination_metadata,
        research_metadata=research_metadata,
        lookback_return_momentum_config=lookback_return_momentum_config,
    )
    reproducibility_metadata = _build_reproducibility_metadata(
        args=args,
        candles=candles,
        strategy_key=strategy.strategy_key,
        strategy_name=strategy.strategy_name,
        strategy_version=strategy_version,
        strategy_parameters=strategy_parameters,
        engine_name=BACKTEST_ENGINE_NAME,
        engine_version=BACKTEST_ENGINE_VERSION,
    )

    start_engine = time.perf_counter()
    engine_config = StrategyEngineConfig(
        starting_cash=effective_starting_cash,
        trade_quantity=args.trade_quantity,
        transaction_cost_config=transaction_cost_config,
        default_liquidity_role=default_liquidity_role,
        interval=args.interval,
        risk_free_rate=args.risk_free_rate,
        position_sizing=position_sizing,
        short_exposure_mode=short_exposure_mode,
        simulated_margin=simulated_margin,
        enforce_candle_continuity=args.enforce_candle_continuity,
        guardrails=guardrails,
        market_regime_by_timestamp=_market_regime_by_timestamp(candles, args),
        pattern_regime_thresholds=pattern_regime_thresholds,
        strict_zero_cost_1m_pattern_runs=args.strict_cost_mode,
        include_cost_sensitivity_report=args.cost_sensitivity_report,
    )
    result = run_strategy_backtest_engine(candles, actions, config=engine_config)
    timings["run_engine_ms"] = _ms(start_engine, time.perf_counter())
    if isinstance(result.summary.metadata, dict):
        result.summary.metadata["cash_denomination"] = cash_denomination_metadata
        result.summary.metadata["research"] = research_metadata

    persisted_run_id = None
    start_persist = time.perf_counter()
    if not args.no_persist:
        repository = PostgresBacktestResultRepository(args.database_url)
        runtime_metadata = _build_runtime_metadata(
            strategy_key=strategy.strategy_key,
            candle_count=len(candles),
            pattern_profile=pattern_profile,
            timings=timings,
        )
        if not is_lookback_return_momentum:
            build_pattern_strategy_explanation(strategy.strategy_key)
        payload = build_strategy_engine_persistence_payload(
            result,
            candles,
            source=args.source,
            symbol=args.symbol,
            interval=args.interval,
            start_time=args.start_time,
            end_time=args.end_time,
            strategy_key=strategy.strategy_key.lower(),
            strategy_name=strategy.strategy_name,
            strategy_version=strategy_version,
            strategy_parameters=strategy_parameters,
            starting_cash=effective_starting_cash,
            trade_quantity=args.trade_quantity,
            engine_name=BACKTEST_ENGINE_NAME,
            engine_version=BACKTEST_ENGINE_VERSION,
            run_metadata=runtime_metadata
            | {
                "cash_denomination": cash_denomination_metadata,
                "cost_aware_entry_filter": _cost_aware_entry_filter_metadata(cost_aware_entry_filter_config),
                "cost_profile": _cost_profile_metadata(args, transaction_cost_config),
                "lookback_return_momentum": (
                    lookback_return_momentum_config.to_metadata()
                    if lookback_return_momentum_config is not None
                    else {
                        "schema_version": "lookback_return_momentum_config_v1",
                        "enabled": False,
                    }
                ),
                "reproducibility": reproducibility_metadata,
                "research": research_metadata,
                "workflow_settings": workflow_settings,
            },
        )
        persisted_run_id = repository.save_completed_backtest(payload)
    timings["persist_ms"] = _ms(start_persist, time.perf_counter())

    start_json = time.perf_counter()
    output = _serialize_output(
        result,
        strategy.strategy_key,
        strategy.strategy_name,
        strategy_type=(
            "lookback_return_momentum"
            if is_lookback_return_momentum
            else "single_pattern"
        ),
    )
    output["reproducibility"] = reproducibility_metadata
    output["cash_denomination"] = cash_denomination_metadata
    output["diagnostics"]["pattern_execution_policy"] = pattern_execution_policy
    output["summary"]["metadata"]["pattern_execution_policy"] = pattern_execution_policy
    output["summary"]["metadata"]["workflow_settings"] = workflow_settings
    output["summary"]["metadata"]["cash_denomination"] = cash_denomination_metadata
    output["summary"]["metadata"]["research"] = research_metadata
    output["summary"]["metadata"]["cost_profile"] = _cost_profile_metadata(args, transaction_cost_config, result)
    output["summary"]["metadata"]["cost_aware_entry_filter"] = _cost_aware_entry_filter_metadata(cost_aware_entry_filter_config)
    output["summary"]["metadata"]["fvg_order_block_confluence"] = _fvg_order_block_confluence_metadata(
        fvg_order_block_confluence_config
    )
    output["summary"]["metadata"]["order_block"] = _order_block_config_metadata(order_block_config)
    output["summary"]["metadata"]["order_block_entry_volume_filter"] = (
        order_block_entry_volume_filter_config.to_metadata()
    )
    output["summary"]["metadata"]["order_block_mtf_filter"] = order_block_mtf_filter_config.to_metadata()
    output["summary"]["metadata"]["order_block_risk_exit"] = order_block_risk_exit_config.to_metadata()
    output["summary"]["metadata"]["liquidity_sweep_reversal"] = liquidity_sweep_config.to_metadata()
    output["summary"]["metadata"]["liquidity_sweep_reversal_risk_exit"] = (
        liquidity_sweep_risk_exit_config.to_metadata()
    )
    output["summary"]["metadata"]["session_range_liquidity_breakout_reversal"] = (
        session_range_liquidity_breakout_reversal_config.to_metadata()
    )
    if lookback_return_momentum_config is not None:
        lrm_diagnostics = _build_lookback_return_momentum_diagnostics(
            actions,
            result,
            lookback_return_momentum_config,
        )
        output["diagnostics"]["lookback_return_momentum"] = lrm_diagnostics
        output["summary"]["metadata"]["lookback_return_momentum"] = (
            lookback_return_momentum_config.to_metadata()
        )
    else:
        retest_opportunity = build_fvg_ob_retest_opportunity_report(
            actions,
            candles,
            regime_by_timestamp=engine_config.market_regime_by_timestamp,
        )
        output["diagnostics"]["fvg_ob_retest_opportunity"] = retest_opportunity
        output["summary"]["metadata"]["fvg_ob_retest_opportunity"] = retest_opportunity
        trendline_forensics = build_trendline_false_breakout_forensics(actions, candles)
        output["diagnostics"]["trendline_false_breakout_forensics"] = trendline_forensics
        output["summary"]["metadata"]["trendline_false_breakout_forensics"] = trendline_forensics
        fvg_entry_diagnostics = _build_fvg_entry_mode_diagnostics(actions, result, pattern_entry_mode, pattern_key=strategy.strategy_key)
        output["diagnostics"]["fvg_entry_mode"] = fvg_entry_diagnostics
        output["diagnostics"]["fvg_retest_v2"] = {
            "schema_version": "fvg_retest_v2_diagnostics_v1",
            "settings": fvg_v2_metadata,
            "entry_trigger": fvg_v2_metadata["entry_trigger"],
            "stop_mode": fvg_v2_metadata["stop_mode"],
            "experimental_scope": "offline_research_only",
            "counts": {
                "filled_entry_count": fvg_entry_diagnostics.get("filled_entry_count"),
                "skipped_entry_count": fvg_entry_diagnostics.get("skipped_entry_count"),
            },
        }
        output["summary"]["metadata"]["fvg_entry_mode"] = fvg_entry_diagnostics
        output["summary"]["metadata"]["fvg_retest_v2"] = output["diagnostics"]["fvg_retest_v2"]
        output["diagnostics"]["pattern_entry_mode"] = fvg_entry_diagnostics
        output["summary"]["metadata"]["pattern_entry_mode"] = fvg_entry_diagnostics
        if args.compare_fvg_entry_modes:
            output["diagnostics"]["fvg_entry_mode_comparison"] = _build_fvg_entry_mode_comparison(
                candles,
                strategy.strategy_key,
                entry_filter_config,
                fvg_entry_config,
                pattern_entry_custom_price,
                engine_config,
                cost_aware_entry_filter_config,
                fvg_order_block_confluence_config,
            )
        if args.compare_pattern_entry_modes:
            output["diagnostics"]["pattern_entry_mode_comparison"] = _build_pattern_entry_mode_comparison(
                candles,
                strategy.strategy_key,
                entry_filter_config,
                fvg_entry_config,
                pattern_entry_custom_price,
                engine_config,
                cost_aware_entry_filter_config,
                fvg_order_block_confluence_config,
                order_block_config,
                order_block_entry_volume_filter_config,
                order_block_mtf_filter_config,
                order_block_risk_exit_config,
            )
    if persisted_run_id is not None:
        output["backtest_run_id"] = persisted_run_id
    if not actions:
        output["warnings"].append("no strategy events")
    elif not output["events"] and not is_lookback_return_momentum:
        output["warnings"].append("no pattern events in executions")
    if output["summary"]["trade_count"] == 0:
        output["warnings"].append("no fills")
    if any(getattr(action, "reason", None) == "RISK_PLAN_INVALID" for action in actions):
        output["warnings"].append("invalid risk plan")
    if output["portfolio"]["ending_position"] != 0:
        output["warnings"].append("open position remains at end of backtest")
    if output["summary"]["metadata"].get("cost_summary", {}).get("zero_transaction_cost_assumption"):
        output["warnings"].append("zero_transaction_cost_assumption")
    if output["summary"]["metadata"].get("short_performance", {}).get("short_close_count", 0) or output["portfolio"]["ending_position"] < 0:
        output["warnings"].append("short_economics_simulation_only")
    if not args.enforce_candle_continuity:
        output["warnings"].append("candle_continuity_not_enforced")
    if not args.enable_market_regime:
        output["warnings"].append("market_regime_disabled")
    if fvg_v2_metadata["enabled"] and not is_lookback_return_momentum:
        output["warnings"].append("fvg_retest_v2_experimental_scope")
    if cash_denomination_metadata.get("assumption_warning"):
        output["warnings"].append("starting_cash_currency_assumed_quote_currency")

    timings["json_output_ms"] = _ms(start_json, time.perf_counter())
    timings["total_elapsed_ms"] = _ms(start_total, time.perf_counter())
    pattern_profile["elapsed_ms"] = timings["build_actions_ms"]
    output["runtime"] = _build_runtime_metadata(
        strategy_key=strategy.strategy_key,
        candle_count=len(candles),
        pattern_profile=pattern_profile,
        timings=timings,
    )["runtime"]
    if args.profile:
        output["profiling"] = {
            **timings,
            "pattern_timings": [pattern_profile],
            "top_functions": _summarize_profiler(profiler) if profiler is not None else [],
        }

    print(json.dumps(_json_safe(output)))
    return 0
