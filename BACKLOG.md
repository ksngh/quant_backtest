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
- Completed (2026-05-22): Task 099 `LEDGER_SEGMENTATION_AND_TEMPLATE_ENFORCEMENT`.

- Completed (2026-05-22): Task 099 follow-up review fix documented explicit 50-task ledger archiving rule in `AGENTS.md`.

- Completed (2026-05-22): Task 100 `TASK_LEDGER_COMPLETION_RECONCILIATION_FOLLOWUP`.

- Completed (2026-05-22): Task 101 `DOCKER_COMPOSE_BACKTEST_PROFILE_CANONICALIZATION`.

- Completed (2026-05-22): Task 102 `CANONICAL_PATTERN_ACTION_BUILDER_CLI_INTEGRATION`.
- Completed (2026-05-22): Task 103 `STRATEGY_PERSISTENCE_MULTIFILL_GRAPH_MARKERS`.

- Completed (2026-05-22): Task 105 `README_AND_API_CONTRACT_CANONICAL_BACKTEST_REFRESH`.

- Completed (2026-05-22): Task 106 `LEGACY_PUBLIC_API_PRUNING`.

- Completed (2026-05-22): Task 107 `STRATEGY_EXECUTION_MAPPING_RETIREMENT`.

- Completed (2026-05-22): Task 108 `PATTERNS_PUBLIC_EXPORT_BOUNDARY_CLEANUP`.


- Completed (2026-05-22): Task 109 `FVG_CACHE_NAMING_OR_PATTERN_CACHE_REGISTRY`.

- Completed (2026-05-22): Task 110 `PATTERN_STRATEGY_OUTPUT_SCHEMA_ENRICHMENT`.

## Current Candidates / Follow-ups
- Completed (2026-05-23): Task 118 `TRANSACTION_COST_CLI_AND_ACCOUNTING_INTEGRATION`.
- Completed (2026-05-23): Task 117 `SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS`.
- Completed (2026-05-23): Task 116 `PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS`.
- Completed (2026-05-23): Task 115 `BACKTEST_METRICS_AND_PERSISTENCE_METADATA_QUALITY`.
- Created (2026-05-22): Task 114 `INTRABAR_STOP_TARGET_AMBIGUITY_POLICY` (task document added; requested as separate task).
- Created (2026-05-22): Task 113 `FVG_NO_LOOKAHEAD_CACHE_CORRECTION` (task document added; requested as separate task).
- Created (2026-05-22): Task 112 `EXECUTION_PRICE_AND_ENTRY_FILL_CONTRACT` (task document added; requested as separate task from Task 111).
- Completed (2026-05-22): Task 111 `CANONICAL_PATTERN_LIFECYCLE_BACKTEST_INTEGRATION` (execution-price/entry-fill contract delivered).
- Candidate: Task 111 `PATTERN_STRATEGY_OUTPUT_CONTRACT_DOCUMENTATION_AND_FIXTURE_EXPANSION` (document enriched stdout schema and broaden deterministic fixtures for short-side/no-fill cases).
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
- Completed (2026-05-22): Task 104 `STRATEGY_POSTGRES_RUNNER_CLI_REFACTOR`.

