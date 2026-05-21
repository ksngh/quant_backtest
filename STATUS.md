# Project Status

## Current Overall Phase
Phase 92: Task 082 strategy backtest architecture boundary completed.

## Current Step
Task 082 completed: documented pattern/risk/strategy/backtesting boundaries and added semantic-to-execution mapping scaffolding for long-only BUY/SELL conversion.

## Current Goal
Execute Task 083 by extracting reusable risk/exit policies from pattern modules into `quant_bitcoin/risk/` with compatibility boundaries.

## Current Active Task
Task `083_RISK_EXIT_EXTRACTION_AND_REUSABLE_POLICIES` (queued, not started).

## Last Completed Step (Short)
Task 082 completed: strategy action model (`ENTER_LONG`/`EXIT_LONG`/`PARTIAL_EXIT_LONG`/`SKIP`) separated from execution accounting sides (`BUY`/`SELL`) with architecture documentation and mapping tests.

## Recommended Next Step
Start Task 083 implementation from `tasks/083_RISK_EXIT_EXTRACTION_AND_REUSABLE_POLICIES.md`.

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
