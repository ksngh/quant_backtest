# Project Backlog (Candidate Work, Not Active)

All items below are **candidates only** and are **not approved implementation tasks** until explicitly assigned.

## Core Follow-Ups
- Completed (2026-05-21): Task 082 strategy-level architecture boundary documented with semantic/execution split and mapping scaffolding.
- Completed (2026-05-21): Task 083 extracted reusable risk/exit contracts into `quant_bitcoin/risk/` with compatibility shims for legacy pattern imports.
- Completed (2026-05-22): Task 084 implemented single-pattern strategy classes with semantic action outputs and factory selection helper.
- Completed (2026-05-22): Task 085 cash-based strategy backtest engine implemented with strategy execution/equity models and deterministic accounting tests.
- Next queued task document created: `tasks/086_STRATEGY_BACKTEST_CLI_AND_PERSISTENCE_REPLACEMENT.md` (strategy-level CLI replacement with BUY/SELL persistence and compatibility routing).
- Next queued task document created: `tasks/087_STRATEGY_BACKTEST_REGRESSION_AND_RESEARCH_TESTS.md` (regression/research tests for strategy accounting, BUY/SELL persistence, and diagnostics).
- Queue policy note: when executing queued tasks, process in ascending order (FIFO by task number), not reverse order.
- Follow-up candidate: refine pattern-backtest financial summary semantics in shared persistence schema (replace current placeholder-neutral cash/equity values if owner requires richer financial outputs).
- Non-FVG deterministic synthetic entry fixtures for broader pattern backtest determinism.
- Liquidity indicator implementation.
- Bid-Ask spread indicator implementation.

## Backend Candidates
- Completed (2026-05-21): Task 080 split Docker Compose startup paths for backtest/backend/db/frontend into independently runnable profile workflows.
- Completed (2026-05-21): Task 079 implemented one-command backend/frontend Docker Compose local startup (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`).
- API contract definition for backend/frontend coordination (`docs/api/API_CONTRACT.md` or equivalent).
- Backend API server for reading saved backtest results.

## Frontend Candidates
- Frontend backtest dashboard consuming persisted/read-model backtest outputs.

## Documentation / Process Candidates
- PR #64 retrospective review.
- Follow-up refinement of area-specific status docs if backend/frontend tracks split further (for example `backend/STATUS.md`, `frontend/STATUS.md`).

## Deferred Verification
- Local Docker runtime verification for previously completed Docker-related tasks (run in Docker-capable environment).

- Follow-up candidate: align pattern persistence graph-point cash/position/equity to candle-timed fills for richer dashboard trace fidelity.