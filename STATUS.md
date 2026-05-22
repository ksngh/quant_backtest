# Project Status

## Current Overall Phase
Phase 126: Task 106 legacy public API pruning completed.

## Current Step
Task 106 completed: deprecated backtesting package-level exports pruned to canonical-first imports and compatibility usage moved to direct module paths.

## Current Goal
Keep canonical strategy-engine-first public API surface while preserving explicit compatibility module imports.

## Current Active Task
No active implementation task (await owner assignment of Task 107+).

## Last Completed Step (Short)
Task 106 completed: `quant_bitcoin.backtesting` public exports now prioritize canonical strategy-engine symbols; legacy Basic/pattern imports require explicit module-level compatibility imports.

## Recommended Next Step
Recommended next task: Task 107 `STRATEGY_EXECUTION_MAPPING_RETIREMENT`.

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
