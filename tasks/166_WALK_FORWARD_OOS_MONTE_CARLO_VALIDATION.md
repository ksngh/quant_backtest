# Goal

Add a validation workflow for walk-forward, out-of-sample, robustness, Monte Carlo, and bootstrap analysis so strategy quality is judged beyond a single backtest period.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed gap:

- Current CLI runs one selected strategy/pattern over one requested historical window.
- There is no canonical walk-forward validation runner, parameter perturbation harness, or Monte Carlo/bootstrapped uncertainty report.

Read and inspect:

- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/performance_metrics.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- persistence run-key/result models
- existing CLI tests and runtime profiling tasks

# Extracted Roles

- Owner role:
  - Quant validation workflow owner.
- Supporting roles:
  - Backtest runner role: executes deterministic folds.
  - Metrics role: summarizes fold distributions.
  - Persistence role: optionally stores validation runs.
- Forbidden roles:
  - No automatic live deployment decision.
  - No ML training unless a future task assigns it.
  - No broad dashboard implementation unless separate task.

# Context

Code-level hints:

- Add a pure planner that divides date ranges into folds:
  - train window;
  - test window;
  - step size.
- The first implementation can run fixed parameters across folds before adding optimization.
- Add robustness sweeps around selected parameters only if config APIs are stable.
- Monte Carlo can initially reshuffle completed trade R-multiples or block-bootstrap returns.
- Store fold summary metadata under a validation run payload if persistence is extended.

Functional intent:

- The owner should see whether results are stable across time, parameters, and trade ordering.

# Scope

- Implement walk-forward/OOS fold generation.
- Add a validation runner that calls the existing canonical strategy backtest path per fold.
- Add aggregate fold metrics: mean, median, min, max, IQR, failure count, positive-fold ratio.
- Add parameter robustness hooks for selected detector/risk thresholds if feasible.
- Add Monte Carlo/bootstrap helper over trades or returns.
- Add CLI or script entry point with deterministic JSON output.

# Out of Scope

- Automated parameter optimization for production.
- Live trading decisions.
- Complex distributed compute.
- Dashboard UI for validation results.

# Requirements

- Fold boundaries must be UTC and deterministic.
- No fold may use future test data for training/config selection.
- Validation output must include fold date ranges and strategy parameters.
- Empty/no-fill folds must be reported, not silently discarded.
- Monte Carlo/bootstrap must record seed/config for reproducibility.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent task context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A user can run a walk-forward validation over a date range and receive fold-level JSON metrics.
- Aggregate validation summary includes distribution and failure information.
- Monte Carlo/bootstrap output is deterministic given a seed.
- No live trading or exchange account behavior is introduced.

# Required Tests

## Unit Tests

- Test fold boundary generation.
- Test aggregate fold metric calculations.
- Test Monte Carlo/bootstrap deterministic seed behavior.

## Integration Tests

- Test validation runner with a small synthetic candle dataset.
- Test no-fill fold handling.

## Contract Tests

- Document validation output schema.
- Ensure persistence changes are additive if implemented.

## Safety Tests

- Confirm validation runner does not place orders or call exchange account endpoints.
- Confirm it can run offline from stored candles.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.

# Verification

Default:

```bash
pytest tests/backtesting/test_walk_forward.py tests/backtesting/test_performance_metrics.py tests/backtesting/test_strategy_cli_persistence.py
pytest
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
