# Task 286: BTCUSDT 1m Data Backfill And Gap Repair

# Goal

Backfill and verify missing BTCUSDT 1-minute closed candle data needed for complete April-20-forward research validation.

# Source Requirement

Owner requested:

```text
ㅇㅇ해결해줘
```

Clean requirement:

- Resolve the data blocker found by Tasks 282-285.
- Local BTCUSDT 1m data must cover the April-20-forward validation range without silent missing-candle gaps.
- Preserve realistic-cost research integrity by repairing data first, before rerunning or promoting any strategy.

# Extracted Roles

- Owner role:
  - Wants the missing BTCUSDT 1m candle coverage repaired so 2026-04-20-forward validation can be run correctly.
- Supporting roles:
  - Market data/backfill role: fetches Binance public historical klines only.
  - Persistence role: inserts or upserts closed candles idempotently without duplicates.
  - Data quality role: audits timestamp continuity, duplicates, OHLCV validity, timezone normalization, and closed-candle status.
  - Reporting role: records before/after coverage, inserted counts, skipped duplicates, repaired gaps, and remaining gaps.
  - Test role: covers range planning, parsing, upsert/dedupe behavior, and endpoint safety.
- Forbidden roles:
  - Do not implement or tune strategies in this task.
  - Do not run broad profitability sweeps as part of data repair.
  - Do not implement live trading.
  - Do not call Binance order/account/private/signed endpoints.
  - Do not use API keys or committed `.env` files.
  - Do not add frontend/backend UI, dashboard, scheduler, futures, leverage, or portfolio optimization behavior.

# Context

- Task 282 found local BTCUSDT 1m data starts at `2026-05-10T00:00:00Z`, not `2026-04-20T00:00:00Z`.
- Task 282 also found an internal missing-candle gap from `2026-05-17T15:19:00Z` to `2026-05-20T00:00:00Z`.
- Task 283/284/285 kept their candidate results research-only because complete April-20-forward OOS validation is data-blocked.
- Task 285 selected a repaired diagnostic candidate but rejected robustness; complete data is required before any future locked OOS/WFO validation can be trusted.
- Existing relevant historical tasks:
  - Task 006 implemented Binance candle downloading concepts.
  - Task 014 implemented PostgreSQL Binance historical backfill.
  - Task 158 implemented candle integrity/gap validation.
  - Task 265 is separate and only targets `1h`/`4h` higher-timeframe backfill.

# Scope

- Inspect the existing Binance downloader/backfill, market data provider, candle validation, and PostgreSQL persistence paths before coding.
- Audit current BTCUSDT 1m database coverage before inserting any data.
- Repair at least these target open-time ranges:
  - Leading missing range: `2026-04-20T00:00:00Z` through `2026-05-09T23:59:00Z`.
  - Internal missing range: `2026-05-17T15:20:00Z` through `2026-05-19T23:59:00Z`.
- Use Binance public historical kline/candle data only.
- Store only closed 1m candles.
- Preserve existing rows and make the operation idempotent.
- Upsert or skip duplicates using the existing candle uniqueness rule, expected to be `source + symbol + interval + open_time` or the local equivalent.
- Validate all repaired data:
  - UTC open/close times.
  - 1-minute open-time spacing.
  - finite numeric OHLCV fields.
  - positive prices.
  - non-negative volume.
  - `high >= max(open, close)`.
  - `low <= min(open, close)`.
  - no duplicate open times.
- Produce a markdown report at `reports/TASK_286_BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR.md`.
- Record before/after data coverage and counts:
  - previous min/max timestamps.
  - previous gap list.
  - requested fetch ranges.
  - fetched candle count.
  - inserted row count.
  - skipped duplicate count.
  - post-repair min/max timestamps.
  - post-repair gap list.
  - remaining upstream or local blockers, if any.
- After the repair, run only a lightweight data coverage audit needed to prove the blocker is resolved.

# Out of Scope

- No strategy tuning.
- No repeated model search.
- No promotion of any Task 281/283/285 candidate.
- No broad OOS/WFO strategy validation beyond confirming that the data range can now be loaded.
- No live trading.
- No real Binance order execution.
- No signed/private/account endpoints.
- No API keys, secrets, or `.env` changes.
- No futures, leverage, portfolio optimization, dashboard, scheduler, backend API, or frontend changes.
- No database schema redesign unless the existing schema cannot store the required 1m candles; if that happens, stop and record the blocker.

# Requirements

- Backfill must be data-only and offline with respect to trading decisions.
- Network calls, if used, must target only public Binance market-data kline endpoints.
- Existing safe downloader/backfill code must be reused where practical instead of creating a parallel incompatible data pipeline.
- The range planner must handle Binance pagination deterministically.
- The repair must be resumable and safe to rerun.
- Existing candles must not be overwritten with inconsistent data silently; any conflicting duplicate row should be reported.
- Time handling must be explicit and UTC-based.
- The post-repair audit must prove continuity from at least `2026-04-20T00:00:00Z` through the latest previously used Task 285 endpoint, `2026-05-28T08:26:00Z`, unless Binance upstream data is unavailable and documented.
- If the database is unavailable, stop with a clear blocker and do not fake success.
- If Binance data is temporarily unavailable, record the exact failed range and retry behavior.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Read `quant_bitcoin/market_data/binance_downloader.py`.
- [x] Read `quant_bitcoin/market_data/binance_backfill.py`.
- [x] Read `quant_bitcoin/market_data/binance_backfill_cli.py`.
- [x] Read `quant_bitcoin/market_data/candle_validation.py`.
- [x] Read `quant_bitcoin/market_data/postgres_provider.py`.
- [x] Read `quant_bitcoin/persistence/postgres.py`.
- [x] Read relevant tests under `tests/market_data/`.
- [x] Confirm no strategy/backtest tuning is included in this task.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- BTCUSDT 1m local data has no missing 1-minute open-time gaps from `2026-04-20T00:00:00Z` through at least `2026-05-28T08:26:00Z`, unless an upstream data outage is proven and documented.
- The leading missing range `2026-04-20T00:00:00Z` through `2026-05-09T23:59:00Z` is filled or explicitly proven unavailable.
- The internal missing range `2026-05-17T15:20:00Z` through `2026-05-19T23:59:00Z` is filled or explicitly proven unavailable.
- No duplicate BTCUSDT 1m open times exist after repair.
- Stored candles pass the project candle validation rules.
- The repair is idempotent: rerunning it does not create duplicates or change valid existing rows unexpectedly.
- The report `reports/TASK_286_BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR.md` documents before/after coverage and all counts.
- No strategy result is promoted by this task.
- No live trading, order endpoint, signed request, API key, secret, or `.env` behavior is introduced.

# Required Tests

## Unit Tests

- Range planner splits the leading and internal missing ranges into Binance-compatible requests.
- Binance kline parser maps open time, close time, OHLCV, and closed-candle status correctly.
- Gap audit detects the known missing 1m ranges.
- Duplicate/upsert planning is deterministic for already-present candles.

## Integration Tests

- Backfill runner with fake Binance responses inserts missing rows and skips existing duplicates.
- Post-repair coverage audit reports no gaps on a synthetic repaired dataset.
- Database/repository integration is covered when a local test database is configured; otherwise document the skip.

## Contract Tests

- Stored data follows the standard candle schema and existing persistence uniqueness contract.
- Provider can load the repaired BTCUSDT 1m range with strict continuity enabled.
- Report metadata uses UTC ISO timestamps.

## Safety Tests

- Confirm no Binance order/account/private endpoints are called.
- Confirm no signed requests, API keys, secrets, or `.env` files are used.
- Confirm strategy modules are not required for the data repair path.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected.
- Existing candles preserved.
- Idempotency verified.
- No hardcoded secrets.
- No real order execution.
- No signed/private/account endpoints.
- No unnecessary abstractions.

# Verification

Default focused verification:

```bash
pytest tests/market_data -q
python -m compileall -q quant_bitcoin
git diff --check
```

Task-specific runtime verification should also include the final BTCUSDT 1m coverage audit command used by the implementation and the before/after report path.

Completed Task 286 verification on 2026-05-31:

- `python -m quant_bitcoin.market_data.t286_btcusdt_1m_gap_repair --dry-run --report-path reports/TASK_286_DRY_RUN_AUDIT.md` found the expected two gaps before repair: `28800` candles from `2026-04-20T00:00:00Z` to `2026-05-09T23:59:00Z`, and `3400` candles from `2026-05-17T15:20:00Z` to `2026-05-19T23:59:00Z`.
- `python -m quant_bitcoin.market_data.t286_btcusdt_1m_gap_repair --report-path reports/TASK_286_BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR.md` completed with `32200` fetched closed candles, `32200` estimated new candles, `0` duplicates, `0` conflicts, and `0` post-repair missing ranges.
- `python -m quant_bitcoin.market_data.t286_btcusdt_1m_gap_repair --report-path reports/TASK_286_IDEMPOTENCY_CHECK.md` completed with no missing ranges and `0` fetched/upserted candles.
- Strict provider continuity verification loaded `55227` candles from `2026-04-20T00:00:00Z` through `2026-05-28T08:26:00Z`.
- SQL duplicate audit returned `0` duplicate BTCUSDT 1m open times and `55227` closed rows for the target range.
- `pytest tests/market_data -q` passed: `111 passed`.
- `python -m compileall -q quant_bitcoin` passed.
- `git diff --check` passed.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
