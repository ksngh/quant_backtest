# Project Status

## Current Overall Phase
Phase 128: Task 108 patterns public export boundary cleanup completed.

## Current Step
Task 108 completed: migrated pattern-risk internal/test imports to canonical `quant_bitcoin.risk` paths while retaining compatibility shims.

## Current Goal
Keep canonical risk import ownership under `quant_bitcoin.risk` while preserving explicit compatibility shims in `quant_bitcoin.patterns`.

## Current Active Task
No active implementation task (await owner assignment of Task 109+).

## Last Completed Step (Short)
Task 108 completed: removed active internal/test dependency on `quant_bitcoin.patterns.risk_exit` and `quant_bitcoin.patterns.exit_simulation` by migrating to canonical `quant_bitcoin.risk` imports.

## Recommended Next Step
Recommended next task: Task 109 `FVG_CACHE_NAMING_OR_PATTERN_CACHE_REGISTRY`.

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
