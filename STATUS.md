# Project Status

## Current Overall Phase
Phase 132: Task 118 transaction-cost CLI and accounting integration completed (2026-05-23).

## Current Step
Task 118 completed: canonical strategy backtest CLI now exposes transaction-cost configuration and passes it into strategy-engine accounting/persistence metadata.

## Current Goal
Run canonical backtests with configurable fee/spread/slippage/liquidity-role while preserving deterministic zero-cost defaults.

## Current Active Task
None (awaiting owner prioritization for next implementation task).

## Last Completed Step (Short)
Task 110 completed: added enriched execution/event/diagnostic fields and warnings for no-fills/risk-plan/open-position cases in strategy CLI output.

## Recommended Next Step
Execute Task 117 `SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS` or reprioritize Tasks 112-116 based on owner direction.

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
