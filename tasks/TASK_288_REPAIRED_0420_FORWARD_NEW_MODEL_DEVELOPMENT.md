# Task 288: Repaired 0420-Forward New Model Development

# Goal

Develop a new deterministic BTCUSDT 1-minute research model on the repaired April-20-forward dataset after Task 287 rejected the prior Task 281/283/285 lineage.

This task is not a rejection-only validation pass. It must implement new principle-first factor, pattern, or strategy logic, run enough DB-persisted backtests, inspect failures, revise the model inside the same task, and continue the implementation/backtest/revision loop until a candidate passes the acceptance gates or a hard data/runtime/safety blocker prevents further trustworthy execution.

Any result remains `RESEARCH_ONLY`. Passing this task does not approve live trading, futures, leverage, margin, or promotion to production.

# Source Requirement

Owner request:

```text
ㅇㅇ 새 모델 개발 task 만들어줘
```

Clean requirement:

- Create a new task for post-Task-287 model development.
- Use the Task 286 repaired BTCUSDT 1m data and the Task 287 failure analysis.
- The next task must allow new deterministic factors, indicators, patterns, and model combinations.
- The next task must not stop merely because the first candidate fails.
- The next task must require realistic fee/spread/slippage accounting, enough trades, consistency across windows, and overfit checks.
- Do not implement or run the new task during this task-creation step.

# Extracted Roles

- Owner role:
  - Wants a new model-development task after the prior locked strategy failed.
  - Wants the next implementation pass to keep iterating rather than ending at a rejection-only report.
- Supporting roles:
  - Quant research lead: derive new model hypotheses from market microstructure principles and Task 287 failure modes.
  - Factor engineer: build completed-candle-only deterministic factors without look-ahead bias.
  - Strategy engineer: implement offline-only candidate signal and exit logic.
  - Backtest engineer: run realistic-cost BTCUSDT 1m backtests on repaired data and persist decision-driving runs to DB.
  - Cost auditor: recompute fee, spread, slippage, notional, gross PnL, and net PnL from persisted trades.
  - Robustness analyst: evaluate full, owner, pre-owner, weekly, WFO, endpoint, cost-stress, outlier, side, session, and regime diagnostics.
  - Reporting role: write a markdown report with candidate formulas, run IDs, pass/fail gates, and research-only conclusion.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - No live trading.
  - No real Binance order execution.
  - No signed/private/order/account exchange endpoints.
  - No API keys, `.env` edits, credential handling, or secret storage.
  - No futures, leverage, borrow, liquidation, funding, or real margin behavior.
  - No machine-learning model unless a later task explicitly authorizes ML.
  - No frontend/backend API/dashboard work unless separately assigned.
  - No strategy promotion beyond research-only.

# Context

Task 286 repaired the local BTCUSDT 1m data blocker:

- Repaired range: `2026-04-20T00:00:00Z` through `2026-05-28T08:26:00Z`.
- Closed candles: `55227`.
- Continuity gaps: `0`.
- Duplicate open-time groups: `0`.
- Report: `reports/TASK_286_BTCUSDT_1M_DATA_BACKFILL_AND_GAP_REPAIR.md`.

Task 287 then replayed the prior locked candidates without retuning:

- Primary candidate: `T285_R3_CORE_SHORT_ONLY_B2`.
- Comparators:
  - `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`.
  - `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Persisted DB runs: `1085` through `1159`.
- Task 287 primary result:
  - full `2026-04-20+`: `-13.0706pct`, `50` completed trips.
  - pre-owner `2026-04-20` through `2026-05-19`: `-17.4283pct`.
  - owner replay `2026-05-20+`: `+6.1764pct`, `10` completed trips.
  - owner replay `2026-05-25+`: `+3.6703pct`, `5` completed trips.
  - independent weekly aggregate: `-8.2103pct`.
  - 2x cost full return: `-27.9587pct`.
  - 3x cost full return: `-40.2970pct`.
- Task 287 cost audit:
  - `75` Task 287 runs.
  - non-zero fee/spread/slippage on all `75`.
  - formula mismatches: `0`.
  - summary mismatches: `0`.

Task 287 Korean failure analysis:

- `docs/research/TASK_287_STRATEGY_FAILURE_ANALYSIS_KO.md`
- Key diagnosis:
  - The rejected model was a short-only failed-rally/liquidity-sweep fade.
  - Owner-window gains were concentrated in a later bearish regime.
  - Full 0420+ and pre-owner windows failed badly.
  - Costs were correctly applied and overwhelmed weak gross edge.
  - The nominal 2R structure became much weaker after realistic one-way cost near `18.8` bps.
  - Prior models were too exposed to regime dependence, outlier winners, and owner-window selection.

Task 288 must explicitly address these failure modes instead of only retuning the same short-only sweep fade.

# Scope

- Add or update offline-only Task 288 research code under:
  - `quant_bitcoin/backtesting/`
  - `quant_bitcoin/indicators/` only if a reusable deterministic indicator is needed.
  - `quant_bitcoin/patterns/` only if a reusable deterministic pattern detector is needed.
  - `quant_bitcoin/strategies/` only if the model naturally belongs as a reusable strategy component.
- Add focused tests under:
  - `tests/backtesting/`
  - `tests/indicators/`, `tests/patterns/`, or `tests/strategies/` only if those areas are changed.
- Generate:
  - `reports/TASK_288_REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT.md`
- Persist every decision-driving backtest run to DB with additive metadata:
  - `research.task_id = TASK_288`
  - `research.parent_task_ids = [TASK_286, TASK_287]`
  - `research.validation_mode = repaired_0420_forward_new_model_development`
  - `research.research_only = true`
  - `research.no_live_trading = true`
  - candidate ID, model family, batch ID, and thesis ID
  - factor snapshot version
  - window ID, start, end, candle count, and continuity status
  - cost profile and cost stress multiplier
  - entry/exit/skip reason metadata
  - pass/fail status and failure reasons
- Use local persisted candles only.
- Use completed-candle-only factor timing.
- Long and research-only cash-bounded synthetic short simulations are allowed inside the backtester.
- Synthetic short behavior must remain a research accounting simulation only; it must not imply futures, margin, borrow, liquidation, or live short availability.

# Out of Scope

- No live trading.
- No real exchange order placement.
- No signed/private/order/account Binance endpoints.
- No public data backfill. If a new data gap is found, record it as a blocker and stop the affected run.
- No API keys, secrets, or `.env` changes.
- No futures, leverage, borrow, funding, liquidation, or real margin modeling.
- No machine learning, hyperparameter optimizer framework, portfolio optimizer, or black-box model.
- No frontend/backend API/dashboard changes.
- No production promotion, paper-trading activation, or live-trading readiness claim.
- No owner-window-only promotion.
- No silent interface redesign of shared backtest result, strategy signal, or persistence contracts.

# Requirements

## Data And Timing Requirements

- Verify strict BTCUSDT 1m data continuity before all decision-driving runs.
- Required local range:
  - start: `2026-04-20T00:00:00Z`
  - end: latest locally available candle, expected at least `2026-05-28T08:26:00Z`
- Confirm:
  - no missing 1m gaps.
  - no duplicate open times.
  - OHLCV invariants pass.
  - timestamps are UTC-normalized.
  - only closed candles are used.
- Signal generation must use completed candles only.
- Execution must be separated from signal generation:
  - signal candle close first.
  - entry on the next executable candle rule.
  - exit handling must state whether it is same-candle, next-open shifted, or close-based.
- If both stop and take-profit are touched in the same 1m candle, use the conservative stop-first assumption unless a candidate explicitly uses next-open shifted exits that avoid intrabar ordering.

## Required Model Development Loop

The implementation task must not stop after a single failed candidate.

Required loop:

1. Start from Task 287 failure modes.
2. Build or reuse completed-candle factor snapshots.
3. Implement at least two materially different principle-first candidate families.
4. Run realistic-cost backtests on predeclared windows.
5. Persist decision-driving runs.
6. Audit cost formulas and summaries.
7. Diagnose failure by trade count, cost drag, side concentration, outlier dependence, regime dependence, and window dependence.
8. Revise candidate logic or add a new candidate family based on that diagnosis.
9. Repeat until:
   - a candidate passes all acceptance gates, or
   - a hard data blocker appears, or
   - a runtime blocker makes further trustworthy execution infeasible, or
   - a safety boundary would be violated, or
   - the owner explicitly pauses.

Do not mark the task complete solely because several candidates failed. A failure-only completion is allowed only when a hard blocker is demonstrated with evidence, or when a broad enough implemented search shows a hard-data constraint similar to Task 280 and the report quantifies why further in-task iteration would be untrustworthy.

## Principle-First Candidate Families

Each candidate must begin from a market phenomenon, not from a simple indicator recipe.

The task must implement or combine at least two of these families:

1. Volatility compression to directional expansion:
   - Rationale: low realized volatility and narrow ranges can accumulate stop orders; breakout can trigger momentum and liquidation-like follow-through.
   - Candidate factors: ATR percentile, realized volatility percentile, Bollinger width percentile, range compression, body expansion, volume expansion, close location value.
   - Must distinguish real breakout from immediate fakeout.
2. Failed auction with continuation/fade discriminator:
   - Rationale: prior failed sweep logic failed because it did not distinguish stop-hunt reversal from squeeze continuation.
   - Candidate factors: sweep depth, close-back-inside strength, displacement body ratio, volume spike, next-bar acceptance/rejection, retest success/failure.
   - Must not simply replay `T285_R3_CORE_SHORT_ONLY_B2`.
3. Trend-aligned pullback continuation:
   - Rationale: BTC can trend after directional pressure, forced liquidations, and momentum participation; pullbacks in aligned regimes may provide better R than chasing breakouts.
   - Candidate factors: EMA/MA slope, rolling HH/HL or LL/LH, ADX-like trend strength if implemented, higher-timeframe resampled trend, pullback depth, volatility-adjusted stop distance.
4. Range-bound mean reversion:
   - Rationale: when trend strength is low and volatility is not expanding, large short-term deviations can mean-revert after liquidity exhaustion.
   - Candidate factors: z-score from rolling mean/VWAP proxy, wick rejection, body reversal, volume spike exhaustion, range percentile, trend filter.
   - Must be disabled in strong trend regimes.
5. Session liquidity regime model:
   - Rationale: BTC trades 24/7 but session liquidity and volatility differ; Asia/Europe/US overlaps can change breakout/fade expectancy.
   - Candidate factors: hour of day, day of week, session high/low, session range, daily open distance, volatility by session.
6. Regime-switching deterministic ensemble:
   - Rationale: Task 287 failed partly because one fixed short-only rule was regime-dependent.
   - Candidate structure: choose breakout, fade, pullback, or no-trade mode using predeclared completed-candle regime features.
   - Must expose the selected regime and submodel in trade metadata.

Any candidate may be long-only, short-only, or both-sided, but a one-sided model must have an explicit market-structure rationale and must pass side/regime concentration checks.

## Required Factors And Metadata

At minimum, factor snapshots must include enough fields to explain each candidate:

- rolling returns over short and medium horizons.
- realized volatility or ATR proxy.
- volatility percentile or regime bucket.
- range percentile or compression metric.
- rolling high/low and breakout/sweep distance.
- candle body ratio and wick ratios.
- close location in candle range.
- volume ratio or volume percentile.
- session/hour/day-of-week.
- higher-timeframe trend proxy from completed 1m resampling, if used.
- fee-adjusted expected reward/risk at entry.

Trade metadata must include:

- candidate ID.
- model family.
- entry reason.
- invalidation reason if skipped.
- factor snapshot at signal time.
- entry price source.
- stop price and stop source.
- target price and target source.
- max hold.
- expected gross R.
- expected net R after estimated costs.
- fee/spread/slippage assumptions.
- exit reason.
- realized gross/net PnL.
- fee/spread/slippage cost breakdown.

## Cost And Execution Requirements

- Use the existing realistic 1m conservative cost profile as the primary assumption unless the codebase has renamed it:
  - taker fee.
  - spread.
  - base slippage.
  - minimum slippage.
  - volatility slippage multiplier.
- Base validation must include non-zero fee, spread, and slippage.
- Stress validation must include:
  - `1x` base cost.
  - `2x` fee/spread/slippage stress.
  - `3x` fee/spread/slippage stress.
  - high-slippage stress comparable to Task 287.
- Zero-cost runs are allowed only as diagnostics and cannot pass acceptance gates.
- Recompute persisted trade-level costs:
  - entry and exit fees are both included.
  - spread cost is non-zero under realistic profiles.
  - slippage cost is non-zero under realistic profiles.
  - total cost equals fee + spread + slippage.
  - formula mismatch count must be `0`.
  - summary mismatch count must be `0`.
- Pre-entry cost-aware reward/risk gate is required:
  - A candidate must not enter if the estimated net reward after fee/spread/slippage is non-positive.
  - A candidate must not enter if net expected R is below the candidate's declared minimum.

## Validation Windows

Run or explicitly block these repaired-data windows:

- `full_0420_latest`: `2026-04-20T00:00:00Z` through latest local candle.
- `pre_owner_0420_0519`: `2026-04-20T00:00:00Z` through `2026-05-19T23:59:00Z`.
- `owner_replay_0520_latest`: `2026-05-20T00:00:00Z` through latest local candle.
- `owner_replay_0525_latest`: `2026-05-25T00:00:00Z` through latest local candle.
- Weekly/non-overlapping independent windows:
  - `w1_0420_0426`
  - `w2_0427_0503`
  - `w3_0504_0510`
  - `w4_0511_0517`
  - `w5_0518_0524`
  - `w6_0525_latest`
- Walk-forward style reporting partitions:
  - `wfo_0420_0503`
  - `wfo_0504_0517`
  - `wfo_0518_latest`
- Endpoint-dependence diagnostics:
  - `full_drop_first_6h`
  - `full_drop_first_24h`
  - `full_drop_last_6h`
  - `full_drop_last_24h`
  - `owner_0520_drop_last_12h`
  - `owner_0520_drop_last_24h`

Because all currently local 0420-forward data has already been inspected in earlier research, any passing result is still research-only. The report must explicitly state that true promotion would require future unseen data.

## Required Metrics

For each persisted run, compute or report:

- total return.
- final equity.
- gross PnL.
- net PnL.
- total cost.
- fee, spread, and slippage cost.
- executed notional.
- effective one-way bps.
- cost/gross-PnL ratio.
- completed round trips.
- active trading days.
- win rate.
- average win.
- average loss.
- profit factor.
- expectancy.
- average R and median R if available.
- max drawdown.
- max consecutive losses.
- average holding time.
- long-only and short-only contribution.
- side trade counts.
- session/hour/day-of-week attribution.
- volatility regime attribution.
- largest winner contribution.
- top-three winner contribution.
- return without top one and without top three winners.
- endpoint-trim sensitivity.
- cost-stress sensitivity.
- no-cost diagnostic delta.
- buy-and-hold baseline over the same window.
- simple MA baseline if already available or trivial to compute.
- final open-position contribution.
- negative cash, impossible position, timestamp disorder, or data-gap anomalies.

## Acceptance Gates

A candidate may be labeled `TARGET_PASSED_RESEARCH_ONLY` only if all required gates pass:

- Full `2026-04-20+` net return is at least `+3pct` after realistic costs.
- Full `2026-04-20+` completed round trips are at least `50`.
- `owner_replay_0520_latest` net return is at least `+3pct` after realistic costs.
- `owner_replay_0520_latest` completed round trips are at least `50`.
- `owner_replay_0525_latest` net return is at least `+3pct` after realistic costs.
- `owner_replay_0525_latest` completed round trips are at least `20`.
- `pre_owner_0420_0519` net return is positive after realistic costs.
- At least `4` independent weekly/partial-week windows are tested.
- At least `75pct` of independent windows with at least `10` completed round trips are positive after costs.
- Aggregate independent-window net return is at least `+3pct` after realistic costs.
- No single independent window contributes more than `60pct` of aggregate net PnL.
- No single trade contributes more than `40pct` of full-window net profit.
- Return without top-three winners remains positive on the full window.
- Cost/gross-PnL ratio is below `0.60` on the full window.
- `2x` cost stress does not turn full-window return below `-1pct`.
- `3x` cost stress is reported.
- Formula-level and summary-level cost audit mismatches are both `0`.
- No timestamp disorder, data gap, duplicate candle, negative-cash anomaly, impossible-position anomaly, or live-trading boundary violation is found.
- Candidate beats buy-and-hold on the full window after costs.
- Candidate beats a simple MA baseline on the full window if the baseline is implemented in this task.
- Parameter sensitivity is not a single-point optimum:
  - adjacent parameter variants around the selected candidate must not collapse into strongly negative full-window performance.
  - exact thresholds must not be over-precise without a market-structure reason.

If a candidate fails, classify it using one or more:

- `LIKELY_OVERFIT_RESEARCH_ONLY`
- `UNSTABLE_RESEARCH_ONLY`
- `COST_FRAGILE_RESEARCH_ONLY`
- `SAMPLE_SIZE_INSUFFICIENT_RESEARCH_ONLY`
- `REGIME_DEPENDENT_RESEARCH_ONLY`
- `OUTLIER_DEPENDENT_RESEARCH_ONLY`
- `REPLAY_OR_DATA_BLOCKED_RESEARCH_ONLY`
- `INVALID_DUE_TO_COST_OR_ACCOUNTING_ANOMALY`
- `HARD_DATA_CONSTRAINT_RESEARCH_ONLY`

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md`.
- [ ] Read this task file.
- [ ] Read `docs/research/TASK_287_STRATEGY_FAILURE_ANALYSIS_KO.md`.
- [ ] Read `reports/TASK_287_REPAIRED_0420_LOCKED_OOS_WFO_VALIDATION.md`.
- [ ] Read relevant Task 286/287 source and tests.
- [ ] Confirm the current active task is Task 288 before coding.
- [ ] Confirm no frontend/backend/API/live-trading scope is needed.
- [ ] Confirm repaired BTCUSDT 1m data coverage is still present.
- [ ] Predeclare candidate families, windows, costs, and pass/fail gates before running the search.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` with Task 288 outcome, blocker state, and next task.
- [ ] Append Task 288 completion or blocker summary to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` to mark Task 288 completed, blocked, or split.
- [ ] Save the Task 288 report under `reports/`.
- [ ] Record all persisted run IDs in the report and status/history entries.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Task 288 implements at least two materially different principle-first candidate families.
- The implementation uses completed-candle-only factors and avoids look-ahead bias.
- Every decision-driving run is persisted to DB with `research.task_id = TASK_288`.
- Realistic fee/spread/slippage costs are non-zero on all realistic-cost decision runs.
- Cost formula mismatch count is `0`.
- Cost summary mismatch count is `0`.
- At least one candidate either:
  - passes all acceptance gates and is labeled `TARGET_PASSED_RESEARCH_ONLY`, or
  - the task documents a hard blocker or hard-data constraint with enough evidence to justify stopping.
- The final report includes:
  - market phenomenon and economic rationale for each candidate family.
  - exact factor formulas.
  - entry, stop, target, max-hold, and early-exit logic.
  - gross and net risk/reward math.
  - cost/slippage break-even analysis.
  - run IDs and window table.
  - side, session, volatility-regime, and outlier attribution.
  - cost-stress and no-cost diagnostics.
  - overfit assessment.
  - final research-only conclusion.
- No live trading, exchange orders, private endpoints, secrets, futures, leverage, or margin behavior are added.
- Project state files are updated after execution.

# Required Tests

## Unit Tests

- Factor snapshots use only completed/prior candles.
- Candidate signal formulas are deterministic.
- Entry, stop, target, max-hold, and early-exit calculations are correct for both long and short if both sides are supported.
- Pre-entry net reward/risk gate rejects cost-negative or below-threshold trades.
- Same-candle stop/take ambiguity uses the declared conservative rule.
- Cost audit helper catches fee, spread, slippage, and summary mismatches.
- Acceptance-gate evaluator classifies pass/fail reasons correctly.
- Parameter sensitivity evaluator rejects single-point fragile candidates.

## Integration Tests

- Task 288 runner can execute a small deterministic fixture without network calls.
- At least two candidate families can be registered and evaluated.
- Persisted-style metadata includes `research.task_id = TASK_288`, candidate ID, model family, window ID, cost profile, and research-only flags.
- A synthetic passing candidate is classified as `TARGET_PASSED_RESEARCH_ONLY`.
- A synthetic failed candidate records failure reasons and does not pass.

## Contract Tests

- Existing Task 281/283/285/287 tests continue to pass unless the task explicitly changes shared helpers with backward-compatible behavior.
- Backtest persistence metadata remains additive and backward compatible.
- No backend/frontend API contract changes are introduced.

## Safety Tests

- No Binance order/account/private endpoint is imported or called.
- No `.env`, API-key, signed request, futures, leverage, or live-order behavior is added.
- Task 288 runner uses local persisted candles only.
- Strategy code does not fetch exchange data or place exchange orders.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected.
- No hardcoded secrets.
- No real order execution.
- No signed/private/account endpoints.
- No futures/leverage/margin behavior.
- No machine-learning or black-box optimizer scope creep.
- No frontend/backend/API scope creep.
- No unnecessary abstractions.
- Candidate families are principle-first, not simple RSI-style indicator recipes.
- Completed-candle-only timing is explicit.
- Cost/slippage assumptions are explicit and audited.
- Owner-window results are not the only evidence.
- Results remain research-only.

# Verification

Default focused verification:

```bash
pytest tests/backtesting/test_t288_repaired_0420_forward_new_model_development.py -q
python -m compileall -q quant_bitcoin tests
git diff --check
```

If shared Task 281/283/285/287 helpers are touched:

```bash
pytest tests/backtesting/test_t281_high_activity_model.py \
  tests/backtesting/test_t283_principle_first_microstructure_strategy.py \
  tests/backtesting/test_t285_regime_robust_multi_window_strategy_repair.py \
  tests/backtesting/test_t287_repaired_0420_locked_oos_wfo_validation.py \
  tests/backtesting/test_t288_repaired_0420_forward_new_model_development.py -q
```

Task-specific runtime verification must include:

```bash
python -m quant_bitcoin.backtesting.t288_repaired_0420_forward_new_model_development
```

The runtime command must save `reports/TASK_288_REPAIRED_0420_FORWARD_NEW_MODEL_DEVELOPMENT.md` and persist decision-driving DB runs before the task can be completed.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- candidate families implemented
- validation windows executed
- DB run IDs persisted
- cost audit result
- pass/fail gate result
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
