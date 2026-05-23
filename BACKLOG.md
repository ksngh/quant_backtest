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
- Completed (2026-05-23): Task 139 `GITIGNORE_ARTIFACT_CLEANUP_AND_PR_RESCOPE` (clean PR branch scope and ignore local/generated artifacts).
- Blocked: Task 138 `GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL` pending explicit owner approval for live order execution.
- Completed (2026-05-23): Task 137 `EXECUTION_FILL_RECONCILIATION_AND_ACTUAL_COST_METRICS`.
- Completed (2026-05-23): Task 136 `BINANCE_SPOT_TESTNET_EXECUTION_CLIENT_SAFETY_AND_POLICY`.
- Completed (2026-05-23): Task 135 `PRODUCT_SPECIFIC_SHORT_POLICY_AND_EXECUTION_BOUNDARIES`.
- Completed (2026-05-23): Task 134 `REALTIME_CANDLE_CLOSE_STRATEGY_TRIGGER_AND_PAPER_EXECUTION`.
- Completed (2026-05-23): Task 133 `ORDER_INTENT_AND_PAPER_EXECUTION_CONTRACT`.
- Completed (2026-05-23): Task 132 `BACKTEST_PERFORMANCE_METRICS_FROM_EQUITY_CURVE`.
- Completed (2026-05-23): Task 131 `MULTI_INTERVAL_BINANCE_CANDLE_ORCHESTRATION` (multi-interval public candle backfill workflow with parser, runner, CLI summary, and tests).
- Completed (2026-05-23): Task 130 `STATE_RECONCILIATION_AND_EXECUTION_TASK_BUNDLE` (reconciled the created 131-138 task window and next-task pointer).
- Completed (2026-05-23): Task 129 `DIAMOND_STATUS_FILTERING_INVESTIGATION` (reproduced Diamond failures, clarified VALID-only default status filter contract, and aligned Diamond tests with explicit status semantics).
- Completed (2026-05-23): Task 128 `STRATEGY_CLI_JSON_TIMESTAMP_SERIALIZATION_FIX` (canonical strategy CLI JSON-safe timestamp metadata serialization + exception logging signature fix).
- Completed (2026-05-23): Task 125 `DASHBOARD_RUNTIME_DISPLAY` (frontend/backend runtime visibility after Task 124 metadata persistence).
- Completed (2026-05-23): Task 127 `PATTERN_BACKTEST_PERFORMANCE_REGRESSION_TESTS` (added 400-candle fixture runtime guardrails across all supported pattern paths and optional benchmark smoke output).
- Completed (2026-05-23): Task 126 `STRATEGY_EXPLANATION_METADATA_ALGORITHM_AND_SL_TP_RATIONALE` (human-readable algorithm/SL/TP rationale metadata + dashboard display after Task 125).
- Completed (2026-05-23): Task 124 `PERSIST_BACKTEST_RUNTIME_METADATA` (persisted canonical runtime metadata under `backtest_runs.metadata.runtime` and included runtime payload in `--no-persist` CLI JSON output).
- Completed (2026-05-23): Task 123 `HOT_LOOP_DATAFRAME_AND_PERSISTENCE_IO_CLEANUP` (removed avoidable deep-copy overhead in canonical pattern strategy/action-builder paths with no-mutation regression coverage).
- Completed (2026-05-23): Task 122 `PIVOT_HEAVY_PATTERN_CANDIDATE_PRUNING` (deterministic recent-pivot/candidate-cap pruning for pivot-heavy detectors).
- Completed (2026-05-23): Task 121 `SHARED_INDICATOR_CACHE_AND_AT_INDEX_PATTERN_DETECTION` (shared cache generalized + at-index Order Block path + duplicate suppression parity tests).
- Completed (2026-05-23): Task 120 `PROFILE_CANONICAL_PATTERN_BACKTEST_RUNTIME` (added optional profiling instrumentation and no-persist regression coverage for phase/runtime bottleneck visibility).
- Completed (2026-05-23): Task 119 `LEDGER_RECHECK_TASKS_111_118` (reconciled root status pointer with latest completed task window and confirmed 111-118 completion chronology across root ledgers).
- Completed (2026-05-23): Task 118 `TRANSACTION_COST_CLI_AND_ACCOUNTING_INTEGRATION`.
- Completed (2026-05-23): Task 117 `SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS`.
- Completed (2026-05-23): Task 116 `PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS`.
- Completed (2026-05-23): Task 115 `BACKTEST_METRICS_AND_PERSISTENCE_METADATA_QUALITY`.
- Completed (2026-05-23): Task 114 `INTRABAR_STOP_TARGET_AMBIGUITY_POLICY`.
- Completed (2026-05-23): Task 113 `FVG_NO_LOOKAHEAD_CACHE_CORRECTION`.
- Completed (2026-05-23): Task 112 `EXECUTION_PRICE_AND_ENTRY_FILL_CONTRACT` (validated explicit execution-price propagation + fallback behavior with targeted strategy/pattern regression suite).
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
