# Project Status

## Current Overall Phase
Phase 61: Status ledger split implementation and focused-context workflow update.

## Current Step
Implementing Task `tasks/STATUS_LEDGER_SPLIT.md` (documentation-only split + working-rule updates).

## Current Goal
Move active-state, historical, and future-candidate content into focused documents so backend/frontend tasks can load only relevant context by default.

## Current Active Task
Task `tasks/STATUS_LEDGER_SPLIT.md` in `Mode: document`.

## Last Completed Step (Short)
Task 058 completed: pattern backtest supports selecting one implemented pattern per run with deterministic metadata and preserved no-live-trading boundary.

## Recommended Next Step
Owner review and approval of this ledger split and focused-context rule update, then assign the next implementation task from `BACKLOG.md`.

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval, credential policy, allowed endpoint policy, and kill-switch design.
- Local Docker runtime verification remains deferred to a Docker-capable environment.

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
- If introduced later, area-focused status docs (for example backend/frontend) should be preferred for area tasks over full project history.
