# Task 309: LOOKBACK_RETURN_MOMENTUM_ATR_RISK_EXIT_REVISION

# Goal

Revise `LOOKBACK_RETURN_MOMENTUM` risk/exit geometry so stop-loss and take-profit distances are based on ATR rather than a fixed percentage of entry price, then run a bounded cost-aware validation to determine whether ATR-based exits resolve the no-entry result observed in Task 308.

# Source Requirement

Owner request:

> 진입가로 하지말고, atr로 하자.. 1 atr 일때 손절 or 익절

# Extracted Roles

- Owner role: defines the strategy-risk requirement and final interpretation standard.
- Supporting roles:
  - Strategy document maintainer: updates `docs/strategy/lookback_return_momentum_v1.md` before implementation or backtest execution.
  - Strategy implementer: revises the momentum strategy risk/exit calculation.
  - Backtest runner: executes only the bounded validation defined in this task.
  - Test maintainer: adds or updates focused tests for ATR risk distance, cost-aware gating, and runner metadata.
- Forbidden roles:
  - Live trader.
  - Real Binance order executor.
  - Frontend/backend API implementer.
  - Parameter optimizer outside the predeclared validation grid.

# Context

Task 305 added cost-aware entry gating to `LOOKBACK_RETURN_MOMENTUM`. Task 308 lowered `entry_threshold` over a predeclared `1m`/`5m`/`15m` grid for `BTCUSDT` from `2026-02-01T00:00:00Z` inclusive through `2026-05-01T00:00:00Z` exclusive. Raw candidates increased, but accepted entries remained `0` because every candidate was blocked by `COST_INFEASIBLE_NET_RR`.

The current risk unit still behaves like a fixed entry-price percentage. The owner clarified that this should be changed to ATR. For this task, `1R` should mean `1 ATR` at entry, not `entry_price * fixed_pct`.

# Scope

- Read the required state files and this task before any implementation.
- Read `docs/strategy/lookback_return_momentum_v1.md` before strategy/code/backtest work.
- Review existing ATR conventions in the project before coding. If a reusable ATR implementation or documented ATR convention exists, use it unless it conflicts with this task.
- Update `docs/strategy/lookback_return_momentum_v1.md` before implementation/backtest execution to document:
  - ATR-based risk distance.
  - ATR formula and period.
  - No-lookahead timing for ATR at entry.
  - Default stop/take-profit multiples.
  - Cost-aware reward/risk gate formulas under ATR risk.
- Implement ATR-based stop-loss and take-profit distance for `LOOKBACK_RETURN_MOMENTUM`.
- Preserve Task 305 cost-aware entry gating, but compute gross reward/risk from the ATR-derived stop/target distance rather than fixed entry-price percentage.
- Run a bounded validation over the same Task 305/308 candle window:
  - symbol: `BTCUSDT`
  - intervals: `1m`, `5m`, `15m`
  - time window: `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`
  - cost assumptions: same conservative spot cost profile used by Task 305/308 unless the strategy document records a stricter predeclared reason.
  - entry thresholds: reuse the Task 308 predeclared lower-threshold grid unchanged unless the owner updates this task before execution.
- Save a task report under `reports/` summarizing implementation, validation runs, cost feasibility, accepted-entry counts, exit mix, gross/net PnL, total cost drag, expectancy, and interpretation.

# Out of Scope

- Live trading.
- Real Binance order execution.
- Signed exchange requests, order endpoints, account endpoints, or private endpoints.
- New frontend/backend/API behavior.
- New data backfill unless the bounded validation preflight proves required local candles are missing.
- Machine learning, futures, leverage, portfolio optimization, or scheduler work.
- Disabling or relaxing the Task 305 cost-aware entry gate for the primary validation.
- Post-result tuning of ATR period, ATR multiples, entry thresholds, or cost assumptions.
- Daily blog `report-ko.html` generation unless the owner explicitly adds that requirement before execution.

# Requirements

- Interpret the owner requirement as:
  - `stop_loss_atr_multiple = 1.0`
  - `take_profit_atr_multiple = 1.0`
  - `1R = ATR_at_entry`
- Use `ATR(14)` as the initial default if the project has no stronger established ATR convention. If an existing convention differs, document the reason before implementation.
- The ATR value used for an entry must be knowable before the entry fill. For next-candle execution, ATR may use completed candles through the signal candle, but must not use the entry candle's future high/low/close.
- If ATR is unavailable, zero, negative, or non-finite, the strategy must not enter and must expose a clear diagnostic reason.
- Long-side geometry:
  - stop: `entry_price - ATR_at_entry * stop_loss_atr_multiple`
  - target: `entry_price + ATR_at_entry * take_profit_atr_multiple`
- Short-side geometry:
  - stop: `entry_price + ATR_at_entry * stop_loss_atr_multiple`
  - target: `entry_price - ATR_at_entry * take_profit_atr_multiple`
- Same-candle stop/target ambiguity handling must remain conservative and documented.
- Runner output and persisted metadata must include enough information to reproduce the ATR risk settings:
  - ATR period
  - ATR calculation convention
  - stop ATR multiple
  - take-profit ATR multiple
  - risk-distance mode
- The validation report must explicitly compare the ATR-risk result against the Task 308 no-entry finding:
  - raw candidates
  - accepted entries
  - cost-blocked entries
  - whether ATR distance made any candidates cost-feasible
  - whether positive gross performance, if present, survived fees/spread/slippage

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read `docs/strategy/lookback_return_momentum_v1.md`.
- [x] Confirm ATR formula/period/no-lookahead timing in the strategy document before code or backtest execution.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` for completion, blockers, or follow-up candidates.

# Acceptance Criteria

- `docs/strategy/lookback_return_momentum_v1.md` documents ATR-based risk/exit behavior before any backtest execution.
- `LOOKBACK_RETURN_MOMENTUM` no longer uses fixed entry-price percentage as its primary risk distance for this assigned workflow.
- Default stop-loss and take-profit distances are both `1 ATR`.
- ATR calculation uses only data available before entry fill.
- Cost-aware entry gating uses ATR-derived planned reward/risk.
- Focused tests cover ATR risk geometry, unavailable ATR handling, long/short stop and target prices, no-lookahead behavior where practical, and cost-gate behavior under ATR distance.
- Bounded validation is executed for `1m`, `5m`, and `15m` over the February-to-May window, or any missing-data blocker is documented before stopping.
- A task report under `reports/` records exact commands, run identifiers if persisted, parameters, results, interpretation, known limitations, and next task.
- No live trading behavior, real order execution, private exchange endpoint usage, hardcoded secrets, or `.env` changes are introduced.

# Required Tests

## Unit Tests

- Add or update focused strategy tests for ATR-based stop/target geometry and invalid ATR handling.
- Add or update cost-aware gate tests proving ATR-derived reward/risk replaces fixed percentage reward/risk.

## Integration Tests

- Run focused momentum strategy/runner tests:

```bash
python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q
```

- If CLI metadata or persistence output changes, run the focused persistence metadata test:

```bash
python -m pytest tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q
```

## Contract Tests

- Verify saved-run metadata or task-report output records ATR period, risk mode, stop ATR multiple, and take-profit ATR multiple.
- Run whitespace verification:

```bash
git diff --check
```

## Safety Tests

- Confirm no code path added by this task calls Binance order/account/private endpoints.
- Confirm no API keys, secrets, or `.env` files are added or modified.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Strategy document updated before implementation/backtest execution.
- No post-result tuning beyond the predeclared validation grid.

# Verification

Default focused verification:

```bash
python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q
python -m pytest tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q
git diff --check
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
  - `reports/TASK_309_LOOKBACK_RETURN_MOMENTUM_ATR_RISK_EXIT_REVISION.md`
  - `reports/task_309_atr_risk_exit_raw_outputs/`
  - project state ledgers
- Implementation summary: replaced the primary momentum risk distance with `ATR_at_entry`, defaulted stop and take-profit distances to `1 ATR`, preserved explicit `fixed_pct` mode for old diagnostics/tests, added invalid ATR diagnostics, wired ATR settings into CLI/config/metadata, and precomputed ATR once per action-building run to keep the 3-month `1m` validation feasible.
- Tests added or updated: ATR risk geometry, ATR no-lookahead context, invalid ATR skip behavior, cost-aware gate behavior under ATR distance, runner CLI metadata, and cost-aware runner wiring.
- Tests run:
  - `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q`
  - `python -m pytest tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q`
  - `git diff --check`
- Validation runs: persisted runs `1180`-`1191` under `TASK_309` using the Task 308 threshold grid and February-to-May window.
- Result: all primary validation candidates remained unfilled. `1m` had no invalid ATR blocks; `5m` had one early invalid ATR block per variant; `15m` had three early invalid ATR blocks per variant. All other candidates were blocked by `COST_INFEASIBLE_NET_RR`.
- Interpretation: ATR risk distance is implemented correctly, but `1 ATR` stop and `1 ATR` target create a 1:1 gross reward/risk. With positive estimated round-trip cost and `min_net_rr=1.0`, net reward/risk is mathematically below `1.0`, so no entries can pass the preserved cost-aware gate.
- Codex self-review result: scope, requirement, role ownership, architecture boundaries, tests, docs, and safety checks passed; no live trading, order endpoint behavior, secrets, or `.env` changes were added.
- Known limitations: no post-result tuning was performed; no daily blog `report-ko.html` was generated because Task 309 excluded it unless explicitly added; filled-trade performance cannot be assessed under the primary gate because accepted entries stayed `0`.
- Recommended next task: create a bounded ATR reward/risk geometry diagnostic that predeclares asymmetric ATR target multiples, or a separate gross-vs-net diagnostic that explicitly relaxes/disables the cost-aware gate for comparison only.
