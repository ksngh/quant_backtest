# Task 281: Owner Window 0520 High-Activity Target Return Search

# Goal

Develop and backtest an offline-only BTCUSDT 1-minute strategy search focused on the single owner window starting 2026-05-20, with enough activity and net return to address the owner feedback that Task 280 traded too little and produced only about 0.3pct.

The task must iterate implementation and DB-persisted backtests until a candidate reaches at least +3.0pct net return after realistic costs on the 2026-05-20+ window while completing at least 50 round trips, or until a hard data/runtime/safety blocker prevents trustworthy continuation.

# Source Requirement

Owner feedback after Task 280:

```text
1. 거래가 너무 적고 2. 3퍼센트가 아니라 0.3퍼센트잖아 다시 해.. 데이터구조 충돌해도 그냥 너가 알아서 조절해. 최소 50번의 거래는 넘어야 해.
3. 그리고 5월 20일자부터 하는걸로 기준으로 해줘. 지금도 마찬가지로 3퍼센트나올때까지 계속하고, 안나오면 반복해야해.
```

Clean requirement:

- Use only the owner target window starting 2026-05-20 as the primary pass/fail benchmark.
- A candidate must complete at least 50 round trips on that window.
- A candidate must produce at least +3.0pct total return after realistic costs.
- If the current model does not pass, continue iterating within this task.
- Missing the +3.0pct or 50-round-trip target is not a stopping condition by itself; continue revising and rerunning within Task 281.
- The agent may adjust model structure, entry frequency, exit timing, spot cash sizing, and may introduce new deterministic models, new indicators, and new pattern detectors within explicit safety boundaries.
- Keep all work offline and research-only.

# Extracted Roles

- Owner role:
  - Rejects low-activity and +0.3pct style results.
  - Wants the target measured from 2026-05-20 only.
  - Allows the research agent to adjust the model and assumptions within the project safety boundary, including new deterministic models, indicators, and patterns.
- Supporting roles:
  - Quant research lead: design high-activity deterministic OHLCV-only candidate families.
  - Strategy implementation role: add or update offline-only research/backtest code.
  - Backtest runner: persist every decision-driving run to DB.
  - Diagnostics role: inspect trade count, net return, cost drag, side/regime behavior, drawdown, and outlier dependence to choose the next batch.
  - Reporting role: update the Task 281 markdown report with run IDs and gate checks.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - Live trading.
  - Real Binance order execution.
  - Exchange private/order/account endpoints.
  - API keys, signed requests, `.env` edits, or credential handling.
  - Futures, leverage, liquidation, funding, or real margin behavior.
  - Machine learning, black-box optimization, unbounded parameter search, or hidden fitting.
  - Frontend/backend API/dashboard work unless separately assigned.

# Context

Task 280 persisted 576 Task 280 DB runs and did not find a candidate that passed its stricter two-window, primary 10pct sizing gates. The best combined Task 280 candidate was `T280_B9_PULLBACK_TW720_TH30P0_CW360_TG250P0_ST120P0`, with Window A return `+0.2057pct` over 9 trips and Window B return `+0.3001pct` over 4 trips at `cash_fraction=0.10`.

The owner now changes the target:

- Primary benchmark is only 2026-05-20+.
- Minimum activity is at least 50 completed round trips.
- Net return target remains +3.0pct.
- The agent should adjust the approach instead of stopping on the prior data-structure blocker.
- The agent must not stop merely because a batch does not reach +3.0pct or 50 round trips; those failures are diagnostics for the next in-task batch.

# Scope

- Create or update offline-only research code under:
  - `quant_bitcoin/backtesting/`
  - `quant_bitcoin/strategies/`
  - `quant_bitcoin/patterns/`
  - `quant_bitcoin/indicators/`
- Add focused tests under:
  - `tests/backtesting/`
  - `tests/strategies/`
  - `tests/patterns/`
  - `tests/safety/`
- Persist all decision-driving owner-window backtests to DB.
- Generate `reports/TASK_281_OWNER_WINDOW_0520_HIGH_ACTIVITY_TARGET_RETURN_SEARCH.md`.
- Reuse additive research metadata conventions:
  - `research.task_id = TASK_281`
  - stable variant ID
  - run group
  - window ID
  - cost profile
  - sizing
  - result status

# Out of Scope

- No live trading.
- No real exchange order placement.
- No private/order/account endpoints.
- No API keys or `.env` changes.
- No futures, leverage, borrow, liquidation, funding, or real margin assumptions.
- No dashboard/backend API work.
- No zero-cost pass claim.
- No hidden lookahead accepted as a valid strategy.
- No unbounded manual curve fitting.

# Requirements

## Primary Window

- Window A only:
  - Start: `2026-05-20T00:00:00Z`.
  - End: latest locally available BTCUSDT 1m candle at execution time.
- If the local DB still ends at `2026-05-28T08:26:00Z`, use that as the actual end and record it in the report.

## Costs

- Primary runs must use `conservative_crypto_1m`.
- Fee, spread, slippage, minimum slippage, and volatility slippage must remain non-zero and be verified from persisted DB rows.
- Zero-cost runs may be used only as diagnostics and must not be accepted.
- Cost accounting must be summarized in the report.

## Activity And Return Gates

A candidate can be reported as `PROMISING_RESEARCH_ONLY` only if all of these pass on the 2026-05-20+ owner window:

- Total return after costs is at least `+3.0pct`.
- Completed round trips are at least `50`.
- Active trade days are at least `5`.
- Cost-to-gross-PnL ratio is below `0.60` unless the candidate has at least `100` round trips and positive daily consistency justifies a high-frequency cost profile.
- No single trade contributes more than `40pct` of net profit.
- Top three trades contribute no more than `70pct` of net profit.
- Final equity, closed-trade PnL, and open-position contribution are separated.
- Candle continuity and timestamp sorting are verified.

## Allowed Adjustments

Within offline research-only boundaries, the implementation may adjust:

- `cash_fraction` up to `1.00` under the existing spot/cash-bounded engine.
- New deterministic model families.
- New completed-candle indicators.
- New completed-candle pattern detectors.
- Entry frequency and cooldown.
- Target/stop/time-exit geometry.
- Long/short side selection.
- Ensemble or voting among deterministic OHLCV-only signals.
- Completed-candle multi-timeframe features derived from local 1m candles.
- Cost/edge gate geometry, provided transaction costs remain non-zero and recorded.

The implementation must not introduce futures, leverage, real borrow, funding, liquidation, or private exchange behavior.

New models, indicators, and patterns must remain deterministic, OHLCV/local-data-only, metadata-rich, and no-lookahead. Strategy code must not fetch market data or call exchange APIs.

## Candidate Families

Attempt at least two high-activity deterministic families before any pause:

1. High-activity trend scalp:
   - Completed-candle EMA/rolling-return regime.
   - Frequent pullback or momentum entries.
   - Fixed bps or ATR target/stop/time exits.
   - Cooldown control to avoid overlapping signals while still exceeding 50 trips.

2. Range/VWAP mean-reversion scalp:
   - Rolling VWAP or range-center deviation.
   - Enter reversion only when projected move can cover costs.
   - Use tight time exits to recycle capital.

3. Liquidity micro-break/fade:
   - Completed-candle range high/low break or failed break.
   - Trade either continuation or fade based on short-horizon regime.
   - Require enough frequency and cost-aware target distance.

4. Deterministic ensemble:
   - Combine the above families with explicit priority rules.
   - No model may use future candles for entry decisions.

## Iterative Development Loop

The task must continue in-task batches:

1. Predeclare each batch's candidate family and bounded parameter grid in code/report metadata.
2. Run owner-window backtests and persist every decision-driving run.
3. If no candidate passes, inspect diagnostics and move to a substantively different next batch.
4. Do not stop because a batch failed.
5. If repeated batches miss +3.0pct or 50 round trips, create the next in-task batch by changing model family, indicator set, pattern detector, sizing, entry timing, or exit geometry.
6. Stop only if acceptance gates pass, a hard runtime/safety blocker appears, or the owner explicitly pauses. A low return or low trade count is not a hard blocker by itself.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm this task file is the assigned task before coding or running validation backtests.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Predeclare candidate grid, sizing ladder, windows, and stop rules.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the current iteration state is accurate.

# Acceptance Criteria

- [x] Task 281 runner or strategy update is implemented under offline-only research boundaries.
- [x] At least two high-activity candidate families are attempted unless a hard blocker appears first.
- [x] Every decision-driving 2026-05-20+ run is persisted to DB with `research.task_id = TASK_281`.
- [x] Best candidate has at least 50 completed round trips, or the task continues in another in-task batch.
- [x] Best candidate reaches at least +3.0pct total return after costs, or the task continues in another in-task batch.
- [x] Fee/spread/slippage cost accounting is verified from persisted rows.
- [x] A report is saved at `reports/TASK_281_OWNER_WINDOW_0520_HIGH_ACTIVITY_TARGET_RETURN_SEARCH.md`.
- [x] The report includes:
  - all Task 281 run IDs;
  - candidate table;
  - 2026-05-20+ returns;
  - trade counts and completed round trips;
  - active days;
  - cash fraction;
  - fee/spread/slippage/total cost;
  - cost-to-gross-PnL;
  - largest/top-three trade contribution;
  - drawdown;
  - pass/fail reason;
  - current iteration state.
- [x] No result is promoted beyond `RESEARCH_ONLY`.

# Required Tests

## Unit Tests

- Candidate grid generation is deterministic and bounded.
- New high-activity signal generation is completed-candle-only.
- Cost gate metadata records pass/fail reason and projected cost.
- Sizing metadata records the tested `cash_fraction`.

## Integration Tests

- Task 281 runner can run a limited deterministic sample.
- Persisted Task 281 metadata includes task ID, variant ID, window ID, run group, cost profile, and sizing.
- Report generation includes failed, diagnostic, and best variants.

## Contract Tests

- Existing saved-run schema fields are not removed or renamed.
- New metadata is additive.
- Existing Task 280 report and persistence code remains readable.

## Safety Tests

- No strategy or validation code imports execution clients.
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
- No unnecessary abstractions.
- No hidden lookahead.
- Fee/spread/slippage costs remain non-zero for accepted runs.

# Verification

Minimum focused verification:

```bash
pytest tests/backtesting -q
python -m compileall -q quant_bitcoin
git diff --check
```

At completion, verify Task 281 run IDs can be read back from DB and regenerated into the markdown report.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- all Task 281 run IDs
- gate-by-gate pass/fail table
- best candidate and why it did or did not pass
- cost-accounting verification result
- overfit/data-snooping risk statement
- Codex self-review result
- known limitations
- current iteration state

# Execution Summary

- Completed on 2026-05-30.
- Implemented `quant_bitcoin/backtesting/t281_high_activity_model.py`.
- Added focused tests in `tests/backtesting/test_t281_high_activity_model.py`.
- Persisted Task 281 DB run IDs: `890`, `891`, `892`, `893`, `894`.
- Best passing candidate: run `892` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Best passing candidate result: `+5.7295pct` total return, `62` completed round trips, `9` active trade days, `0.4151` cost/gross-PnL, `0.2248` largest-winner/net contribution, `0.5483` top-three-winners/net contribution.
- Cost readback verified non-zero fee, spread, and slippage for accepted runs.
- Post-completion run `892` fee audit recomputed persisted trade metadata against `gross_notional * bps / 10000`: `21,970,384.07` total notional, `21,970.38` fee at `10.0` bps per execution, `40,668.89` total fee/spread/slippage cost, and `0` formula mismatches.
- Report saved at `reports/TASK_281_OWNER_WINDOW_0520_HIGH_ACTIVITY_TARGET_RETURN_SEARCH.md`.
- Current iteration state: Task 281 reached the owner-window +3pct and 50-round-trip gates under `PROMISING_RESEARCH_ONLY`; result remains fixed-window tuned and must not be promoted beyond research without future locked OOS/walk-forward validation.
