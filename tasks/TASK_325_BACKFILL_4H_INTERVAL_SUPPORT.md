# Task 325: Backfill 4h Interval Support

# Goal

Enable the Binance public candle backfill workflow to accept and backfill `4h`
candles through `backfill --interval 4h` and multi-interval backfill lists.

This task is intentionally narrow. It adds `4h` market-data backfill interval
support only. It does not wire higher-timeframe strategy context, run a real
backfill, run strategy backtests, or change live-trading behavior.

# Source Requirement

Owner request:

```text
4시간봉도 가져올 수 있게끔 backfill --interval 에 추가해줘.
```

Clean requirement:

- Add support for four-hour candles: `4h`.
- Support `4h` anywhere the existing Binance public candle REST backfill
  workflow validates or advertises supported `--interval` values.
- Support `4h` in multi-interval input such as `--intervals 1m,1h,4h,1d`.
- Preserve existing supported intervals and behavior.
- Keep the task limited to data collection/backfill plumbing and tests.

# Extracted Roles

- Owner role:
  - Wants `4h` candles to be retrievable with the existing backfill CLI.
- Supporting roles:
  - Market-data role: extend interval validation and duration handling for
    public Binance `4h` klines.
  - CLI role: ensure `--interval 4h` and `--intervals ...4h...` are accepted
    and discoverable in help text.
  - Persistence/provider role: confirm candle identity remains
    `source + symbol + interval + open_time`.
  - Documentation role: update command docs if supported intervals are listed.
  - Test role: cover `4h` validation, parsing, dispatch, duration, and public
    endpoint safety with fakes.
  - Status-tracking role: update `STATUS.md`, `PROJECT_HISTORY.md`, and
    `BACKLOG.md`.
- Forbidden roles:
  - No live trading.
  - No real order execution.
  - No Binance order/account/private endpoints.
  - No API keys, signed requests, secrets, or `.env` changes.
  - No strategy signal logic.
  - No strategy/backtest execution.
  - No higher-timeframe strategy-context wiring; Task 265 remains the broader
    context task.
  - No report, image, daily payload, or frontend/backend dashboard changes.

# Context

- Task 298 added REST backfill support for `1h` and `1d`, while explicitly
  leaving broader `1h`/`4h` strategy-context work to Task 265.
- The current request is narrower than Task 265: only make `4h` available in
  the public market-data backfill interval path.
- Candle continuity validation already has higher-timeframe concepts in some
  project areas; this task must inspect current market-data source/tests before
  implementation rather than assuming every backfill allowlist is complete.

# Scope

- Inspect current market-data backfill modules:
  - `quant_bitcoin/market_data/binance_downloader.py`
  - `quant_bitcoin/market_data/binance_backfill.py`
  - `quant_bitcoin/market_data/binance_backfill_cli.py`
  - `quant_bitcoin/market_data/candle_validation.py`
  - related tests under `tests/market_data/`
- Add or confirm support for:
  - `4h`
- Ensure single-interval CLI can request:

```bash
quant-bitcoin-binance-backfill --symbol BTCUSDT --interval 4h
```

- Ensure multi-interval CLI can include:

```bash
quant-bitcoin-binance-backfill --symbol BTCUSDT --intervals 1m,1h,4h,1d
```

- Preserve idempotent upsert behavior by `source`, `symbol`, `interval`, and
  candle open time.
- Keep public Binance kline endpoint usage only.
- Update README or command documentation if the supported interval list is
  visible there.
- Add focused tests with fake HTTP/provider/repository objects.

# Out of Scope

- No real DB backfill execution or DB mutation.
- No strategy-context wiring.
- No higher-timeframe filters.
- No strategy/model/backtest implementation.
- No saved strategy backtest runs.
- No database schema migration unless the current schema cannot store
  interval-specific candles and the blocker is documented before proceeding.
- No dashboard/frontend/API changes.
- No scheduler or automatic recurring backfill.
- No live trading.
- No real Binance order execution.
- No order/account/private endpoints.
- No secrets, API keys, signed requests, or `.env` changes.
- No reports/images/payloads/manifests.

# Requirements

- `4h` must be accepted anywhere the REST backfill workflow validates Binance
  candle intervals.
- `4h` duration handling must map to four-hour spacing for pagination,
  latest-closed-candle detection, and continuity checks where applicable.
- Existing interval behavior must remain backward-compatible.
- CLI help or documentation must make `4h` discoverable if supported intervals
  are listed.
- Backfill must request Binance public kline/candle market-data endpoints only.
- Backfill must not use signed requests.
- Backfill must not call exchange order/account/private endpoints.
- Backfill must remain idempotent.
- Tests must avoid network calls and real exchange endpoints.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 325 is the assigned task.
- [x] Read this task file before implementation.
- [x] Read relevant market-data/backfill source files.
- [x] Confirm this task does not require a strategy document because it is
  market-data backfill work, not strategy/model/backtest implementation.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open
  question, or completion state changed.
- [x] Append a concise Task 325 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and
  verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Backfill interval validation accepts `4h`.
- Backfill CLI can request `4h` through `--interval`.
- Multi-interval backfill can include `4h` with existing intervals.
- Interval duration handling treats `4h` as exactly four hours.
- Existing intervals still work.
- Idempotent persistence behavior is preserved.
- Tests prove `4h` support without real network calls.
- No strategy/backtest execution is added.
- No live trading, signed request, order endpoint, account endpoint, API key,
  secret, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Interval allowlist/validation accepts `4h`.
- Invalid intervals remain rejected.
- Interval-duration helper maps `4h` to `14,400,000` milliseconds.
- Candle continuity validation supports `4h` if the backfill path relies on it.

## Integration Tests

- Backfill runner/CLI invokes fake backfill calls for `4h`.
- Multi-interval CLI input including `1m,1h,4h,1d` is parsed and dispatched
  deterministically.
- Existing interval backfill tests continue to pass.

## Contract Tests

- If command docs list supported intervals, update and test/search for `4h`.
- Persistence payloads keep interval values explicit and unchanged.

## Safety Tests

- Confirm no Binance order/account/private endpoints are introduced.
- Confirm no signed request data or API keys are used.
- Confirm tests do not call real network endpoints.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Market-data code does not contain strategy logic.
- Strategy code does not fetch market data.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint usage.
- No unnecessary abstractions.
- Tests added or updated.
- Verification commands run.

# Verification

Recommended focused verification:

```bash
pytest tests/market_data/test_binance_downloader.py tests/market_data/test_binance_backfill.py tests/market_data/test_binance_backfill_cli.py tests/market_data/test_candle_validation.py -q
```

Also run:

```bash
git diff --check -- quant_bitcoin/market_data tests/market_data README.md tasks/TASK_325_BACKFILL_4H_INTERVAL_SUPPORT.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
rg -n "4h|interval|kline|klines" quant_bitcoin/market_data tests/market_data README.md tasks/TASK_325_BACKFILL_4H_INTERVAL_SUPPORT.md
rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" quant_bitcoin/market_data tests/market_data tasks/TASK_325_BACKFILL_4H_INTERVAL_SUPPORT.md
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the
result in the final summary.

# Implementation Result

- Completed: Added `4h` to the Binance public REST kline interval allowlist in
  `quant_bitcoin/market_data/binance_downloader.py`.
- Completed: Existing backfill validation, CLI help, and multi-interval parsing
  now accept `4h` because they consume the shared REST allowlist.
- Completed: Existing interval duration logic maps `4h` to `14,400,000`
  milliseconds through the generic hour-unit path.
- Completed: README supported historical backfill interval docs now include
  `4h`.
- Completed: Focused fake-backed tests cover downloader `4h` validation,
  backfill request dispatch, interval duration, interval-list parsing,
  multi-interval runner/CLI dispatch, CLI help, and `4h` candle continuity.
- Completed: No real DB backfill execution, DB mutation, strategy-context
  wiring, strategy/backtest execution, live trading behavior, order/account
  endpoint behavior, signed request behavior, secret, or `.env` change was
  added.
- Verification:
  - `python -m pytest tests/market_data/test_binance_downloader.py tests/market_data/test_binance_backfill.py tests/market_data/test_binance_backfill_cli.py tests/market_data/test_candle_validation.py -q` -> `68 passed`
  - `python -m pytest tests/market_data -q` -> `124 passed`
  - `python -m py_compile quant_bitcoin/market_data/binance_downloader.py quant_bitcoin/market_data/binance_backfill.py quant_bitcoin/market_data/binance_backfill_cli.py quant_bitcoin/market_data/candle_validation.py` -> passed
  - `git diff --check -- quant_bitcoin/market_data tests/market_data README.md tasks/TASK_325_BACKFILL_4H_INTERVAL_SUPPORT.md STATUS.md PROJECT_HISTORY.md BACKLOG.md` -> passed
  - `rg -n "4h|interval|kline|klines" quant_bitcoin/market_data tests/market_data README.md tasks/TASK_325_BACKFILL_4H_INTERVAL_SUPPORT.md` -> passed; `4h` appears in the expected allowlist/docs/tests.
  - `rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" quant_bitcoin/market_data tests/market_data tasks/TASK_325_BACKFILL_4H_INTERVAL_SUPPORT.md` -> only existing public-market-data safety guards, tests, and declarative task text; no new unsafe endpoint or secret behavior.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before
merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
