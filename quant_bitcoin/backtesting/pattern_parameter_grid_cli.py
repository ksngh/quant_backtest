from __future__ import annotations

import argparse
import json
from typing import Any

import pandas as pd

from quant_bitcoin.backtesting.json_metadata import json_ready
from quant_bitcoin.backtesting.pattern_parameter_grid import (
    PatternParameterGridConfig,
    run_pattern_parameter_grid,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run an offline deterministic parameter grid for pattern backtests."
    )
    parser.add_argument("--csv", required=True, help="Local CSV with timestamp/open/high/low/close/volume columns.")
    parser.add_argument("--pattern", required=True, help="Pattern key, for example FAIR_VALUE_GAP or TRENDLINE_BREAK.")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Grid parameter as path=value1,value2. Example: entry.mode=market_on_confirmation_close,limit_at_entry_reference",
    )
    parser.add_argument("--max-combinations", type=int, default=100)
    parser.add_argument("--warning-combinations", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--starting-cash", type=float, default=10000.0)
    parser.add_argument("--trade-quantity", type=float, default=1.0)
    parser.add_argument("--interval", default="1m")
    args = parser.parse_args(argv)

    try:
        candles = pd.read_csv(args.csv)
        payload = run_pattern_parameter_grid(
            candles,
            pattern=args.pattern,
            grid=_parse_grid(args.param),
            config=PatternParameterGridConfig(
                max_combinations=args.max_combinations,
                warning_combinations=args.warning_combinations,
                dry_run=args.dry_run,
                starting_cash=args.starting_cash,
                trade_quantity=args.trade_quantity,
                interval=args.interval,
            ),
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(json_ready(payload), sort_keys=True))
    return 0


def _parse_grid(params: list[str]) -> dict[str, tuple[Any, ...]]:
    grid: dict[str, tuple[Any, ...]] = {}
    for item in params:
        if "=" not in item:
            raise ValueError(f"invalid --param format: {item}")
        path, raw_values = item.split("=", 1)
        path = path.strip()
        if not path:
            raise ValueError(f"invalid --param path: {item}")
        values = tuple(_parse_value(value.strip()) for value in raw_values.split(",") if value.strip())
        if not values:
            raise ValueError(f"parameter path has no values: {path}")
        grid[path] = values
    return grid or {"entry.mode": ("market_on_confirmation_close",)}


def _parse_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"none", "null"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." not in value:
            return int(value)
        return float(value)
    except ValueError:
        return value


if __name__ == "__main__":
    raise SystemExit(main())
