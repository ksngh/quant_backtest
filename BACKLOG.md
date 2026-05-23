# Project Backlog (Current Window)

This file keeps a **high-signal recent window** only.
Older items are preserved in fixed 50-task segmented archives:

- `docs/ledger_archives/backlog_task_001_050.md`
- `docs/ledger_archives/backlog_task_051_100.md`

All items below are candidate/planning pointers unless marked completed.

## Recent Task Window (Tasks 101-150)
- Completed (2026-05-24): Task 150 `BACKTEST_DASHBOARD_VISUAL_ANALYTICS_UPGRADE` (chart zoom/range, compact trade review, curated metadata/parameters, strategy indicators, pattern algorithm/economic explanation).
- Completed (2026-05-24): Task 149 `BACKTEST_POSITION_SIGNAL_AND_ACCOUNT_STATE_SEMANTICS` (semantic long/short signal, execution-side separation, cash/free-cash/equity display semantics).
- Completed (2026-05-23): Task 148 `BACKTEST_ACCOUNTING_DOCUMENTATION_CONSISTENCY`.
- Completed (2026-05-23): Task 147 `BACKTEST_ACCOUNTING_REFACTOR_AFTER_CASH_AND_MARGIN`.
- Completed (2026-05-23): Task 146 `BACKTEST_CASH_EQUITY_DISPLAY_AND_API_SEMANTICS`.
- Completed (2026-05-23): Task 145 `CANONICAL_CLI_PERSISTENCE_WIRING_FOR_SIZING_MARGIN`.
- Completed (2026-05-23): Task 144 `ACCOUNT_STATE_VISIBILITY_FIELDS`.
- Completed (2026-05-23): Task 143 `SIMULATED_MARGIN_INITIAL_MARGIN_GUARD`.
- Completed (2026-05-23): Task 142 `SHORT_BUYING_POWER_POLICY`.
- Completed (2026-05-23): Task 141 `LONG_CASH_BOUNDED_ENTRY_EXECUTION`.
- Completed (2026-05-23): Task 140 `POSITION_SIZING_POLICY_CONTRACT`.
- Completed (2026-05-23): Task 139 `GITIGNORE_ARTIFACT_CLEANUP_AND_PR_RESCOPE` (clean PR branch scope and ignore local/generated artifacts).
- Blocked: Task 138 `GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL` pending explicit owner approval for live order execution.
- Completed (2026-05-23): Task 137 `EXECUTION_FILL_RECONCILIATION_AND_ACTUAL_COST_METRICS`.
- Completed (2026-05-23): Task 136 `BINANCE_SPOT_TESTNET_EXECUTION_CLIENT_SAFETY_AND_POLICY`.
- Completed (2026-05-23): Task 135 `PRODUCT_SPECIFIC_SHORT_POLICY_AND_EXECUTION_BOUNDARIES`.
- Completed (2026-05-23): Task 134 `REALTIME_CANDLE_CLOSE_STRATEGY_TRIGGER_AND_PAPER_EXECUTION`.
- Completed (2026-05-23): Task 133 `ORDER_INTENT_AND_PAPER_EXECUTION_CONTRACT`.
- Completed (2026-05-23): Task 132 `BACKTEST_PERFORMANCE_METRICS_FROM_EQUITY_CURVE`.
- Completed (2026-05-23): Task 131 `MULTI_INTERVAL_BINANCE_CANDLE_ORCHESTRATION`.
- Completed (2026-05-23): Task 130 `STATE_RECONCILIATION_AND_EXECUTION_TASK_BUNDLE`.
- Completed (2026-05-23): Task 129 `DIAMOND_STATUS_FILTERING_INVESTIGATION`.
- Completed (2026-05-23): Task 128 `STRATEGY_CLI_JSON_TIMESTAMP_SERIALIZATION_FIX`.
- Completed (2026-05-23): Task 127 `PATTERN_BACKTEST_PERFORMANCE_REGRESSION_TESTS`.
- Completed (2026-05-23): Task 126 `STRATEGY_EXPLANATION_METADATA_ALGORITHM_AND_SL_TP_RATIONALE`.
- Completed (2026-05-23): Task 125 `DASHBOARD_RUNTIME_DISPLAY`.
- Completed (2026-05-23): Task 124 `PERSIST_BACKTEST_RUNTIME_METADATA`.
- Completed (2026-05-23): Task 123 `HOT_LOOP_DATAFRAME_AND_PERSISTENCE_IO_CLEANUP`.
- Completed (2026-05-23): Task 122 `PIVOT_HEAVY_PATTERN_CANDIDATE_PRUNING`.
- Completed (2026-05-23): Task 121 `SHARED_INDICATOR_CACHE_AND_AT_INDEX_PATTERN_DETECTION`.
- Completed (2026-05-23): Task 120 `PROFILE_CANONICAL_PATTERN_BACKTEST_RUNTIME`.
- Completed (2026-05-23): Task 119 `LEDGER_RECHECK_TASKS_111_118`.
- Completed (2026-05-23): Task 118 `TRANSACTION_COST_CLI_AND_ACCOUNTING_INTEGRATION`.
- Completed (2026-05-23): Task 117 `SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS`.
- Completed (2026-05-23): Task 116 `PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS`.
- Completed (2026-05-23): Task 115 `BACKTEST_METRICS_AND_PERSISTENCE_METADATA_QUALITY`.
- Completed (2026-05-23): Task 114 `INTRABAR_STOP_TARGET_AMBIGUITY_POLICY`.
- Completed (2026-05-23): Task 113 `FVG_NO_LOOKAHEAD_CACHE_CORRECTION`.
- Completed (2026-05-23): Task 112 `EXECUTION_PRICE_AND_ENTRY_FILL_CONTRACT`.
- Completed (2026-05-22): Task 111 `CANONICAL_PATTERN_LIFECYCLE_BACKTEST_INTEGRATION`.
- Completed (2026-05-22): Task 110 `PATTERN_STRATEGY_OUTPUT_SCHEMA_ENRICHMENT`.
- Completed (2026-05-22): Task 109 `FVG_CACHE_NAMING_OR_PATTERN_CACHE_REGISTRY`.
- Completed (2026-05-22): Task 108 `PATTERNS_PUBLIC_EXPORT_BOUNDARY_CLEANUP`.
- Completed (2026-05-22): Task 107 `STRATEGY_EXECUTION_MAPPING_RETIREMENT`.
- Completed (2026-05-22): Task 106 `LEGACY_PUBLIC_API_PRUNING`.
- Completed (2026-05-22): Task 105 `README_AND_API_CONTRACT_CANONICAL_BACKTEST_REFRESH`.
- Completed (2026-05-22): Task 104 `STRATEGY_POSTGRES_RUNNER_CLI_REFACTOR`.
- Completed (2026-05-22): Task 103 `STRATEGY_PERSISTENCE_MULTIFILL_GRAPH_MARKERS`.
- Completed (2026-05-22): Task 102 `CANONICAL_PATTERN_ACTION_BUILDER_CLI_INTEGRATION`.
- Completed (2026-05-22): Task 101 `DOCKER_COMPOSE_BACKTEST_PROFILE_CANONICALIZATION`.

## Current Candidates / Follow-ups
- Follow-up candidate: add visual regression/UI tests for dashboard marker/table rendering once a frontend test harness is assigned.
- Candidate: `PATTERN_STRATEGY_OUTPUT_CONTRACT_DOCUMENTATION_AND_FIXTURE_EXPANSION` (document enriched stdout schema and broaden deterministic fixtures for short-side/no-fill cases).
- Follow-up candidate: refine pattern-backtest financial summary semantics in shared persistence schema if owner requires richer financial outputs.
- Follow-up candidate: align pattern persistence graph-point cash/position/equity to candle-timed fills for richer dashboard trace fidelity.
- Non-FVG deterministic synthetic entry fixtures for broader pattern backtest determinism.
- Liquidity indicator implementation.
- Bid-Ask spread indicator implementation.

## Backend/Frontend Candidates
- Follow-up candidate: add a dedicated frontend unit/component test harness for dashboard helper/rendering behavior if future UI work continues.
- API contract evolution for any future backend/frontend coordination beyond the current read-only dashboard.
- Backend API extensions only when assigned by a future backend task.
- Frontend dashboard extensions only when assigned by a future frontend task.

## Deferred Verification
- Local Docker runtime verification for previously completed Docker-related tasks in a Docker-capable environment.
- Backend FastAPI route tests require a Python environment with `fastapi` installed.

## Ledger Maintenance
- Completed (2026-05-24): Reconciled root backlog archive pointers to fixed 50-task ranges and moved Tasks 088-100 entries into `docs/ledger_archives/backlog_task_051_100.md`.
