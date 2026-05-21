# Frontend Area Rules

## Ownership

Frontend owns dashboard user-interface implementation only.

## Allowed

- Implement dashboard UI from `docs/api/API_CONTRACT.md` when assigned.
- Fetch read-only backtest run data from backend API endpoints.
- Render list/detail charts, markers, metadata, and warning surfaces.

## Forbidden

- Direct database connections (including PostgreSQL access).
- Backtest execution logic in frontend.
- Live trading controls or exchange account/order actions.
- Auth/login implementation unless explicitly assigned in a future task.
- Backend repository/read-model code changes unless explicitly assigned.

## Visualization Boundary

Frontend must clearly distinguish:
- close price charting
- equity charting
- trade markers
- API warnings (including placeholder-neutral financial semantics)
