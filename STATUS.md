# Project Status

## Current Overall Phase
Phase 161: Task 128 strategy CLI JSON timestamp serialization fix completed (2026-05-23).

## Current Step
Task 128 fixed canonical strategy CLI JSON serialization of timestamp-like values and corrected strategy/pattern CLI exception logging calls.

## Current Goal
Maintain canonical strategy CLI output stability and address unrelated strategy test failures if assigned.

## Current Active Task
No active implementation task (awaiting owner assignment after Task 128 completion).

## Last Completed Step (Short)
Task 128 completed with recursive JSON-safe CLI output serialization and regression coverage for timestamp metadata plus exception logging.

## Recommended Next Step
Owner to assign next task. Candidate: investigate existing Diamond strategy unit-test failures around default pattern status filtering.

## Current Blockers (Short)
- Full pytest currently has two unrelated failures in `tests/strategies/test_single_pattern_strategies.py` for Diamond bullish/bearish entry expectations versus current status filtering behavior.
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
