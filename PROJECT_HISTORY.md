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
