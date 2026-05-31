# Task 265: Higher-Timeframe 1h/4h Backfill And Strategy Context

# Goal

Enable `1h` and `4h` candle backfill and make those completed higher-timeframe candles available to the strategy backtest path so FVG v2/channel research can use 1m entries with 1h/4h context.

# Source Requirement

Owner requested:

```text
1시간봉, 4시간 봉도 backfill 하고 전략에 넣을 수 있게끔 해줘
```

Clean requirement:

- Backfill Binance public-market-data candles for `1h` and `4h`.
- Store and read those intervals through the existing candle persistence/provider path.
- Wire completed `1h` and `4h` candles into strategy backtests as higher-timeframe context.
- Preserve no-lookahead semantics: a 1h/4h candle is visible only after it is fully closed.

# Extracted Roles

- Owner role:
  - Wants 1h and 4h data available and usable by strategy logic, not just stored.
- Supporting roles:
  - Market data/backfill role: validates and backfills public Binance `1h`/`4h` klines without order/account endpoints.
  - Persistence/provider role: stores interval-specific candles and loads them by interval.
  - Strategy runner role: loads higher-timeframe candles for the same source/symbol/date range and passes completed context into FVG strategy configuration.
  - Multi-timeframe alignment role: enforces completed-candle visibility and records no-lookahead metadata.
  - CLI/documentation role: exposes clear flags/commands and explains default/override behavior.
  - Test role: covers backfill interval support, strategy context wiring, and no-lookahead boundaries.
- Forbidden roles:
  - Do not implement live trading.
  - Do not call Binance order/account/private endpoints.
  - Do not use API keys or signed requests.
  - Do not add scheduler/dashboard/database schema migrations unless existing schema is insufficient and explicitly justified.
  - Do not silently change trade entry rules beyond the assigned higher-timeframe context/alignment behavior.

# Context

- Task 014 implemented PostgreSQL Binance historical candle backfill for public market data.
- Task 131 added multi-interval backfill orchestration for intervals such as `1m,5m,15m`.
- Task 226 added completed-candle multi-timeframe aggregation/alignment semantics.
- Task 227/228 added multi-timeframe trend-score capability when higher-timeframe candle context is supplied.
- Current strategy CLI primarily loads the selected base interval, currently default `1m`; it does not yet load stored `1h` and `4h` candles from PostgreSQL into FVG strategy runs by default.
- Recent owner workflow focuses on FVG v2 channel entries from 1m candles.

# Scope

- Confirm and extend Binance backfill interval validation/support for `1h` and `4h`.
- Ensure multi-interval backfill can run `1m,1h,4h` or equivalent owner command.
- Load stored `1h` and `4h` candles from PostgreSQL for strategy backtests when enabled.
- Add CLI controls, for example:
  - `--higher-timeframe-intervals 1h,4h`
  - `--enable-higher-timeframe-context`
  - or an FVG-specific equivalent if that matches existing patterns better.
- Pass completed 1h/4h context into the FVG strategy/trend-score path without lookahead.
- Record metadata:
  - requested higher-timeframe intervals
  - loaded candle counts by interval
  - actual loaded ranges by interval
  - completed-candle visibility/no-lookahead semantics
  - missing interval/context warnings
- Update README/API contract or command guide for backfill and strategy run commands.
- Add focused tests.

# Out of Scope

- No live trading.
- No real Binance order execution.
- No exchange account/private endpoint use.
- No API keys or `.env` changes.
- No frontend dashboard changes unless a later task explicitly asks for 1h/4h visualization.
- No scheduler or automatic recurring backfill.
- No profitability claims or automatic strategy promotion.
- No strategy parameter optimization.

# Requirements

- `1h` and `4h` backfill must use public kline/candle market-data endpoints only.
- Existing `1m` backfill behavior must remain compatible.
- Backfill must remain idempotent and interval-specific.
- Strategy backtest must be able to load `1h` and `4h` context for the same `source`, `symbol`, and requested time window.
- Higher-timeframe candles must be completed before they are visible to a 1m strategy row.
- Missing `1h`/`4h` data must be explicit in metadata and warnings, not silently treated as neutral alignment.
- The default owner FVG command behavior must be documented if 1h/4h context is defaulted on or opt-in.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Read `quant_bitcoin/market_data/binance_downloader.py`.
- [ ] Read `quant_bitcoin/market_data/binance_backfill.py`.
- [ ] Read `quant_bitcoin/market_data/binance_backfill_cli.py`.
- [ ] Read `quant_bitcoin/market_data/candle_validation.py`.
- [ ] Read `quant_bitcoin/market_data/postgres_provider` or current provider implementation.
- [ ] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [ ] Read `quant_bitcoin/backtesting/multitimeframe_candles.py`.
- [ ] Read `quant_bitcoin/patterns/fair_value_gap.py`.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append a concise completion note to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Backfill CLI supports `1h` and `4h` intervals, including a multi-interval command path.
- Backfill tests prove public-market-data-only behavior and interval validation for `1h`/`4h`.
- Strategy CLI can load and pass `1h`/`4h` completed context into FVG strategy evaluation.
- FVG strategy metadata records 1h/4h availability and no-lookahead timing.
- Missing higher-timeframe context is explicit in output metadata/warnings.
- Existing 1m-only strategy runs remain compatible.
- No live trading, signed request, account endpoint, order endpoint, credential, or `.env` behavior is introduced.

# Required Tests

## Unit Tests

- Interval validation supports `1h` and `4h`.
- Multi-timeframe alignment keeps incomplete 1h/4h candles unavailable.
- Higher-timeframe context metadata is deterministic.

## Integration Tests

- Backfill CLI or runner invokes backfill for `1h` and `4h` using fakes.
- Strategy runner loads base `1m` candles plus stored `1h`/`4h` candles via fake providers/repositories.
- FVG strategy receives higher-timeframe context and records expected MTF metadata.

## Contract Tests

- README/command guide documents 1h/4h backfill and strategy run commands.
- API/metadata contract documents higher-timeframe context fields if output schema changes.

## Safety Tests

- Confirm no Binance order/account/private endpoints are called.
- Confirm no signed request data or API keys are used.
- Confirm strategy code does not fetch market data directly or place orders.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.

# Verification

Default:

```bash
pytest tests/market_data/test_binance_downloader.py tests/market_data/test_binance_backfill.py tests/market_data/test_binance_backfill_cli.py tests/backtesting/test_multitimeframe_candles.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/patterns/test_fair_value_gap.py -q
git diff --check
```

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
