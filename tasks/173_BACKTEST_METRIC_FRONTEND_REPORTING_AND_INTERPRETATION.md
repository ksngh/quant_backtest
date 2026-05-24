# Goal

Expose the currently implemented research/performance metrics in the saved-run dashboard and API diagnostics so a user can judge a backtest beyond total return and trade count.

# Source Requirement

Owner request after reviewing weak backtest results: summarize what is missing in the current backtest report, show Sharpe ratio and other useful performance metrics, and explain results clearly in the frontend.

Latest repo findings:
- `quant_bitcoin/backtesting/performance_metrics.py` already computes annualized return/volatility, Sharpe, Sortino, Calmar, max drawdown, drawdown duration, total return, lifecycle trade metrics, exposure, turnover, and grouped attribution.
- `quant_bitcoin/backtesting/strategy_engine.py` stores `performance_metrics`, `trade_attribution`, `cost_summary`, and `short_economics` in summary metadata.
- `backend/quant_backtest_api/services/backtest_results.py` exposes research diagnostics, but frontend panels currently emphasize final equity, total return, trade count, cash, charts, trade table, strategy explanation, parameters, and runtime.
- `frontend/src/app/page.tsx` should surface these metrics as first-class analysis cards with plain-language interpretation.

# Extracted Roles

- Owner role:
  - Backtest report UX and research-diagnostics owner.
  - Owns which performance metrics are shown and how they are interpreted.
- Supporting roles:
  - Backend API role: exposes existing diagnostics safely.
  - Frontend role: renders read-only analytics.
  - Backtesting role: preserves metric definitions and does not change fills.
- Forbidden roles:
  - No strategy logic change.
  - No live trading.
  - No exchange endpoint behavior.
  - No dashboard ability to run backtests.

# Context

The current dashboard already has charting and strategy explanation panels, but it does not make Sharpe/Sortino/Calmar, drawdown duration, profit factor, expectancy, exposure, turnover, cost drag, or attribution obvious. As a result, a bad strategy looks merely like “low total return” instead of explaining whether the problem is low hit rate, poor payoff ratio, cost drag, drawdown persistence, low exposure, bad short-side behavior, or pattern/regime weakness.

# Scope

- Add a dedicated frontend `Performance Diagnostics` panel.
- Read metrics from `detail.summary.metadata.performance_metrics`, `trade_attribution`, and `cost_summary`.
- Show at least:
  - total return,
  - annualized return,
  - annualized volatility,
  - Sharpe ratio,
  - Sortino ratio,
  - Calmar ratio,
  - max drawdown,
  - max drawdown duration,
  - hit ratio,
  - payoff ratio,
  - expectancy,
  - profit factor,
  - average/median R,
  - max consecutive losses,
  - exposure fraction,
  - turnover ratio,
  - cost-to-gross-PnL ratio,
  - zero-cost assumption flag.
- Add plain-language interpretation labels:
  - `Poor risk-adjusted return`,
  - `Cost drag high`,
  - `Low hit rate`,
  - `Negative expectancy`,
  - `Drawdown recovery weak`,
  - `No completed trade lifecycle`.
- Update `frontend/src/types/api.ts` only as needed.
- Update `docs/api/API_CONTRACT.md` if newly consumed fields need documentation.
- Keep raw JSON hidden behind details/debug only.

# Out of Scope

- No new performance metric formulas unless required by missing existing metadata.
- No strategy parameter tuning.
- No backend DB schema migration unless existing metadata cannot be read.
- No live trading or execution changes.

# Requirements

- Existing metadata must be used when present and missing legacy metadata must render safely.
- Display metrics as user-facing cards/tables, not raw JSON.
- Each metric must have a short tooltip or helper label explaining what it means.
- Negative or problematic values must be visually distinguishable but not alarmist.
- Dashboard must still work for legacy runs that do not have `trade_attribution`.
- Frontend must not call DB directly or run backtests.

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

- Saved run detail page shows Sharpe, Sortino, Calmar, max drawdown, hit ratio, expectancy, profit factor, exposure, turnover, and cost summary when present.
- Legacy runs render `No metric available` rather than crashing.
- Zero-cost runs show a clear warning.
- The panel makes it possible to identify whether poor performance came from hit rate, payoff, cost, drawdown, or exposure.
- No trading or backend execution behavior is introduced.

# Required Tests

## Unit Tests

- Add frontend helper tests if a frontend test harness exists or create a minimal helper-only test target for:
  - metric extraction from nested metadata,
  - missing metric fallback,
  - risk label classification,
  - zero-cost warning classification.

## Integration Tests

- Add or update backend service tests to ensure diagnostics include `performance_metrics`, `trade_attribution`, and `cost_summary` for runs that have them.
- Add a frontend fixture path if a harness is available.

## Contract Tests

- Confirm API contract documents the nested metric paths used by the frontend.

## Safety Tests

- Confirm no order/account endpoint, API key, `.env`, or live trading behavior is added.

# Verification

Default:

```bash
pytest backend/tests/test_backtest_results_service_runtime.py
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
  - `.gitignore`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `frontend/STATUS.md`
  - `frontend/package.json`
  - `frontend/tsconfig.test.json`
  - `frontend/src/app/page.tsx`
  - `frontend/src/lib/performanceDiagnostics.ts`
  - `frontend/src/styles/globals.css`
  - `frontend/tests/performanceDiagnostics.test.ts`
  - `backend/tests/test_backtest_results_service_runtime.py`
  - `docs/api/API_CONTRACT.md`
  - `tasks/173_BACKTEST_METRIC_FRONTEND_REPORTING_AND_INTERPRETATION.md`
- Implementation summary:
  - Added a read-only `Performance Diagnostics` panel to the saved-run detail dashboard.
  - Extracted nested saved-run `performance_metrics`, `trade_attribution`, and `cost_summary` metadata through a helper module.
  - Rendered user-facing cards for total/annualized return, volatility, Sharpe, Sortino, Calmar, drawdown, hit ratio, expectancy, profit factor, cost drag, exposure, and turnover.
  - Added helper text/tooltips, safe legacy `No metric available` fallback, and explicit zero-cost assumption warning.
  - Documented the frontend-consumed nested metadata paths in the API contract.
- Tests added or updated:
  - Added frontend helper tests for metric extraction, missing metadata fallback, risk labels, and zero-cost classification.
  - Updated backend diagnostics service test coverage for `cost_summary`.
- Tests run:
  - `npm --prefix frontend run test:helpers`
  - `npm --prefix frontend run build`
  - `pytest backend/tests/test_backtest_results_service_runtime.py`
  - `pytest`
  - `curl -s http://localhost:3000`
  - `git diff --check`
- Codex self-review result:
  - Scope stayed inside Task 173 frontend/API-diagnostics reporting.
  - No strategy logic, backtest fills, live trading, exchange endpoints, API keys, or `.env` behavior were added.
  - Backend change was test-only and verified existing read-only diagnostics exposure.
- Known limitations:
  - Browser automation could not be used because the required browser-control execution tool was not exposed in this session; local HTTP response and production build were verified instead.
  - Legacy runs without saved metadata show unavailable metrics rather than synthesized values.
- Recommended next task:
  - Task 174 `BACKTEST_POOR_PERFORMANCE_FORENSIC_DIAGNOSTICS`.
