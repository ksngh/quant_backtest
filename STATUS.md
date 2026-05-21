# Project Status

## Current Overall Phase
Phase 93: Task 083 reusable risk/exit policy boundary completed.

## Current Step
Task 083 completed: extracted generic risk/exit plan and exit simulation contracts into `quant_bitcoin/risk/` and preserved legacy `quant_bitcoin/patterns/*` imports through compatibility shims.

## Current Goal
Execute Task 084 by implementing single-pattern strategy classes under `quant_bitcoin/strategies/` using the semantic action contract.

## Current Active Task
Task `084_SINGLE_PATTERN_STRATEGY_IMPLEMENTATIONS` (queued, not started).

## Last Completed Step (Short)
Task 083 completed: moved generic risk/exit ownership out of `patterns` into reusable `risk` package and verified deterministic pattern risk/exit tests remain green.

## Recommended Next Step
Start Task 084 implementation from `tasks/084_SINGLE_PATTERN_STRATEGY_IMPLEMENTATIONS.md`.

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
