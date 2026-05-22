# Project Status

## Current Overall Phase
Phase 125: Task 105 README/API canonical backtest refresh completed.

## Current Step
Task 105 completed: README/API/backend warning language aligned to canonical strategy-backtest CLI and legacy placeholder warning semantics.

## Current Goal
Keep canonical strategy-backtest documentation and API warning semantics aligned with persisted-run behavior.

## Current Active Task
No active implementation task (await owner assignment of Task 106+).

## Last Completed Step (Short)
Task 105 completed: canonical CLI docs now prefer `quant-bitcoin-strategy-backtest`; compatibility aliases and legacy placeholder warnings are explicitly documented.

## Recommended Next Step
Recommended next task: Task 106 `LEGACY_PUBLIC_API_PRUNING`.

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
