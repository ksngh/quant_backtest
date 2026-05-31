# Task 279: Strategy Robustness Validation Matrix After Low-Trade Task 278 Result

# Goal

Define and execute a stricter BTCUSDT 1-minute strategy validation matrix so a candidate cannot pass only by one full-window directional position or endpoint mark-to-market. Task 278 met the owner's +3pct total-return check, but the selected result is not strategy-grade because it effectively holds one simulated short across the window.

This task must decide and apply the non-negotiable tests that a serious quant candidate must pass before it can be treated as more than a research diagnostic.

# Source Requirement

Owner feedback after Task 278:

```text
야 ㅅㅂ 거래를 한번만 하잖냐... 여러모로 테스트 해봐야 할 것들을 정해봐 거래 횟수말고도..
```

Clean requirement:

- Acknowledge that Task 278's low-trade inverse hold result is insufficient as a strategy validation result.
- Define a broader validation checklist beyond trade count.
- Convert that checklist into an executable research task.
- Keep Task 278's result `RESEARCH_ONLY`.
- Do not proceed to promotion, live trading, or paper-trading readiness from Task 278.

# Extracted Roles

- Owner role:
  - Rejects one-position total-return passing as insufficient.
  - Wants a broader test matrix for candidate quality.
- Supporting roles:
  - Quant research lead: define robustness, out-of-sample, cost, regime, and tail-risk checks.
  - Backtest runner: execute DB-persisted validation runs only after task assignment.
  - Strategy diagnostics role: compute contribution, exposure, cost, regime, and stability metrics.
  - Reporting role: save a markdown report with pass/fail status for each validation gate.
  - Status tracker: update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
- Forbidden roles:
  - Live trading.
  - Real Binance order execution.
  - Exchange order/account/private endpoint calls.
  - API keys, signed requests, `.env` edits, or credential handling.
  - Futures, leverage, liquidation, funding, borrow, or real margin behavior.
  - Machine learning, black-box optimization, hidden optimizer fitting, or unbounded parameter search.
  - Frontend/backend API/dashboard changes unless separately assigned.

# Context

Task 278 selected `T278_V001_INVERSE_TREND_HOLD_CF_0P75`:

- Window A run `155`: `+3.1738pct`
- Window B run `156`: `+3.4440pct`
- It used conservative 1m fee/spread/slippage and persisted to DB.
- It passed the owner's total-return check but did so with a single full-window simulated short exposure.
- That means it is vulnerable to endpoint selection, data snooping, regime hindsight, and low sample size.

The next validation pass must treat Task 278 as a benchmark to beat, not as an acceptable finished strategy.

# Scope

- Create or update offline-only research validation code if needed under:
  - `quant_bitcoin/backtesting/`
  - `quant_bitcoin/strategies/`
  - `quant_bitcoin/patterns/`
  - `quant_bitcoin/indicators/`
- Add focused tests under:
  - `tests/backtesting/`
  - `tests/strategies/`
  - `tests/patterns/`
  - `tests/safety/`
- Persist all qualifying validation backtests to DB.
- Generate `reports/TASK_279_STRATEGY_ROBUSTNESS_VALIDATION_MATRIX.md`.
- Compare any candidate against Task 278 runs `155` and `156`, Task 277 diagnostics `149` and `150`, and an always-flat baseline.

# Out of Scope

- No live trading.
- No real exchange order placement.
- No private/order/account endpoints.
- No API keys or `.env` changes.
- No futures, leverage, borrow, liquidation, or funding assumptions.
- No dashboard/backend API work.
- No claim that a strategy is production-ready.
- No weakening transaction costs to pass a gate.
- No unbounded search after seeing validation failures.

# Requirements

## Candidate Pool

Evaluate at minimum:

- Task 278 `T278_INVERSE_TREND_HOLD` as a diagnostic benchmark only.
- The best deterministic pattern candidate from Task 277 by realistic-cost combined return.
- At least one new or revised deterministic multi-trade candidate if existing candidates fail the gates.

Every candidate must be run with:

```bash
--symbol BTCUSDT
--interval 1m
--starting-cash 1000000
--starting-cash-currency USDT
--cost-profile conservative_crypto_1m
```

Sizing tests must include:

- `cash_fraction=0.10`
- `cash_fraction=0.25`
- `cash_fraction=0.50`
- `cash_fraction=0.75`

Runs above `cash_fraction=0.10` are sizing diagnostics unless the report clearly states why the larger sizing is acceptable without leverage.

## Mandatory Validation Gates Beyond Trade Count

A candidate can be called `PROMISING_RESEARCH_ONLY` only if it passes all mandatory gates below. Otherwise it remains `DIAGNOSTIC_ONLY`.

1. Sample-size and activity gate:
   - At least `20` completed round trips on Window A.
   - At least `8` completed round trips on Window B.
   - At least `3` active calendar days in each owner window.
   - No single continuous position may cover more than `35pct` of the tested window.

2. Endpoint-dependence gate:
   - Re-run after excluding the first `60` minutes and last `60` minutes of each window.
   - Re-run with entries delayed by one candle where the architecture allows it.
   - Candidate fails if most profit disappears only because the exact first or final candle was used.

3. Outlier-contribution gate:
   - Largest winning trade must contribute no more than `40pct` of net profit.
   - Top three winning trades must contribute no more than `70pct` of net profit.
   - Removing the best trade must not turn both owner windows negative.

4. Cost-resilience gate:
   - Conservative 1m costs must be non-zero and verified from persisted DB rows.
   - High-slippage stress, or equivalent 2x fee/spread/slippage stress, must not erase more than `70pct` of conservative-cost net profit.
   - Gross edge per completed round trip must exceed estimated round-trip cost by at least `2.0x` on average.

5. Drawdown and tail-risk gate:
   - Max drawdown must be recorded.
   - Max drawdown must be less than or equal to `1.5x` net return for the same window unless explicitly justified.
   - Longest drawdown duration and longest loss streak must be reported.
   - The 5th percentile trade PnL and worst trade PnL must be reported.

6. Exposure and turnover gate:
   - Time in market must be reported by side.
   - Total notional turnover must be reported.
   - Cost-to-gross-PnL ratio must be below `0.40`.
   - Strategy must not rely on being almost always short or almost always long unless it is explicitly classified as a directional benchmark.

7. Regime and side gate:
   - Report performance by completed-candle regime buckets: trend up, trend down, range, high volatility, low volatility.
   - Report performance by side: long, short, flat.
   - Report session/time-of-day buckets if timestamp coverage supports it.
   - If one side contributes more than `80pct` of net PnL, the strategy must be documented as side-biased and compared against same-side buy/short-hold benchmarks.

8. Parameter-stability gate:
   - Test a small predeclared neighborhood around key thresholds, such as `-20pct`, baseline, and `+20pct`.
   - At least two neighboring parameter variants must remain positive after costs on both owner windows.
   - The selected variant cannot be an isolated needle in the grid.

9. Split and OOS gate:
   - Treat the 2026-05-20+ and 2026-05-25+ owner windows as development evidence only.
   - Validate on at least two untouched windows if enough local DB candle data exists.
   - If untouched windows are not available, record a blocker and do not promote the candidate.
   - Predeclare split boundaries before running validation.

10. Benchmark gate:
   - Compare against always-flat.
   - Compare against long buy-and-hold over the same windows.
   - Compare against cash-bounded short hold over the same windows.
   - Compare against Task 278 runs `155` and `156`.
   - A multi-trade candidate must beat Task 278 on risk-adjusted evidence, not merely raw return at larger sizing.

11. Execution-assumption gate:
   - Verify no lookahead in indicators, signals, exits, and metadata.
   - Verify no open-position endpoint dependency.
   - Verify final equity, closed-trade PnL, and mark-to-market contribution are separated.
   - Verify candle continuity and timestamp sorting for every tested window.

12. Persistence and auditability gate:
   - Every qualifying validation run must have a DB run ID.
   - Every run must record variant ID, sizing, costs, window, candle count, and result status.
   - Failed, low-trade, no-fill, dominated, and diagnostic variants must be included in the report.

## Stop Rules

Stop the task when one of these is true:

- A candidate passes all mandatory gates and is documented as `PROMISING_RESEARCH_ONLY`.
- All predeclared candidates fail and the report explains why.
- Local DB data is insufficient for OOS validation and this is recorded as a blocker.
- Runtime or persistence failures prevent trustworthy validation.

Do not continue tuning after validation failure unless a new task explicitly authorizes another bounded development pass.

# Status Tracking

## Completion Notes

- Completed on 2026-05-29 as `RESEARCH_ONLY`.
- Persisted Task 279 validation runs in DB: `159` through `295`, 135 rows total.
- Planned matrix size was 154 runs; the optional Order Block expansion was stopped after three owner-window runs because it was already strongly dominated, slow, and fee-dominated. SRLBR, FVG inverse, and LSR validation groups were persisted broadly.
- Validation report: `reports/TASK_279_STRATEGY_ROBUSTNESS_VALIDATION_MATRIX.md`.
- Task 278 runs `155` and `156` remain `DIAGNOSTIC_ONLY`; their one-position directional result fails the Task 279 sample-size, endpoint/exposure concentration, OOS, and promotion robustness gates.
- No tested candidate passed all mandatory gates. SRLBR variants had adequate activity but failed cost, OOS, benchmark, parameter-stability, drawdown, endpoint, and outlier gates. FVG, OB, and LSR branches failed sample/activity and/or cost gates.
- Cost accounting was verified from persisted run metadata: conservative runs used `conservative_crypto_1m`, stress runs used `high_slippage_stress`, and no candidate had enough net edge after fee/spread/slippage.
- OOS windows were available and executed for the broadly persisted candidates: `2026-05-10T00:00:00Z` to `2026-05-14T00:00:00Z`, and `2026-05-14T00:00:00Z` to `2026-05-18T00:00:00Z`.
- DB readback confirmed 135 Task 279 rows with min run ID `159` and max run ID `295`; saved cost profiles were `conservative_crypto_1m` and `high_slippage_stress`.
- Focused verification passed:
  - `pytest tests/backtesting/test_strategy_validation_metrics.py tests/backtesting/test_pattern_postgres_runner_cli.py::test_research_metadata_cli_records_task_variant_and_window -q`
  - `python -m compileall -q quant_bitcoin/backtesting/strategy_validation_metrics.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py quant_bitcoin/backtesting/t279_validation_matrix.py`
  - `python -m quant_bitcoin.backtesting.t279_validation_matrix --finalize-only`
  - `git diff --check -- quant_bitcoin/backtesting/strategy_postgres_runner_core.py quant_bitcoin/backtesting/strategy_validation_metrics.py quant_bitcoin/backtesting/t279_validation_matrix.py tests/backtesting/test_strategy_validation_metrics.py tests/backtesting/test_pattern_postgres_runner_cli.py reports/TASK_279_STRATEGY_ROBUSTNESS_VALIDATION_MATRIX.md STATUS.md BACKLOG.md PROJECT_HISTORY.md tasks/TASK_279_STRATEGY_ROBUSTNESS_VALIDATION_MATRIX.md`

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read this task file before coding or running validation backtests.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Predeclare candidate list, split windows, sizing ladder, and parameter-neighborhood grid.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Task 278's one-position result is explicitly classified as `DIAGNOSTIC_ONLY`.
- A validation report is saved at `reports/TASK_279_STRATEGY_ROBUSTNESS_VALIDATION_MATRIX.md`.
- Every mandatory gate above is evaluated with pass/fail status.
- Every qualifying validation backtest is persisted to DB.
- Cost accounting is verified from persisted rows.
- OOS availability is verified and either executed or recorded as a blocker.
- No result is promoted beyond `RESEARCH_ONLY`.

# Required Tests

## Unit Tests

- Contribution metrics handle one trade, many trades, no winners, and negative net PnL.
- Exposure metrics separate long, short, and flat time.
- Endpoint-exclusion window logic removes first/last boundary candles deterministically.
- Parameter-neighborhood generation is deterministic and bounded.

## Integration Tests

- Validation runner, if added, can load saved run metadata and emit a pass/fail gate summary.
- Strategy backtests used by the matrix persist run IDs and cost metadata.
- Report generation includes failed and diagnostic variants.

## Contract Tests

- Existing saved-run schema fields are not removed or renamed.
- New validation metadata is additive.
- DB run IDs remain stable references in reports.

## Safety Tests

- No strategy or validation code imports execution clients.
- No test calls real exchange order/account endpoints.
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
- Task 278 remains research-only.

# Verification

Minimum focused verification:

```bash
pytest tests/backtesting tests/strategies tests/safety -q
git diff --check
```

At completion, also verify every qualifying validation run can be read back from DB by run ID.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- all validation run IDs
- gate-by-gate pass/fail table
- best candidate and why it did or did not pass
- comparison to Task 278 runs `155` and `156`
- cost-accounting verification result
- OOS validation result or blocker
- overfit/data-snooping risk statement
- Codex self-review result
- known limitations
- recommended next task
