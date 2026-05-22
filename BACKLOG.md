# Project Backlog (Current Window)

This file keeps a **high-signal recent window** only.
Older items are preserved in segmented archives:

- `docs/ledger_archives/backlog_task_001_050.md`
- `docs/ledger_archives/backlog_task_051_087.md`

All items below are candidate/planning pointers unless marked completed.

## Recent Task Window (Tasks 088-099)
- Completed (2026-05-22): Task 088 `STRATEGY_ACTION_LONG_SHORT_CONTRACT`.
- Completed (2026-05-22): Task 089 `STRATEGY_ENGINE_LONG_SHORT_COST_ACCOUNTING`.
- Completed (2026-05-22): Task 090 `RSI_CANONICAL_ENGINE_MIGRATION`.
- Completed (2026-05-22): Task 091 `PATTERN_STRATEGY_LONG_SHORT_ENABLEMENT`.
- Completed (2026-05-22): Task 092 `PATTERN_RISK_EXIT_ACTION_BUILDER`.
- Completed (2026-05-22): Task 093 `ENTRY_FILL_INTRABAR_INTEGRATION`.
- Completed (2026-05-22): Task 094 `PATTERN_DETECTION_PERFORMANCE_OPTIMIZATION`.
- Completed (2026-05-22): Task 095 `CANONICAL_CLI_AND_PERSISTENCE_MIGRATION`.
- Completed (2026-05-22): Task 096 `LEGACY_DEPRECATED_BACKTEST_CLEANUP`.
- Completed (2026-05-22): Task 097 `CANONICAL_BACKTEST_REGRESSION_AND_RESEARCH_TEST_SUITE`.
- Completed (2026-05-22): Task 098 `TASK_STATUS_LEDGER_SYNCHRONIZATION`.
- Active (2026-05-22): Task 099 `LEDGER_SEGMENTATION_AND_TEMPLATE_ENFORCEMENT`.

- Completed (2026-05-22): Task 099 follow-up review fix documented explicit 50-task ledger archiving rule in `AGENTS.md`.

## Current Candidates / Follow-ups
- Follow-up candidate: refine pattern-backtest financial summary semantics in shared persistence schema (replace current placeholder-neutral cash/equity values if owner requires richer financial outputs).
- Follow-up candidate: align pattern persistence graph-point cash/position/equity to candle-timed fills for richer dashboard trace fidelity.
- Non-FVG deterministic synthetic entry fixtures for broader pattern backtest determinism.
- Liquidity indicator implementation.
- Bid-Ask spread indicator implementation.

## Backend/Frontend Candidates
- API contract definition for backend/frontend coordination (`docs/api/API_CONTRACT.md` or equivalent).
- Backend API server for reading saved backtest results.
- Frontend backtest dashboard consuming persisted/read-model backtest outputs.

## Deferred Verification
- Local Docker runtime verification for previously completed Docker-related tasks (run in Docker-capable environment).
