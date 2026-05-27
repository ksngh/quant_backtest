# Project Status

## Current Overall Phase
Phase 282: FVG retest v2 research batch complete through Task 237 (2026-05-27).

## Current Step
Task 237 `FVG_RETEST_V2_DOCUMENTATION_LEDGER_RECONCILIATION_AND_ARCHIVE_CHECK` is complete. No next task is currently assigned.

## Current Goal
Keep the completed offline, no-lookahead FVG retest v2 research batch documented, reproducible, and clearly separated from live-trading approval.

## Current Active Task
No active task is assigned after Task 237.

## Last Completed Step (Short)
Completed Task 237: reconciled FVG v2 documentation, status, history, backlog, and archive state; no 201-250 archive is required yet.

## Recommended Next Step
Owner should assign the next explicit task before implementation continues. Candidate next work: run the FVG v2 WFO/OOS protocol on an approved fixed dataset or defer until a new research/data task is created.

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval for Task 138, credential policy, allowed endpoint policy, and kill-switch design.
- Task 170 audit confirms live execution also needs max-notional guards, symbol filter checks, stale-data checks, duplicate-order idempotency, restart reconciliation, cancel/replace and partial-fill policy, monitoring/alerting, and secret-management policy before Task 138 can be unblocked.
- Local Docker runtime verification remains deferred to a Docker-capable environment.
- Backend FastAPI route tests are not runnable in the current Python environment because `fastapi` is not installed; FastAPI-independent backend service tests passed.
- In-app browser automation could not be used in this session because the required Node REPL browser-control tool was not exposed; local Next server HTML response was verified with `curl`.

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
