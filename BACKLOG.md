# Project Backlog (Candidate Work, Not Active)

All items below are **candidates only** and are **not approved implementation tasks** until explicitly assigned.

## Core Follow-Ups
- Completed (2026-05-21): Task 082 strategy-level architecture boundary documented with semantic/execution split and mapping scaffolding.
- Completed (2026-05-21): Task 083 extracted reusable risk/exit contracts into `quant_bitcoin/risk/` with compatibility shims for legacy pattern imports.
- Completed (2026-05-22): Task 084 implemented single-pattern strategy classes with semantic action outputs and factory selection helper.
- Completed (2026-05-22): Task 085 cash-based strategy backtest engine implemented with strategy execution/equity models and deterministic accounting tests.
- Completed (2026-05-22): Task 086 strategy-level CLI replacement with compatibility alias routing.
- Completed (2026-05-22): Task 087 strategy backtest regression/research tests for accounting, BUY/SELL outputs, DIAMOND diagnostics, and no-exchange safety checks.
- Queue policy note: when executing queued tasks, process in ascending order (FIFO by task number), not reverse order.
- Completed (2026-05-22): Task 088 strategy action contract expanded to include explicit long/short semantics and helper mappings.
- Completed (2026-05-22): Task 089 STRATEGY_ENGINE_LONG_SHORT_COST_ACCOUNTING implementation with deterministic long/short cost-aware accounting.
- Completed (2026-05-22): Task 090 RSI_CANONICAL_ENGINE_MIGRATION migrated RSI PostgreSQL CLI to canonical StrategyEngine path using RSI strategy-action adapter with compatibility persistence/output mappings.
- Completed (2026-05-22): Task 091 PATTERN_STRATEGY_LONG_SHORT_ENABLEMENT implemented bullish/ bearish pattern-to-long/short strategy action emission with focused tests.
- Completed (2026-05-22): Task 092 PATTERN_RISK_EXIT_ACTION_BUILDER implemented canonical pattern risk/exit simulation to strategy-action conversion with focused tests.
- Completed (2026-05-22): Task 093 ENTRY_FILL_INTRABAR_INTEGRATION integrated entry simulation outcomes into pattern action generation with no-fill diagnostics and filled-entry metadata propagation.
- Completed (2026-05-22): Task 094 PATTERN_DETECTION_PERFORMANCE_OPTIMIZATION implemented FVG cached/local-index detection path with CLI integration and deterministic parity tests.
- Completed (2026-05-22): Task 095 CANONICAL_CLI_AND_PERSISTENCE_MIGRATION implemented canonical strategy-engine persistence adapter and CLI payload migration.
- Completed (2026-05-22): Task 096 LEGACY_DEPRECATED_BACKTEST_CLEANUP explicitly deprecated legacy backtest modules and clarified canonical CLI preference.
- Completed (2026-05-22): Task 097 CANONICAL_BACKTEST_REGRESSION_AND_RESEARCH_TEST_SUITE added canonical persistence regression coverage and verification runs (with one unrelated pre-existing compose-test baseline failure).
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
