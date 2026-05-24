from __future__ import annotations

import argparse
import cProfile
from datetime import datetime, timezone
import json
import os
import pstats
import time
from collections.abc import Sequence
from math import isfinite
from urllib.parse import urlsplit, urlunsplit

import pandas as pd

from quant_bitcoin.backtesting.json_metadata import json_ready, metadata_hash as json_metadata_hash
from quant_bitcoin.backtesting.pattern_action_builder import build_pattern_trade_actions
from quant_bitcoin.backtesting.costs import LiquidityRole, TransactionCostConfig
from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES, break_even_cost_bps, cost_profile, manual_cost_overrides_present
from quant_bitcoin.backtesting.performance_metrics import calculate_performance_metrics
from quant_bitcoin.backtesting.pattern_invalidation import soft_invalidation_for_event
from quant_bitcoin.backtesting.fvg_detection_cache import (
    IndicatorCache,
    PatternEvaluationContext,
)
from quant_bitcoin.patterns.entry_simulation import PatternEntryConfig, PatternEntryMode, PatternEntryStatus
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
from quant_bitcoin.indicators.market_regime import MarketRegimeConfig, calculate_market_regime
from quant_bitcoin.backtesting.strategy_persistence_adapter import (
    build_strategy_engine_persistence_payload,
)
from quant_bitcoin.market_data import PostgresCandleDataProvider
from quant_bitcoin.persistence import (
    BACKTEST_ENGINE_NAME,
    BACKTEST_ENGINE_VERSION,
    PostgresBacktestResultRepository,
)
from quant_bitcoin.risk.exit_plan import RiskExitPlanStatus
from quant_bitcoin.strategies.actions import StrategyAction, StrategyActionType
from quant_bitcoin.strategies.pattern_execution_policy import policy_for_pattern, validate_pattern_entry_mode
from quant_bitcoin.strategies.pattern_explanations import build_pattern_strategy_explanation
from quant_bitcoin.strategies.patterns import FairValueGapStrategy, OrderBlockStrategy, PatternEntryFilterConfig, strategy_for_pattern

DEFAULT_DATABASE_URL = "postgresql://quant_bitcoin:quant_bitcoin_dev@localhost:5432/quant_bitcoin"
DEFAULT_SOURCE = "binance_spot"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1m"
DEFAULT_STRATEGY = "FAIR_VALUE_GAP"


def build_parser(prog: str, include_strategy: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
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
    parser.add_argument("--fvg-entry-max-wait-bars", type=int, default=None)
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
    parser.add_argument("--start-time", type=_optional_timestamp, default=None)
    parser.add_argument("--end-time", type=_optional_timestamp, default=None)
    parser.add_argument("--starting-cash", type=float, default=10000.0)
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
    parser.add_argument("--liquidity-role", type=_liquidity_role, default=LiquidityRole.TAKER.value)
    parser.add_argument("--risk-free-rate", type=_finite_float, default=0.0)
    parser.add_argument("--enforce-candle-continuity", action="store_true")
    parser.add_argument("--enable-market-regime", action="store_true")
    parser.add_argument("--market-regime-window", type=int, default=20)
    parser.add_argument("--market-regime-min-trading-value", type=_non_negative_finite_float, default=1_000_000.0)
    parser.add_argument("--max-account-drawdown", type=_positive_finite_float, default=None)
    parser.add_argument("--max-consecutive-losses", type=int, default=None)
    parser.add_argument("--max-daily-loss", type=_positive_finite_float, default=None)
    parser.add_argument("--no-persist", action="store_true")
    parser.add_argument("--profile", action="store_true")
    return parser


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
    pattern_execution_policy: dict[str, object] | None = None,
    workflow_settings: dict[str, object] | None = None,
    cost_profile_metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "pattern": strategy_key,
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
        "cost_profile": cost_profile_metadata,
        "position_sizing": position_sizing.to_metadata(),
        "fvg_entry": fvg_entry_metadata or _build_fvg_entry_metadata(
            PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            PatternEntryConfig(),
            None,
        ),
        "pattern_execution_policy": pattern_execution_policy,
        "workflow_settings": workflow_settings,
        "short_exposure_policy": policy_metadata["short_exposure_policy"],
        "simulated_margin": simulated_margin.to_metadata(),
        "risk_free_rate": risk_free_rate,
    }


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
            "starting_cash": args.starting_cash,
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


def _liquidity_role(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in {LiquidityRole.MAKER.value, LiquidityRole.TAKER.value}:
        raise argparse.ArgumentTypeError("liquidity-role must be MAKER or TAKER")
    return normalized


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
    if not args.enable_market_regime:
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
    return {
        "schema_version": "canonical_cli_workflow_settings_v1",
        "enforce_candle_continuity": bool(args.enforce_candle_continuity),
        "market_regime_enabled": bool(args.enable_market_regime),
        "market_regime": {
            "enabled": bool(args.enable_market_regime),
            "window": args.market_regime_window,
            "minimum_average_trading_value": args.market_regime_min_trading_value,
        },
        "guardrails": guardrails.to_metadata(),
    }


def _select_strategy_key(args: argparse.Namespace) -> str:
    return (args.pattern or getattr(args, "strategy", None) or DEFAULT_STRATEGY).upper()


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
    )


def _selected_fvg_entry_mode(args: argparse.Namespace) -> PatternEntryMode:
    mode = PatternEntryMode(str(args.fvg_entry_mode).upper())
    custom_price = getattr(args, "fvg_entry_custom_price", None)
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
    else:
        mode = policy_for_pattern(strategy_key).default_entry_mode
    custom_price = getattr(args, "fvg_entry_custom_price", None)
    if mode is PatternEntryMode.LIMIT_AT_CUSTOM_PRICE and custom_price is None:
        raise ValueError("limit_at_custom_price requires --fvg-entry-custom-price")
    if mode is not PatternEntryMode.LIMIT_AT_CUSTOM_PRICE and custom_price is not None:
        raise ValueError("--fvg-entry-custom-price requires --pattern-entry-mode limit_at_custom_price")
    validate_pattern_entry_mode(strategy_key, mode)
    return mode


def _selected_fvg_entry_config(args: argparse.Namespace) -> PatternEntryConfig:
    expire_status = PatternEntryStatus(str(args.fvg_entry_expire_status).upper())
    return PatternEntryConfig(
        max_wait_bars=args.fvg_entry_max_wait_bars,
        expire_status=expire_status,
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
        "custom_price": custom_price,
        "economic_interpretation": _fvg_entry_economic_interpretation(mode),
        "default_behavior_preserved": mode is PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
        "scope": "backtest_research_only",
    }


def _fvg_entry_economic_interpretation(mode: PatternEntryMode) -> str:
    if mode in (PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE, PatternEntryMode.MARKET_ON_NEXT_OPEN):
        return "momentum_continuation_after_confirmation"
    if mode in (
        PatternEntryMode.LIMIT_AT_ENTRY_REFERENCE,
        PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT,
        PatternEntryMode.LIMIT_AT_PATTERN_BOUNDARY,
        PatternEntryMode.LIMIT_AT_CUSTOM_PRICE,
    ):
        return "imbalance_retest_or_rebalancing_entry"
    return "unknown"


def _build_actions(
    candles: pd.DataFrame,
    strategy_key: str,
    entry_filter_config: PatternEntryFilterConfig | None = None,
    *,
    fvg_entry_mode: PatternEntryMode | None = None,
    pattern_entry_mode: PatternEntryMode | None = None,
    fvg_entry_config: PatternEntryConfig | None = None,
    fvg_entry_custom_price: float | None = None,
    pattern_policy_metadata: dict[str, object] | None = None,
):
    strategy = strategy_for_pattern(strategy_key, entry_filter_config=entry_filter_config)
    actions: list[StrategyAction] = []
    cache = (
        IndicatorCache.for_pattern(candles, strategy.detector_config)
        if isinstance(strategy, (FairValueGapStrategy, OrderBlockStrategy))
        else None
    )
    seen_event_ids = set()

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
            if isinstance(strategy, (FairValueGapStrategy, OrderBlockStrategy))
            else strategy.evaluate(candles.iloc[:index])
        )
        actions.extend(
            _expand_raw_actions(
                raw_actions,
                candles,
                index,
                pattern_entry_mode=pattern_entry_mode or (fvg_entry_mode if strategy.strategy_key == "FAIR_VALUE_GAP" else None),
                fvg_entry_config=fvg_entry_config if strategy.strategy_key == "FAIR_VALUE_GAP" else None,
                fvg_entry_custom_price=fvg_entry_custom_price if strategy.strategy_key == "FAIR_VALUE_GAP" else None,
                pattern_policy_metadata=pattern_policy_metadata,
            )
        )

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

        event = type("PatternEventProxy", (), metadata)()
        built_actions = build_pattern_trade_actions(
            event,
            risk_plan,
            candles.iloc[index:],
            entry_action_timestamp=action.timestamp,
            confirmation_candle=candles.iloc[index - 1],
            position_side=side,
            entry_quantity=action.quantity,
            soft_invalidation=soft_invalidation_for_event(event, risk_plan),
            entry_mode=pattern_entry_mode or PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE,
            entry_config=fvg_entry_config,
            entry_custom_price=fvg_entry_custom_price,
        )
        expanded.extend(_actions_with_policy_metadata(built_actions, pattern_policy_metadata))
    return expanded


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
            "name": f"{strategy_key}_PATTERN_STRATEGY",
            "strategy_type": "single_pattern",
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


def _serialize_output(result, strategy_key: str, strategy_name: str) -> dict[str, object]:
    events = _serialize_events(result.executions)
    diagnostics = {
        "pattern_event_count": len(events),
        "execution_count": len(result.executions),
        "event_ids": sorted({e["pattern_event_id"] for e in events}),
    }
    return {
        "strategy": {
            "name": strategy_name,
            "strategy_type": "single_pattern",
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
    trade_metrics = ((result.summary.metadata or {}).get("trade_attribution") or {}).get("trade_metrics", {})
    timing_aggregate = ((result.summary.metadata or {}).get("timing_diagnostics") or {}).get("aggregate", {})
    return {
        "schema_version": "fvg_entry_mode_diagnostics_v1",
        "selected_entry_mode": mode.value,
        "economic_interpretation": _fvg_entry_economic_interpretation(mode),
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
        "entry_not_filled_reasons": sorted({str((action.metadata or {}).get("reason")) for action in missed_actions if (action.metadata or {}).get("reason")}),
    }


def _build_fvg_entry_mode_comparison(
    candles: pd.DataFrame,
    strategy_key: str,
    entry_filter_config: PatternEntryFilterConfig,
    entry_config: PatternEntryConfig,
    custom_price: float | None,
    engine_config: StrategyEngineConfig,
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
    ):
        _, actions = _build_actions(
            candles,
            strategy_key,
            entry_filter_config,
            fvg_entry_mode=mode,
            fvg_entry_config=entry_config,
            fvg_entry_custom_price=custom_price if mode is PatternEntryMode.LIMIT_AT_CUSTOM_PRICE else None,
        )
        result = run_strategy_backtest_engine(candles, actions, config=engine_config)
        modes[mode.value] = _build_fvg_entry_mode_diagnostics(actions, result, mode)
    return {
        "schema_version": "fvg_entry_mode_comparison_v1",
        "comparison_scope": "read_only_backtest_research",
        "modes": modes,
    }


def run(
    argv: Sequence[str] | None = None,
    *,
    prog: str = "quant-bitcoin-strategy-backtest",
    include_strategy: bool = True,
) -> int:
    args = build_parser(prog, include_strategy).parse_args(argv)
    strategy_key = _select_strategy_key(args)
    pattern_entry_mode = _selected_pattern_entry_mode(args, strategy_key)
    fvg_entry_config = _selected_fvg_entry_config(args)
    fvg_entry_metadata = _build_fvg_entry_metadata(
        pattern_entry_mode,
        fvg_entry_config,
        args.fvg_entry_custom_price,
    )
    pattern_execution_policy = validate_pattern_entry_mode(strategy_key, pattern_entry_mode).to_metadata(
        selected_entry_mode=pattern_entry_mode
    )
    transaction_cost_config, default_liquidity_role = _build_transaction_cost_config(args)
    position_sizing = _build_position_sizing_config(args)
    short_exposure_mode, simulated_margin = _build_simulated_margin_config(args)
    guardrails = _build_guardrail_config(args)
    workflow_settings = _workflow_settings_metadata(args, guardrails)
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
        print(
            json.dumps(
                _json_safe(
                    _empty_output(
                        strategy_key,
                        args.starting_cash,
                        interval=args.interval,
                        risk_free_rate=args.risk_free_rate,
                        policy_metadata=policy_metadata,
                    )
                )
            )
        )
        return 0
    pattern_profile["candle_count"] = int(len(candles))

    start_build = time.perf_counter()
    if profiler is not None:
        profiler.enable()
    entry_filter_config = _build_pattern_entry_filter_config(args)
    strategy, actions = _build_actions(
        candles,
        strategy_key,
        entry_filter_config,
        pattern_entry_mode=pattern_entry_mode,
        fvg_entry_config=fvg_entry_config,
        fvg_entry_custom_price=args.fvg_entry_custom_price,
        pattern_policy_metadata=pattern_execution_policy,
    )
    if profiler is not None:
        profiler.disable()
    timings["build_actions_ms"] = _ms(start_build, time.perf_counter())
    pattern_profile["actions_emitted"] = len(actions)
    pattern_profile["events_detected"] = sum(1 for a in actions if getattr(a, "metadata", None) and a.metadata.get("event_id"))
    strategy_version = "strategy_engine_v1"
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
        pattern_execution_policy=pattern_execution_policy,
        workflow_settings=workflow_settings,
        cost_profile_metadata=_cost_profile_metadata(args, transaction_cost_config),
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
        starting_cash=args.starting_cash,
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
    )
    result = run_strategy_backtest_engine(candles, actions, config=engine_config)
    timings["run_engine_ms"] = _ms(start_engine, time.perf_counter())

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
        strategy_explanation = build_pattern_strategy_explanation(strategy.strategy_key)
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
            starting_cash=args.starting_cash,
            trade_quantity=args.trade_quantity,
            engine_name=BACKTEST_ENGINE_NAME,
            engine_version=BACKTEST_ENGINE_VERSION,
            run_metadata=runtime_metadata | {"reproducibility": reproducibility_metadata},
        )
        persisted_run_id = repository.save_completed_backtest(payload)
    timings["persist_ms"] = _ms(start_persist, time.perf_counter())

    start_json = time.perf_counter()
    output = _serialize_output(result, strategy.strategy_key, strategy.strategy_name)
    output["reproducibility"] = reproducibility_metadata
    output["diagnostics"]["pattern_execution_policy"] = pattern_execution_policy
    output["summary"]["metadata"]["pattern_execution_policy"] = pattern_execution_policy
    output["summary"]["metadata"]["workflow_settings"] = workflow_settings
    output["summary"]["metadata"]["cost_profile"] = _cost_profile_metadata(args, transaction_cost_config, result)
    fvg_entry_diagnostics = _build_fvg_entry_mode_diagnostics(actions, result, pattern_entry_mode)
    output["diagnostics"]["fvg_entry_mode"] = fvg_entry_diagnostics
    output["summary"]["metadata"]["fvg_entry_mode"] = fvg_entry_diagnostics
    if args.compare_fvg_entry_modes:
        output["diagnostics"]["fvg_entry_mode_comparison"] = _build_fvg_entry_mode_comparison(
            candles,
            strategy.strategy_key,
            entry_filter_config,
            fvg_entry_config,
            args.fvg_entry_custom_price,
            engine_config,
        )
    if persisted_run_id is not None:
        output["backtest_run_id"] = persisted_run_id
    if not actions:
        output["warnings"].append("no strategy events")
    elif not output["events"]:
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
