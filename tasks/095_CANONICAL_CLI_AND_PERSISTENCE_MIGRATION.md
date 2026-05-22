# Task 095: CANONICAL_CLI_AND_PERSISTENCE_MIGRATION

## Status
Planned (created by Codex, implementation not started)

## Goal
Migrate active CLI and persistence paths to the canonical `StrategyEngine` result model so RSI and pattern backtests produce/persist comparable outputs.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `quant_bitcoin/backtesting/postgres_runner_cli.py`
- `quant_bitcoin/backtesting/pattern_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/persistence/postgres.py`
- `db/init/001_schema.sql`
- backend/API contract docs if present

## Problem
CLI/persistence paths are not fully unified around canonical strategy-engine outputs, and persistence compatibility across RSI/pattern/strategy CLI flows must be standardized and verified.

## Required Implementation
Create canonical persistence adapter module:
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`

Suggested function:
- `build_strategy_engine_persistence_payload(result, candles, *, source, symbol, interval, start_time, end_time, strategy_key, strategy_name, strategy_version, strategy_parameters, starting_cash, trade_quantity) -> BacktestPersistencePayload`

Mapping responsibilities:
- `StrategyExecution -> BacktestTradePayload`
- `StrategyEquityPoint -> BacktestGraphPointPayload`
- `StrategyBacktestSummary -> BacktestResultPayload`

Long/short persistence semantics:
- preserve execution side (`BUY`/`SELL`) in persisted signal.
- preserve semantic action metadata (`action_type`, `position_side`) in persisted metadata.

Update active CLI paths so canonical adapter is used where applicable:
- RSI CLI path
- pattern CLI path
- strategy CLI path

## Out of Scope
- No DB schema migration unless strictly required.
- No frontend implementation.
- No live trading behavior.
- No strategy semantic changes.

## Tests
Add/update tests for:
- RSI CLI persistence of canonical graph points.
- Pattern CLI persistence of canonical graph points.
- Short execution persistence includes action metadata.
- Equity graph values are non-placeholder and reflect canonical equity points.
- API/read-model compatibility for loading persisted runs.

## Acceptance Criteria
- Active CLIs persist `StrategyBacktestResult` consistently.
- Pattern persistence no longer writes placeholder-neutral equity when canonical result exists.
- Dashboard/API can consume persisted canonical runs.
- Existing DB schema is reused.
- Tests pass.
- `STATUS.md` and `PROJECT_HISTORY.md` are updated.

## Verification
- `pytest -q tests/backtesting/test_postgres_runner_cli.py`
- `pytest -q tests/backtesting/test_pattern_postgres_runner_cli.py`
- `pytest -q tests/persistence`
- `pytest -q`
- `git diff --check`
