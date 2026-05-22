# Project Status

## Current Overall Phase
Phase 94: Task 084 single-pattern strategy implementations completed.

## Current Step
Task 084 completed: added single-pattern strategy classes under `quant_bitcoin/strategies/patterns.py` with semantic action outputs and long-only short-disabled skip behavior.

## Current Goal
Execute Task 085 by implementing the cash-based strategy backtest engine.

## Current Active Task
Task `085_CASH_BASED_STRATEGY_BACKTEST_ENGINE` (queued, not started).

## Last Completed Step (Short)
Task 084 completed: implemented six single-pattern strategies plus factory selection and strategy tests including bullish ENTER_LONG and bearish SHORT_DISABLED semantics.

## Recommended Next Step
Start Task 085 implementation from `tasks/085_CASH_BASED_STRATEGY_BACKTEST_ENGINE.md`.

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
