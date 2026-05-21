# Project Status

## Current Overall Phase
Phase 84: Docker Compose service split workflows implemented.

## Current Step
Task 080 completed: compose startup paths split by service profiles (db/backend/frontend/backtest).

## Current Goal
Keep split compose workflows verifiable and documented in Docker-capable environments.

## Current Active Task
Task `080_DOCKER_COMPOSE_SERVICE_SPLIT` (completed).

## Last Completed Step (Short)
Task 080 completed: split compose profiles added for db/backend/frontend/backtest with explicit commands documented; optional ingestion profile retained.

## Recommended Next Step
Run Docker-capable smoke verification for each profile path (`db`, `backend`, `frontend`, `backtest`) and capture results in project history.

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
