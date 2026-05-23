# Project Status

## Current Overall Phase
Phase 158: Task 125 dashboard runtime display completed (2026-05-23).

## Current Step
Task 125 exposed runtime summary in dashboard list/detail views with backward-compatible API serialization and safe missing-runtime fallbacks.

## Current Goal
Execute Task 126 strategy explanation metadata display, then Task 127 runtime regression guardrail tests.

## Current Active Task
Task 126 is the current active optimization task; Task 127 remains a defined follow-up.

## Last Completed Step (Short)
Task 125 completed with runtime serialization in list responses and runtime breakdown rendering in dashboard summary/detail cards; next step is Task 126, then Task 127.

## Recommended Next Step
Implement Task 126 (strategy explanation metadata and display), then Task 127 (performance regression tests).

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval, credential policy, allowed endpoint policy, and kill-switch design.
- Local Docker runtime verification remains deferred to a Docker-capable environment.
- Frontend package install/build remains blocked in this environment by npm registry access restrictions.

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
