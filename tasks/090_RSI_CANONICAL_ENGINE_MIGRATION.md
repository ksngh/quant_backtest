# Task 090: RSI_CANONICAL_ENGINE_MIGRATION

## Status
Completed (2026-05-22)

## Goal
Migrate RSI backtesting onto the canonical `StrategyEngine` path while keeping `BasicBacktester` temporarily for compatibility.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `quant_bitcoin/strategies/rsi.py`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/backtesting/basic.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/postgres_runner_cli.py`
- `tests/backtesting/test_basic_backtest.py`
- `tests/backtesting/test_postgres_runner_cli.py`
- `tests/strategies/test_rsi_strategy.py`

## Problem
Current RSI flow uses BUY/SELL/HOLD signals with `BasicBacktester`, while pattern strategies use `StrategyAction` with `StrategyEngine`, creating duplicate accounting paths and inconsistent result semantics.

## Required Implementation
- Create RSI strategy-action adapter (suggested module: `quant_bitcoin/strategies/rsi_actions.py`).
- Suggested class:
  - `RsiActionStrategy(window=14, buy_threshold=30.0, sell_threshold=70.0)`
  - `evaluate(candles_so_far, portfolio_state=None) -> list[StrategyAction]`
- Behavior:
  - If RSI <= buy_threshold and no long position: emit `ENTER_LONG`.
  - If RSI >= sell_threshold and long position > 0: emit `EXIT_LONG`.
  - Otherwise: emit `[]`.
- If portfolio state injection is not available immediately, use deterministic adapter logic in CLI layer to avoid duplicate entries.
- Update `quant_bitcoin/backtesting/postgres_runner_cli.py` so active RSI CLI path uses:
  - `StrategyAction` generation
  - `run_strategy_backtest_engine(...)`
- Keep output shape as compatible as practical, allowing canonical field expansion.

## BasicBacktester Handling
- Do not delete `BasicBacktester` in this task.
- Mark as legacy/deprecated via docstring/comment if needed.

## Out of Scope
- No deletion of legacy code yet.
- No pattern strategy modifications.
- No short RSI logic.
- No live trading behavior.

## Tests
Add/update coverage so:
- RSI action adapter emits `ENTER_LONG` and `EXIT_LONG` deterministically.
- RSI CLI returns deterministic JSON.
- RSI CLI uses `StrategyEngine` path.
- Persistence remains functional when enabled.
- Existing RSI calculation tests remain valid.

## Acceptance Criteria
- RSI active backtest path uses `StrategyEngine`.
- `BasicBacktester` is no longer the active PostgreSQL RSI CLI execution path.
- Output remains usable for persistence/API/dashboard consumers.
- Tests pass.
- `STATUS.md` and `PROJECT_HISTORY.md` are updated.

## Verification
- `pytest -q tests/strategies/test_rsi_strategy.py`
- `pytest -q tests/backtesting/test_postgres_runner_cli.py`
- `pytest -q tests/backtesting/test_strategy_engine.py`
- `pytest -q`
- `git diff --check`
