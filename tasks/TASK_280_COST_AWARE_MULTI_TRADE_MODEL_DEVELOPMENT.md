# Task 280: Cost-Aware Multi-Trade BTCUSDT 1m Model Development After Task 279 Failures

# Goal

Develop and backtest a new BTCUSDT 1-minute deterministic multi-trade strategy family that directly addresses the Task 279 failure modes: fee drag, insufficient edge per trade, one-position endpoint dependence, low sample size, and unstable OOS behavior.

This is not another rejection-only validation pass. The task must implement or combine bounded new model logic, run enough DB-persisted backtests, inspect failures only to choose the next variant, and keep iterating inside this same task until a candidate passes the acceptance gates or a hard data/runtime/safety blocker prevents further trustworthy execution.

# Source Requirement

Owner feedback after Task 279:

```text
탈락만 쳐 했는데 왜 니가 끝낸거야
```

Clean requirement:

- Do not stop strategy development merely because the first validation batch failed.
- Use Task 279 failures as input to build the next model.
- Require enough trades, realistic fee/spread/slippage accounting, and consistent behavior.
- Continue through implementation/backtest/revision loops instead of only labeling candidates as failed.
- Do not stop this task by writing a next-task recommendation after failures; continue the next batch within Task 280 unless a hard blocker or explicit owner pause occurs.
- Keep all work offline and research-only.

# Extracted Roles

- Owner role:
  - Rejects a workflow that only eliminates candidates and stops.
  - Wants a strategy-development loop that uses failed evidence to create better candidates.
  - Requires enough trades, proper cost accounting, and consistency across windows.
- Supporting roles:
  - Quant research lead: translate Task 279 failure modes into new model hypotheses and acceptance gates.
  - Strategy implementation role: add deterministic OHLCV-only strategy/pattern logic within the existing architecture.
  - Backtest runner: persist every target-window and validation-window backtest to DB.
  - Diagnostics role: compare trade count, cost drag, gross edge, outliers, endpoint sensitivity, OOS, and side/regime behavior so the next variant can be selected inside this task.
  - Reporting role: save a markdown report with accepted/rejected variants, current iteration state, and the next in-task batch when needed.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - Live trading.
  - Real Binance order execution.
  - Exchange private/order/account endpoints.
  - API keys, signed requests, `.env` edits, or credential handling.
  - Futures, leverage, borrow, liquidation, funding, or real margin behavior.
  - Machine learning, black-box optimization, unbounded parameter search, or hidden fitting.
  - Frontend/backend API/dashboard work unless separately assigned.

# Context

Task 279 produced enough evidence to reject the current candidate families:

- Task 278 run `155`/`156` achieved raw +3pct only through one simulated directional position and remains `DIAGNOSTIC_ONLY`.
- SRLBR variants had enough trades but failed because cost/gross-PnL ratios were far above acceptable levels.
- Order Block produced many trades but was heavily fee-dominated.
- FVG inverse and LSR branches lacked enough consistent activity and/or failed costs.
- High-turnover 1m entries need a larger expected move per trade, fewer weak entries, and a stronger pre-trade cost budget.

The next candidate should not aim to maximize trade count by itself. It should aim for repeatable net expectancy after costs with enough trades to avoid one-position or one-outlier dependence.

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
- Persist all target-window and validation-window backtests to DB.
- Generate `reports/TASK_280_COST_AWARE_MULTI_TRADE_MODEL_DEVELOPMENT.md`.
- Reuse Task 279 research metadata conventions:
  - `research.task_id = TASK_280`
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
- No weakening transaction costs to pass.
- No single-position full-window directional hold as an accepted strategy.
- No unbounded manual curve fitting.

# Requirements

## Non-Negotiable Cost Budget

Every implemented candidate must enforce a pre-entry cost/edge gate:

- Use `--cost-profile conservative_crypto_1m` for primary runs.
- Estimate full round-trip cost from fee, spread, slippage, minimum slippage, and volatility slippage assumptions.
- Skip entries where projected gross reward is less than `3.0x` estimated round-trip cost.
- Skip entries where projected net reward is below `0.10pct` of trade notional unless explicitly justified by a low-risk high-frequency profile.
- Record cost gate metadata for passed and rejected candidates.

## Candidate Thesis Pool

Implement or combine at least two of the following thesis tracks before any pause. If the first batch fails, continue to another batch within this task rather than creating a new task:

1. Volatility-compression expansion:
   - Detect low realized range/ATR compression followed by expansion candle.
   - Trade only when expected move to structure/liquidity target exceeds cost budget.
   - Avoid entering after the expansion is already exhausted.

2. Session VWAP/range reclaim:
   - Build completed-candle session VWAP or rolling VWAP proxy from local OHLCV.
   - Enter only on reclaim/rejection with volume confirmation and nearby invalidation.
   - Use session high/low or measured move target.

3. Liquidity sweep with continuation filter:
   - Reuse liquidity sweep evidence but require follow-through structure instead of one-candle reversal only.
   - Add completed-candle trend/regime filter so short/long side is not chosen by hindsight.
   - Use no-lookahead stop and target from the sweep/structure.

4. Multi-timeframe completed-candle filter:
   - Use completed 15m/30m context from local DB or completed base-candle resampling only.
   - Do not use incomplete higher-timeframe candles.
   - Require 1m entries to align with a higher-timeframe regime or liquidity boundary.

The final implemented strategy can be one new model or a deterministic ensemble of these tracks, but each signal must remain explainable and metadata-rich.

## Windows

Primary owner windows:

- Window A: `2026-05-20T00:00:00Z` to latest locally available BTCUSDT 1m candle at or before `2026-05-28T08:26:00Z`.
- Window B: `2026-05-25T00:00:00Z` to latest locally available BTCUSDT 1m candle at or before `2026-05-28T08:26:00Z`.

OOS windows, if local DB data remains available:

- OOS 1: `2026-05-10T00:00:00Z` to `2026-05-14T00:00:00Z`.
- OOS 2: `2026-05-14T00:00:00Z` to `2026-05-18T00:00:00Z`.

Endpoint robustness windows:

- Trim first `60` minutes and last `60` minutes from Window A.
- Trim first `60` minutes and last `60` minutes from Window B.
- Run one-candle delayed-entry diagnostics where architecture allows.

## Sizing

Primary validation sizing:

- `cash_fraction=0.10`

Secondary sizing diagnostics only after the 0.10 variant is not obviously invalid:

- `cash_fraction=0.25`
- `cash_fraction=0.50`
- `cash_fraction=0.75`

No candidate may be accepted because larger sizing crossed a return threshold if `cash_fraction=0.10` fails consistency or cost gates.

## Iterative Development Loop

The task must run repeated development batches inside Task 280:

1. Predeclare the first candidate family and parameter grid.
2. Implement the model or model combination.
3. Run primary owner-window backtests and persist them.
4. If it fails, inspect recorded diagnostics only to choose the next variant:
   - insufficient trades;
   - cost/gross-PnL too high;
   - weak gross edge;
   - outlier dependence;
   - endpoint dependence;
   - side/regime concentration;
   - OOS breakdown.
5. Revise only within the predeclared model family or move to the next predeclared thesis track.
6. Persist failed and diagnostic variants too.
7. If the current batch budget is exhausted without a passing candidate, write an interim report section and start the next predeclared batch within Task 280.
8. Stop only when acceptance criteria pass, a hard data/runtime/safety blocker prevents trustworthy execution, or the owner explicitly pauses the loop.

Per-batch search budget:

- Up to `3` thesis tracks.
- Up to `20` variants per thesis track.
- Up to `60` total variants.
- Every owner-window candidate run that influences a decision must be persisted.

If a batch is exhausted without a passing candidate, the next batch must change at least one substantive thesis component, such as target construction, entry timing, regime filter, or cost-gate geometry. It must not merely widen sizing or weaken costs.

## Acceptance Gates

A candidate can be reported as `PROMISING_RESEARCH_ONLY` only if all of these pass:

- Window A total return at `cash_fraction=0.10` is at least `+3.0pct` after costs.
- Window B total return at `cash_fraction=0.10` is at least `+3.0pct` after costs.
- At least `20` completed round trips on Window A.
- At least `8` completed round trips on Window B.
- At least `3` active calendar days in each owner window.
- No single trade contributes more than `40pct` of net profit.
- Top three trades contribute no more than `70pct` of net profit.
- Cost-to-gross-PnL ratio is below `0.40`.
- Conservative 1m costs are non-zero and verified from persisted DB rows.
- High-slippage stress does not erase more than `70pct` of conservative-cost net profit.
- Endpoint-trim and delayed-entry diagnostics do not flip both owner windows negative.
- OOS windows are either positive after costs or explicitly documented as the blocker that prevents promotion.
- Final equity, closed-trade PnL, and mark-to-market/open-position contribution are separated.
- Candle continuity and timestamp sorting are verified for every tested window.

If no candidate passes all gates in the current batch, the task must not present the project as complete. It must:

- classify every candidate as `DIAGNOSTIC_ONLY`;
- append the batch result to the Task 280 report;
- continue with the next in-task batch unless blocked or explicitly paused by the owner.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Read this task file before coding or running validation backtests.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Predeclare thesis tracks, candidate grid, windows, sizing ladder, and stop rules.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append a concise completion note to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A new bounded multi-trade strategy/model development pass is implemented or explicitly blocked by local data/runtime constraints.
- At least two thesis tracks are attempted before any pause.
- Every decision-driving owner-window run is persisted to DB.
- Fee/spread/slippage cost accounting is verified from persisted rows.
- A report is saved at `reports/TASK_280_COST_AWARE_MULTI_TRADE_MODEL_DEVELOPMENT.md`.
- The report includes:
  - all run IDs;
  - variant table;
  - owner-window returns;
  - OOS returns;
  - trade counts;
  - active days;
  - cost-to-gross-PnL;
  - largest/top-three trade contribution;
  - drawdown;
  - endpoint/delay results;
  - pass/fail reason;
  - current iteration state;
  - next in-task batch if no pass and execution is not blocked.
- No result is promoted beyond `RESEARCH_ONLY`.

# Required Tests

## Unit Tests

- Cost/edge gate rejects trades whose projected reward is below estimated round-trip cost multiple.
- Candidate metadata records projected reward, estimated cost, and pass/fail reason.
- New signal detector uses completed candles only.
- Parameter-grid generation is deterministic and bounded.

## Integration Tests

- Strategy CLI can run the new model on a small deterministic candle fixture.
- Persisted Task 280 metadata includes task ID, variant ID, window ID, run group, cost profile, and sizing.
- Report generation includes failed and diagnostic variants.

## Contract Tests

- Existing saved-run schema fields are not removed or renamed.
- New metadata is additive.
- Existing Task 277/278/279 report and persistence code remains readable.

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
- No endpoint-only profitability accepted.
- Fee/spread/slippage costs remain conservative and non-zero.
- Failed candidates do not end the overall research direction; the next batch continues inside Task 280 unless blocked or explicitly paused.

# Verification

Minimum focused verification:

```bash
pytest tests/backtesting tests/strategies tests/patterns tests/safety -q
python -m compileall -q quant_bitcoin
git diff --check
```

At completion, also verify Task 280 run IDs can be read back from DB and regenerated into the markdown report.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- all Task 280 run IDs
- gate-by-gate pass/fail table
- best candidate and why it did or did not pass
- comparison to Task 278 and Task 279 failures
- cost-accounting verification result
- OOS validation result or blocker
- overfit/data-snooping risk statement
- Codex self-review result
- known limitations
- current iteration state

# Execution Result

Status: `HARD_DATA_CONSTRAINT_RESEARCH_ONLY` as of 2026-05-29.

- Implemented offline-only Task 280 runner at `quant_bitcoin/backtesting/t280_cost_aware_model.py`.
- Added focused tests at `tests/backtesting/test_t280_cost_aware_model.py`.
- Persisted 576 Task 280 DB runs (`296`-`889`) across repeated in-task batches `batch1` through `batch9`.
- Saved aggregate report at `reports/TASK_280_COST_AWARE_MULTI_TRADE_MODEL_DEVELOPMENT.md`.
- Best combined candidate: `T280_B9_PULLBACK_TW720_TH30P0_CW360_TG250P0_ST120P0`.
- Best candidate Window A: run `864`, `+0.2057pct`, 9 trips, cost/gross `0.6190`.
- Best candidate Window B: run `865`, `+0.3001pct`, 4 trips, cost/gross `0.3308`.
- Acceptance gates were not met at mandatory primary `cash_fraction=0.10`.
- Hard data constraint recorded: a perfect-hindsight close-to-close switching diagnostic for Window B is approximately `+1.9146pct` at 10pct sizing after approximate 38bps round-trip cost, below the required `+3.0000pct` before implementable signal constraints.
- No candidate is promoted.
