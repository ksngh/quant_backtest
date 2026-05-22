# Project Status

## Current Overall Phase
Phase 110: Task 090 RSI canonical engine migration completed; Task 091 queued.

## Current Step
Task 090 completed: PostgreSQL RSI CLI now runs via canonical strategy-action engine path; Task 091 queued next.

## Current Goal
Execute Task 091 PATTERN_STRATEGY_LONG_SHORT_ENABLEMENT per owner assignment.

## Current Active Task
Task `091_PATTERN_STRATEGY_LONG_SHORT_ENABLEMENT` (queued, implementation pending).

## Last Completed Step (Short)
Task 090 completed: RSI PostgreSQL CLI migrated to canonical StrategyEngine via RSI strategy-action adapter, with compatibility output/persistence mapping preserved and focused tests updated.

## Recommended Next Step
Implement Task 091 pattern strategy long/short enablement, then update tests/state docs.

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
