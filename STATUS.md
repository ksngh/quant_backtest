# Project Status

## Current Overall Phase
Phase 173: Tasks 140-148 cash/sizing/accounting window completed (2026-05-23).

## Current Step
Completed the sequential cash/sizing/accounting window from Task 140 through Task 148.

## Current Goal
Keep the new backtest sizing, cash/equity, simulated short, CLI/persistence, display, and documentation contracts stable under regression tests.

## Current Active Task
No active implementation task. Tasks 140-148 are completed; Task 138 remains blocked pending explicit live-order approval.

## Last Completed Step (Short)
Task 148 completed after Tasks 140-147: docs and ledgers now match the new cash-bounded sizing, short buying-power, simulated-margin, account-state, CLI/persistence, display/API, and refactor work.

## Recommended Next Step
No new next implementation task is assigned. Task 138 remains blocked unless the owner explicitly approves live order execution.

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval for Task 138, credential policy, allowed endpoint policy, and kill-switch design.
- Local Docker runtime verification remains deferred to a Docker-capable environment.
- Backend FastAPI route tests are not runnable in the current Python environment because `fastapi` is not installed; FastAPI-independent backend service tests passed.

## Current Safety Boundary
- No live trading.
- No real Binance order execution.
- No API keys in code.
- No committed `.env` files.
- No signed exchange requests.
- No order/account endpoint usage.
- Testnet signed order request code exists only in the explicit execution client and is covered by fake-HTTP tests; live order execution remains disabled.

## Focused Context Pointers
- Historical/completed ledger: `PROJECT_HISTORY.md`
- Future/deferred candidate work: `BACKLOG.md`
- Backend area status: `backend/STATUS.md`
- Frontend area status: `frontend/STATUS.md`
