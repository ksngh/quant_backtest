# Project Status

## Current Overall Phase
Phase 97: Task 087 strategy backtest regression and research tests completed.

## Current Step
Task 087 completed: added regression/research tests for strategy accounting, CLI BUY/SELL outputs, DIAMOND diagnostics, metadata persistence, and no-exchange behavior checks.

## Current Goal
Prepare next queued task after Task 087 completion (owner assignment required).

## Current Active Task
Task `087_STRATEGY_BACKTEST_REGRESSION_AND_RESEARCH_TESTS` (completed).

## Last Completed Step (Short)
Task 087 completed: added deterministic regression/research coverage for strategy backtest cash/position/equity accounting and CLI execution semantics.

## Recommended Next Step
Wait for owner to assign/create the next task document (FIFO order).

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
