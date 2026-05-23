# Project History (Recent Window)

This file keeps recent completion context only.
Older history is preserved in fixed 50-task segmented archives:

- `docs/ledger_archives/project_history_task_001_050.md`
- `docs/ledger_archives/project_history_task_051_100.md`

## Recent Completion Window (Tasks 101-148)
- 2026-05-22: Completed Task 101 `DOCKER_COMPOSE_BACKTEST_PROFILE_CANONICALIZATION`; switched Docker Compose backtest profile to canonical strategy runner CLI and aligned websocket-ingestion compose assertion to env-interpolated `DATABASE_URL` semantics.
- 2026-05-22: Completed Task 102 `CANONICAL_PATTERN_ACTION_BUILDER_CLI_INTEGRATION`; integrated canonical pattern action builder into strategy PostgreSQL CLI action assembly and added regression test coverage.
- 2026-05-22: Completed Task 103 `STRATEGY_PERSISTENCE_MULTIFILL_GRAPH_MARKERS`; made graph-point marker metadata multi-fill safe for same-timestamp executions while keeping scalar marker compatibility.
- 2026-05-22: Completed Task 104 `STRATEGY_POSTGRES_RUNNER_CLI_REFACTOR`; split canonical strategy CLI into focused core/entry modules and kept contract-compatible behavior with updated CLI tests.
- 2026-05-22: Completed Task 105 `README_AND_API_CONTRACT_CANONICAL_BACKTEST_REFRESH`; updated README/API/backend warning text to prefer canonical strategy backtest CLI and classify placeholder-neutral warnings as older compatibility-run diagnostics.
- 2026-05-22: Completed Task 106 `LEGACY_PUBLIC_API_PRUNING`; pruned deprecated package-level backtesting exports from `quant_bitcoin.backtesting.__all__`, migrated tests/docs to explicit compatibility module imports, and kept canonical strategy-engine symbols as primary public imports.
- 2026-05-22: Completed Task 107 `STRATEGY_EXECUTION_MAPPING_RETIREMENT`; removed long-only mapping helper module and migrated mapping tests to canonical long/short strategy action helper coverage.
- 2026-05-22: Completed Task 108 `PATTERNS_PUBLIC_EXPORT_BOUNDARY_CLEANUP`; migrated pattern-risk internal and test imports to canonical `quant_bitcoin.risk` ownership while keeping compatibility shims explicit.
- 2026-05-22: Completed Task 109 `FVG_CACHE_NAMING_OR_PATTERN_CACHE_REGISTRY`; renamed cache ownership to `fvg_detection_cache`, migrated internal imports/tests, and preserved legacy import compatibility via re-export shim.
- 2026-05-22: Completed Task 110 `PATTERN_STRATEGY_OUTPUT_SCHEMA_ENRICHMENT`; enriched strategy CLI JSON executions/events/diagnostics, added warning classification for no-fills/invalid-risk/open-position cases, and extended CLI persistence tests.
- 2026-05-22: Added Task 111 `CANONICAL_PATTERN_LIFECYCLE_BACKTEST_INTEGRATION` task document from owner requirements; no implementation executed in that step.
- 2026-05-22: Completed Task 111 execution-price and entry-fill contract integration; added optional `StrategyAction.requested_price`, engine explicit-price execution with validation/fallback, and pattern action-builder price propagation with regression tests.
- 2026-05-22: Added Tasks 112-118 task documents as separate owner-requested tasks; no implementation executed in that creation step.
- 2026-05-22: Revalidated Task 111 via targeted regression suite (`test_strategy_engine`, `test_pattern_action_builder`, `test_entry_simulation`); all tests passed.
- 2026-05-23: Completed Task 112 `EXECUTION_PRICE_AND_ENTRY_FILL_CONTRACT`; confirmed requested-price execution path for long/short entry/exit actions, close fallback behavior, and pattern action-builder/entry-simulation integration.
- 2026-05-23: Completed Task 113 `FVG_NO_LOOKAHEAD_CACHE_CORRECTION`; corrected optimized FVG cache path to evaluate with current-index candle prefixes only and added no-lookahead regression coverage.
- 2026-05-23: Completed Task 114 `INTRABAR_STOP_TARGET_AMBIGUITY_POLICY`; made stop exits emit explicit intrabar precedence metadata and preserved conservative stop-first resolution.
- 2026-05-23: Completed Task 115 `BACKTEST_METRICS_AND_PERSISTENCE_METADATA_QUALITY`; separated filled vs skipped/blocked execution metrics, aligned legacy `trade_count`, and enriched persistence trade metadata.
- 2026-05-23: Completed Task 116 `PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS`; added default VALID-only pattern filters with optional weak/score/risk-reward gating and engine-owned quantity handling.
- 2026-05-23: Completed Task 117 `SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS`; corrected short close win/loss counting and validated summary/CLI metadata limitations for unsupported margin economics.
- 2026-05-23: Completed Task 118 `TRANSACTION_COST_CLI_AND_ACCOUNTING_INTEGRATION`; added canonical CLI transaction-cost args/validation/liquidity-role parsing and surfaced transaction-cost metadata.
- 2026-05-23: Completed Task 119 `LEDGER_RECHECK_TASKS_111_118`; audited Tasks 111-118 in STATUS/BACKLOG/PROJECT_HISTORY and updated root status pointers.
- 2026-05-23: Added Tasks 120-127 task documents from owner-provided optimization pack requirements; no implementation executed in that creation step.
- 2026-05-23: Completed Task 120 `PROFILE_CANONICAL_PATTERN_BACKTEST_RUNTIME`; added optional `--profile` timing/cProfile instrumentation and no-persist profiling regression coverage.
- 2026-05-23: Completed Task 121 `SHARED_INDICATOR_CACHE_AND_AT_INDEX_PATTERN_DETECTION`; generalized shared indicator cache builder, added Order Block at-index detection, and added rolling-prefix parity coverage.
- 2026-05-23: Completed Task 122 `PIVOT_HEAVY_PATTERN_CANDIDATE_PRUNING`; added deterministic recent-pivot windows and candidate caps for pivot-heavy detectors.
- 2026-05-23: Completed Task 123 `HOT_LOOP_DATAFRAME_AND_PERSISTENCE_IO_CLEANUP`; removed avoidable deep copies in canonical pattern strategy/action-builder hot paths with no-mutation coverage.
- 2026-05-23: Completed Task 124 `PERSIST_BACKTEST_RUNTIME_METADATA`; added canonical runtime payload to strategy CLI stdout and persisted it under `backtest_runs.metadata.runtime`.
- 2026-05-23: Completed Task 125 `DASHBOARD_RUNTIME_DISPLAY`; exposed optional runtime summary fields in API serialization and dashboard UI with backend unit coverage.
- 2026-05-23: Completed Task 126 `STRATEGY_EXPLANATION_METADATA_ALGORITHM_AND_SL_TP_RATIONALE`; added strategy explanation metadata, persistence, and dashboard display.
- 2026-05-23: Completed Task 127 `PATTERN_BACKTEST_PERFORMANCE_REGRESSION_TESTS`; added fixture-based 400-candle runtime regression tests across supported patterns.
- 2026-05-23: Completed Task 128 `STRATEGY_CLI_JSON_TIMESTAMP_SERIALIZATION_FIX`; added recursive JSON-safe serialization and corrected strategy/pattern CLI exception logging calls.
- 2026-05-23: Completed Task 129 `DIAMOND_STATUS_FILTERING_INVESTIGATION`; reproduced Diamond failures, clarified VALID-only default filter behavior, and aligned tests.
- 2026-05-23: Completed Task 130 `STATE_RECONCILIATION_AND_EXECUTION_TASK_BUNDLE`; confirmed Tasks 131-138 as the next task window and recorded Task 138 as live-execution-blocked.
- 2026-05-23: Completed Task 131 `MULTI_INTERVAL_BINANCE_CANDLE_ORCHESTRATION`; added interval-list parsing, multi-interval backfill runner/CLI output, invalid-interval preflight failure, and regression coverage.
- 2026-05-23: Completed Task 132 `BACKTEST_PERFORMANCE_METRICS_FROM_EQUITY_CURVE`; added equity-curve performance metrics, interval-aware annualization, CLI metadata exposure, and persistence propagation.
- 2026-05-23: Completed Task 133 `ORDER_INTENT_AND_PAPER_EXECUTION_CONTRACT`; added order-intent/execution-report/fill models, deterministic action conversion, and paper execution client.
- 2026-05-23: Completed Task 134 `REALTIME_CANDLE_CLOSE_STRATEGY_TRIGGER_AND_PAPER_EXECUTION`; added closed-candle realtime runner with idempotent source/symbol/interval/open_time/strategy handling.
- 2026-05-23: Completed Task 135 `PRODUCT_SPECIFIC_SHORT_POLICY_AND_EXECUTION_BOUNDARIES`; added ProductMode policy contract, deterministic spot short rejection, and policy integration tests.
- 2026-05-23: Completed Task 136 `BINANCE_SPOT_TESTNET_EXECUTION_CLIENT_SAFETY_AND_POLICY`; added testnet-only signed Spot order client, endpoint allowlist, fail-closed credentials, fake HTTP mapping, and safety tests.
- 2026-05-23: Completed Task 137 `EXECUTION_FILL_RECONCILIATION_AND_ACTUAL_COST_METRICS`; added execution-quality reconciliation for VWAP, slippage, commission, and simulated-vs-actual deltas.
- 2026-05-23: Task 138 `GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL` inspected but not implemented because it requires explicit owner approval for live order execution.
- 2026-05-23: Created Task 139 `GITIGNORE_ARTIFACT_CLEANUP_AND_PR_RESCOPE`; no implementation executed in the creation step.
- 2026-05-23: Completed Task 139 `GITIGNORE_ARTIFACT_CLEANUP_AND_PR_RESCOPE`; added ignore rules, created a clean scoped branch for Tasks 130-139, and left unrelated tracked frontend changes unstaged.
- 2026-05-23: Created and format-checked Tasks 140-148 against `tasks/TASK_TEMPLATE.md`; set Task 140 active.
- 2026-05-23: Completed Task 140 `POSITION_SIZING_POLICY_CONTRACT`; added explicit backtest position-sizing/margin policy models with validation and backward-compatible `trade_quantity` behavior.
- 2026-05-23: Completed Task 141 `LONG_CASH_BOUNDED_ENTRY_EXECUTION`; made long entries explicitly cash-bounded with deterministic resize/block metadata and high-price regression coverage.
- 2026-05-23: Completed Task 142 `SHORT_BUYING_POWER_POLICY`; made default simulated shorts cash-bounded so oversized short exposure is resized or blocked.
- 2026-05-23: Completed Task 143 `SIMULATED_MARGIN_INITIAL_MARGIN_GUARD`; added opt-in backtest-only simulated-margin initial-margin checks with leverage metadata.
- 2026-05-23: Completed Task 144 `ACCOUNT_STATE_VISIBILITY_FIELDS`; added additive account-state fields for free cash, margin used, locked short proceeds, available buying power, and cash semantics.
- 2026-05-23: Completed Task 145 `CANONICAL_CLI_PERSISTENCE_WIRING_FOR_SIZING_MARGIN`; wired sizing and simulated-margin options through CLI, JSON output, and persistence metadata.
- 2026-05-23: Completed Task 146 `BACKTEST_CASH_EQUITY_DISPLAY_AND_API_SEMANTICS`; updated API contract and frontend display/types to distinguish cash balance from free cash.
- 2026-05-23: Completed Task 147 `BACKTEST_ACCOUNTING_REFACTOR_AFTER_CASH_AND_MARGIN`; localized sizing, affordability, margin, and account-state helper logic without changing public result fields.
- 2026-05-23: Completed Task 148 `BACKTEST_ACCOUNTING_DOCUMENTATION_CONSISTENCY`; reconciled README, architecture/API/dashboard docs, task checklists, and ledgers after Tasks 140-147.

## Active Historical Notes
- Live trading approval/credential policy/endpoint allowlist/kill-switch design remains unresolved and blocks Task 138.
- Docker runtime verification remains environment-dependent where Docker is unavailable.
- Backend FastAPI route tests require a Python environment with `fastapi` installed.
- 2026-05-24: Ledger range cleanup reconciled root `BACKLOG.md` and `PROJECT_HISTORY.md` with the fixed 50-task archive rule by replacing partial archives with `*_task_051_100.md` archives and keeping root ledgers focused on Tasks 101-148.
