# Task 096: LEGACY_DEPRECATED_BACKTEST_CLEANUP

## Status
Completed (2026-05-22)

## Goal
Remove or clearly deprecate legacy backtest code after canonical StrategyEngine migration is complete.

## Preconditions
This task should be executed only after Tasks 088-095 are completed and canonical behavior is verified by tests.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `PROJECT_HISTORY.md`
- `BACKLOG.md`
- `quant_bitcoin/backtesting/basic.py`
- `quant_bitcoin/backtesting/pattern_strategy.py`
- `quant_bitcoin/patterns/exit_simulation.py`
- `quant_bitcoin/patterns/risk_exit.py`
- `quant_bitcoin/risk/exit_simulation.py`
- `quant_bitcoin/risk/exit_plan.py`
- CLI entrypoints in `pyproject.toml`
- all tests importing legacy modules

## Problem
Legacy modules may remain after canonical migration and can create confusion around active engine ownership, import boundaries, and test coverage intent.

## Cleanup Policy
For each reviewed file/module, choose one explicit decision:
- `REMOVE`
- `DEPRECATE_AND_KEEP`
- `KEEP_AS_TEST_FIXTURE`

Do not remove anything before validating imports and test impacts.

## Candidate Legacy Items
Review at minimum:
- `quant_bitcoin/backtesting/basic.py`
- `quant_bitcoin/backtesting/pattern_strategy.py`
- `quant_bitcoin/patterns/exit_simulation.py` (compatibility shim)
- `quant_bitcoin/patterns/risk_exit.py` (compatibility shim)
- old CLI wrappers
- tests that only validate legacy execution paths

## Required Implementation
1. Inventory legacy/deprecated modules and classify each with cleanup decision.
2. Update imports toward canonical modules where active code still references legacy paths.
3. Remove obsolete tests or rewrite them to validate canonical paths.
4. For retained modules, add clear deprecation docstring, e.g.:
   - `Deprecated: use quant_bitcoin.backtesting.strategy_engine instead.`
5. Update `README.md` and docs to remove/clarify deprecated path references.
6. Update `BACKLOG.md` by removing or marking completed cleanup candidates.

## Out of Scope
- No strategy semantic changes.
- No new feature development.
- No safety-boundary removals.
- No live trading behavior.

## Acceptance Criteria
- No active CLI uses deprecated backtest path.
- No active docs instruct use of deprecated path.
- Tests primarily validate canonical StrategyEngine path.
- Deprecated modules are removed or explicitly marked.
- Any retained import-compatibility behavior is intentionally documented.
- Full test suite passes.
- `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` are updated.

## Verification
- `pytest -q`
- `python -m compileall quant_bitcoin`
- `git diff --check`
