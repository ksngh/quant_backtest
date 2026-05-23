# Project Status

## Current Overall Phase
Phase 153: Task 120 profiling runtime instrumentation completed (2026-05-23).

## Current Step
Task 120 profiling instrumentation implemented and verified with no-persist integration test.

## Current Goal
Execute Task 121 shared indicator cache + at-index pattern detection, then Tasks 122-124 optimization/persistence, Task 125 dashboard runtime display, Task 126 strategy explanation metadata, then Task 127 performance regression tests.

## Current Active Task
Task 121 is the current active optimization task; Tasks 122-127 remain defined follow-ups.

## Last Completed Step (Short)
Task 120 completed with profiling output phase timings/top functions; next step is Task 121 execution, then Tasks 122-127 in sequence.

## Recommended Next Step
Implement Task 121 (shared indicator cache + at-index FVG/Order Block), then Task 122 (pivot-heavy pruning), Task 123 (hot-loop DataFrame/I-O cleanup), Task 124 (persist runtime metadata), Task 125 (dashboard runtime display), Task 126 (strategy explanation metadata and display), then Task 127 (performance regression tests).

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
