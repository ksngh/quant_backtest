# Backtest Dashboard Local Development

This document describes the local read-only dashboard workflow for persisted backtest results.

## Scope and Safety

- Read-only dashboard only (`/api/health`, `/api/backtest-runs`, `/api/backtest-runs/{id}`).
- No login/auth in this phase.
- No live trading.
- No exchange order/account endpoints.
- Frontend must call backend API only (never PostgreSQL directly).

## Compose split startup profiles (Task 080)

Docker Compose services are now split by profile so you can start only what you need:

```bash
# DB only
docker compose --profile db up -d

# Backend + DB
docker compose --profile backend up -d

# Frontend + Backend + DB
docker compose --profile frontend up -d

# Backtest runner + DB (one-shot help command by default)
docker compose --profile backtest up backtest

# Full dashboard stack + backtest helper
docker compose --profile full up -d
```

Notes:
- `frontend` profile includes backend/db dependencies automatically.
- `backtest` profile starts a dedicated `backtest` service and db.
- `websocket-ingestor` remains optional under `ingestion` profile:

```bash
docker compose --profile ingestion up websocket-ingestor
```

## 1) Start PostgreSQL (if available)

If Docker is available in your environment:

```bash
docker compose up -d postgres
```

Or use any local PostgreSQL instance and export:

```bash
export DATABASE_URL='postgresql://user:pass@localhost:5432/quant_backtest'
```

## 2) Persist at least one completed backtest result

Use an existing CLI that writes persisted backtest outputs:

```bash
python -m quant_bitcoin.backtesting.postgres_runner_cli --help
python -m quant_bitcoin.backtesting.pattern_postgres_runner_cli --help
```

Run one CLI with your local dataset/config so one completed run exists in
`backtest_runs/backtest_results/backtest_trades/backtest_graph_points`.

## 3) Start FastAPI backend

From repo root:

```bash
export DATABASE_URL='postgresql://user:pass@localhost:5432/quant_backtest'
python -m uvicorn backend.quant_backtest_api.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend URL: `http://localhost:8000`

Check health:

```bash
curl http://localhost:8000/api/health
```

## 4) Start frontend

From `frontend/`:

```bash
npm install
NEXT_PUBLIC_BACKTEST_API_BASE_URL=http://localhost:8000 npm run dev
```

Frontend URL: `http://localhost:3000`

## 5) Smoke path

1. Open `http://localhost:3000`.
2. Confirm completed run list loads.
3. Select a run row.
4. Confirm summary cards, close-price chart, equity chart, trade markers, and trades table render.
5. Confirm cash-balance/free-cash labels render when account-state metadata is present.
6. Confirm strategy/run/result metadata panels render.

## 6) Placeholder-neutral equity/cash limitation

Some older persisted pattern runs can contain placeholder-neutral cash/equity values from pre-canonical compatibility history.

Expected behavior:
- Backend returns warning entries in `warnings`.
- Frontend displays warning banner/panel.
- If equity series is all zero, UI shows explicit caution and should not imply real PnL quality.

## 7) Cash/free-cash display limitation

For new canonical strategy-engine runs, trade/result metadata can include
`free_cash_after`, `margin_used_after`, `short_proceeds_locked_after`, and
`cash_after_semantics`. The dashboard should show `cash_after` as a cash
balance and use free-cash metadata for spendable-cash display when available.

Legacy runs may not have this metadata. In that case the UI should preserve the
raw cash/equity fields and avoid implying that short-sale proceeds are free
buying power.

## 8) Verification commands

```bash
pytest -q backend/tests
cd frontend && npm run build
git diff --check
```

If environment limits package installation or runtime services, document the limitation and run available static checks.
