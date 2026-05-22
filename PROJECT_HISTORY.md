# Project History (Historical Reference)

This file archives completed and historical project status details.
It is **not** the active execution dashboard. For active work, use `STATUS.md`.

## Archived Active-State Snapshot (Before Ledger Split)
- Phase: 61 (Status Ledger Split Task Definition).
- Step: Task `STATUS_LEDGER_SPLIT` document creation.
- Goal: define split from `STATUS.md` into `STATUS.md` + `PROJECT_HISTORY.md` + `BACKLOG.md`.
- Active task at that time: planning-only `tasks/STATUS_LEDGER_SPLIT.md`.

## Completed Step History (Detailed)
- Task 058: Pattern Backtest All Implemented Pattern Selection implementation.
  - Added focused pattern registry for `FAIR_VALUE_GAP`, `TRENDLINE_BREAK`, `ORDER_BLOCK`, `CUP_AND_HANDLE`, `DIAMOND`, `ADAM_AND_EVE`.
  - Preserved `FAIR_VALUE_GAP` default and one-pattern-per-run validation.
  - Preserved deterministic strategy metadata and no live-order behavior.
  - Verification included targeted tests, full `pytest`, CLI help, and `git diff --check`.
- Task 057 implementation:
  - Clarified `quant-bitcoin-pattern-backtest --help` wording.
  - Default JSON strategy metadata renamed to `FAIR_VALUE_GAP_PATTERN_STRATEGY`.
  - Added tested `--pattern FAIR_VALUE_GAP` seam with unsupported-pattern rejection.
- Task 057 task-document creation completed.
- Task 056 implementation:
  - Added `quant-bitcoin-pattern-backtest` script entrypoint via `pattern_postgres_runner_cli.py`.
  - Restricted to completed `1m` candles from PostgreSQL provider.
  - Reused Task 055 backtest workflow and emitted deterministic JSON summary.
  - Added CLI tests and verified script registration; direct script invocation depended on package installation constraints in this environment.

## Completed Phase/Checklist Ledger (Archived)
- Foundation completed and verified: Python setup, market-data contract, CSV provider, RSI strategy, basic backtest, paper trader.
- Data ingestion/storage evolution completed: Binance downloader, PostgreSQL backfill, WebSocket ingestion, bounded/unbounded ingestion workflows, Docker service task implementation (with local runtime verification deferred where environment-limited).
- Backtest persistence and read-model evolution completed for tasks 021-025.
- Indicator/pattern document intake, mechanical definitions, and implemented indicator/pattern batches completed through tasks 027-055 as tracked in prior `STATUS.md` history.
- Pattern CLI evolution completed through tasks 056-058.
- Runtime error logging task 059 completed and verified.
- Task 060 implementation completed and verified for supported PostgreSQL backtest CLIs.
  - Added default persistence (with `--no-persist` opt-out) for `quant-bitcoin-pattern-backtest`.
  - Added deterministic pattern backtest persistence payload mapping into existing run/result/trade/graph persistence boundaries.
  - Added/updated pattern CLI persistence tests including persisted `backtest_run_id` and no-persist path behavior.

- Task 061 completed (documentation/process only):
  - Added explicit AGENTS policy requiring task-completion synchronization across `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
  - Confirmed backlog candidate semantics and synchronized current candidate items.
  - Preserved `STATUS.md` as active-state pointer and `PROJECT_HISTORY.md` as historical ledger.

## Historical Open-Question / Context Archive
- Live trading approval, credential policy, sandbox/testnet policy, endpoint allowlist, and kill-switch design remained unresolved and blocking for any real execution phase.
- Task 024 decisions archived:
  - `db/init/001_schema.sql` as first-start schema source of truth.
  - `db/changes/` reserved for existing-database state-change SQL.
  - Initialization executes managed command files; runtime DML remains application-owned.
- Task 025 intake-process archive:
  - Owner-provided indicator documents saved under `tasks/indicators/`.
  - Pattern source documents saved under `tasks/patterns/` when explicitly assigned.
- Pattern strategy assumptions archive:
  - `FAIR_VALUE_GAP` default.
  - One explicit supported pattern per run.
  - One simulated open position at a time.
  - Entry on confirmation candle, exit check from next completed candle.
  - Same-candle event order by pattern type, direction, then event id.
- Liquidity and bid-ask spread filters remained unavailable as reusable modules at that snapshot.

## Historical Verification Notes
- Repeated completed-task verification commonly included targeted unit/integration tests, full `pytest`, CLI help checks, and `git diff --check`.
- Docker runtime startup verification remained deferred where Docker was unavailable in the cloud environment.

- Task 062 completed (documentation/process only):
  - Added `docs/15_RESEARCH_PROTOCOL.md` defining formal research lifecycle states from `IDEA` through `WALK_FORWARD_VALIDATED` and terminal outcomes (`PAPER_ONLY_CANDIDATE`, `RESEARCH_ONLY`, `REJECTED`).
  - Added governance for train/validation/test/holdout separation, pre-declared parameter search spaces, multiple-testing controls, baseline comparisons, and required net assumptions (fees, spread, slippage, fill).
  - Reiterated that research evidence is insufficient for live trading and preserved existing live-trading blocker conditions.

- Task 063 completed (implementation + tests):
  - Added `quant_bitcoin/market_data/data_quality.py` with deterministic `audit_standard_candles(...)` plus config/report/issue/severity dataclasses.
  - Added checks for standard schema columns, timestamp parsing/order, duplicates, expected interval gaps, OHLC validation, volume validation, zero-volume metrics, and optional expected boundary-gap warnings.
  - Added `tests/market_data/test_data_quality.py` covering valid data, missing columns, unsorted timestamps, duplicates, interval gaps, invalid OHLC, negative/zero volume, empty input handling, and non-mutation of caller input.

- Task 064 completed (implementation + tests):
  - Added `quant_bitcoin/backtesting/costs.py` with pure transaction cost contract: `ExecutionSide`, `LiquidityRole`, `TransactionCostConfig`, `TransactionCostBreakdown`, and deterministic helpers for basis-point conversion, effective execution price, and gross-vs-net cost breakdown.
  - Added validation for non-negative finite config values and positive finite price/quantity values, plus optional volatility-adjusted slippage with minimum slippage floor.
  - Added `tests/backtesting/test_costs.py` covering config validation, BUY/SELL effective-price directionality, maker/taker fee behavior, spread/slippage accounting, volatility-adjusted slippage, and input validation.


- Task 065 completed (implementation + tests):
  - Added `quant_bitcoin/patterns/entry_simulation.py` with pure pattern entry contract types (`PatternEntryMode`, `PatternEntryStatus`, `PatternEntryConfig`, `PatternEntryPlan`, `PatternEntrySimulationResult`) and deterministic helpers for event-based plan creation and completed-candle entry fill simulation.
  - Added market fill modes (confirmation-close and next-open), limit fill modes (entry reference, midpoint, boundary, custom price), deterministic max-wait no-fill handling, required candle schema/sort validation, and invalid-plan result path for missing event fields.
  - Added `tests/patterns/test_entry_simulation.py` covering market/limit fills, no-fill windows, cancelled expiry behavior, missing columns, unsorted candles, invalid event-field behavior, and non-mutation of caller input.

- Task 066 completed (implementation + tests + docs):
  - Added `docs/18_INTRABAR_SEQUENCING_POLICY.md` documenting OHLC intrabar ambiguity impact, policy mode semantics, and conservative-promotion guidance.
  - Added `quant_bitcoin/backtesting/intrabar_policy.py` with deterministic pure intrabar touch detection and ambiguity resolution contract (`IntrabarSequencingMode`, `IntrabarTouch`, `IntrabarDecision`, `IntrabarPolicyConfig`).
  - Added `tests/backtesting/test_intrabar_policy.py` covering long/short ambiguous same-candle outcomes, conservative/optimistic/stress modes, skip-ambiguous behavior, and input validation.

- Task 067 completed (implementation + tests):
  - Added `quant_bitcoin/backtesting/equity_curve.py` with pure reusable equity-curve dataclasses and functions for deterministic candle-by-candle cash/position/equity tracking and drawdown calculation from high-water mark.
  - Added compatibility for `BacktestTrade` and generic trade-like rows (`timestamp`, `side`/`signal`, `price`, `quantity`, optional `cost`) while preserving non-mutation of caller inputs and strict standard-candle validation.
  - Added `tests/backtesting/test_equity_curve.py` covering no-trade curves, mark-to-market long behavior, buy/sell close behavior, deterministic drawdown, missing columns, unsorted timestamps, empty-candle config handling, and non-mutation checks.


- Task 068 completed (implementation + tests + docs):
  - Added `quant_bitcoin/backtesting/pattern_event_study.py` with reusable event-study dataclasses (`PatternEventStudyRecord`, `PatternForwardLabelConfig`, `PatternForwardLabel`, `PatternEventStudyDataset`) and deterministic conversion helpers (`pattern_event_to_study_record`, `records_to_dataframe`).
  - Added `docs/19_PATTERN_EVENT_STUDY_SCHEMA.md` documenting boundaries between detection/event-study/backtest/promotion, canonical event and future-label fields, and no-look-ahead requirements.
  - Added `tests/backtesting/test_pattern_event_study.py` covering FVG-like conversion, generic conversion with missing optional fields, deterministic DataFrame serialization, and optional metadata behavior.
- 2026-05-21: Completed Task 069 `FAIR_VALUE_GAP_EVENT_STUDY_EXTRACTION`; added rolling-prefix no-look-ahead FVG event extraction into canonical event-study records with duplicate suppression and focused backtesting tests.

- 2026-05-21: Completed Task 070 `FAIR_VALUE_GAP_STRATEGY_V1_SPECIFICATION`; added formal FVG V1 strategy specification doc with frozen hypothesis, entry/exit defaults, conservative intrabar promotion policy, net cost/fill requirements, OOS walk-forward requirements, and explicit rejection/promotions gates.

- 2026-05-21: Completed Task 071 `MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL`; added `docs/21_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md` and `tasks/071_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md` defining experiment-family controls, pre-declared search spaces, family-wise variant counting, locked holdout policy, baseline-comparison requirements, and conservative paper-only promotion gates.
- 2026-05-21: Completed Task 072 by adding deterministic multiple-testing helpers (`bonferroni_threshold`, `benjamini_hochberg_thresholds`, `count_strategy_variants`) and focused unit tests for nominal behavior, validation failures, monotonicity, and type stability.

- 2026-05-21: Completed Task 073 `BACKTEST_RESULT_DASHBOARD_API_CONTRACT`; added `docs/api/API_CONTRACT.md` with read-only `/api` dashboard endpoints, query/response/error contracts, frontend consumption boundaries, and required warnings for pattern placeholder-neutral financial semantics.

- 2026-05-21: Completed Task 074 `BACKEND_FRONTEND_DIRECTORY_AND_AGENTS_BOUNDARIES`; added backend/frontend directory scaffolds, area-specific `AGENTS.md` and `STATUS.md` files, placeholder package entry files, and root AGENTS routing rules for backend/frontend/backtest responsibilities.

- 2026-05-21: Completed Task 075 `FASTAPI_BACKTEST_RESULT_READ_API_IMPLEMENTATION`; implemented read-only FastAPI backend endpoints for health/list/detail using persisted repository read models, placeholder warning exposure, backend API tests, and status updates.

- 2026-05-21: Completed Task 076 `FRONTEND_DASHBOARD_BOOTSTRAP`; bootstrapped frontend with Next.js App Router + React + TypeScript, minimal dashboard shell, typed API client and API types aligned to contract, and status updates.

- 2026-05-21: Completed Task 077 `FRONTEND_BACKTEST_RESULT_DASHBOARD_IMPLEMENTATION`; implemented interactive frontend dashboard list/detail views, SVG price/equity charts with trade markers, warning surfaces for placeholder equity semantics, trades table, metadata panels, and status updates.

- 2026-05-21: Completed Task 078 `BACKTEST_DASHBOARD_INTEGRATION_AND_VERIFICATION`; verified backend/frontend contract alignment, fixed backend detail serialization conformance, added local development/smoke workflow documentation, and updated status tracking docs.

- 2026-05-21: Created Task 079 `BACKEND_FRONTEND_DOCKER_COMPOSE_SETUP` from owner request for one-command backend/frontend compose startup; implementation intentionally not started in this step per state-driven workflow.

- 2026-05-21: Completed Task 079 `BACKEND_FRONTEND_DOCKER_COMPOSE_SETUP`; added compose services for postgres/backend/frontend, optional ingestion profile retention, backend/frontend Dockerfiles, and documented environment-limited compose verification (docker unavailable in runner).

- 2026-05-21: Created Task 080 `DOCKER_COMPOSE_SERVICE_SPLIT` from owner request to separate compose startup flows for backtest/backend/db/frontend; implementation intentionally not started in this step per state-driven workflow.
- 2026-05-21: Completed Task 080 `DOCKER_COMPOSE_SERVICE_SPLIT`; refactored `docker-compose.yml` to profile-based split startup paths (`db`, `backend`, `frontend`, `backtest`, optional `ingestion`, plus `full`) and documented deterministic profile commands in local dashboard development docs.


- 2026-05-21: Completed Task 081 `BACKTEST_STARTING_CASH_ALIGNMENT`; updated pattern PostgreSQL backtest CLI persistence mapping to honor user-configured `--starting-cash` and remove unconditional `starting_cash=0`/`ending_cash=0` placeholders, with focused CLI/persistence tests.
- 2026-05-21: Created Task 082 `STRATEGY_BACKTEST_ARCHITECTURE_BOUNDARY` from owner request; implementation intentionally not started in this step per state-driven workflow.
- 2026-05-21: Created Task 083 `RISK_EXIT_EXTRACTION_AND_REUSABLE_POLICIES` from owner request; implementation intentionally not started in this step per state-driven workflow.

- 2026-05-21: Created Task 084 `SINGLE_PATTERN_STRATEGY_IMPLEMENTATIONS` from owner request; implementation intentionally not started in this step per state-driven workflow.

- 2026-05-21: Created Task 085 `CASH_BASED_STRATEGY_BACKTEST_ENGINE` from owner request; implementation intentionally not started in this step per state-driven workflow.

- 2026-05-21: Created Task 086 `STRATEGY_BACKTEST_CLI_AND_PERSISTENCE_REPLACEMENT` from owner request; implementation intentionally not started in this step per state-driven workflow.

- 2026-05-21: Created Task 087 `STRATEGY_BACKTEST_REGRESSION_AND_RESEARCH_TESTS` from owner request; implementation intentionally not started in this step per state-driven workflow.

- 2026-05-21: Completed Task 082 `STRATEGY_BACKTEST_ARCHITECTURE_BOUNDARY`; added strategy/backtest boundary decision doc (`docs/22_STRATEGY_BACKTEST_ARCHITECTURE.md`), canonical semantic strategy action contract (`quant_bitcoin/strategies/actions.py`), long-only semantic-to-execution side mapping helper (`quant_bitcoin/backtesting/strategy_execution_mapping.py`), and focused mapping tests.

- 2026-05-21: Completed Task 083 `RISK_EXIT_EXTRACTION_AND_REUSABLE_POLICIES`; added reusable risk/exit ownership modules (`quant_bitcoin/risk/exit_plan.py`, `quant_bitcoin/risk/exit_simulation.py`), added compatibility shims in `quant_bitcoin/patterns/risk_exit.py` and `quant_bitcoin/patterns/exit_simulation.py`, updated `quant_bitcoin/risk/__init__.py` exports, and documented the boundary in `docs/23_RISK_EXIT_REUSABLE_POLICY_BOUNDARY.md`.

- 2026-05-22: Completed Task 084 `SINGLE_PATTERN_STRATEGY_IMPLEMENTATIONS`; added `quant_bitcoin/strategies/patterns.py` with six single-pattern strategy classes + factory, emitting semantic actions (`ENTER_LONG`/`SKIP`) with long-only `SHORT_DISABLED` behavior and risk-plan wiring, plus focused strategy tests.

- 2026-05-22: Completed Task 085 `CASH_BASED_STRATEGY_BACKTEST_ENGINE`; added `strategy_models.py` + `strategy_engine.py` for long-only BUY/SELL cashflow accounting, partial/full exit execution rows, equity/drawdown timeline points, and summary metrics, with focused deterministic tests in `tests/backtesting/test_strategy_engine.py`.

- 2026-05-22: Completed Task 086 `STRATEGY_BACKTEST_CLI_AND_PERSISTENCE_REPLACEMENT`; added strategy-level CLI (`quant-bitcoin-strategy-backtest`), routed compatibility pattern CLI to strategy runner, and updated CLI tests for strategy/pattern alias behavior.

- 2026-05-22: Completed Task 087 `STRATEGY_BACKTEST_REGRESSION_AND_RESEARCH_TESTS`; added deterministic regression/research tests for strategy engine accounting (cash/equity movement, partial exits, exit reasons, metadata preservation), DIAMOND strategy diagnostics, strategy CLI BUY/SELL output semantics, and no-network behavior assertions.


- 2026-05-22: Created Task 088 `STRATEGY_ACTION_LONG_SHORT_CONTRACT` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 089 `STRATEGY_ENGINE_LONG_SHORT_COST_ACCOUNTING` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 090 `RSI_CANONICAL_ENGINE_MIGRATION` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 091 `PATTERN_STRATEGY_LONG_SHORT_ENABLEMENT` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 092 `PATTERN_RISK_EXIT_ACTION_BUILDER` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 093 `ENTRY_FILL_INTRABAR_INTEGRATION` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 094 `PATTERN_DETECTION_PERFORMANCE_OPTIMIZATION` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 095 `CANONICAL_CLI_AND_PERSISTENCE_MIGRATION` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 096 `LEGACY_DEPRECATED_BACKTEST_CLEANUP` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Created Task 097 `CANONICAL_BACKTEST_REGRESSION_AND_RESEARCH_TEST_SUITE` task document from owner assignment; per state-driven workflow, implementation not started in this step.

- 2026-05-22: Completed Task 088 `STRATEGY_ACTION_LONG_SHORT_CONTRACT`; expanded canonical strategy actions with short-side action enums, added semantic helper mappings (entry/exit, position side, execution side), added compatibility `execution_side`/`position_side` fields on strategy executions while keeping `side`, and added focused strategy-action mapping tests.

- 2026-05-22: Completed Task 089 `STRATEGY_ENGINE_LONG_SHORT_COST_ACCOUNTING`; upgraded strategy engine to deterministic long/short signed-position accounting, integrated transaction cost config/liquidity role semantics, added compatibility execution cost fields (`raw_price`, `effective_price`, fee/spread/slippage/total cost), blocked opposite-side re-entry while open, and expanded accounting tests for long/short/cost/drawdown behavior.


- 2026-05-22: Completed Task 090 `RSI_CANONICAL_ENGINE_MIGRATION`; added `RsiActionStrategy` adapter emitting `ENTER_LONG`/`EXIT_LONG`, migrated PostgreSQL RSI CLI execution to canonical `StrategyEngine` path with deterministic portfolio-state action gating, preserved compatibility JSON/persistence summaries/trade signals, and added focused adapter/CLI regression coverage.


- 2026-05-22: Completed Task 091 `PATTERN_STRATEGY_LONG_SHORT_ENABLEMENT`; updated pattern strategy direction semantics to map bullish events to `ENTER_LONG` and bearish events to `ENTER_SHORT`, added `pattern_direction_to_position_side` helper, enriched action metadata with `pattern_direction`/`position_side`, removed default SHORT_DISABLED skip behavior, and updated focused strategy regression tests.


- 2026-05-22: Completed Task 092 `PATTERN_RISK_EXIT_ACTION_BUILDER`; added `quant_bitcoin/backtesting/pattern_action_builder.py` to convert pattern events + risk/exit simulations into canonical strategy actions (`ENTER_*`, `PARTIAL_EXIT_*`, `EXIT_*`) with preserved metadata (event id/type, exit reason/target/stop/ratios) and realized R multiple mapping, plus focused tests in `tests/backtesting/test_pattern_action_builder.py`.


- 2026-05-22: Completed Task 093 `ENTRY_FILL_INTRABAR_INTEGRATION`; integrated pattern entry simulation into action builder with entry mode/config inputs, emitted SKIP diagnostics for non-filled/invalid entries, preserved filled-entry metadata (`fill_price`, `fill_timestamp`, `fill_candle_index`, `entry_mode`, `intrabar_policy`), and kept canonical risk-exit action conversion behavior with focused regression coverage.
