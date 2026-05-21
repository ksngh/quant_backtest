# Task 078: BACKTEST_DASHBOARD_INTEGRATION_AND_VERIFICATION

## Goal
Verify backend/frontend integration for the read-only backtest dashboard.

## Required Work
1. Contract conformance review and small mismatch fixes.
2. Create/update `docs/api/BACKTEST_DASHBOARD_LOCAL_DEVELOPMENT.md`.
3. Backend verification (`pytest -q backend/tests`) or document limits.
4. Frontend build verification (`cd frontend && npm run build`) or document limits.
5. End-to-end smoke path validation when environment supports it.

## Out of Scope
- No auth/login.
- No live trading.
- No backtest execution endpoint.
- No DB redesign.

## Docs/Status
- Update `STATUS.md`, `backend/STATUS.md`, `frontend/STATUS.md`, `PROJECT_HISTORY.md`.
