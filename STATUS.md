# Project Status

## Current Overall Phase
Phase 111: Task 091 pattern strategy long/short enablement completed; Task 092 queued.

## Current Step
Task 091 completed: pattern strategies now emit long/short semantic entry actions for bullish/bearish events; Task 092 queued next.

## Current Goal
Execute Task 092 PATTERN_RISK_EXIT_ACTION_BUILDER per owner assignment.

## Current Active Task
Task `092_PATTERN_RISK_EXIT_ACTION_BUILDER` (queued, implementation pending).

## Last Completed Step (Short)
Task 091 completed: PatternStrategyBase direction handling now maps bullish->long and bearish->short semantic entries with position metadata, and no default SHORT_DISABLED skip.

## Recommended Next Step
Implement Task 092 pattern risk/exit action builder, then update tests/state docs.

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
