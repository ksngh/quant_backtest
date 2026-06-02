# Task 324: LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION

# Goal

Define and execute a `Lookback Return Momentum V2` validation that keeps the current lookback-return momentum signal family but removes transaction-cost calculation from the experiment and exits positions when either the stop-loss or take-profit reaches `1 ATR`.

This is a future strategy/backtest task. It must not be executed until assigned after this task file exists.

# Source Requirement

Owner request after Task 323 frontend PR:

> 다음 전략 실행할건데 이거 task로 둬줘. 지금까지의 모멘텀 전략과 똑같은데 v2로 둘거야. 비용 계산 하지말고 손절 및 익절을 atr 1인 경우에 그냥 청산해버려. 기간은 마찬가지로 두고.

Interpreted as:

- Create a future task for the next momentum strategy execution.
- Strategy family: `LOOKBACK_RETURN_MOMENTUM`.
- New version label: `v2`.
- Same diagnostic period as the latest momentum validation window:
  - `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`.
- Same interval set as the current momentum validation family unless the owner changes it:
  - `1m`, `5m`, `15m`.
- Same signal family as the current momentum strategy.
- Primary behavioral difference:
  - disable cost-aware entry filtering;
  - disable transaction-cost PnL adjustments for this diagnostic;
  - use symmetric `1 ATR` stop-loss and `1 ATR` take-profit exits.

# Extracted Roles

- Owner role:
  - Requests the next strategy execution task.
  - Chooses the strategy family, version label, no-cost diagnostic assumption, ATR exit geometry, and period continuity.
- Supporting roles:
  - Strategy-document maintainer: create or update the appropriate `docs/strategy/lookback_return_momentum_v2.md` document before any implementation or backtest execution.
  - Strategy/backtest implementer: update only the assigned momentum strategy/config/runner behavior needed for the V2 no-cost ATR-1 diagnostic.
  - Backtest runner: preflight local data coverage and run the predeclared validation only after the strategy document exists.
  - Report writer: save a concise task report that separates the no-cost diagnostic conclusion from real cost-aware deployability.
  - Test/verification role: update focused tests for any strategy/config/runner behavior change and run required verification.
- Forbidden roles:
  - Live trading or real order executor.
  - Exchange account/order endpoint caller.
  - Frontend/dashboard implementer.
  - Backend API implementer.
  - DB schema mutator.
  - Post-result parameter searcher.

# Context

Relevant existing strategy document:

- `docs/strategy/lookback_return_momentum_v1.md`

Current V1 family facts:

- Signal uses completed close-to-close lookback return:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
```

- Latest diagnostics used `BTCUSDT` `1m`, `5m`, and `15m` over:

```text
2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z
```

- Task 309 introduced ATR-based risk distance.
- Task 311 tested asymmetric take-profit multiples and cost-aware entry feasibility.
- This task intentionally asks a different question:
  - If cost calculation is removed and both stop/take-profit are `1 ATR`, does the raw momentum signal produce a useful gross/no-cost diagnostic path?

Important interpretation boundary:

- A no-cost result is not a deployable performance claim.
- Positive no-cost results may show that raw signal timing has directional value before costs.
- Negative no-cost results would be stronger evidence against this exact V2 geometry, but still would not reject momentum strategies generally.

# Scope

- Read required state files and this task before implementation.
- Read `docs/strategy/lookback_return_momentum_v1.md`.
- If `docs/strategy/lookback_return_momentum_v2.md` does not exist, create it from `docs/strategy/STRATEGY_TEMPLATE.md`, document the V2 rules below, update state files, and stop before implementation/backtest execution if required by the project strategy-document rule.
- If the V2 strategy document already exists and matches this task, continue with implementation/execution.
- Define V2 strategy identity:
  - strategy key/name: keep the `LOOKBACK_RETURN_MOMENTUM` family unless the codebase requires a versioned key.
  - strategy version: `v2`.
  - stable report-facing title: `Lookback Return Momentum V2`.
- Reuse the same signal family and no-lookahead completed-candle assumptions as V1.
- Predeclared validation parameters:
  - `1m`: `lookback_bars = 20`, `holding_bars = 5`, `entry_threshold = 0.0004`.
  - `5m`: `lookback_bars = 12`, `holding_bars = 6`, `entry_threshold = 0.0006`.
  - `15m`: `lookback_bars = 8`, `holding_bars = 4`, `entry_threshold = 0.0008`.
  - These are the lowest Task 308/311 thresholds and are used here as a fixed predeclared comparison point, not a new tuning search.
- V2 exit/risk parameters:
  - `risk_distance_mode = atr`.
  - `atr_period = 14`.
  - `atr_smoothing = RMA`.
  - `stop_loss_atr_multiple = 1.0`.
  - `take_profit_atr_multiple = 1.0`.
  - stop/target checks start from the next completed candle after entry.
  - if both stop and take-profit are touched in the same candle, preserve the existing stop-first ambiguity policy unless the V2 strategy document explicitly changes it.
  - if neither stop nor take-profit is reached by `holding_bars`, keep the existing time-exit behavior unless the V2 strategy document explicitly changes it.
- No-cost diagnostic settings:
  - disable `cost_aware_entry_filter`.
  - set transaction-cost assumption to zero or otherwise prevent fee/spread/slippage from reducing PnL for this task.
  - do not compute cost feasibility as an entry blocker.
  - report clearly that the run is a no-cost gross diagnostic.
- Preflight local candle coverage for `BTCUSDT` `1m`, `5m`, and `15m` over the target window before execution.
- Run the predeclared V2 validation only after the strategy document exists.
- Persist or save results using the existing project conventions.
- Save a task report under `reports/` summarizing:
  - data coverage;
  - exact parameters;
  - trade count;
  - win/loss and exit mix;
  - gross/no-cost PnL and return;
  - expectancy or average R if available;
  - side/timeframe attribution;
  - comparison against relevant V1 no-entry/cost-aware context;
  - why no-cost results must not be interpreted as real cost-aware deployability.
- Update required state files after execution.

# Out of Scope

- Live trading.
- Real Binance order execution.
- Exchange account/order/private endpoints.
- Frontend or backend API/dashboard changes.
- DB schema changes.
- Candle backfill unless local data coverage is missing and a bounded public candle backfill is explicitly required by the preflight.
- Post-result parameter search or threshold tuning.
- Adding new filters such as volume, trend score, FVG, order block, higher-timeframe confirmation, liquidity filters, or session filters.
- Changing the report/blog daily-report workflow.
- Publishing a Tistory daily report unless a later task explicitly asks for it.

# Requirements

- The V2 strategy document must exist before implementation or backtest execution.
- V2 must keep the lookback-return momentum signal family and completed-candle no-lookahead assumptions.
- V2 must disable cost-aware entry filtering for this diagnostic.
- V2 must not subtract fee/spread/slippage from PnL in this diagnostic.
- V2 must use symmetric `1 ATR` stop-loss and `1 ATR` take-profit distances.
- The validation period must remain:

```text
2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z
```

- The interval set must remain `1m`, `5m`, `15m`.
- The run must be predeclared. Do not tune thresholds, holding bars, ATR period, or ATR multiples after seeing results.
- The report must explicitly distinguish:
  - raw no-cost directional/exit diagnostic;
  - cost-aware real-world viability.
- No live trading or exchange order behavior may be introduced.

# Status Tracking

## Before Implementation

- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md`.
- [ ] Read `STATUS.md`.
- [ ] Read this task.
- [ ] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [ ] Find or create `docs/strategy/lookback_return_momentum_v2.md` before implementation/backtest execution.
- [ ] If the V2 strategy document had to be created, update state files and stop if required by the project strategy-document rule.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm this is a no-cost diagnostic strategy/backtest task, not a deployability claim.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update the V2 strategy document if implementation changes strategy logic, cost assumptions, execution assumptions, validation windows, or research/live boundary.
- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append completion progress to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` if this task was completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `docs/strategy/lookback_return_momentum_v2.md` exists and documents the V2 no-cost ATR-1 rules before any backtest execution.
- V2 validation runs over `BTCUSDT` `1m`, `5m`, and `15m` for the February-to-May window, or records a precise data blocker.
- Cost-aware entry filtering is disabled.
- Fee/spread/slippage are not subtracted from PnL for this diagnostic.
- Stop-loss and take-profit both use `1 ATR` at entry.
- No post-result tuning occurs.
- Results are saved and summarized in a task report under `reports/`.
- The report states whether V2 gross/no-cost behavior is positive or negative without claiming real cost-aware viability.
- Required tests and verification commands pass, or blockers are recorded.
- No live trading, exchange order endpoint, account endpoint, secret, or `.env` behavior is introduced.

# Required Tests

## Unit Tests

- Add or update focused strategy/config/runner tests if implementation changes are needed:
  - V2 config disables cost-aware entry filtering.
  - zero-cost/no-cost setting prevents fee/spread/slippage PnL reduction.
  - stop-loss at `1 ATR` exits correctly.
  - take-profit at `1 ATR` exits correctly.
  - same-candle stop/take-profit ambiguity follows the documented policy.
  - invalid ATR still blocks entry with a diagnostic reason.

## Integration Tests

- Run the focused momentum strategy/backtest tests that cover:
  - V2 parameter serialization/metadata;
  - no-cost run configuration;
  - persisted or saved result metadata needed for later report interpretation.

## Contract Tests

- Verify the V2 strategy document and report mention the no-cost diagnostic boundary:

```bash
rg -n "v2|no-cost|zero|cost_aware|1 ATR|ATR" docs/strategy/lookback_return_momentum_v2.md reports tasks/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md
```

## Safety Tests

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env" quant_bitcoin backend frontend docs/strategy reports STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md
```

Expected: no unsafe live-trading/order/secret behavior is introduced; declarative safety text and existing redaction tests are acceptable.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Strategy document exists before implementation/backtest execution.
- No post-result tuning.
- No cost-aware entry filter remains active in V2 diagnostic runs.
- No transaction costs are subtracted in V2 diagnostic PnL.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No unnecessary abstractions.

# Verification

Default focused verification:

```bash
pytest tests/strategies tests/backtesting
git diff --check
```

Add narrower backend/persistence/runner tests if the implementation touches those areas.

If local data or dependencies are unavailable, document the blocker and run the subset that is available.

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
