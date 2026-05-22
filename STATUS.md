# Project Status

## Current Overall Phase
Phase 95: Task 085 cash-based strategy backtest engine completed.

## Current Step
Task 085 completed: added reusable strategy backtest engine with BUY/SELL cashflow accounting, partial exits, equity curve points, and strategy summary outputs.

## Current Goal
Execute Task 086 by wiring strategy backtest CLI + persistence replacement to use Task 085 engine outputs.

## Current Active Task
Task `086_STRATEGY_BACKTEST_CLI_AND_PERSISTENCE_REPLACEMENT` (queued, not started).

## Last Completed Step (Short)
Task 085 completed: implemented strategy-level cash accounting engine with execution/equity models and deterministic engine tests.

## Recommended Next Step
Start Task 086 implementation from `tasks/086_STRATEGY_BACKTEST_CLI_AND_PERSISTENCE_REPLACEMENT.md`.

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
