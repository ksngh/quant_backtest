# Task 298: Backfill 1h and 1d Interval Support

# Goal

Enable the candle backfill workflow to accept and backfill `1h` and `1d` intervals.

This task is intentionally focused on market-data backfill interval support only. It does not wire higher-timeframe context into strategies, does not run strategy backtests, and does not add live-trading behavior.

# Source Requirement

Owner request:

```text
아니 일단 backfill에 한시간 단위랑 1일 단위도 넣을 수 있게 해줘.. 그런 task 만들어줘
```

Clean requirement:

- Add support for one-hour candles: `1h`.
- Add support for one-day candles: `1d`.
- Support these intervals in the existing Binance public candle backfill workflow.
- Preserve existing supported intervals and behavior.
- Keep the task limited to data collection/backfill plumbing and tests.

# Extracted Roles

- Owner role:
  - Wants the backfill path to handle hourly and daily candle intervals before broader strategy-context work.
- Supporting roles:
  - Market-data role: extend interval validation and downloader/backfill orchestration for `1h` and `1d`.
  - CLI role: ensure users can request `1h`, `1d`, or multi-interval combinations including them.
  - Persistence/provider role: confirm stored candles remain interval-specific and idempotent.
  - Test role: add focused tests for interval validation, CLI parsing, and backfill orchestration using fakes.
  - Status-tracking role: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No live trading.
  - No real order execution.
  - No Binance order/account/private endpoints.
  - No API keys, signed requests, secrets, or `.env` changes.
  - No strategy signal logic.
  - No strategy/backtest execution.
  - No report, image, daily payload, or `image_manifest.json` generation.
  - No scheduler/dashboard/frontend/backend API changes unless a later assigned task explicitly asks for them.

# Context

- Task 014 implemented PostgreSQL Binance historical candle backfill for public market data.
- Task 131 added multi-interval backfill orchestration for intervals such as `1m`, `5m`, and `15m`.
- Task 286 added a focused BTCUSDT 1m data audit/repair runner and repaired the 1m dataset.
- Task 265 exists as a broader future task for `1h`/`4h` backfill plus strategy context. This Task 298 is narrower and should be executed first if the owner only wants backfill interval support for `1h` and `1d`.

# Scope

- Inspect current market-data backfill modules:
  - downloader interval allowlist/validation.
  - backfill runner/orchestration.
  - backfill CLI parsing.
  - candle validation assumptions.
  - persistence/provider interval handling if needed.
- Add or confirm support for:
  - `1h`
  - `1d`
- Ensure multi-interval backfill can include the new intervals, for example:

```bash
... --intervals 1m,1h,1d
```

or the project’s existing equivalent CLI syntax.

- Preserve idempotent upsert behavior by `source`, `symbol`, `interval`, and candle open time.
- Keep public Binance kline endpoint usage only.
- Add focused tests with fake HTTP/provider/repository objects where possible.
- Update command documentation only if the existing command guide/backfill docs list supported intervals.

# Out of Scope

- No strategy-context wiring.
- No `4h` implementation unless it is already supported or must be touched to preserve existing behavior.
- No higher-timeframe filters.
- No strategy/model/backtest implementation.
- No saved strategy backtest runs.
- No database schema migration unless the current schema cannot store interval-specific candles and the blocker is documented before proceeding.
- No dashboard/frontend/API changes.
- No scheduler or automatic recurring backfill.
- No live trading.
- No real Binance order execution.
- No order/account/private endpoints.
- No secrets, API keys, or `.env` changes.
- No reports/images/payloads/manifests.

# Requirements

- `1h` and `1d` must be accepted anywhere the backfill workflow validates Binance candle intervals.
- Existing interval behavior must remain backward-compatible.
- CLI help or documentation should make `1h` and `1d` discoverable if supported intervals are documented.
- Backfill must request Binance public kline/candle market-data endpoints only.
- Backfill must not use signed requests.
- Backfill must not call exchange order/account/private endpoints.
- Backfill must remain idempotent.
- Tests must avoid network calls and real exchange endpoints.
- Any interval-specific time continuity assumptions must account for:
  - `1h`: one-hour candle spacing.
  - `1d`: one-day candle spacing.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 298 is the assigned task.
- [x] Read this task file before implementation.
- [x] Read relevant market-data/backfill source files.
- [x] Confirm this task does not require a strategy document because it is market-data backfill work, not strategy/model/backtest implementation.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 298 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Backfill interval validation accepts `1h`.
- Backfill interval validation accepts `1d`.
- Backfill CLI can request `1h` and `1d`.
- Multi-interval backfill can include `1h` and `1d` together with existing intervals.
- Existing intervals still work.
- Idempotent persistence behavior is preserved.
- Tests prove `1h` and `1d` support without real network calls.
- No strategy/backtest execution is added.
- No live trading, signed request, order endpoint, account endpoint, API key, secret, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Interval allowlist/validation accepts `1h`.
- Interval allowlist/validation accepts `1d`.
- Invalid intervals remain rejected.
- Continuity or interval-duration helpers map `1h` to one hour.
- Continuity or interval-duration helpers map `1d` to one day.

## Integration Tests

- Backfill runner/CLI invokes fake backfill calls for `1h`.
- Backfill runner/CLI invokes fake backfill calls for `1d`.
- Multi-interval CLI input including `1m,1h,1d` is parsed and dispatched deterministically.
- Existing interval backfill tests continue to pass.

## Contract Tests

- If command docs list supported intervals, update and test/search for `1h` and `1d`.
- Persistence payloads keep interval values explicit and unchanged.

## Safety Tests

- Tests confirm no Binance order/account/private endpoints are introduced.
- Tests do not call real network endpoints.
- No API keys or signed request fields are needed.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Market data code does not contain strategy logic.
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

If exact test files differ, run the focused market-data/backfill tests added or modified by this task.

Also run:

```bash
git diff --check -- quant_bitcoin/market_data tests/market_data docs STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_298_BACKFILL_1H_1D_INTERVAL_SUPPORT.md
rg -n "1h|1d|interval|kline|klines" quant_bitcoin/market_data tests/market_data docs tasks/TASK_298_BACKFILL_1H_1D_INTERVAL_SUPPORT.md
rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" quant_bitcoin/market_data tests/market_data tasks/TASK_298_BACKFILL_1H_1D_INTERVAL_SUPPORT.md
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# Implementation Result

- Completed: `1h` and `1d` are accepted by the Binance public REST downloader/backfill path.
- Completed: Backfill interval stepping maps `1h` to `3,600,000` ms and `1d` to `86,400,000` ms for latest-closed and pagination behavior.
- Completed: Multi-interval parsing and CLI dispatch can run deterministic fake backfills for `1m,1h,1d`.
- Completed: CLI help and README list supported historical backfill intervals.
- Completed: Existing minute intervals remain supported, and WebSocket minute-only validation was left unchanged because Task 298 is backfill-only.
- Completed: Tests use fake HTTP/repository objects and do not call network or exchange endpoints.
- Verification:
  - `pytest tests/market_data/test_binance_downloader.py tests/market_data/test_binance_backfill.py tests/market_data/test_binance_backfill_cli.py tests/market_data/test_candle_validation.py -q` -> `64 passed`
  - `pytest tests/market_data -q` -> `120 passed`
  - `git diff --check -- quant_bitcoin/market_data tests/market_data README.md tasks/TASK_298_BACKFILL_1H_1D_INTERVAL_SUPPORT.md STATUS.md PROJECT_HISTORY.md BACKLOG.md` -> passed
  - `rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" quant_bitcoin/market_data tests/market_data tasks/TASK_298_BACKFILL_1H_1D_INTERVAL_SUPPORT.md` -> only existing documentation, test assertions, and public-endpoint guards; no new exchange order/account/private behavior.

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
