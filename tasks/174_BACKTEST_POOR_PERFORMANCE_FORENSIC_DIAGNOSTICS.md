# Goal

Add automated diagnostics that explain why a saved backtest performed poorly, separating economic weakness from mechanical timing, fill, risk, cost, and attribution issues.

# Source Requirement

Owner request: current backtests show poor performance; analyze whether the reason is economic invalidity, bad entry/exit timing, algorithmic buy/sell timing, risk management, or metric interpretation.

Latest repo findings:
- Task 172 fixed an FVG actual-fill/risk-plan mismatch where take-profit could be a realized loss.
- Current engine stores cost summary, trade attribution, short-economics warnings, and performance metrics.
- Frontend still lacks a run-level “why did this backtest perform poorly?” explanation panel.

# Extracted Roles

- Owner role:
  - Backtest forensics owner.
  - Owns diagnostic taxonomy and user-facing explanation.
- Supporting roles:
  - Backtesting role: computes deterministic diagnostic flags.
  - API role: exposes diagnostics read-only.
  - Frontend role: renders concise explanations.
- Forbidden roles:
  - No strategy tuning.
  - No live trading.
  - No exchange/order endpoint calls.

# Context

Bad performance can come from several different sources:
- strategy edge is absent;
- entry chases displacement too late;
- exit target/stop is asymmetric;
- partial exits harvest small wins and leave large losses;
- costs consume gross edge;
- soft invalidation fires too late or too early;
- shorts lose due to simulated economics mismatch;
- position sizing overexposes the account;
- run has too few trades to infer anything.

The repo has many raw metrics now, but no classifier that turns them into a clear diagnosis.

# Scope

- Add a pure helper module such as `quant_bitcoin/backtesting/performance_diagnostics.py`.
- Input: summary metadata, executions/trades, graph points, and optional run parameters.
- Output schema: `backtest_performance_diagnostics_v1`.
- Implement deterministic flags:
  - `NEGATIVE_EXPECTANCY`,
  - `LOW_HIT_RATE`,
  - `POOR_PAYOFF_RATIO`,
  - `HIGH_COST_DRAG`,
  - `LARGE_OR_PERSISTENT_DRAWDOWN`,
  - `NO_COMPLETED_TRADES`,
  - `LOW_EXPOSURE`,
  - `HIGH_TURNOVER`,
  - `SHORT_SIMULATION_ONLY`,
  - `ZERO_COST_ASSUMPTION`,
  - `ENTRY_FILL_REFERENCE_DIVERGENCE`,
  - `TAKE_PROFIT_NEGATIVE_PNL_ANOMALY`,
  - `SOFT_INVALIDATION_DOMINANT`,
  - `TIME_STOP_DOMINANT`,
  - `STOP_LOSS_DOMINANT`.
- Add severity levels: `INFO`, `WARNING`, `CRITICAL`.
- Include `evidence` values and `suggested_next_analysis`.
- Expose through backend `diagnostics`.
- Show in frontend as `Run Diagnosis` panel.

# Out of Scope

- Do not mutate strategy behavior.
- Do not mark a strategy “profitable” or “unprofitable” without evidence.
- Do not use ML or external data.
- Do not add live execution behavior.

# Requirements

- Diagnostics must be deterministic from persisted run data.
- Diagnostics must distinguish mechanical anomalies from poor alpha.
- If `TAKE_PROFIT` has negative PnL, it must be a critical anomaly.
- If sample size is too small, the panel must say inference is weak.
- If metadata is missing, produce partial diagnostics with warnings.
- Frontend must show concise top findings first and raw details only behind disclosure.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Poor runs show at least one clear reason category.
- A fixture with negative expectancy and low hit rate produces both flags.
- A fixture with high gross PnL but negative net PnL produces high-cost-drag flag.
- A fixture with take-profit negative PnL produces critical anomaly.
- API and frontend render diagnostics safely for legacy runs.
- No strategy or fill behavior changes occur.

# Required Tests

## Unit Tests

- Add tests for each diagnostic flag using small synthetic summaries/executions.
- Add missing metadata tests.

## Integration Tests

- Backend service test: diagnostics appear under run detail response.
- Frontend build must pass after panel addition.

## Contract Tests

- Document `backtest_performance_diagnostics_v1`.

## Safety Tests

- Confirm diagnostics are read-only and no execution code is imported into frontend/backend API.

# Verification

Default:

```bash
pytest tests/backtesting/test_performance_metrics.py backend/tests/test_backtest_results_service_runtime.py
npm --prefix frontend run build
pytest
git diff --check
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are covered by deterministic regression tests.
- Frontend/API changes remain read-only and do not run backtests or place orders.

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

# Completion Notes

- Files changed:
  - `quant_bitcoin/backtesting/performance_diagnostics.py`
  - `quant_bitcoin/backtesting/strategy_engine.py`
  - `quant_bitcoin/backtesting/__init__.py`
  - `backend/quant_backtest_api/services/backtest_results.py`
  - `backend/tests/test_backtest_results_service_runtime.py`
  - `tests/backtesting/test_performance_diagnostics.py`
  - `frontend/src/app/page.tsx`
  - `frontend/src/styles/globals.css`
  - `docs/api/API_CONTRACT.md`
  - `STATUS.md`, `BACKLOG.md`, `PROJECT_HISTORY.md`, `frontend/STATUS.md`
  - `tasks/174_BACKTEST_POOR_PERFORMANCE_FORENSIC_DIAGNOSTICS.md`
- Implementation summary:
  - Added pure `calculate_backtest_performance_diagnostics()` with schema `backtest_performance_diagnostics_v1`.
  - Implemented deterministic severity flags for alpha weakness, risk/reward weakness, cost drag, drawdown persistence, sample weakness, exposure/turnover, short simulation caveats, zero-cost assumptions, fill/reference divergence, negative-PnL take-profit anomaly, and dominant exit reasons.
  - Strategy-engine summaries now include persisted `performance_diagnostics`.
  - Backend detail responses expose saved diagnostics or compute partial diagnostics from persisted summary/trade/graph rows for legacy runs.
  - Frontend now renders a concise read-only `Run Diagnosis` panel with raw details behind disclosure.
- Tests added or updated:
  - Added synthetic unit coverage for every required diagnostic flag and missing metadata behavior.
  - Updated backend service diagnostics test for `performance_diagnostics`.
- Tests run:
  - `pytest tests/backtesting/test_performance_diagnostics.py tests/backtesting/test_performance_metrics.py backend/tests/test_backtest_results_service_runtime.py`
  - `npm --prefix frontend run test:helpers`
  - `npm --prefix frontend run build`
  - `pytest`
  - `git diff --check`
- Codex self-review result:
  - Scope stayed inside Task 174 read-only diagnostics/reporting.
  - No strategy tuning, live trading, exchange order/account endpoint, API key, or `.env` behavior was added.
  - Backend/API/frontend changes remain derived from persisted data and do not run backtests.
- Known limitations:
  - Thresholds are deterministic heuristics, not profitability claims.
  - Legacy rows can only receive partial diagnostics when metadata is missing.
- Recommended next task:
  - Task 175 `ENTRY_EXIT_TIMING_FORENSICS_AND_MFE_MAE_METRICS`.
