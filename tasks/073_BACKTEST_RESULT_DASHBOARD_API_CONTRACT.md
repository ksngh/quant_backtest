# Task 073: BACKTEST_RESULT_DASHBOARD_API_CONTRACT

## Goal
Define the first read-only backend/frontend API contract for completed backtest dashboard views.

## Scope
- `GET /api/health`
- `GET /api/backtest-runs`
- `GET /api/backtest-runs/{backtest_run_id}`
- Optional `GET /api/backtest-runs/{backtest_run_id}/chart`

## Required Rules
- Read-only only.
- No backtest execution endpoint.
- No login/auth.
- No live trading/order/account endpoint.
- Include warning semantics for pattern placeholder-neutral cash/equity rows.

## Acceptance
- Contract doc exists and is usable by backend/frontend tasks.
