from __future__ import annotations

import argparse
import json
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.strategy_engine import StrategyEngineConfig
from quant_bitcoin.backtesting.walk_forward import (
    WalkForwardConfig,
    build_rsi_action_builder,
    monte_carlo_trade_return_bootstrap,
    run_walk_forward_validation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run offline walk-forward validation over a local candle CSV.")
    parser.add_argument("--csv", required=True, help="Local CSV with timestamp/open/high/low/close/volume columns.")
    parser.add_argument("--train-window", required=True, help="Pandas Timedelta string, for example 30min or 7D.")
    parser.add_argument("--test-window", required=True, help="Pandas Timedelta string, for example 10min or 1D.")
    parser.add_argument("--step-size", required=True, help="Pandas Timedelta string used to advance folds.")
    parser.add_argument("--strategy", choices=["rsi"], default="rsi")
    parser.add_argument("--rsi-window", type=int, default=14)
    parser.add_argument("--rsi-buy-threshold", type=float, default=30.0)
    parser.add_argument("--rsi-sell-threshold", type=float, default=70.0)
    parser.add_argument("--starting-cash", type=float, default=10000.0)
    parser.add_argument("--trade-quantity", type=float, default=1.0)
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
    }
    payload = run_walk_forward_validation(
        candles,
        config=WalkForwardConfig(args.train_window, args.test_window, args.step_size),
        action_builder=build_rsi_action_builder(
            window=args.rsi_window,
            buy_threshold=args.rsi_buy_threshold,
            sell_threshold=args.rsi_sell_threshold,
        ),
        engine_config=StrategyEngineConfig(
            starting_cash=args.starting_cash,
            trade_quantity=args.trade_quantity,
            interval=args.interval,
        ),
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
