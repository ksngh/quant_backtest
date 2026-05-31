# Task 282: Task 281 Locked OOS/WFO Validation From 2026-04-20

# Goal

Validate the Task 281 selected strategy (`T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`, DB run `892`) without further tuning, using BTCUSDT 1-minute data from 2026-04-20 onward and multiple predeclared validation windows to determine whether the Task 281 result is robust or likely overfit to the 2026-05-20+ owner window.

# Source Requirement

Owner request after the Task 281 fee audit:

```text
Validate the rest properly again. Check whether anything looks strange, whether it is overfit, and test multiple different periods starting from April 20.
```

Clean requirement:

- Do not tune or alter the selected Task 281 strategy to fit new periods.
- Re-run the locked Task 281 selected model from 2026-04-20 onward.
- Test multiple predeclared subperiods, not only the original 2026-05-20+ owner window.
- Check for abnormal behavior, cost-accounting issues, outlier dependence, endpoint dependence, overfit/data-snooping symptoms, side/layer concentration, and trade consistency.
- Persist every decision-driving validation run to DB.
- Save a markdown report that clearly says whether run `892` remains research-only, is OOS-supported research-only, or is rejected as likely overfit.

# Extracted Roles

- Owner role:
  - Requests stricter validation beyond the Task 281 owner window.
  - Wants April 20 onward included.
  - Wants anomalies and overfit risk checked directly.
- Supporting roles:
  - Quant validation lead: define locked OOS/WFO protocol and pass/fail gates.
  - Backtest runner: execute locked model runs and persist results to DB.
  - Diagnostics role: inspect cost, notional, PnL concentration, layer/side attribution, time-slice consistency, drawdown, and endpoint dependence.
  - Reporting role: write a concise markdown report with run IDs, gate table, and overfit conclusion.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - Live trading.
  - Real Binance order execution.
  - Exchange private/order/account endpoints.
  - API keys, signed requests, `.env` edits, or credential handling.
  - Futures, leverage, borrow, liquidation, funding, or real margin behavior.
  - Model retuning, parameter search, feature search, or strategy redesign inside this validation task.
  - Frontend/backend API/dashboard work unless separately assigned.

# Context

Task 281 selected run `892` on the fixed 2026-05-20+ owner window:

- Strategy: `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Return: `+5.7295pct`.
- Completed round trips: `62`.
- Active trade days: `9`.
- Max drawdown: `-1.3248pct`.
- Cost/gross-PnL ratio: `0.4151`.
- Fee audit: `21,970,384.07` executed notional, `21,970.38` fee at `10.0` bps per execution, `40,668.89` total fee/spread/slippage cost, and `0` cost formula mismatches.

The result remains `PROMISING_RESEARCH_ONLY` because the selected strategy was chosen after inspecting the fixed owner window.

# Scope

- Add or update offline-only validation code under:
  - `quant_bitcoin/backtesting/`
- Add focused tests under:
  - `tests/backtesting/`
- Generate:
  - `reports/TASK_282_TASK281_LOCKED_OOS_WFO_VALIDATION_FROM_0420.md`
- Persist all validation runs to DB with additive metadata:
  - `research.task_id = TASK_282`
  - `research.source_task_id = TASK_281`
  - `research.locked_source_run_id = 892`
  - `research.locked_variant_id = T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`
  - validation window ID
  - validation group
  - cost profile
  - pass/fail status
  - no-retune declaration

# Out of Scope

- No strategy redesign.
- No new factor/model search.
- No parameter optimization or selecting a new best model.
- No zero-cost pass claim.
- No live trading.
- No real exchange order placement.
- No private/order/account endpoints.
- No API keys or `.env` changes.
- No futures, leverage, borrow, liquidation, funding, or real margin assumptions.
- No dashboard/backend API work.

# Requirements

## Locked Strategy

- Use the Task 281 selected variant exactly:
  - `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`
- Do not change:
  - core target/stop/hold geometry
  - scout target/stop/hold geometry
  - core/scout fractions
  - Sunday/session skip rule
  - preempt behavior
  - cost profile for primary validation
  - completed-candle-only entry logic
- Any code refactor must preserve the locked action stream for the original 2026-05-20+ owner window, or else explain and block completion.

## Data Windows

Primary validation must attempt these windows if data exists:

- `full_0420_latest`: 2026-04-20T00:00:00Z through latest locally available BTCUSDT 1m candle.
- `pre_owner_0420_0519`: 2026-04-20T00:00:00Z through 2026-05-19T23:59:00Z.
- `owner_replay_0520_latest`: 2026-05-20T00:00:00Z through latest locally available BTCUSDT 1m candle, used only as a reproducibility check against Task 281 run `892`.
- Weekly fixed slices:
  - `w1_0420_0426`
  - `w2_0427_0503`
  - `w3_0504_0510`
  - `w4_0511_0517`
  - `w5_0518_0524`
  - `w6_0525_latest`
- Endpoint-dependence slices:
  - `full_0420_latest_drop_first_day`
  - `full_0420_latest_drop_last_day`
  - `owner_0520_latest_drop_last_12h`
  - `owner_0520_latest_drop_last_24h`
- If the local DB has no candles before 2026-05-20, record that as a hard data blocker and do not fabricate April data.

## Cost And Stress Tests

- Primary validation runs must use `conservative_crypto_1m`.
- Cost stress runs must include at least:
  - `high_slippage_stress` on `full_0420_latest`
  - `high_slippage_stress` on `pre_owner_0420_0519`
  - `high_slippage_stress` on `owner_replay_0520_latest`
- Zero-cost runs are allowed only as diagnostics and must not be considered passing.
- Recompute cost formulas from persisted trade metadata:
  - fee = `gross_notional * fee_bps / 10000`
  - spread = `gross_notional * spread_bps / 10000`
  - slippage = `gross_notional * effective_slippage_bps / 10000`
  - total = fee + spread + slippage
- Record mismatch counts and max absolute mismatch.

## Robustness And Anomaly Checks

For each validation run, compute and report:

- total return
- completed round trips
- active trade days
- final equity
- closed-trade net PnL
- open-position contribution
- max drawdown
- gross PnL
- total fee/spread/slippage/total cost
- total executed notional
- effective one-way cost bps
- cost/gross-PnL ratio
- largest winner contribution
- top-three winner contribution
- best/worst day contribution
- core vs scout PnL and cost attribution
- long vs short PnL and trade count
- Sunday/session-filter concentration
- endpoint-trim sensitivity
- stress-cost sensitivity
- candle continuity/timestamp sorting status
- final open-position status
- any negative cash, impossible position, or cost mismatch anomaly

## Pass/Fail Interpretation

The locked strategy can be labeled `OOS_SUPPORTED_RESEARCH_ONLY` only if all of these hold:

- Original owner-window replay remains close to run `892` within explainable persistence/rerun tolerance.
- `full_0420_latest` is positive after costs.
- `pre_owner_0420_0519` is positive after costs.
- At least half of weekly slices with at least 10 completed round trips are positive after costs.
- No single trade contributes more than `40pct` of full-window net profit.
- Top three trades contribute no more than `70pct` of full-window net profit.
- Cost/gross-PnL ratio is below `0.60` on the full window.
- High-slippage stress does not flip full-window and pre-owner validation into a severe loss greater than `-3pct`.
- No cost-accounting mismatch, negative-cash anomaly, timestamp disorder, or live-trading boundary issue is found.

If any of these fail, report the strategy as one of:

- `LIKELY_OVERFIT_RESEARCH_ONLY`
- `UNSTABLE_RESEARCH_ONLY`
- `DATA_BLOCKED_RESEARCH_ONLY`
- `INVALID_DUE_TO_COST_OR_ACCOUNTING_ANOMALY`

No result may be promoted beyond research-only in this task.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm this task file is the assigned task before coding or running validation backtests.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Predeclare validation windows, cost profiles, and stop rules.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- [x] Task 282 validation runner or script is implemented under offline-only research boundaries.
- [x] The locked Task 281 run `892` variant is replayed without parameter retuning.
- [x] April 20 onward data availability is checked and recorded.
- [x] Every decision-driving validation run is persisted to DB with `research.task_id = TASK_282`.
- [x] Conservative-cost validation is attempted across the predeclared full, pre-owner, owner-replay, weekly, and endpoint-trim windows when data is available; full/endpoint windows with the 2026-05-17 to 2026-05-20 internal candle gap are recorded as blocked instead of forced.
- [x] High-slippage stress validation is attempted on the full, pre-owner, and owner-replay windows when data is available; the full stress window is recorded as blocked by the same internal candle gap.
- [x] Cost accounting is recomputed from persisted trade metadata and mismatch counts are reported.
- [x] Anomaly checks are reported.
- [x] Overfit/robustness conclusion is explicitly stated.
- [x] A report is saved at `reports/TASK_282_TASK281_LOCKED_OOS_WFO_VALIDATION_FROM_0420.md`.
- [x] No result is promoted beyond `RESEARCH_ONLY`.

# Execution Summary

- Completed on 2026-05-30.
- Implemented `quant_bitcoin/backtesting/t282_task281_locked_validation.py`.
- Added focused tests in `tests/backtesting/test_t282_task281_locked_validation.py`.
- Local BTCUSDT 1m data requested from `2026-04-20T00:00:00Z`; actual local availability starts at `2026-05-10T00:00:00Z` and ends at `2026-05-28T08:26:00Z`.
- Internal local candle gap found between `2026-05-17T15:19:00Z` and `2026-05-20T00:00:00Z`; full 0420-latest and related endpoint/stress full windows are blocked rather than forced.
- Persisted Task 282 DB run IDs: `900`, `901`, `902`, `903`, `904`, `905`, `906`, `907`, `908`, `909`.
- Owner replay run `901` reproduced Task 281 run `892`: `+5.7295pct`, `62` completed round trips, and zero cost-audit mismatches.
- Pre-owner conservative run `900` failed: `-2.7997pct`, `54` completed round trips, cost/gross-PnL `2.4482`.
- Pre-owner high-slippage stress run `908` failed severely: `-8.9497pct`.
- Weekly validation with at least 10 trips was mixed: `2/3` positive, with `w4_0511_0517` negative and post-owner weeks positive.
- Cost audit recomputed fee/spread/slippage from persisted metadata for all persisted Task 282 runs; mismatch count was `0` for every persisted run.
- Final interpretation: `LIKELY_OVERFIT_RESEARCH_ONLY`.
- Report saved at `reports/TASK_282_TASK281_LOCKED_OOS_WFO_VALIDATION_FROM_0420.md`.

# Required Tests

## Unit Tests

- Validation window generation is deterministic and bounded.
- Locked Task 281 candidate selection resolves only the run `892` variant.
- Cost-audit recomputation detects mismatched fee/spread/slippage metadata.
- Robustness gate classification is deterministic.

## Integration Tests

- Validation runner can execute a limited deterministic sample without live exchange calls.
- Persisted Task 282 metadata includes task ID, source task ID, locked source run ID, locked variant ID, window ID, validation group, cost profile, and no-retune declaration.
- Report generation includes pass/fail gates, cost audit, anomaly checks, and overfit conclusion.

## Contract Tests

- Existing saved-run schema fields are not removed or renamed.
- New metadata is additive.
- Existing Task 281 report and runner remain readable.

## Safety Tests

- No validation code imports execution clients.
- No test calls real exchange order/account/private endpoints.
- No API key, signed request, `.env`, or live trading behavior is added.
- All validation remains offline and deterministic.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No exchange order/account endpoint calls.
- No strategy retuning hidden inside validation.
- No unnecessary abstractions.

# Verification

Minimum focused verification:

```bash
pytest tests/backtesting -q
python -m compileall -q quant_bitcoin
git diff --check
```

At completion, verify Task 282 run IDs can be read back from DB and regenerated into the markdown report.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- all Task 282 run IDs
- data availability from 2026-04-20
- validation windows executed
- gate-by-gate pass/fail table
- cost-accounting audit result
- anomaly findings
- overfit/data-snooping conclusion
- Codex self-review result
- known limitations
- recommended next task
