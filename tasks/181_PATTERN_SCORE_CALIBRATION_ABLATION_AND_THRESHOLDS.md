# Goal

Validate whether pattern score components actually predict forward performance by adding score-bucket calibration, component ablation, and threshold sensitivity reports.

# Source Requirement

Current repo now records pattern score components and limitations, but the score is still explicitly a heuristic quality score, not a calibrated probability. Poor backtest performance may mean the score threshold is selecting weak setups or that placeholder score components dominate.

# Extracted Roles

- Owner role:
  - Pattern score research owner.
- Supporting roles:
  - Metrics role: groups outcomes by score.
  - Pattern role: exposes component metadata.
  - Frontend role: explains score reliability.
- Forbidden roles:
  - No automatic production parameter optimization.
  - No live trading.
  - No unsupported alpha claims.

# Context

A pattern score can look precise while failing to predict returns. The repo now exposes component metadata, but there is no calibration report showing whether higher scores produce better hit ratio, average R, or expectancy.

# Scope

- Add score calibration analytics:
  - bucket trades by pattern_score,
  - compute hit ratio, expectancy, average R, median R, profit factor by bucket,
  - compare score component presence/placeholder rate,
  - component ablation report where possible,
  - threshold sensitivity for `minimum_pattern_score`.
- Add warnings:
  - no monotonic improvement across score buckets,
  - too few trades per bucket,
  - placeholder component dominates score,
  - high-score bucket still negative expectancy.
- Expose in diagnostics/API/frontend.
- Document that this is research evidence, not live trading approval.

# Out of Scope

- No automatic threshold changes.
- No ML calibration unless assigned later.
- No live trading.

# Requirements

- Calibration report must be deterministic.
- Must support legacy trades without score metadata.
- Must group by pattern type and score bucket where possible.
- Frontend must show score reliability separately from strategy explanation.

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

Assumptions before implementation:
- Score calibration is read-only evidence; it must not mutate `minimum_pattern_score` or strategy thresholds.
- Legacy rows without score metadata produce a partial report with warnings.
- Component ablation is approximated from component presence/placeholder metadata when exact counterfactual trades are unavailable.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Synthetic data with higher score/lower performance produces warning.
- Missing score metadata produces partial report.
- Dashboard shows score bucket table when available.
- Existing pattern tests still pass.

# Required Tests

## Unit Tests

- Score bucketing.
- Monotonicity warning.
- Placeholder component warning.

## Integration Tests

- Backend diagnostics includes score calibration.
- Frontend build after panel addition.

## Contract Tests

- API docs for score calibration diagnostics.

## Safety Tests

- No strategy threshold mutation.

# Verification

Default:

```bash
pytest tests/patterns tests/backtesting/test_performance_metrics.py backend/tests/test_backtest_results_service_runtime.py
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

# Completion Summary

- Files changed:
  - `quant_bitcoin/backtesting/score_calibration.py`
  - `quant_bitcoin/backtesting/strategy_engine.py`
  - `backend/quant_backtest_api/services/backtest_results.py`
  - `frontend/src/app/page.tsx`
  - `docs/api/API_CONTRACT.md`
  - `tests/backtesting/test_score_calibration.py`
  - `backend/tests/test_backtest_results_service_runtime.py`
- Implementation summary:
  - Added deterministic `pattern_score_calibration_v1` diagnostics with score buckets, hit ratio, expectancy, R metrics, profit factor, placeholder component analysis, component present/absent average-R deltas, threshold sensitivity, and warning flags.
  - Stored diagnostics in strategy-engine summary metadata and exposed read-only API fallback diagnostics for legacy saved runs.
  - Added a frontend Score Reliability panel with bucket table and warning labels.
- Tests added or updated:
  - Added score calibration unit tests for monotonicity, missing metadata, placeholder dominance, and threshold sensitivity.
  - Updated backend runtime diagnostics test to assert score calibration exposure.
- Tests run:
  - `pytest tests/backtesting/test_score_calibration.py backend/tests/test_backtest_results_service_runtime.py`
  - `npm --prefix frontend run build`
  - `pytest tests/patterns tests/backtesting/test_performance_metrics.py tests/backtesting/test_score_calibration.py backend/tests/test_backtest_results_service_runtime.py`
  - `pytest`
  - `git diff --check`
- Codex self-review result:
  - Scope stayed within Task 181; no live trading, order endpoints, API keys, `.env`, or strategy threshold mutation were added.
- Known limitations:
  - Component ablation is observational from component presence/absence metadata, not a true counterfactual rerun.
- Recommended next task:
  - Task 182.
