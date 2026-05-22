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

