# Project Status

## Current Overall Phase
Phase 133: Task 117 short-accounting consistency and limitations completed (2026-05-23).

## Current Step
Task 117 completed: short win/loss counting now uses closing executions (including BUY short exits), short PnL behavior is regression-tested, and short-model limitations remain explicit in summary metadata/CLI output.

## Current Goal
Keep canonical long/short accounting internally consistent while making unsupported short-economics limitations explicit in outputs.

## Current Active Task
None (awaiting owner prioritization for next implementation task).

## Last Completed Step (Short)
Task 117 completed: corrected short-close win/loss accounting, added short accounting regression coverage, and preserved explicit short-model limitations metadata.

## Recommended Next Step
Execute Task 116 `PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS` or reprioritize Tasks 112-115 based on owner direction.

## Current Blockers (Short)
- Live trading remains blocked pending explicit owner approval, credential policy, allowed endpoint policy, and kill-switch design.
- Local Docker runtime verification remains deferred to a Docker-capable environment.
- Frontend package install/build remains blocked in this environment by npm registry access restrictions.

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
