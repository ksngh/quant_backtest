# Project Status

## Current Overall Phase
Phase 85: Task 081 backtest starting-cash alignment implemented.

## Current Step
Task 081 completed: pattern PostgreSQL backtest persistence now reflects configured starting cash and simulated ending cash.

## Current Goal
Keep backtest cash semantics consistent across runners and verify in Docker-capable environments.

## Current Active Task
Task `081_BACKTEST_STARTING_CASH_ALIGNMENT` (completed).

## Last Completed Step (Short)
Task 081 completed: added `--starting-cash` and `--trade-quantity` to pattern backtest CLI and removed unconditional zero cash placeholders in persisted run/result payload fields.

## Recommended Next Step
Create follow-up task to align graph-point cash/position/equity with candle-by-candle event timing if richer portfolio tracing is required.

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
