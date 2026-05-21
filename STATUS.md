# Project Status

## Current Overall Phase
Phase 82: Backend/frontend Docker Compose local startup completed.

## Current Step
Task 079 completed with one-command backend/frontend Docker Compose local startup wiring.

## Current Goal
Keep dashboard local runtime and verification stable across containerized and non-containerized workflows.

## Current Active Task
Task `079_BACKEND_FRONTEND_DOCKER_COMPOSE_SETUP` (completed).

## Last Completed Step (Short)
Task 079 completed: added root Docker Compose services for postgres/backend/frontend with host port mappings and container-network API base URL wiring, kept websocket ingestor as optional profile, and added dedicated backend/frontend Dockerfiles. Verification: `docker compose config` (environment-limited: docker unavailable) and `git diff --check`.

## Recommended Next Step
Add focused smoke checks/docs follow-up for Docker-capable environments (compose up/down verification and API/UI health assertions).

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
