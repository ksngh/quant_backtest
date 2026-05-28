# Project Status

## Current Overall Phase
Phase 284: Dashboard UX/API filter planning created through Task 246 (2026-05-28).

## Current Step
Tasks 242-246 have been created from owner dashboard feedback. No implementation has started for these tasks.

## Current Goal
Improve saved-backtest dashboard usability while keeping it read-only: chart-first inspection, collapsible diagnostics, filterable saved-run navigation, and per-trade cost detail visibility.

## Current Active Task
No active implementation task is in progress. Task 242 is the recommended next assigned task.

## Last Completed Step (Short)
Created Tasks 242-246: chart interaction/layout, collapsible indicator diagnostics, backend run-list filters, frontend filter UI, and trade-row cost detail disclosure.

## Recommended Next Step
Assign Task 242 `DASHBOARD_CHART_INTERACTION_AND_LAYOUT` first, then Task 243, Task 244, Task 245, and Task 246. Task 244 should be completed before Task 245 unless both are explicitly assigned together.

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
