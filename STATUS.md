# Project Status

## Current Overall Phase
Phase 124: Task 104 strategy PostgreSQL runner CLI refactor completed.

## Current Step
Task 104 completed: canonical strategy PostgreSQL CLI refactored into focused core + entrypoint modules.

## Current Goal
Maintain canonical strategy CLI behavior while keeping parser/orchestration/persistence/output responsibilities modular and readable.

## Current Active Task
No active implementation task (await owner assignment of Task 105+).

## Last Completed Step (Short)
Task 104 completed: strategy CLI wiring moved into focused core module while preserving wrapper compatibility and output contract.

## Recommended Next Step
Recommended next task: Task 105 `README_AND_API_CONTRACT_CANONICAL_BACKTEST_REFRESH`.

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
