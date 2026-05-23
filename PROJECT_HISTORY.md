# Project History (Recent Window)

This file keeps recent completion context only.
Older history is preserved in segmented archives:

- `docs/ledger_archives/project_history_task_001_050.md`
- `docs/ledger_archives/project_history_task_051_087.md`

## Recent Completion Window (Tasks 088-099)
- 2026-05-22: Completed Task 088 `STRATEGY_ACTION_LONG_SHORT_CONTRACT`; expanded strategy-action long/short semantics and compatibility execution fields.
- 2026-05-22: Completed Task 089 `STRATEGY_ENGINE_LONG_SHORT_COST_ACCOUNTING`; added deterministic long/short cost-aware accounting and execution-cost metadata.
- 2026-05-22: Completed Task 090 `RSI_CANONICAL_ENGINE_MIGRATION`; migrated RSI PostgreSQL CLI path to canonical strategy engine with compatibility mappings.
- 2026-05-22: Completed Task 091 `PATTERN_STRATEGY_LONG_SHORT_ENABLEMENT`; enabled bullish/bearish long/short action emission.
- 2026-05-22: Completed Task 092 `PATTERN_RISK_EXIT_ACTION_BUILDER`; added canonical pattern risk/exit simulation-to-action conversion.
- 2026-05-22: Completed Task 093 `ENTRY_FILL_INTRABAR_INTEGRATION`; integrated entry-fill/intrabar outcomes and no-fill diagnostics into action generation.
- 2026-05-22: Completed Task 094 `PATTERN_DETECTION_PERFORMANCE_OPTIMIZATION`; added FVG cache/local-index detection path and parity tests.
- 2026-05-22: Completed Task 095 `CANONICAL_CLI_AND_PERSISTENCE_MIGRATION`; unified persistence adapter usage for canonical strategy flows.
- 2026-05-22: Completed Task 096 `LEGACY_DEPRECATED_BACKTEST_CLEANUP`; added explicit deprecation markers and canonical CLI guidance.
- 2026-05-22: Completed Task 097 `CANONICAL_BACKTEST_REGRESSION_AND_RESEARCH_TEST_SUITE`; added persistence-regression tests and verification notes.
- 2026-05-22: Completed Task 098 `TASK_STATUS_LEDGER_SYNCHRONIZATION`; reconciled task-file statuses with ledgers and confirmed Task 099 as next active task.
- 2026-05-22: Completed Task 099 `LEDGER_SEGMENTATION_AND_TEMPLATE_ENFORCEMENT`; segmented root ledgers into recent windows + deterministic archives and enforced task-template rule.

- 2026-05-22: Task 099 follow-up review fix added explicit 50-task archive-chunk policy to `AGENTS.md` for `BACKLOG.md`/`PROJECT_HISTORY.md` segmentation governance.

- 2026-05-22: Completed Task 100 `TASK_LEDGER_COMPLETION_RECONCILIATION_FOLLOWUP`; reconciled Task 098 file status with root ledgers and confirmed no active implementation task pending owner assignment of Task 101+.

- 2026-05-22: Completed Task 101 `DOCKER_COMPOSE_BACKTEST_PROFILE_CANONICALIZATION`; switched Docker Compose backtest profile to canonical strategy runner CLI and aligned websocket-ingestion compose assertion to env-interpolated DATABASE_URL semantics.

- 2026-05-22: Completed Task 106 `LEGACY_PUBLIC_API_PRUNING`; pruned deprecated package-level backtesting exports from `quant_bitcoin.backtesting.__all__`, migrated tests/docs to explicit compatibility module imports, and kept canonical strategy-engine symbols as primary public imports.

## Active Historical Notes
- Live trading approval/credential policy/endpoint allowlist/kill-switch design remains unresolved and blocking any real-execution phase.
- Docker runtime verification remains environment-dependent where Docker is unavailable.

- 2026-05-22: Completed Task 102 `CANONICAL_PATTERN_ACTION_BUILDER_CLI_INTEGRATION`; integrated canonical pattern action builder into strategy PostgreSQL CLI action assembly and added regression test coverage.

- 2026-05-22: Completed Task 103 `STRATEGY_PERSISTENCE_MULTIFILL_GRAPH_MARKERS`; made graph-point marker metadata multi-fill safe for same-timestamp executions while keeping scalar marker compatibility.
- 2026-05-22: Completed Task 104 `STRATEGY_POSTGRES_RUNNER_CLI_REFACTOR`; split canonical strategy CLI into focused core/entry modules and kept contract-compatible behavior with updated CLI tests.
- 2026-05-22: Completed Task 105 `README_AND_API_CONTRACT_CANONICAL_BACKTEST_REFRESH`; updated README/API/backend warning text to prefer canonical strategy backtest CLI and classify placeholder-neutral warnings as older compatibility-run diagnostics.


- 2026-05-22: Completed Task 107 `STRATEGY_EXECUTION_MAPPING_RETIREMENT`; removed long-only mapping helper module and migrated mapping tests to canonical long/short strategy action helper coverage.

- 2026-05-22: Completed Task 108 `PATTERNS_PUBLIC_EXPORT_BOUNDARY_CLEANUP`; migrated pattern-risk internal and test imports to canonical `quant_bitcoin.risk` ownership while keeping compatibility shims explicit.

- 2026-05-22: Completed Task 109 `FVG_CACHE_NAMING_OR_PATTERN_CACHE_REGISTRY`; renamed cache ownership to `fvg_detection_cache`, migrated internal imports/tests, and preserved legacy import compatibility via re-export shim.

- 2026-05-22: Completed Task 110 `PATTERN_STRATEGY_OUTPUT_SCHEMA_ENRICHMENT`; enriched strategy CLI JSON executions/events/diagnostics, added warning classification for no-fills/invalid-risk/open-position cases, and extended CLI persistence tests.
- 2026-05-22: Added Task 111 `CANONICAL_PATTERN_LIFECYCLE_BACKTEST_INTEGRATION` task document from owner requirements; no implementation executed in this step.
- 2026-05-22: Completed Task 111 execution-price and entry-fill contract integration; added optional StrategyAction requested_price, engine explicit-price execution with validation+fallback, and pattern action-builder price propagation with regression tests.
- 2026-05-22: Added Task 112 `EXECUTION_PRICE_AND_ENTRY_FILL_CONTRACT` task document as a separate task per owner request; no implementation executed in this step.
- 2026-05-22: Added Task 113 `FVG_NO_LOOKAHEAD_CACHE_CORRECTION` task document as a separate task per owner request; no implementation executed in this step.
- 2026-05-22: Added Task 114 `INTRABAR_STOP_TARGET_AMBIGUITY_POLICY` task document as a separate task per owner request; no implementation executed in this step.
- 2026-05-22: Added Task 115 `BACKTEST_METRICS_AND_PERSISTENCE_METADATA_QUALITY` task document as a separate task per owner request; no implementation executed in this step.
- 2026-05-22: Added Task 116 `PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS` task document as a separate task per owner request; no implementation executed in this step.
- 2026-05-22: Added Task 117 `SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS` task document as a separate task per owner request; no implementation executed in this step.
- 2026-05-22: Added Task 118 `TRANSACTION_COST_CLI_AND_ACCOUNTING_INTEGRATION` task document as a separate task per owner request; no implementation executed in this step.
- 2026-05-22: Revalidated Task 111 `CANONICAL_PATTERN_LIFECYCLE_BACKTEST_INTEGRATION` via targeted regression suite (`test_strategy_engine`, `test_pattern_action_builder`, `test_entry_simulation`); all tests passed and current active task remains Task 118.

- 2026-05-23: Completed Task 118 `TRANSACTION_COST_CLI_AND_ACCOUNTING_INTEGRATION`; added canonical CLI transaction-cost args/validation/liquidity-role parsing, wired cost config into strategy engine, and surfaced transaction-cost metadata in summary/persistence-backed strategy parameters with passing targeted regression tests.
- 2026-05-23: Completed Task 117 `SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS`; corrected short-close win/loss counting to use all closing executions, added deterministic short realized-PnL/allow_short=False regression tests, and validated summary/CLI metadata limitations for unsupported margin economics.


- 2026-05-23: Completed Task 116 `PATTERN_ENTRY_FILTERING_AND_SIZING_CONTROLS`; added default VALID-only pattern filters with optional weak/score/risk-reward gating, removed hardcoded pattern entry quantity in favor of engine trade_quantity, and added CLI/config+regression coverage for optional quantity overrides.

- 2026-05-23: Completed Task 115 `BACKTEST_METRICS_AND_PERSISTENCE_METADATA_QUALITY`; separated filled vs skipped/blocked execution metrics in summary metadata, aligned legacy trade_count with filled executions, enriched persistence trade metadata (lifecycle+cost fields), and added targeted accounting/persistence regression coverage.
- 2026-05-23: Completed Task 114 `INTRABAR_STOP_TARGET_AMBIGUITY_POLICY`; made stop exits emit explicit intrabar precedence metadata, preserved conservative stop-first resolution for ambiguous same-candle stop/target touches, and added long/short + action-builder regression coverage.

- 2026-05-23: Completed Task 113 `FVG_NO_LOOKAHEAD_CACHE_CORRECTION`; corrected optimized FVG cache path to evaluate with current-index candle prefixes only and added regression coverage proving future fill/break candles cannot change historical event output.
- 2026-05-23: Completed Task 112 `EXECUTION_PRICE_AND_ENTRY_FILL_CONTRACT`; confirmed engine requested-price execution path for long/short entry/exit actions, preserved close fallback when requested_price is absent/invalid, and revalidated pattern action-builder + entry-simulation integration via targeted tests.


- 2026-05-23: Completed Task 119 `LEDGER_RECHECK_TASKS_111_118`; audited Tasks 111-118 in STATUS/BACKLOG/PROJECT_HISTORY and updated root status phase/step/goal pointers to align with latest completed task (Task 118).
- 2026-05-23: Added Task 120 `PROFILE_CANONICAL_PATTERN_BACKTEST_RUNTIME` task document from owner-provided optimization pack requirements; no implementation executed in this step.
- 2026-05-23: Added Task 121 `SHARED_INDICATOR_CACHE_AND_AT_INDEX_PATTERN_DETECTION` task document from owner-provided optimization pack requirements; no implementation executed in this step.
- 2026-05-23: Added Task 122 `PIVOT_HEAVY_PATTERN_CANDIDATE_PRUNING` task document from owner-provided optimization pack requirements; no implementation executed in this step.
- 2026-05-23: Added Task 123 `HOT_LOOP_DATAFRAME_AND_PERSISTENCE_IO_CLEANUP` task document from owner-provided optimization pack requirements; no implementation executed in this step.
- 2026-05-23: Added Task 124 `PERSIST_BACKTEST_RUNTIME_METADATA` task document from owner-provided optimization pack requirements; no implementation executed in this step.
- 2026-05-23: Added Task 125 `DASHBOARD_RUNTIME_DISPLAY` task document from owner-provided optimization pack requirements; no implementation executed in this step.
- 2026-05-23: Added Task 126 `STRATEGY_EXPLANATION_METADATA_ALGORITHM_AND_SL_TP_RATIONALE` task document from owner-provided optimization pack requirements; no implementation executed in this step.
- 2026-05-23: Added Task 127 `PATTERN_BACKTEST_PERFORMANCE_REGRESSION_TESTS` task document from owner-provided optimization pack requirements; no implementation executed in this step.
- 2026-05-23: Completed Task 120 `PROFILE_CANONICAL_PATTERN_BACKTEST_RUNTIME`; added optional `--profile` timing/cProfile instrumentation to canonical strategy runner output (`load/build/engine/persist/json/total` + pattern timing + top cumulative functions) and added no-persist profiling regression coverage.

- 2026-05-23: Completed Task 121 `SHARED_INDICATOR_CACHE_AND_AT_INDEX_PATTERN_DETECTION`; generalized shared indicator cache builder for pattern detectors, added Order Block at-index detection with early seen-event suppression, wired canonical runner to reuse cache/evaluate_at for Order Block, and added rolling-prefix parity regression coverage for optimized Order Block path.
- 2026-05-23: Completed Task 122 `PIVOT_HEAVY_PATTERN_CANDIDATE_PRUNING`; added deterministic recent-pivot windows and candidate caps for Trendline Break/Cup and Handle/Diamond/Adam and Eve detection paths and validated existing pattern fixtures via targeted regression suite.

- 2026-05-23: Completed Task 123 `HOT_LOOP_DATAFRAME_AND_PERSISTENCE_IO_CLEANUP`; removed avoidable deep copies in canonical pattern strategy/action-builder hot paths, preserved caller input immutability with explicit regression coverage, and revalidated canonical pattern runner optimization suites.

- 2026-05-23: Completed Task 124 `PERSIST_BACKTEST_RUNTIME_METADATA`; added canonical runtime payload (`runtime_schema_version`, strategy/candle context, phase timings, pattern timings) to strategy CLI stdout and persisted it under `backtest_runs.metadata.runtime` without changing deterministic run-key construction, with targeted CLI/persistence regression tests.

- 2026-05-23: Completed Task 125 `DASHBOARD_RUNTIME_DISPLAY`; exposed optional runtime summary fields in `/api/backtest-runs` serialization, updated dashboard run list/runtime breakdown UI with human-readable duration formatting and missing-runtime fallbacks, and added backend service runtime-summary unit coverage.

- 2026-05-23: Completed Task 126 `STRATEGY_EXPLANATION_METADATA_ALGORITHM_AND_SL_TP_RATIONALE`; added pattern strategy explanation metadata builder for all supported patterns, persisted explanation payload under `strategy_configs.metadata.explanation`, rendered dashboard explanation cards with safe fallback for legacy runs missing metadata, and validated via targeted strategy/persistence/backend tests.

- 2026-05-23: Completed Task 127 `PATTERN_BACKTEST_PERFORMANCE_REGRESSION_TESTS`; added fixture-based 400-candle runtime regression tests across all supported patterns plus optional `@pytest.mark.benchmark` smoke output reporting pattern/candle/runtime/event/action counts.

- 2026-05-23: Completed Task 128 `STRATEGY_CLI_JSON_TIMESTAMP_SERIALIZATION_FIX`; added recursive JSON-safe serialization for canonical strategy CLI stdout payloads, corrected strategy/pattern CLI exception logging calls, and covered timestamp metadata serialization plus logger signature regressions. Targeted CLI tests passed; full pytest surfaced two unrelated Diamond strategy status-filtering expectation failures.

- 2026-05-23: Added Task 129 `DIAMOND_STATUS_FILTERING_INVESTIGATION` task document from owner assignment; no implementation executed in this step.

- 2026-05-23: Completed Task 129 `DIAMOND_STATUS_FILTERING_INVESTIGATION`; reproduced failing Diamond bullish/bearish tests, confirmed default VALID-only status-filter behavior, aligned Diamond test fixtures to set explicit `pattern_status="VALID"`, and added regression coverage for missing-status skip behavior with passing targeted Diamond strategy tests.
- 2026-05-23: Completed Task 130 `STATE_RECONCILIATION_AND_EXECUTION_TASK_BUNDLE`; confirmed created Tasks 131-138 as the next task window, recorded Task 138 as live-execution-blocked pending explicit owner approval, and set Task 131 as the next implementation task.
- 2026-05-23: Completed Task 131 `MULTI_INTERVAL_BINANCE_CANDLE_ORCHESTRATION`; added order-preserving interval-list parsing, multi-interval backfill runner/CLI output, invalid-interval preflight failure, and regression coverage for per-interval execution plus candle identity separation.
- 2026-05-23: Completed Task 132 `BACKTEST_PERFORMANCE_METRICS_FROM_EQUITY_CURVE`; added pure equity-curve performance metrics, interval-aware annualization, CLI summary metadata exposure, persistence metadata propagation, and targeted metric/CLI/persistence tests.
- 2026-05-23: Completed Task 133 `ORDER_INTENT_AND_PAPER_EXECUTION_CONTRACT`; added canonical order-intent/execution-report/fill models, deterministic strategy-action conversion, paper execution client with dry-run and simulated-short controls, and execution/backtesting regression coverage.
- 2026-05-23: Completed Task 134 `REALTIME_CANDLE_CLOSE_STRATEGY_TRIGGER_AND_PAPER_EXECUTION`; added closed-candle realtime runner using stored candles as strategy input, idempotent source/symbol/interval/open_time/strategy handling, dry-run/paper execution handoff, and WebSocket/execution regression coverage.
- 2026-05-23: Completed Task 135 `PRODUCT_SPECIFIC_SHORT_POLICY_AND_EXECUTION_BOUNDARIES`; added ProductMode policy contract, deterministic spot short rejection, short-model limitation metadata, and paper/realtime policy integration tests while preserving backtest short simulation.
- 2026-05-23: Completed Task 136 `BINANCE_SPOT_TESTNET_EXECUTION_CLIENT_SAFETY_AND_POLICY`; added testnet-only signed Spot order client, endpoint allowlist, environment credential fail-closed handling, fake HTTP response mapping, and safety tests proving no live URL/default or spot short request path is used.
- 2026-05-23: Completed Task 137 `EXECUTION_FILL_RECONCILIATION_AND_ACTUAL_COST_METRICS`; added execution-quality reconciliation for VWAP, side-aware slippage, commission asset preservation, quote-commission availability, simulated-vs-actual deltas, and realtime output serialization with passing execution/persistence/backtesting tests.
- 2026-05-23: Task 138 `GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL` inspected but not implemented because the task requires explicit owner approval for live order execution before code execution; live trading remains blocked.
