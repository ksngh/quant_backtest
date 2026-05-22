# Project Status

## Current Overall Phase
Phase 116: Task 096 legacy deprecated backtest cleanup completed; Task 097 queued.

## Current Step
Task 096 completed: legacy backtest modules were explicitly deprecated and canonical strategy CLI guidance was clarified; Task 097 queued next.

## Current Goal
Execute Task 097 CANONICAL_BACKTEST_REGRESSION_AND_RESEARCH_TEST_SUITE per owner assignment.

## Current Active Task
Task `097_CANONICAL_BACKTEST_REGRESSION_AND_RESEARCH_TEST_SUITE` (queued, implementation pending).

## Last Completed Step (Short)
Task 096 completed: deprecated legacy backtest modules (`basic.py`, `pattern_strategy.py`, `postgres_runner_cli.py`) and clarified canonical strategy CLI preference in README.

## Recommended Next Step
Implement Task 097 canonical backtest regression/research test suite, then update tests/state docs.

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
