from __future__ import annotations

from collections.abc import Sequence

from quant_bitcoin.runtime_logging import log_runtime_exception

from .strategy_postgres_runner_core import (
    PostgresCandleDataProvider,
    StrategyAction,
    StrategyActionType,
    _build_actions,
    build_pattern_trade_actions,
    build_parser,
    run,
    strategy_for_pattern,
)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv)
    except Exception:
        log_runtime_exception(__name__)
        return 1
