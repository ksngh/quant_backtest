# Task 284: Task 283 Multi-Axis Robustness Revalidation

# Goal

Revalidate the Task 283 best research strategy `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` from multiple independent angles without retuning. The task must verify cost accounting, execution assumptions, data coverage, side/regime/session dependence, endpoint sensitivity, cost stress, outlier dependence, baseline comparison, and overfit risk.

This is a validation-only research task. It must not promote the strategy to live trading.

# Source Requirement

Owner request:

```text
검증해봐 다시 여러 방향으로
```

Clean requirement:

- Take the completed Task 283 best candidate and replay it as a locked model.
- Do not change entry logic, exit logic, thresholds, or sizing unless the task records a deliberate diagnostic-only variant separately from the locked replay.
- Validate the result across multiple windows, cost assumptions, execution assumptions, market regimes, sessions, long/short side, and baseline comparisons.
- Persist all decision-driving validation runs to DB.
- Produce a markdown report with pass/fail gates and an explicit research-only conclusion.

# Extracted Roles

- Owner role:
  - Requests deeper validation from several directions after Task 283 passed the owner target windows.
  - Needs clear evidence on whether the result is robust or just fixed-window overfit.
- Supporting roles:
  - Validation lead: define the locked replay matrix and acceptance gates.
  - Backtest auditor: recompute fees, spread, slippage, notional, and net PnL from trade logs.
  - Data-quality auditor: verify local BTCUSDT 1m coverage and identify gaps before making period claims.
  - Quant researcher: analyze side, session, regime, outlier, endpoint, and cost sensitivity.
  - Reporting role: save a markdown validation report with run IDs, results, and interpretation.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - Live trading.
  - Real Binance order execution.
  - Exchange private/order/account endpoints.
  - API keys, signed requests, `.env`, credential handling, or live account access.
  - Futures, leverage, real borrow, funding, liquidation, or margin assumptions.
  - Strategy retuning disguised as validation.
  - Frontend/backend API/dashboard work unless separately assigned.

# Context

Task 283 implemented an offline principle-first BTCUSDT 1m research runner and selected `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` as the best target-window candidate.

Known Task 283 results:

- 2026-05-20+ owner window: run `950`, `+5.7327pct`, `62` round trips, cost-audit mismatch count `0`.
- 2026-05-25+ owner window: run `951`, `+3.5337pct`, `17` round trips, cost-audit mismatch count `0`.
- Endpoint trims stayed positive on the tested target windows.
- High-cost stress stayed above `-3pct`.
- Zero-cost diagnostic was materially higher than conservative-cost replay, showing costs are important.
- Available pre-owner validation run `959` returned `-2.6638pct`.

Known data blocker from Tasks 282 and 283:

- Local BTCUSDT 1m data does not fully cover 2026-04-20 onward.
- Available local data starts at 2026-05-10T00:00:00Z.
- There is an internal gap from 2026-05-17T15:19:00Z to 2026-05-20T00:00:00Z.
- This task must not claim a complete April-20-forward validation unless the missing data has been repaired by a separate assigned task.

# Scope

- Read and reuse the Task 283 implementation and report:
  - `quant_bitcoin/backtesting/t283_principle_first_microstructure_strategy.py`
  - `tests/backtesting/test_t283_principle_first_microstructure_strategy.py`
  - `reports/TASK_283_PRINCIPLE_FIRST_BTC_MICROSTRUCTURE_STRATEGY_DEVELOPMENT.md`
- Add task-local validation code only if the current Task 283 runner cannot express the required locked replay matrix cleanly.
- Allowed code locations:
  - `quant_bitcoin/backtesting/`
  - `tests/backtesting/`
- Generate:
  - `reports/TASK_284_TASK283_MULTI_AXIS_ROBUSTNESS_REVALIDATION.md`
- Persist decision-driving validation runs to DB with additive metadata:
  - `research.task_id = TASK_284`
  - `research.parent_task_id = TASK_283`
  - `research.locked_candidate_id = T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`
  - `research.validation_mode = locked_multi_axis_revalidation`
  - `research.no_retune = true`
  - `research.research_only = true`
  - validation group, window ID, cost profile, execution assumption, side/regime/session bucket when applicable.

# Out of Scope

- No live trading.
- No real order placement.
- No Binance private/order/account endpoint usage.
- No API keys or credential work.
- No futures, leverage, liquidation, funding, or margin simulation.
- No optimization loop to improve returns.
- No modification of Task 283 candidate thresholds for the primary locked validation.
- No dashboard/frontend/backend API changes.
- No claim that the model is production-ready.

# Requirements

## Locked Replay Rule

- The primary validation must replay exactly the Task 283 best candidate logic.
- Any diagnostic variant must be clearly labeled `DIAGNOSTIC_ONLY` and excluded from locked pass/fail promotion.
- Do not choose the best result from the validation matrix as a new model.

## Data Coverage Audit

- Report local BTCUSDT 1m start/end timestamps.
- Report missing intervals and candle continuity gaps.
- Explicitly distinguish:
  - complete local validation windows.
  - partial windows.
  - data-blocked requested windows.
- Attempt 2026-04-20-forward validation only as a coverage audit unless data is present.

## Validation Matrix

Run or generate equivalent diagnostics for the locked candidate across:

- Owner replay:
  - 2026-05-20+.
  - 2026-05-25+.
- Available pre-owner windows:
  - 2026-05-10 to the 2026-05-17 internal gap.
  - Any complete sub-windows available before 2026-05-20.
- Endpoint sensitivity:
  - drop first 6h, 12h, 24h.
  - drop last 6h, 12h, 24h.
  - split by first half / second half where data allows.
- Cost sensitivity:
  - conservative base cost.
  - fee 2x.
  - slippage 2x.
  - fee and slippage 2x.
  - high-spread/high-slippage stress.
  - zero-cost diagnostic only.
- Execution assumption sensitivity:
  - existing conservative same-candle stop-first rule.
  - one-candle delayed entry diagnostic if implementable.
  - exit-next-open versus same-candle stop/take diagnostic if implementable without retuning.
- Side attribution:
  - long-only contribution.
  - short-only contribution.
  - side trade count, win rate, average R, total cost, and net PnL.
- Session attribution:
  - Asia, Europe, US, and low-liquidity/off-session buckets.
  - weekday/weekend if enough sample exists.
- Regime attribution:
  - high versus low realized volatility.
  - trend-aligned versus counter-trend trades.
  - volume expansion versus normal volume trades.
- Outlier dependence:
  - largest winner contribution.
  - top-three winner contribution.
  - return after removing largest winner.
  - return after removing top-three winners.
- Baselines:
  - buy-and-hold over the same windows.
  - simple MA trend baseline if already available or trivial task-local implementation is low risk.
  - random-entry baseline using fixed seed, same approximate trade count, side distribution, and holding-time distribution if implementable within reasonable runtime.

## Cost Audit

For every persisted validation run:

- Recompute gross PnL, fee, spread, slippage, and total transaction cost from saved trades.
- Confirm DB summary costs match trade-level totals within rounding tolerance.
- Confirm entry and exit fees are both included.
- Confirm spread and slippage are non-zero for conservative/stress profiles.
- Report effective one-way bps and round-trip cost.
- Report cost/gross PnL and cost/net PnL where meaningful.
- Flag any mismatch as a validation failure.

## Safety And Bias Checks

- Confirm no exchange private/order/account endpoints are imported or called.
- Confirm no API key or `.env` handling is introduced.
- Confirm signal candle and execution candle are separated.
- Confirm factor snapshots use completed candles only.
- Confirm MTF features, if used, are from completed higher-timeframe candles only.
- Confirm stop/take same-candle ambiguity is handled conservatively.
- Confirm no overlapping positions unless explicitly documented as existing Task 283 behavior.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Read Task 283 source, tests, and report.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if this task is completed, blocked, reprioritized, or split.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- [x] The locked Task 283 candidate is replayed without retuning.
- [x] Multiple validation axes are executed or explicitly marked not runnable with a concrete blocker.
- [x] Every decision-driving run is persisted to DB with `research.task_id = TASK_284`.
- [x] Fee, spread, and slippage accounting is recomputed from trade logs and has mismatch count `0` for all passing-cost-audit runs.
- [x] The report clearly states whether the strategy remains research-only, likely overfit, data-blocked, or robust enough for a later paper-trading design task.
- [x] The report does not claim April-20-forward validation unless full data coverage exists.
- [x] Tests cover any new validation helper code.
- [x] No live trading, signed requests, private endpoints, API keys, or `.env` changes are introduced.

# Required Tests

## Unit Tests

- Add focused tests for any new validation helpers, cost-audit helpers, attribution helpers, or baseline generators.
- Existing Task 283 tests must still pass.

## Integration Tests

- Run the Task 284 validation runner on local BTCUSDT 1m data when available.
- Persist validation runs to DB unless the database is unavailable, in which case record the blocker and save local report diagnostics.

## Contract Tests

- Verify persisted metadata includes `research.task_id = TASK_284`, parent task ID, locked candidate ID, no-retune flag, and research-only flag.
- Verify cost audit metadata is present in the report and/or persisted run metadata.

## Safety Tests

- Verify Task 284 code does not import exchange order/private/account clients.
- Verify no API key, `.env`, or signed request behavior is added.

# Verification

Default focused verification:

```bash
pytest tests/backtesting/test_t283_principle_first_microstructure_strategy.py -q
```

If Task 284 adds tests:

```bash
pytest tests/backtesting/test_t283_principle_first_microstructure_strategy.py tests/backtesting/test_t284_task283_multi_axis_robustness_revalidation.py -q
```

Repository checks:

```bash
python -m compileall -q quant_bitcoin
git diff --check
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- validation axes executed
- DB run IDs persisted
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task

# Execution Summary

- Added `quant_bitcoin/backtesting/t284_task283_multi_axis_robustness_revalidation.py`.
- Added `tests/backtesting/test_t284_task283_multi_axis_robustness_revalidation.py`.
- Generated `reports/TASK_284_TASK283_MULTI_AXIS_ROBUSTNESS_REVALIDATION.md`.
- Replayed the Task 283 locked candidate `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` without retuning.
- Persisted 34 Task 284 validation runs: `960`-`993`.
- Final status: `ROBUSTNESS_REJECTED_RESEARCH_ONLY`.
- Failed robustness gates:
  - available pre-owner replay returned `-2.6638pct`.
  - endpoint diagnostics were positive in `15/16` cases; `owner_0525_latest_first_half` returned `-0.0148pct`.
  - April-20-forward OOS remains data-blocked because local data starts `2026-05-10T00:00:00Z` and has a `2026-05-17T15:19:00Z` to `2026-05-20T00:00:00Z` gap.
- Cost audit: all 34 persisted runs had formula mismatch `0` and summary mismatch `0`.
- Base 0520 replay run `960`: `+5.7327pct`, `62` trips, cost `40,593.49`, one-way effective cost `18.4765` bps.
- Base 0525 replay run `961`: `+3.5337pct`, `17` trips, cost `19,432.60`, one-way effective cost `18.6560` bps.
- Pre-owner high-slippage stress run `989`: `-8.6028pct`, confirming the model is not robust outside the fixed owner window.

# Verification Results

```bash
pytest tests/backtesting/test_t283_principle_first_microstructure_strategy.py tests/backtesting/test_t284_task283_multi_axis_robustness_revalidation.py -q
python -m quant_bitcoin.backtesting.t284_task283_multi_axis_robustness_revalidation
python -m quant_bitcoin.backtesting.t284_task283_multi_axis_robustness_revalidation --report-existing
```

Additional final verification commands are recorded in the assistant completion summary.

# Codex Self-Review Result

- Scope respected: Task 284 only; no Task 283 strategy retuning.
- Architecture respected: offline backtesting/research module only.
- Safety respected: no live trading, no exchange order/private/account endpoints, no API keys, no `.env` changes.
- Tests added: focused Task 284 helper/contract/safety tests.
- Known limitation: a second full rerun stalled before persisting new runs, so the final report was regenerated from the already persisted Task 284 DB runs with `--report-existing`.

# Recommended Next Task

Create and execute a data repair/backfill task for missing BTCUSDT 1m coverage from `2026-04-20T00:00:00Z` to `2026-05-10T00:00:00Z` and the internal `2026-05-17T15:19:00Z` to `2026-05-20T00:00:00Z` gap before any complete April-20-forward OOS claim.

# Post-Completion Owner-Question Audit

Owner questioned whether the Task 284 result looked anomalous. A read-only audit was performed after completion:

- DB readback confirmed Task 283/284 paired runs match exactly:
  - Task 283 run `950` and Task 284 run `960`: same return, same cost totals, same 62 paired event PnLs.
  - Task 283 run `951` and Task 284 run `961`: same return, same cost totals, same 17 paired event PnLs.
  - Task 283 run `959` and Task 284 run `962`: same return, same cost totals, same 54 paired event PnLs.
- In-memory reruns without DB persistence reproduced the persisted returns and costs for `owner_0520_latest`, `owner_0525_latest`, and `available_pre_owner_0510_0517`.
- Manual event-level gross PnL recomputation on run `960` matched persisted `gross_pnl` within floating point tolerance; max observed event formula difference was approximately `3.64e-11`.
- Data coverage was rechecked:
  - `2026-05-10T00:00:00Z` to `2026-05-17T15:19:00Z`: 11,000 unique 1m candles.
  - `2026-05-20T00:00:00Z` to `2026-05-28T08:26:00Z`: 12,027 unique 1m candles.
  - `2026-05-25T00:00:00Z` to `2026-05-28T08:26:00Z`: 4,827 unique 1m candles.
  - one internal gap remains from `2026-05-17T15:19:00Z` to `2026-05-20T00:00:00Z`, missing 3,400 one-minute candles.
- The apparent anomaly is therefore not a persistence/cost formula issue. The result is structurally weak because:
  - 0520 replay profit is almost entirely from SHORTs: LONG net `-2,125.15`, SHORT net `+59,452.47`.
  - pre-owner replay is cost-dominated: gross `20,150.20`, cost `46,788.59`, net `-26,638.39`.
  - pre-owner high-slippage stress is much worse at `-8.6028pct`.
  - 0520 and 0525 windows overlap, so they are not independent validation samples.
