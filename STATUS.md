# Project Status

## Current Overall Phase
Phase 108: Task 088 strategy action long/short contract completed; Task 089 queued.

## Current Step
Task 088 completed: strategy action long/short contract added; Task 089 queued next.

## Current Goal
Execute Task 089 STRATEGY_ENGINE_LONG_SHORT_COST_ACCOUNTING per owner assignment.

## Current Active Task
Task `089_STRATEGY_ENGINE_LONG_SHORT_COST_ACCOUNTING` (queued, implementation pending).

## Last Completed Step (Short)
Task 088 completed: expanded strategy semantic actions to long/short contract with action-side mapping helpers and compatibility execution side fields.

## Recommended Next Step
Implement Task 089 long/short strategy engine cost accounting, then update tests/state docs.

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
