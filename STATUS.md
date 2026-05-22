# Project Status

## Current Overall Phase
Phase 109: Task 089 strategy engine long/short cost accounting completed; Task 090 queued.

## Current Step
Task 089 completed: strategy engine long/short cost accounting integrated; Task 090 queued next.

## Current Goal
Execute Task 090 RSI_CANONICAL_ENGINE_MIGRATION per owner assignment.

## Current Active Task
Task `090_RSI_CANONICAL_ENGINE_MIGRATION` (queued, implementation pending).

## Last Completed Step (Short)
Task 089 completed: strategy engine now supports deterministic long/short signed-position accounting with integrated transaction-cost metadata and no double-counted spread/slippage semantics.

## Recommended Next Step
Implement Task 090 RSI canonical engine migration, then update tests/state docs.

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
