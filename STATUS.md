# Project Status

## Current Overall Phase
Phase 134: Task 116 pattern entry filtering and sizing controls completed (2026-05-23).

## Current Step
Task 116 completed: canonical pattern strategies now default-filter non-VALID events, support configurable weak/score/risk-reward gates, and defer position sizing to engine trade quantity unless explicit override is configured.

## Current Goal
Keep canonical pattern entries conservative and configurable while preserving deterministic strategy-engine sizing contracts.

## Current Active Task
None (awaiting owner prioritization for next implementation task).

## Last Completed Step (Short)
Task 116 completed: added pattern-entry filters and optional quantity override, wired CLI args/config persistence, and added strategy/CLI regression coverage.

## Recommended Next Step
Execute Task 115 `BACKTEST_METRICS_AND_PERSISTENCE_METADATA_QUALITY` or reprioritize Tasks 112-114 based on owner direction.

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
