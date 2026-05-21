# Project Status

## Current Overall Phase
Phase 91: Task 087 strategy backtest regression and research tests queued.

## Current Step
Task 087 created and queued: add regression and research-facing tests for strategy-level backtest accounting and persistence.

## Current Goal
Execute Task 087 by adding deterministic regression tests for BUY/SELL persistence, cash/equity movement, and diagnostics.

## Current Active Task
Task `087_STRATEGY_BACKTEST_REGRESSION_AND_RESEARCH_TESTS` (created, not started).

## Last Completed Step (Short)
Task 081 completed: added `--starting-cash` and `--trade-quantity` to pattern backtest CLI and removed unconditional zero cash placeholders in persisted run/result payload fields.

## Recommended Next Step
Start Task 087 implementation from `tasks/087_STRATEGY_BACKTEST_REGRESSION_AND_RESEARCH_TESTS.md` with deterministic synthetic regression coverage.

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval, credential policy, allowed endpoint policy, and kill-switch design.
- Local Docker runtime verification remains deferred to a Docker-capable environment.
- Frontend package install/build remains blocked in this environment by npm registry access restrictions.
- Backend API tests require FastAPI package availability in environment.

## Current Safety Boundary
- No live trading.
- No real Binance order execution.
- No API keys in code.
- No committed `.env` files.
- No signed exchange requests.
- No order/account endpoint usage.

## Focused Context Pointers
- Historical/completed ledger: `PROJECT_HISTORY.md`
- Future/deferred candidate work: `BACKLOG.md`
- Backend area status: `backend/STATUS.md`
- Frontend area status: `frontend/STATUS.md`
