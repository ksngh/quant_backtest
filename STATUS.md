# Project Status

## Current Overall Phase
Phase 160: Task 127 performance regression guardrail tests completed (2026-05-23).

## Current Step
Task 127 added lightweight 400-candle pattern runtime regression coverage and optional benchmark marker output for canonical evaluate_at paths.

## Current Goal
Maintain and extend canonical pattern runtime regression guardrails as needed.

## Current Active Task
No active implementation task (awaiting owner assignment after Task 127 completion).

## Last Completed Step (Short)
Task 127 completed with fixture-based runtime regression tests for all supported pattern keys plus optional benchmark smoke output.

## Recommended Next Step
Owner to assign next task (candidate: follow-up runtime guardrails tuning if needed).

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
