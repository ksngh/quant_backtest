# Project Status

## Current Overall Phase
Phase 127: Task 107 strategy execution mapping retirement completed.

## Current Step
Task 107 completed: retired long-only strategy execution mapping helper and moved mapping coverage to canonical long/short action helpers.

## Current Goal
Keep canonical long/short action helper APIs as the single action-to-side mapping contract.

## Current Active Task
No active implementation task (await owner assignment of Task 108+).

## Last Completed Step (Short)
Task 107 completed: removed `quant_bitcoin.backtesting.strategy_execution_mapping`; tests now validate canonical `strategies.actions` long/short execution and position side mappings.

## Recommended Next Step
Recommended next task: Task 108 `PATTERNS_PUBLIC_EXPORT_BOUNDARY_CLEANUP`.

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
