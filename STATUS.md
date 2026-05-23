# Project Status

## Current Overall Phase
Phase 159: Task 126 strategy explanation metadata completed (2026-05-23).

## Current Step
Task 126 added persisted strategy explanation metadata and dashboard explanation sections (algorithm/entry/SL/TP/rationale/limitations) with backward-compatible missing-metadata fallbacks.

## Current Goal
Execute Task 127 runtime/performance regression guardrail tests.

## Current Active Task
Task 127 is the current active optimization task.

## Last Completed Step (Short)
Task 126 completed with strategy explanation metadata persisted on strategy configs and rendered in dashboard explanation cards; next step is Task 127.

## Recommended Next Step
Implement Task 127 (performance regression tests).

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
