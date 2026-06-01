# Task 299: Lookback Return Momentum Initial Validation

# Goal

Run the first bounded validation of the implemented `LOOKBACK_RETURN_MOMENTUM` strategy.

This task is for testing and research validation only. It must not change strategy logic, tune parameters, add filters, or promote the strategy for live use.

# Source Requirement

Owner request:

```text
ㅇㅋ 이제 테스트 해볼 수 있나?? 모멘텀 전략?
```

Clean requirement:

- Check whether the implemented Lookback Return Momentum strategy can be tested now.
- Create the required validation/backtest task before any strategy test execution.
- Run focused implementation tests and bounded strategy backtests only after the task is assigned for execution.

# Extracted Roles

- Owner role:
  - Wants to test the newly implemented momentum baseline.
- Supporting roles:
  - Strategy validation role: run the existing implementation without changing logic.
  - Backtest role: execute bounded `LOOKBACK_RETURN_MOMENTUM` runs on predeclared timeframes/windows.
  - Data role: verify required candle data exists before running each interval.
  - Reporting role: write a concise Task 299 validation report with metrics and blockers.
  - Status-tracking role: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No strategy logic changes.
  - No parameter tuning or search.
  - No new filters, indicators, FVG, Order Block, ATR filter, volume filter, trend score, MTF filter, reverse entry, trailing stop, partial take profit, or model family changes.
  - No live trading.
  - No real Binance order execution.
  - No exchange order/account/private endpoints.
  - No API keys, signed requests, secrets, or `.env` changes.
  - No candle backfill or candle DB mutation in this task.
  - No dashboard/frontend/backend API changes.
  - No daily report payload, image generation, `image_manifest.json`, or blog report generation.

# Context

- Task 296 created `docs/strategy/lookback_return_momentum_v1.md`.
- Task 297 implemented `LOOKBACK_RETURN_MOMENTUM` and focused tests passed.
- Task 298 added `1h` and `1d` support to backfill, but did not execute real DB backfill or strategy backtests.
- This task is the first validation task for the momentum strategy. It must read the strategy document before execution.

# Scope

- Read:
  - `docs/strategy/lookback_return_momentum_v1.md`
  - Task 297 implementation and tests as needed.
- Run focused implementation tests for the strategy:
  - `tests/strategies/test_lookback_return_momentum.py`
  - `tests/backtesting/test_lookback_return_momentum_runner.py`
- Preflight candle availability for:
  - `BTCUSDT` `1m`
  - `BTCUSDT` `5m`
  - `BTCUSDT` `15m`
- Run no-tuning default-parameter validation if data exists:
  - `1m`: `lookback_bars=20`, `holding_bars=5`, `entry_threshold=0.001`
  - `5m`: `lookback_bars=12`, `holding_bars=6`, `entry_threshold=0.0015`
  - `15m`: `lookback_bars=8`, `holding_bars=4`, `entry_threshold=0.002`
- Use implemented v1 risk:
  - `risk_distance_pct=0.002`
  - `stop_loss_r=1.0`
  - `take_profit_r=1.5`
- Use realistic existing cost assumptions from the current backtest CLI defaults or explicitly selected conservative cost profile.
- Save strategy backtest run records only if the existing CLI workflow normally persists them; do not mutate candle data.
- Write a concise validation report:
  - `reports/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`

# Out of Scope

- No candle backfill execution.
- No data repair.
- No new strategy implementation.
- No parameter sweep.
- No optimization against owner windows.
- No result-based parameter changes.
- No strategy promotion.
- No live trading.
- No exchange order/account/private endpoints.
- No secrets or `.env` changes.
- No frontend/backend/dashboard/API work.
- No daily-report payload or images.

# Requirements

- Read the strategy document before any backtest execution.
- Execute only the documented v1 strategy behavior.
- Do not change strategy code unless a failing implementation test reveals a clear bug; if that happens, stop and create a separate fix task.
- Confirm whether required candle data exists before running each interval.
- If `5m` or `15m` candles are missing, record the blocker and skip that interval rather than backfilling in this task.
- Preserve research-only interpretation.
- Report:
  - interval
  - window
  - parameters
  - number of candles
  - trade count
  - completed trade count
  - gross/net PnL
  - total return
  - win rate
  - profit factor
  - max drawdown if available
  - total fees/spread/slippage if available
  - exit reason breakdown if available
  - data availability blockers
- Do not claim profitability from a single run.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 299 is the assigned task.
- [x] Read this task file before validation.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Confirm no strategy document blocker exists.
- [x] Record assumptions, blockers, or unclear status items before execution.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 299 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Focused momentum strategy tests are run and results are recorded.
- Strategy document is read before validation.
- Candle availability is checked before each interval run.
- `1m` default validation is run if data is available.
- `5m` default validation is run if data is available, otherwise skipped with blocker recorded.
- `15m` default validation is run if data is available, otherwise skipped with blocker recorded.
- No parameter tuning is performed.
- No strategy code change is performed.
- No candle backfill or candle DB mutation is performed.
- A concise Task 299 validation report is saved.
- State files are updated after execution.
- No live trading, signed request, order endpoint, account endpoint, API key, secret, or `.env` behavior is added.

# Required Tests

## Unit Tests

- Run existing `LOOKBACK_RETURN_MOMENTUM` strategy unit tests.
- Confirm long/short/no-trade, insufficient lookback, duplicate-position prevention, stop/target/time-exit, and same-candle stop-first coverage still passes.

## Integration Tests

- Run existing backtest runner/CLI tests for `LOOKBACK_RETURN_MOMENTUM`.
- Run bounded validation backtests only through the existing offline backtest path.

## Contract Tests

- Confirm validation uses documented strategy parameters.
- Confirm report records research-only status and data windows.
- Confirm no undocumented filters or reverse-entry behavior are used.

## Safety Tests

- Confirm no exchange order/account/private endpoint is used.
- Confirm no API keys, signed requests, secrets, or `.env` files are needed.
- Confirm no real Binance order execution is possible from the strategy validation path.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Strategy code does not fetch market data.
- Market-data code does not contain strategy logic.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account/private endpoint usage.
- No unnecessary abstractions.
- Tests and validation commands run.
- Report is concise and does not overclaim.

# Verification

Focused tests:

```bash
pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q
```

Validation commands:

```bash
quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --interval 1m \
  --start-time 2026-05-20T00:00:00Z \
  --end-time 2026-05-28T08:15:00Z \
  --cost-profile conservative_crypto_1m \
  --enforce-candle-continuity \
  --starting-cash 1000000 \
  --starting-cash-currency KRW \
  --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --research-task-id TASK_299 \
  --research-variant-id lookback_return_momentum_v1_default \
  --research-window-id bounded_recent_20260520_20260528_1m \
  --research-run-group initial_validation

quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --interval 15m \
  --start-time 2026-05-20T00:00:00Z \
  --end-time 2026-05-28T08:15:00Z \
  --cost-profile conservative_crypto_1m \
  --enforce-candle-continuity \
  --starting-cash 1000000 \
  --starting-cash-currency KRW \
  --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --research-task-id TASK_299 \
  --research-variant-id lookback_return_momentum_v1_default \
  --research-window-id bounded_recent_20260520_20260528_15m \
  --research-run-group initial_validation
```

Safety checks:

```bash
rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" quant_bitcoin/strategies quant_bitcoin/backtesting tests/strategies tests/backtesting tasks/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md
git diff --check -- reports tasks/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
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

# Completion Summary

- Files changed:
  - `reports/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`
  - `tasks/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Implementation summary:
  - Ran focused existing momentum tests.
  - Preflighted `BTCUSDT` `1m`/`5m`/`15m` candle availability.
  - Skipped `5m` because local closed candles are missing.
  - Persisted bounded no-tuning validation runs `1160` (`1m`) and `1161` (`15m`) with default strategy parameters and `conservative_crypto_1m` costs.
  - Saved concise validation report at `reports/TASK_299_LOOKBACK_RETURN_MOMENTUM_INITIAL_VALIDATION.md`.
- Tests added or updated:
  - None. Task 299 was validation/reporting only.
- Tests run:
  - `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` -> `13 passed`.
- Codex self-review result:
  - Passed. Scope stayed within Task 299 validation/reporting, no strategy logic or unrelated files were changed, no new abstractions were added, focused tests and validation runs were executed, state files were updated, no secrets or `.env` files were touched, and no live trading or exchange order/account/private endpoint behavior was added.
- Known limitations:
  - `5m` validation is blocked by missing local `BTCUSDT` `5m` candles.
  - Full available `1m` validation was interrupted before persistence because it was oversized for the initial bounded task.
  - Results are a first bounded diagnostic only, not OOS/WFO validation.
  - Short results are simulation-only and omit real borrow/funding/liquidation mechanics.
- Recommended next task:
  - Execute Task 300 if the owner wants the daily-report template/style rule update next, or create a separate future task for `5m` candle backfill / locked OOS diagnostics if continuing `LOOKBACK_RETURN_MOMENTUM`.
