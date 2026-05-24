from __future__ import annotations

import argparse
import json
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.cost_profiles import COST_PROFILES, cost_profile, manual_cost_overrides_present
from quant_bitcoin.backtesting.costs import TransactionCostConfig
from quant_bitcoin.backtesting.sizing import PositionSizingConfig, PositionSizingMode
from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig
from quant_bitcoin.backtesting.walk_forward import (
    WalkForwardConfig,
    build_pattern_action_builder,
    build_rsi_action_builder,
    monte_carlo_trade_return_bootstrap,
    run_walk_forward_validation,
)
from quant_bitcoin.patterns.entry_simulation import PatternEntryConfig, PatternEntryMode, PatternEntryStatus
from quant_bitcoin.strategies.patterns import PatternEntryFilterConfig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run offline walk-forward validation over a local candle CSV.")
    parser.add_argument("--csv", required=True, help="Local CSV with timestamp/open/high/low/close/volume columns.")
    parser.add_argument("--train-window", required=True, help="Pandas Timedelta string, for example 30min or 7D.")
    parser.add_argument("--test-window", required=True, help="Pandas Timedelta string, for example 10min or 1D.")
    parser.add_argument("--step-size", required=True, help="Pandas Timedelta string used to advance folds.")
    parser.add_argument("--strategy", choices=["rsi", "pattern"], default="rsi")
    parser.add_argument("--rsi-window", type=int, default=14)
    parser.add_argument("--rsi-buy-threshold", type=float, default=30.0)
    parser.add_argument("--rsi-sell-threshold", type=float, default=70.0)
    parser.add_argument("--pattern", help="Pattern key for --strategy pattern, for example FAIR_VALUE_GAP or ORDER_BLOCK.")
    parser.add_argument("--entry-mode", default=PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE.value, help="Pattern entry simulation mode.")
    parser.add_argument("--entry-max-wait-bars", type=int, default=None)
    parser.add_argument("--entry-expire-status", default=PatternEntryStatus.NOT_FILLED.value)
    parser.add_argument("--entry-custom-price", type=float, default=None)
    parser.add_argument("--allowed-pattern-statuses", default="VALID")
    parser.add_argument("--min-pattern-score", type=float, default=None)
    parser.add_argument("--starting-cash", type=float, default=10000.0)
    parser.add_argument("--trade-quantity", type=float, default=1.0)
    parser.add_argument("--sizing-mode", choices=[mode.value for mode in PositionSizingMode], default=PositionSizingMode.FIXED_QUANTITY.value)
    parser.add_argument("--sizing-value", type=float, default=None)
    parser.add_argument("--cost-profile", choices=sorted(COST_PROFILES), default="zero")
    parser.add_argument("--maker-fee-bps", type=float, default=0.0)
    parser.add_argument("--taker-fee-bps", type=float, default=0.0)
    parser.add_argument("--spread-bps", type=float, default=0.0)
    parser.add_argument("--slippage-bps", type=float, default=0.0)
    parser.add_argument("--interval", default="1m")
    parser.add_argument("--monte-carlo-seed", type=int, default=0)
    parser.add_argument("--monte-carlo-iterations", type=int, default=100)
    args = parser.parse_args(argv)

    candles = pd.read_csv(args.csv)
    strategy_parameters = {
        "strategy": args.strategy,
        "rsi_window": args.rsi_window,
        "rsi_buy_threshold": args.rsi_buy_threshold,
        "rsi_sell_threshold": args.rsi_sell_threshold,
        "pattern": args.pattern,
        "entry_mode": args.entry_mode,
        "allowed_pattern_statuses": args.allowed_pattern_statuses,
        "minimum_pattern_score": args.min_pattern_score,
        "cost_profile": args.cost_profile,
        "sizing_mode": args.sizing_mode,
        "sizing_value": args.sizing_value,
    }
    payload = run_walk_forward_validation(
        candles,
        config=WalkForwardConfig(args.train_window, args.test_window, args.step_size),
        action_builder=_action_builder(args),
        engine_config=_engine_config(args),
        strategy_parameters=strategy_parameters,
    )
    net_pnl_values = [
        float(fold["summary"]["net_pnl"])
        for fold in payload["folds"]
        if isinstance(fold.get("summary"), dict)
    ]
    payload["monte_carlo"] = monte_carlo_trade_return_bootstrap(
        net_pnl_values,
        iterations=args.monte_carlo_iterations,
        seed=args.monte_carlo_seed,
    )
    print(json.dumps(_json_safe(payload), sort_keys=True))
    return 0


def _action_builder(args: argparse.Namespace):
    if args.strategy == "rsi":
        return build_rsi_action_builder(
            window=args.rsi_window,
            buy_threshold=args.rsi_buy_threshold,
            sell_threshold=args.rsi_sell_threshold,
        )
    if not args.pattern:
        raise ValueError("--strategy pattern requires --pattern")
    entry_mode = PatternEntryMode(str(args.entry_mode).upper().replace("-", "_"))
    if entry_mode is PatternEntryMode.LIMIT_AT_CUSTOM_PRICE and args.entry_custom_price is None:
        raise ValueError("LIMIT_AT_CUSTOM_PRICE requires --entry-custom-price")
    statuses = tuple(sorted({value.strip().upper() for value in args.allowed_pattern_statuses.split(",") if value.strip()}))
    return build_pattern_action_builder(
        pattern=args.pattern,
        entry_filter_config=PatternEntryFilterConfig(
            allowed_statuses=statuses or ("VALID",),
            minimum_pattern_score=args.min_pattern_score,
        ),
        entry_mode=entry_mode,
        entry_config=PatternEntryConfig(
            max_wait_bars=args.entry_max_wait_bars,
            expire_status=PatternEntryStatus(str(args.entry_expire_status).upper().replace("-", "_")),
        ),
        entry_custom_price=args.entry_custom_price,
    )


def _engine_config(args: argparse.Namespace) -> StrategyEngineConfig:
    return StrategyEngineConfig(
        starting_cash=args.starting_cash,
        trade_quantity=args.trade_quantity,
        interval=args.interval,
        transaction_cost_config=_transaction_cost_config(args),
        position_sizing=_position_sizing_config(args),
    )


def _transaction_cost_config(args: argparse.Namespace) -> TransactionCostConfig:
    overrides = {
        "maker_fee_bps": args.maker_fee_bps,
        "taker_fee_bps": args.taker_fee_bps,
        "spread_bps": args.spread_bps,
        "slippage_bps": args.slippage_bps,
    }
    if args.cost_profile != "zero" and manual_cost_overrides_present(overrides):
        raise ValueError("manual cost bps overrides cannot be combined with a non-zero --cost-profile in walk-forward CLI")
    if args.cost_profile != "zero":
        return cost_profile(args.cost_profile).config
    return TransactionCostConfig(**overrides)


def _position_sizing_config(args: argparse.Namespace) -> PositionSizingConfig:
    mode = PositionSizingMode(args.sizing_mode)
    return PositionSizingConfig(mode=mode, value=args.sizing_value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


if __name__ == "__main__":
    raise SystemExit(main())
