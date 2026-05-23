# Project Status

## Current Overall Phase
Phase 155: Task 122 pivot-heavy pattern candidate pruning completed (2026-05-23).

## Current Step
Task 122 added deterministic candidate caps/recent-pivot pruning for Trendline Break, Cup and Handle, Diamond, and Adam and Eve.

## Current Goal
Execute Task 123 hot-loop DataFrame/persistence I/O cleanup, then Tasks 124-127 in sequence.

## Current Active Task
Task 123 is the current active optimization task; Tasks 124-127 remain defined follow-ups.

## Last Completed Step (Short)
Task 122 completed with deterministic pruning/candidate caps for pivot-heavy detectors; next step is Task 123, then Tasks 124-127 in sequence.

## Recommended Next Step
Implement Task 123 (hot-loop DataFrame/I-O cleanup), then Task 124 (persist runtime metadata), Task 125 (dashboard runtime display), Task 126 (strategy explanation metadata and display), then Task 127 (performance regression tests).

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
