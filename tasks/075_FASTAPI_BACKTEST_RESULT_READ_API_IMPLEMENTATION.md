# Task 075: FASTAPI_BACKTEST_RESULT_READ_API_IMPLEMENTATION

## Goal
Implement read-only FastAPI backend endpoints for persisted backtest results.

## Required Context
- `AGENTS.md`
- `backend/AGENTS.md`
- `STATUS.md`
- `backend/STATUS.md`
- `docs/api/API_CONTRACT.md`
- `db/init/001_schema.sql`
- `quant_bitcoin/persistence/postgres.py`
- `pyproject.toml`

## Endpoints
- `GET /api/health`
- `GET /api/backtest-runs` (filters + limit max 100)
- `GET /api/backtest-runs/{backtest_run_id}`

## Rules
- Reuse `PostgresBacktestResultRepository` read methods.
- No backtest execution from API.
- No exchange/live/order/account behavior.
- Surface placeholder warning semantics.

## Tests
- health, list, limit validation, detail success, detail 404, warning behavior.

## Docs/Status
- Update `STATUS.md`, `backend/STATUS.md`, `PROJECT_HISTORY.md`.
