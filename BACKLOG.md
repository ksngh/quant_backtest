# Project Backlog (Candidate Work, Not Active)

All items below are **candidates only** and are **not approved implementation tasks** until explicitly assigned.

## Core Follow-Ups
- Follow-up candidate: implementation task for multiple-testing helper utilities (`bonferroni_threshold`, `benjamini_hochberg_thresholds`, `count_strategy_variants`) with unit tests and edge-case validation (input validation, empty inputs, sorting assumptions, type stability).
- Follow-up candidate: refine pattern-backtest financial summary semantics in shared persistence schema (replace current placeholder-neutral cash/equity values if owner requires richer financial outputs).
- Non-FVG deterministic synthetic entry fixtures for broader pattern backtest determinism.
- Liquidity indicator implementation.
- Bid-Ask spread indicator implementation.

## Backend Candidates
- API contract definition for backend/frontend coordination (`docs/api/API_CONTRACT.md` or equivalent).
- Backend API server for reading saved backtest results.

## Frontend Candidates
- Frontend backtest dashboard consuming persisted/read-model backtest outputs.

## Documentation / Process Candidates
- PR #64 retrospective review.
- Follow-up refinement of area-specific status docs if backend/frontend tracks split further (for example `backend/STATUS.md`, `frontend/STATUS.md`).

## Deferred Verification
- Local Docker runtime verification for previously completed Docker-related tasks (run in Docker-capable environment).
