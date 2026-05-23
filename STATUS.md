# Project Status

## Current Overall Phase
Phase 174: Ledger archive range cleanup completed (2026-05-24).

## Current Step
Reconciled `BACKLOG.md` and `PROJECT_HISTORY.md` with the fixed 50-task archive rule from `AGENTS.md`.

## Current Goal
Keep root ledgers focused on the current high-signal window while preserving older history in deterministic archive files.

## Current Active Task
No active implementation task. Task 099 ledger segmentation follow-up is complete; Task 138 remains blocked pending explicit live-order approval.

## Last Completed Step (Short)
Replaced partial ledger archives with fixed `*_task_051_100.md` archives and trimmed root ledgers to the Tasks 101-148 recent window plus active notes.

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
