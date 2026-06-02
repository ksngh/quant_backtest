# Task 305: Lookback Return Momentum 5m Cost-Aware RR Revision

# Goal

Revise `LOOKBACK_RETURN_MOMENTUM` so the next validation includes `5m` candles and entry decisions account for transaction costs and net reward/risk before taking trades.

This task must also update the strategy document so it clearly explains why this project tests a momentum strategy and why `1m`, `5m`, and `15m` are the intended comparison timeframes.

# Source Requirement

Owner request:

```text
지금 테스트 했던 모멘텀 전략을 5분봉을 넣어서 해줘.
그리고 전략 문서를 수정해줘.
그리고 지금보니까 비용을 고려를 안하고 손익비를 안따지는 거 같더라구.
이거 수정해줘.
그리고 전략 문서에는 1,5,15분봉을 사용하는 이유를 명확히 해야 할거야.
그리고 모멘텀 전략을 사용하는 이유도 명확히 했으면 좋겠고.
위 내용을 반영하는 task 만들어줘
```

Owner follow-up:

```text
ㅇㅇ 아니 저기서 캔들 범위를 3개월로 잡아줘. 2월~5월로 해줘
```

Clean requirement:

- Create a task for the previously tested `LOOKBACK_RETURN_MOMENTUM` strategy.
- Include `BTCUSDT` `5m` candles in the next validation.
- Use the owner-requested three-month February-to-May window for candle preflight/backfill and validation.
- Interpret the requested three-month "2월~5월" window as:

```text
start inclusive: 2026-02-01T00:00:00Z
end exclusive:   2026-05-01T00:00:00Z
```

- If the owner later clarifies that all of May should be included, update this task before execution rather than silently changing the window.
- If local `5m` candles are missing, perform a bounded public-market-data backfill for the required validation window before running the `5m` backtest.
- Update `docs/strategy/lookback_return_momentum_v1.md` before implementation/backtest execution.
- Clarify why the strategy uses momentum at all.
- Clarify why the comparison uses `1m`, `5m`, and `15m`.
- Modify the strategy/backtest path so entries consider estimated transaction costs and net reward/risk before entering.
- Re-run bounded validation for `1m`, `5m`, and `15m` after the strategy/document update.
- Keep all results research-only.

# Extracted Roles

- Owner role:
  - Wants the existing momentum strategy corrected so it does not ignore trading costs or practical reward/risk.
  - Wants the missing `5m` validation interval included.
  - Wants the strategy rationale and timeframe rationale documented clearly.
- Supporting roles:
  - Strategy documentation role: update the momentum strategy document before any code or backtest execution.
  - Strategy implementation role: add cost-aware net reward/risk entry gating to `LOOKBACK_RETURN_MOMENTUM`.
  - Backtest runner role: wire the cost-aware gate into the offline strategy backtest path and CLI/config metadata.
  - Market-data role: verify `BTCUSDT` `5m` candle availability and backfill only the bounded required `5m` window if missing.
  - Validation role: run focused tests and bounded `1m`/`5m`/`15m` validations with the revised logic.
  - Reporting role: save a concise Task 305 validation report.
  - Status-tracking role: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No live trading.
  - No real Binance order execution.
  - No exchange order/account/private endpoints.
  - No signed requests, API keys, secrets, or `.env` changes.
  - No frontend/backend/API/dashboard changes.
  - No report/blog artifact generation unless a later task explicitly requests it.
  - No parameter optimization or broad search beyond the predeclared validation runs.
  - No new filters such as ATR, volume, trend score, FVG, Order Block, higher-timeframe confirmation, liquidity target, reverse entry, partial take profit, or trailing stop.

# Context

- Task 296 created `docs/strategy/lookback_return_momentum_v1.md`.
- Task 297 implemented `LOOKBACK_RETURN_MOMENTUM`.
- Task 299 ran the first bounded validation:
  - `1m`: saved run `1160`, `-37.9957%`, `1285` completed trades.
  - `15m`: saved run `1161`, `-6.8468%`, `169` completed trades.
  - `5m`: skipped because local closed candles were missing.
- The Task 305 validation/backfill window is changed from the short Task 299 window to the owner-requested three-month February-to-May window:

```text
2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z
```

- Task 298 already added public REST backfill support for `1h` and `1d`; existing backfill support for `5m` should remain available.
- The current strategy has gross stop/target mechanics through `risk_distance_pct`, `stop_loss_r`, and `take_profit_r`, but it does not block entries whose planned reward is infeasible after estimated fees, spread, and slippage.
- Existing generic cost-aware entry filter semantics exist in the pattern backtest path. This task should reuse the same concepts where practical without changing unrelated pattern behavior.

# Scope

Allowed files:

- `docs/strategy/lookback_return_momentum_v1.md`
- Relevant `LOOKBACK_RETURN_MOMENTUM` source under `quant_bitcoin/strategies/`.
- Relevant offline strategy backtest runner/CLI code under `quant_bitcoin/backtesting/`.
- Relevant market-data/backfill code only if a bug prevents bounded `5m` backfill through existing public kline support.
- Focused tests under `tests/strategies/`, `tests/backtesting/`, and `tests/market_data/` as needed.
- New report:
  - `reports/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md`
- This task file.
- State files:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`

Required execution order:

1. Read `AGENTS.md`, `BACKLOG.md`, `PROJECT_HISTORY.md`, `STATUS.md`, and this task file.
2. Read `docs/strategy/lookback_return_momentum_v1.md`.
3. Update the strategy document before any implementation or backtest execution.
4. Implement cost-aware net reward/risk entry gating.
5. Add/update focused tests.
6. Verify or backfill bounded `BTCUSDT` `5m` candles.
7. Run bounded validation for `1m`, `5m`, and `15m`.
8. Save a Task 305 validation report.
9. Update state files.

# Out of Scope

- No live trading.
- No real exchange orders.
- No exchange order/account/private endpoints.
- No signed Binance requests.
- No secrets, API keys, or `.env` changes.
- No dashboard/frontend/backend API changes.
- No strategy promotion beyond `research_only`.
- No broad parameter sweep.
- No result-based threshold tuning after seeing the new `5m` result.
- No daily report payload, PNG image generation, `report-ko.md` rewrite, or blog report generation.
- No unrelated candle backfills beyond the bounded `BTCUSDT` `5m` window required for this validation.

# Requirements

## Strategy Document Requirements

Update `docs/strategy/lookback_return_momentum_v1.md` before code or backtest execution.

The document must clearly state why a momentum strategy is being tested:

- It is a simple falsifiable baseline for whether recent BTCUSDT close-to-close directional pressure persists.
- It gives a low-complexity reference before adding pattern filters, trend filters, or higher-timeframe confirmation.
- It helps separate "directional signal exists" from "directional signal survives costs and reward/risk constraints".
- It remains research-only and is not a live-trading strategy.

The document must clearly state why the validation compares `1m`, `5m`, and `15m`:

- `1m`: highest turnover and fastest reaction; useful for seeing whether very short continuation exists, but expected to be most cost-sensitive and noisy.
- `5m`: middle layer between noise and slow response; intended to test whether a one-hour lookback and thirty-minute hold reduce churn while preserving continuation.
- `15m`: lower-turnover comparison; intended to test whether slower candles reduce cost drag and whipsaw at the expense of fewer trades and slower signal response.

The document must include the concrete default window meaning:

| Timeframe | lookback_bars | holding_bars | entry_threshold | Interpretation |
|---|---:|---:|---:|---|
| `1m` | 20 | 5 | 0.001 | last 20 minutes -> next 5 minutes |
| `5m` | 12 | 6 | 0.0015 | last 1 hour -> next 30 minutes |
| `15m` | 8 | 4 | 0.002 | last 2 hours -> next 1 hour |

The document must define the revised cost-aware reward/risk gate:

- Compute planned gross reward from entry to take-profit.
- Compute planned gross risk from entry to stop.
- Estimate one-side cost from fee, spread, and slippage assumptions.
- Estimate round-trip cost as `2 * one_side_cost_bps`.
- Compute:

```text
net_reward_bps = gross_reward_bps - round_trip_cost_bps
net_risk_bps = gross_risk_bps + round_trip_cost_bps
net_rr = net_reward_bps / net_risk_bps
```

- Reject an entry if:
  - gross reward is non-positive.
  - gross risk is non-positive.
  - estimated net reward is below the predeclared minimum.
  - estimated net reward/risk is below the predeclared minimum.

The document must predeclare initial Task 305 gate defaults before implementation. Proposed defaults unless changed with written rationale in the strategy document:

```text
cost_aware_entry_filter_enabled = true for validation runs with nonzero cost assumptions
min_net_reward_bps = 0.0
min_net_rr = 1.0
liquidity_role = taker
```

If the implementation changes the public strategy metadata version, the strategy document must record the new version and explain how Task 305 results differ from Task 299 v1 results.

## Implementation Requirements

- Add cost-aware net reward/risk entry gating to `LOOKBACK_RETURN_MOMENTUM`.
- The gate must use planned entry, stop, and take-profit prices already produced by the strategy.
- The gate must use the active backtest cost assumptions where available.
- The gate must fail closed when a cost-aware decision cannot be computed in a validation run that claims cost-aware filtering is enabled.
- The gate must not fetch data, persist records, or call exchange APIs from strategy code.
- Accepted entry metadata must include cost-aware fields:
  - enabled.
  - blocked.
  - block reason.
  - gross reward bps.
  - gross risk bps.
  - estimated one-side cost bps.
  - estimated round-trip cost bps.
  - net reward bps.
  - net risk bps.
  - net RR.
  - minimum net reward bps.
  - minimum net RR.
- Blocked entries should be countable in diagnostics. If the existing strategy runner does not persist explicit `SKIP` rows for this strategy family, the task must at least include aggregate skipped-entry counts in the validation report or metadata.
- Reuse existing cost-aware filter concepts and CLI flags where practical:
  - `--enable-cost-aware-entry-filter`
  - `--min-net-reward-bps`
  - `--min-net-rr`
- Do not change unrelated pattern strategy behavior.

## 5m Data Requirements

- Preflight local `BTCUSDT` `5m` candles before backtesting.
- If `5m` candles for `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z` are missing or discontinuous, run a bounded public Binance kline backfill for only the required `5m` window.
- The backfill must use public market-data endpoints only.
- The backfill must not use API keys or signed requests.
- After backfill, verify:
  - closed candle count is nonzero.
  - no duplicate open-time groups.
  - no gaps for the required bounded window.

## Validation Requirements

Use the owner-requested three-month February-to-May validation window:

```text
start inclusive: 2026-02-01T00:00:00Z
end exclusive:   2026-05-01T00:00:00Z
```

The validation report must record the runner's exact end-time semantics and the last included closed candle for each interval.

Run revised no-tuning validation for:

- `BTCUSDT` `1m`
- `BTCUSDT` `5m`
- `BTCUSDT` `15m`

Use the documented timeframe defaults unless the strategy document explicitly changes them before execution.

Use realistic existing cost assumptions, preferably the same `conservative_crypto_1m` cost profile used in Task 299 unless the strategy document records a better named profile before execution.

The validation report must include:

- strategy version / cost-aware gate version.
- data availability and continuity for `1m`, `5m`, and `15m`.
- whether `5m` backfill was performed.
- parameters by timeframe.
- cost-aware gate thresholds.
- attempted entry count if available.
- blocked-entry count and block reasons if available.
- completed trade count.
- gross PnL.
- net PnL.
- total return.
- win rate.
- profit factor.
- max drawdown.
- fee/spread/slippage totals.
- exit reason breakdown.
- comparison against Task 299 only as historical context, not as a tuned optimization target, because Task 305 uses a longer validation window.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Confirm Task 305 is the assigned task.
- [x] Read this task file before implementation.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Confirm the strategy document update is done before code/backtest execution.
- [x] Confirm whether local `BTCUSDT` `5m` candles exist for the required window.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise Task 305 completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md`.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `docs/strategy/lookback_return_momentum_v1.md` clearly explains why momentum is used.
- `docs/strategy/lookback_return_momentum_v1.md` clearly explains why `1m`, `5m`, and `15m` are compared.
- The strategy document defines cost-aware net reward/risk formulas and predeclared gate defaults.
- `LOOKBACK_RETURN_MOMENTUM` entries can be blocked when estimated costs make net reward/risk insufficient.
- Cost-aware metadata is attached to accepted entries and available for diagnostics.
- Blocked entries are countable or otherwise summarized in the Task 305 report.
- Local `BTCUSDT` `5m` data is available and continuous for the bounded validation window, or a blocker is recorded if public backfill cannot complete.
- Revised bounded validation is run for `1m`, `5m`, and `15m` after the strategy update.
- `reports/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md` exists.
- The report keeps results research-only and does not claim live readiness.
- No live trading, order endpoint, account endpoint, signed request, secret, or `.env` behavior is added.
- State files are updated after execution.

# Required Tests

## Unit Tests

- Add or update strategy tests proving:
  - cost-aware gate blocks a long entry when round-trip costs make net reward/RR insufficient.
  - cost-aware gate blocks a short entry when round-trip costs make net reward/RR insufficient.
  - a long entry passes when net reward and net RR meet thresholds.
  - a short entry passes when net reward and net RR meet thresholds.
  - cost-aware metadata includes gross reward/risk, estimated cost, net reward, net risk, net RR, thresholds, and block reason.
  - existing no-lookahead, flat-only, stop, take-profit, time-exit, and stop-first tests still pass.

## Integration Tests

- Add or update strategy runner/CLI tests proving:
  - `LOOKBACK_RETURN_MOMENTUM` can receive cost-aware entry filter settings.
  - validation metadata records the cost-aware filter config.
  - `1m`, `5m`, and `15m` timeframe defaults still resolve correctly.
  - no unrelated pattern strategy behavior changes.

## Contract Tests

- Verify strategy document and implementation metadata agree on:
  - strategy version or entry-filter version.
  - cost-aware formulas.
  - `1m`/`5m`/`15m` defaults.
- Verify `reports/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md` records 5m data availability/backfill status and validation results.
- Verify persisted run metadata, if saved, includes the cost-aware gate configuration.

## Safety Tests

- Search changed strategy/backtest/market-data code for accidental live behavior:

```bash
rg -n "order|account|signed|api_key|secret|ENABLE_LIVE_TRADING" quant_bitcoin/strategies quant_bitcoin/backtesting quant_bitcoin/market_data tests reports/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md tasks/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md
```

- Confirm any matches are documentation/safety text or pre-existing non-live test fixtures only.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Strategy code does not fetch market data.
- Strategy code does not call exchange APIs.
- Backfill uses public market-data endpoints only.
- Backtest code does not place orders.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No unnecessary abstractions.
- Strategy document updated before code/backtest execution.
- Tests added or updated for cost-aware RR behavior.
- Results remain research-only.

# Verification

Recommended focused verification:

```bash
python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q
python -m pytest tests/market_data/test_binance_backfill.py tests/market_data/test_binance_backfill_cli.py tests/market_data/test_binance_downloader.py tests/market_data/test_candle_validation.py -q
python -m json.tool reports/blog_payloads/lookback-return-momentum/v1/20260520-20260528/payload.json >/dev/null
git diff --check -- docs/strategy/lookback_return_momentum_v1.md quant_bitcoin/strategies quant_bitcoin/backtesting tests reports tasks/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md STATUS.md PROJECT_HISTORY.md BACKLOG.md
```

Recommended bounded `5m` backfill command if preflight confirms missing local candles:

```bash
quant-bitcoin-binance-backfill \
  --symbol BTCUSDT \
  --interval 5m \
  --start-time 2026-02-01T00:00:00Z \
  --end-time 2026-05-01T00:00:00Z
```

Recommended validation commands after implementation and data preflight:

```bash
quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --interval 1m \
  --start-time 2026-02-01T00:00:00Z \
  --end-time 2026-05-01T00:00:00Z \
  --cost-profile conservative_crypto_1m \
  --enable-cost-aware-entry-filter \
  --min-net-reward-bps 0 \
  --min-net-rr 1.0 \
  --enforce-candle-continuity \
  --starting-cash 1000000 \
  --starting-cash-currency KRW \
  --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --research-task-id TASK_305 \
  --research-variant-id lookback_return_momentum_cost_aware_rr \
  --research-window-id three_month_20260201_20260501_1m \
  --research-run-group cost_aware_rr_validation

quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --interval 5m \
  --start-time 2026-02-01T00:00:00Z \
  --end-time 2026-05-01T00:00:00Z \
  --cost-profile conservative_crypto_1m \
  --enable-cost-aware-entry-filter \
  --min-net-reward-bps 0 \
  --min-net-rr 1.0 \
  --enforce-candle-continuity \
  --starting-cash 1000000 \
  --starting-cash-currency KRW \
  --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --research-task-id TASK_305 \
  --research-variant-id lookback_return_momentum_cost_aware_rr \
  --research-window-id three_month_20260201_20260501_5m \
  --research-run-group cost_aware_rr_validation

quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --interval 15m \
  --start-time 2026-02-01T00:00:00Z \
  --end-time 2026-05-01T00:00:00Z \
  --cost-profile conservative_crypto_1m \
  --enable-cost-aware-entry-filter \
  --min-net-reward-bps 0 \
  --min-net-rr 1.0 \
  --enforce-candle-continuity \
  --starting-cash 1000000 \
  --starting-cash-currency KRW \
  --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --research-task-id TASK_305 \
  --research-variant-id lookback_return_momentum_cost_aware_rr \
  --research-window-id three_month_20260201_20260501_15m \
  --research-run-group cost_aware_rr_validation
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
  - `docs/strategy/lookback_return_momentum_v1.md`
  - `quant_bitcoin/strategies/lookback_return_momentum.py`
  - `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
  - `tests/strategies/test_lookback_return_momentum.py`
  - `tests/backtesting/test_lookback_return_momentum_runner.py`
  - `tests/backtesting/test_strategy_cli_persistence.py`
  - `reports/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md`
  - `tasks/TASK_305_LOOKBACK_RETURN_MOMENTUM_5M_COST_AWARE_RR_REVISION.md`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Implementation summary:
  - Updated the strategy document before code/backtest execution with momentum rationale, `1m`/`5m`/`15m` rationale, and the cost-aware net reward/risk gate.
  - Added `cost_aware_entry_filter_v1` support to `LOOKBACK_RETURN_MOMENTUM`.
  - Wired existing runner cost-aware CLI settings into the momentum action builder.
  - Added diagnostics for candidate, accepted, and cost-blocked entries.
  - Added saved run metadata for cost-aware gate config, cost profile, workflow settings, and momentum config.
- Tests added or updated:
  - Strategy tests for long/short cost-aware blocking, long/short accepted metadata, and volatility-adjusted slippage.
  - Runner tests for cost-aware settings reaching `LOOKBACK_RETURN_MOMENTUM`.
  - Persistence test coverage for saved run metadata carrying cost/workflow settings.
- Tests run:
  - `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` -> `19 passed`
  - `python -m pytest tests/market_data/test_binance_backfill.py tests/market_data/test_binance_backfill_cli.py tests/market_data/test_binance_downloader.py tests/market_data/test_candle_validation.py -q` -> `64 passed`
  - `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q` -> `20 passed`
- Validation results:
  - `1m` saved run `1162`: 79,981 candidates, 0 accepted, 79,981 cost-blocked.
  - `5m` saved run `1163`: 17,171 candidates, 0 accepted, 17,171 cost-blocked.
  - `15m` saved run `1164`: 5,937 candidates, 0 accepted, 5,937 cost-blocked.
  - No new `5m` backfill was required; local `5m` candles were complete for the bounded window.
- Codex self-review result:
  - Completed; no live trading, exchange order/account/private endpoints, signed requests, secrets, `.env` changes, frontend/backend/API changes, or unrelated pattern behavior changes were added.
- Known limitations:
  - The revised cost gate blocked every candidate under `conservative_crypto_1m`, so realized win rate, profit factor, and exit behavior are unavailable for Task 305.
  - No parameter tuning or alternative risk/target geometry was attempted in this task.
- Recommended next task:
  - Create a separate strategy-revision task to decide whether to change the fixed risk distance, take-profit multiple, or cost-profile assumptions before any further validation. Do not tune those changes inside Task 305.
