# Project Status

## Current Overall Phase
Phase 115: Task 095 canonical CLI and persistence migration completed; Task 096 queued.

## Current Step
Task 095 completed: canonical strategy-engine persistence adapter now unifies RSI/pattern strategy persistence payload mapping; Task 096 queued next.

## Current Goal
Execute Task 096 LEGACY_DEPRECATED_BACKTEST_CLEANUP per owner assignment.

## Current Active Task
Task `096_LEGACY_DEPRECATED_BACKTEST_CLEANUP` (queued, implementation pending).

## Last Completed Step (Short)
Task 095 completed: added canonical strategy persistence adapter; migrated RSI and strategy/pattern CLI persistence mapping to StrategyEngine payload semantics.

## Recommended Next Step
Implement Task 096 legacy deprecated backtest cleanup, then update tests/state docs.

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
