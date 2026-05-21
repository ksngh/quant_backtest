# Backend Area Rules

## Ownership

Backend owns API application wiring and HTTP serialization for the read-only backtest dashboard.

## Allowed

- Implement FastAPI application code when assigned by a backend task.
- Consume existing persistence read models and repositories.
- Map repository read models into API response schemas from `docs/api/API_CONTRACT.md`.
- Add backend-focused tests using dependency overrides/fakes where possible.

## Forbidden

- Calling exchange order/account endpoints.
- Starting live trading behavior.
- Running new backtests from dashboard API endpoints unless a future task explicitly allows it.
- Exposing API keys or credentials in responses/logs.
- Implementing frontend UI concerns in backend modules.

## Safety Boundary

- API remains read-only for completed backtest result views in this phase.
- Health endpoint may report process/database status only.
