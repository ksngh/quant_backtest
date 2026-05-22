# Project Status

## Current Overall Phase
Phase 114: Task 094 pattern detection performance optimization completed; Task 095 queued.

## Current Step
Task 094 completed: FVG path now uses cached indicator/pattern evaluation for local index detection; Task 095 queued next.

## Current Goal
Execute Task 095 CANONICAL_CLI_AND_PERSISTENCE_MIGRATION per owner assignment.

## Current Active Task
Task `095_CANONICAL_CLI_AND_PERSISTENCE_MIGRATION` (queued, implementation pending).

## Last Completed Step (Short)
Task 094 completed: Added FVG optimization cache/context path and strategy CLI integration to avoid repeated full-prefix detection for FVG.

## Recommended Next Step
Implement Task 095 canonical CLI and persistence migration, then update tests/state docs.

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
