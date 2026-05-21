# Project Status

## Current Overall Phase
Phase 92: Task 087 strategy backtest regression and research tests completed.

## Current Step
Task 087 completed: added regression coverage for strategy persistence BUY/SELL rows, cash/equity movement, and exit-reason preservation.

## Current Goal
Track follow-up candidate work from Task 087, if any, and wait for explicit assignment of the next task.

## Current Active Task
Task `087_STRATEGY_BACKTEST_REGRESSION_AND_RESEARCH_TESTS` (completed).

## Last Completed Step (Short)
Task 087 completed: added regression tests and fixed persistence mapping to emit BUY/SELL executions, accurate quantity accounting, buy/sell counts, cash/equity movement, and preserved exit reasons.

## Recommended Next Step
Wait for owner assignment of the next task document (no automatic scope expansion).

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
