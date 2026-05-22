from __future__ import annotations
from collections.abc import Sequence
from quant_bitcoin.runtime_logging import log_runtime_exception
from quant_bitcoin.backtesting.strategy_postgres_runner_cli import run

def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(argv, prog="quant-bitcoin-pattern-backtest", include_strategy=False)
    except Exception as exc:
        log_runtime_exception(__name__, exc)
        return 1
