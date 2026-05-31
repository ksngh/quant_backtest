# Task 287: Repaired 0420 Locked OOS/WFO Validation

# Goal

Run locked no-retune OOS/WFO validation on the repaired complete BTCUSDT 1-minute dataset from `2026-04-20T00:00:00Z` through the latest locally available candle, using realistic costs, strict data continuity, DB persistence, and robustness gates before any strategy promotion claim.

# Source Requirement

Owner requested after Task 286 repaired the missing BTCUSDT 1m data:

```text
ㅇㅇ 고고
```

Clean requirement:

- Use the Task 286 repaired BTCUSDT 1m data.
- Re-run locked validation across April-20-forward windows.
- Do not retune models against validation results.
- Persist every decision-driving validation run to DB.
- Clearly report whether the prior candidates remain rejected, become OOS-supported research-only, or require a new research task.

# Extracted Roles

- Owner role:
  - Wants the next validation step executed now that the missing 1m candle data is repaired.
- Supporting roles:
  - Quant validation lead: define locked OOS/WFO protocol, pass/fail gates, and final interpretation.
  - Backtest runner: execute locked candidates on repaired complete BTCUSDT 1m data and persist all runs.
  - Cost auditor: recompute fee/spread/slippage/notional/PnL from persisted trade metadata.
  - Data-quality auditor: verify strict 1m continuity before simulation.
  - Robustness analyst: evaluate independent windows, endpoint dependence, outlier dependence, side/session/regime attribution, and cost stress.
  - Reporting role: write a markdown report with run IDs, gate table, and research-only conclusion.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No strategy retuning, parameter search, or new factor/model discovery in this task.
  - No live trading.
  - No real Binance order execution.
  - No exchange private/order/account endpoints.
  - No API keys, signed requests, `.env` edits, or credential handling.
  - No futures, leverage, borrow, liquidation, funding, or real margin behavior.
  - No frontend/backend API/dashboard work unless separately assigned.

# Context

Task 286 repaired the BTCUSDT 1m data blocker:

- Repaired leading gap: `2026-04-20T00:00:00Z` through `2026-05-09T23:59:00Z`.
- Repaired internal gap: `2026-05-17T15:20:00Z` through `2026-05-19T23:59:00Z`.
- Inserted/fetched closed candles: `32200`.
- Verified continuous closed candle range: `2026-04-20T00:00:00Z` through `2026-05-28T08:26:00Z`.
- Verified closed candle count: `55227`.
- Verified duplicate BTCUSDT 1m open-time count: `0`.
- Report: `reports/TASK_286_BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR.md`.

Prior candidate state:

- Task 281 run `892`, `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`, passed the 2026-05-20+ owner window but failed available pre-owner/stress validation in Task 282.
- Task 283/284 best candidate `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` passed fixed owner windows but failed available pre-owner and robustness checks.
- Task 285 selected diagnostic repair `T285_R3_CORE_SHORT_ONLY_B2` with independent aggregate `+3.1737pct`, but rejected robustness because it had only `19` completed trips, positive windows were only `60pct`, return without top-three winners was `-2.2531pct`, earliest OOS was cost-dominated, and `2x` cost stress fell to `-3.6686pct`.
- These older failures were partly constrained by incomplete April/May data. Task 287 must rerun locked validation on the repaired complete data, not retune.

# Scope

- Add or update offline-only Task 287 validation code under:
  - `quant_bitcoin/backtesting/`
- Add focused tests under:
  - `tests/backtesting/`
- Generate:
  - `reports/TASK_287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION.md`
- Persist every decision-driving run to DB with additive metadata:
  - `research.task_id = TASK_287`
  - `research.parent_task_ids = [TASK_281, TASK_283, TASK_285, TASK_286]` where relevant
  - `research.validation_mode = repaired_0420_locked_oos_wfo`
  - `research.no_retune = true`
  - `research.research_only = true`
  - locked candidate ID
  - locked source task/run IDs when applicable
  - window ID, start, end, candle count, continuity status
  - cost profile and cost stress multiplier
  - pass/fail status and failure reasons
- Primary locked validation candidate:
  - Task 285 selected diagnostic repair: `T285_R3_CORE_SHORT_ONLY_B2`.
- Required locked comparison candidates:
  - Task 283/284 best candidate: `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`.
  - Task 281 selected candidate: `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Reuse existing Task 281/283/284/285 code paths where possible.
- If existing runners cannot replay a candidate on repaired data without retuning, record the exact blocker and do not silently approximate the strategy.

# Out of Scope

- No new model search.
- No parameter optimization.
- No factor discovery.
- No strategy redesign.
- No promotion beyond research-only.
- No live trading.
- No real Binance order placement.
- No signed/private/account endpoints.
- No API keys, secrets, or `.env` changes.
- No futures, leverage, liquidation, funding, borrow, or margin simulation.
- No frontend/backend API/dashboard changes.
- No data backfill beyond verifying Task 286 coverage; any new data gap must be recorded as a blocker.

# Requirements

## Data Validation

- Before any backtest, verify strict BTCUSDT 1m continuity over the requested validation range.
- Required target range:
  - Start: `2026-04-20T00:00:00Z`.
  - End: latest locally available BTCUSDT 1m candle, expected at least `2026-05-28T08:26:00Z`.
- Confirm:
  - no duplicate open times.
  - no missing 1m gaps.
  - OHLCV invariants pass.
  - timestamps are UTC-normalized.
  - closed candles only.
- If data validation fails, stop validation, save a blocker report, and do not fabricate or interpolate candles.

## Locked Candidate Rules

- Candidates must be replayed without retuning.
- Do not change entry logic, exit logic, cost assumptions, thresholds, sizing, session filters, regime filters, or side gates for locked validation.
- Any unavoidable code refactor must reproduce the original owner-window action stream or record a blocker.
- Fixed owner windows may be used only as replay diagnostics, not as sufficient evidence.
- If a candidate cannot be replayed exactly, classify it as `REPLAY_BLOCKED_RESEARCH_ONLY` and explain why.

## Validation Windows

Run or explicitly block these repaired-data windows:

- `full_0420_latest`: `2026-04-20T00:00:00Z` through latest local candle.
- `pre_owner_0420_0519`: `2026-04-20T00:00:00Z` through `2026-05-19T23:59:00Z`.
- `owner_replay_0520_latest`: `2026-05-20T00:00:00Z` through latest local candle.
- `owner_replay_0525_latest`: `2026-05-25T00:00:00Z` through latest local candle.
- Weekly/non-overlapping windows:
  - `w1_0420_0426`
  - `w2_0427_0503`
  - `w3_0504_0510`
  - `w4_0511_0517`
  - `w5_0518_0524`
  - `w6_0525_latest`
- Endpoint-dependence diagnostics:
  - `full_drop_first_6h`
  - `full_drop_first_24h`
  - `full_drop_last_6h`
  - `full_drop_last_24h`
  - `owner_0520_drop_last_12h`
  - `owner_0520_drop_last_24h`
- Walk-forward style slices:
  - at least three chronological train/test-like locked evaluation slices where no parameters are learned or changed; these are reporting partitions, not optimization folds.

## Cost And Execution Assumptions

- Primary validation must use the existing realistic conservative 1m cost profile used by Tasks 281-285, unless the candidate has a locked explicit cost profile that must be replayed.
- Cost stress must include:
  - `1x` base cost.
  - `2x` fee/spread/slippage stress.
  - `3x` fee/spread/slippage stress.
  - high-slippage stress matching prior Task 282/284 diagnostics if available.
- Zero-cost runs are allowed only as diagnostics and cannot pass promotion gates.
- Recompute cost formulas from persisted trade metadata:
  - entry and exit fees both included.
  - spread cost non-zero under realistic profiles.
  - slippage cost non-zero under realistic profiles.
  - total cost equals fee + spread + slippage.
  - formula mismatch count must be `0`.
  - summary mismatch count must be `0`.
- Preserve conservative same-candle stop/take ambiguity assumptions from the underlying candidate implementation.
- Preserve signal/execution separation and completed-candle-only factor timing.

## Metrics And Diagnostics

For every persisted validation run, compute and report:

- total return.
- final equity.
- net PnL.
- gross PnL.
- total cost.
- fee, spread, slippage.
- executed notional.
- effective one-way bps.
- cost/gross-PnL ratio.
- completed round trips.
- active trade days.
- win rate.
- average win/loss.
- profit factor.
- expectancy.
- max drawdown.
- max consecutive losses.
- average holding time.
- long-only result and short-only result.
- side trade counts.
- session/day-of-week attribution where available.
- regime attribution where available.
- largest winner contribution.
- top-three winner contribution.
- return without top one and top three winners.
- endpoint-trim sensitivity.
- cost-stress sensitivity.
- buy-and-hold baseline over the same window.
- simple MA baseline if already available or trivial to compute without adding strategy scope.
- final open-position contribution.
- negative cash or impossible position anomalies.

## Pass / Fail Gates

A candidate may be labeled `OOS_SUPPORTED_RESEARCH_ONLY` only if all of these pass:

- Full `2026-04-20+` net return is at least `+3pct` after realistic costs.
- Full `2026-04-20+` completed round trips are at least `50`.
- `pre_owner_0420_0519` net return is positive after realistic costs.
- At least `4` independent non-overlapping weekly/partial-week windows are tested.
- At least `75pct` of independent windows with at least `10` completed round trips are positive after costs.
- Aggregate independent-window net return exceeds `+3pct` after realistic costs.
- No single independent window contributes more than `60pct` of aggregate net PnL.
- No single trade contributes more than `40pct` of full-window net profit.
- Return without top-three winners remains positive.
- Cost/gross-PnL ratio is below `0.60` on the full window.
- `2x` cost stress does not turn full-window return below `-1pct`.
- `3x` cost stress is reported, even if it fails.
- Formula-level and summary-level cost audit mismatches are both `0`.
- No timestamp disorder, candle gap, negative-cash anomaly, impossible-position anomaly, or live-trading boundary violation is found.
- Owner-window replay results reproduce prior saved runs within explainable tolerance.

If any gate fails, classify the candidate as one of:

- `LIKELY_OVERFIT_RESEARCH_ONLY`
- `UNSTABLE_RESEARCH_ONLY`
- `COST_FRAGILE_RESEARCH_ONLY`
- `SAMPLE_SIZE_INSUFFICIENT_RESEARCH_ONLY`
- `REPLAY_BLOCKED_RESEARCH_ONLY`
- `INVALID_DUE_TO_COST_OR_ACCOUNTING_ANOMALY`

No candidate may be promoted beyond research-only in this task.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read this task file.
- [x] Read Task 281/282, Task 283/284, Task 285, and Task 286 reports/source files relevant to replay and validation.
- [x] Confirm the current active task is Task 287 before coding or running validation.
- [x] Confirm no frontend/backend/API/live-trading scope is needed.
- [x] Confirm Task 286 repaired data coverage is still present before running backtests.
- [x] Predeclare validation windows, candidate list, cost profiles, and stop rules.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` with Task 287 outcome, blocker state, and next task.
- [x] Append Task 287 completion or blocker summary to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark Task 287 completed, blocked, or split.
- [x] Save the Task 287 report under `reports/`.
- [x] Record all persisted run IDs in the report and status/history entries.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Execution Summary

- Implemented `quant_bitcoin/backtesting/t287_repaired_0420_locked_oos_wfo_validation.py`.
- Added focused tests in `tests/backtesting/test_t287_repaired_0420_locked_oos_wfo_validation.py`.
- Generated `reports/TASK_287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION.md`.
- Persisted Task 287 DB runs `1085` through `1159` inclusive, `75` runs total.
- Repaired data guard passed:
  - start `2026-04-20T00:00:00Z`
  - end `2026-05-28T08:26:00Z`
  - closed candles `55227`
  - expected continuous candles `55227`
  - gaps `0`
  - duplicate open-time groups `0`
- Primary `T285_R3_CORE_SHORT_ONLY_B2` result:
  - full `2026-04-20+`: `-13.0706pct`, `50` completed trips.
  - pre-owner `2026-04-20` through `2026-05-19`: `-17.4283pct`.
  - owner replay `2026-05-20+`: `+6.1764pct`, `10` completed trips.
  - owner replay `2026-05-25+`: `+3.6703pct`, `5` completed trips.
  - independent weekly aggregate: `-8.2103pct`, positive windows `0.3333`.
  - 2x cost full return: `-27.9587pct`.
  - 3x cost full return: `-40.2970pct`.
  - high-slippage full return: `-32.4273pct`.
- Task 283 comparator result:
  - full `2026-04-20+`: `-15.0301pct`, `318` completed trips.
  - independent weekly aggregate: `-10.0735pct`.
- Task 281 comparator result:
  - full `2026-04-20+`: `-14.7305pct`, `318` completed trips.
  - independent weekly aggregate: `-10.0970pct`.
- Final Task 287 status: `LOCKED_PRIMARY_REJECTED_RESEARCH_ONLY`.
- Cost verification readback:
  - task287 run count `75`
  - run/result `validation_mode=repaired_0420_locked_oos_wfo` count `75`/`75`
  - run/result source-reference run ID count `75`/`75`
  - bad research metadata `0`
  - formula mismatches `0`
  - summary mismatches `0`
  - non-zero fee/spread/slippage runs `75`
  - max absolute mismatch `0`
- No strategy was promoted beyond research-only.
- Added Korean strategy failure analysis document:
  - `docs/research/TASK_287_STRATEGY_FAILURE_ANALYSIS_KO.md`
  - Covers the selected strategy's microstructure/economic rationale, exact signal/risk-cost math, experiment protocol, validation limits, and why the strategy failed.
  - No new model-development task was created in this documentation step.

# Verification Results

```bash
python -m pytest tests/backtesting/test_t287_repaired_0420_locked_oos_wfo_validation.py -q
# 7 passed

python -m compileall quant_bitcoin/backtesting/t287_repaired_0420_locked_oos_wfo_validation.py tests/backtesting/test_t287_repaired_0420_locked_oos_wfo_validation.py
# passed

python -m quant_bitcoin.backtesting.t287_repaired_0420_locked_oos_wfo_validation
# wrote reports/TASK_287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION.md with 75 persisted Task 287 runs

python -m pytest tests/backtesting/test_t281_high_activity_model.py tests/backtesting/test_t283_principle_first_microstructure_strategy.py tests/backtesting/test_t284_task283_multi_axis_robustness_revalidation.py tests/backtesting/test_t285_regime_robust_multi_window_strategy_repair.py tests/backtesting/test_t287_repaired_0420_locked_oos_wfo_validation.py -q
# 31 passed
```

# Acceptance Criteria

- A Task 287 locked validation runner exists or existing runners are orchestrated without retuning.
- Strict repaired-data coverage is verified before simulation.
- The Task 285 selected candidate is replayed on repaired full `2026-04-20+` data or explicitly blocked.
- Task 281 and Task 283/284 locked comparison candidates are replayed or explicitly blocked.
- All decision-driving validation runs are persisted to DB with `research.task_id = TASK_287`.
- Realistic cost, `2x`, and `3x` cost stress results are reported.
- Cost audit mismatch counts are computed and are `0` for any candidate considered valid.
- Independent windows, owner replay windows, endpoint trims, side attribution, outlier attribution, and baselines are included in the report.
- The report clearly states final status for each candidate and an overall Task 287 conclusion.
- No strategy is promoted beyond research-only.
- No live trading, signed requests, private endpoints, API keys, `.env`, futures, or leverage behavior is added.

# Required Tests

## Unit Tests

- Repaired validation window generation is deterministic.
- Candidate registry resolves the exact locked candidate IDs and rejects unknown IDs.
- Coverage guard rejects missing gaps or duplicate timestamps.
- Pass/fail gate evaluator enforces `+3pct`, `50` trips, independent-window, outlier, and cost-stress gates.
- Cost audit helper catches formula and summary mismatches.
- Report summary serializes UTC ISO timestamps and candidate statuses deterministically.

## Integration Tests

- Task 287 runner can execute a small deterministic fixture across multiple windows without network or live exchange calls.
- Persisted-style metadata includes `research.task_id = TASK_287`, no-retune flag, repaired-data declaration, candidate ID, window ID, and cost profile.
- A synthetic failed candidate is classified as research-only with clear failure reasons.

## Contract Tests

- Existing Task 281/282/283/284/285 tests continue to pass.
- Backtest persistence metadata remains additive and backward compatible.
- No backend/frontend API contract changes are introduced.

## Safety Tests

- No Binance order/account/private endpoint is imported or called.
- No `.env`, API-key, signed request, futures, leverage, or live-order behavior is added.
- Task 287 runner uses local persisted candles only for strategy validation.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected.
- No hardcoded secrets.
- No real order execution.
- No signed/private/account endpoints.
- No unnecessary abstractions.
- Candidate replay is locked and no-retune.
- Repaired data coverage is verified before simulation.
- Owner windows are diagnostic, not the only OOS evidence.
- Results remain research-only.

# Verification

Default focused verification:

```bash
pytest tests/backtesting/test_t281_high_activity_model.py tests/backtesting/test_t282_task281_locked_validation.py tests/backtesting/test_t283_principle_first_microstructure_strategy.py tests/backtesting/test_t284_task283_multi_axis_robustness_revalidation.py tests/backtesting/test_t285_regime_robust_multi_window_strategy_repair.py -q
python -m compileall -q quant_bitcoin
git diff --check
```

If Task 287 adds tests:

```bash
pytest tests/backtesting/test_t287_repaired_0420_locked_oos_wfo_validation.py -q
```

Task-specific runtime verification must include the Task 287 validation command and the saved report path.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- validation candidates executed
- validation windows executed
- DB run IDs persisted
- cost audit result
- multi-window pass/fail result
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
