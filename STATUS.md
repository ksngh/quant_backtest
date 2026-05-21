# Project Status

## Current Overall Phase
Phase 81: Backtest dashboard integration and verification completed.

## Current Step
Task 078 completed with contract conformance fixes and local development workflow documentation.

## Current Goal
Keep backend/frontend dashboard integration stable and verifiable for local developer workflows.

## Current Active Task
Task `078_BACKTEST_DASHBOARD_INTEGRATION_AND_VERIFICATION` (completed).

## Last Completed Step (Short)
Task 078 completed: verified API/frontend integration against `docs/api/API_CONTRACT.md`, fixed backend detail serialization to contract nested `run.market` and strategy key names, added local development workflow doc for PostgreSQL/backtest persistence/backend/frontend startup + smoke steps, and updated status docs. Verification: `pytest -q backend/tests` (environment-limited), `cd frontend && npm run build` (environment-limited), and `git diff --check`.

## Recommended Next Step
Add focused API contract tests and frontend component-level tests to reduce regression risk for run/detail shape and warning rendering.

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
