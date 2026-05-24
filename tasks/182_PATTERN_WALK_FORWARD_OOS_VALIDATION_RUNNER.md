# Goal

Extend the walk-forward/OOS validation framework from RSI-only foundation to supported pattern strategies, so pattern performance can be checked out-of-sample.

# Source Requirement

Current repo has `walk_forward.py` and `walk_forward_cli.py`, but the CLI supports RSI only. The owner wants to understand poor performance and whether the strategy has economic validity; this requires pattern OOS validation, not just in-sample backtest.

# Extracted Roles

- Owner role:
  - Pattern validation owner.
- Supporting roles:
  - Backtesting engine role.
  - Pattern strategy role.
  - CLI/reporting role.
- Forbidden roles:
  - No optimizer that silently selects best result.
  - No live trading.
  - No exchange endpoint behavior.

# Context

A single in-sample backtest can be poor due to one regime, or good due to luck. Pattern strategies need fold-based validation to distinguish alpha from parameter/period dependence.

# Scope

- Add pattern action builder support to walk-forward framework.
- CLI options:
  - `--strategy pattern`,
  - `--pattern`,
  - `--entry-mode` if available,
  - `--allowed-pattern-statuses`,
  - `--min-pattern-score`,
  - cost profile/bps,
  - sizing mode.
- For each fold:
  - build actions using only train+current test history without future leakage,
  - run engine on test window,
  - record fold summary, attribution, cost, and diagnostics.
- Aggregate:
  - positive fold ratio,
  - median return,
  - median expectancy,
  - fold drawdown distribution,
  - fold trade count,
  - pattern/regime fold stability.
- Optionally persist validation result or output JSON only in this task.

# Out of Scope

- No automatic parameter optimization unless the task explicitly defines train selection.
- No live trading.
- No frontend backtest execution.

# Requirements

- Pattern walk-forward CLI runs at least FVG and Order Block on deterministic fixture.
- Fold actions do not use candles after each signal point.
- Output includes fold-level and aggregate diagnostics.
- Existing RSI walk-forward remains working.

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
- Pattern walk-forward validation is offline JSON/reporting only and does not persist or execute live orders.
- Initial supported pattern CLI coverage can share the existing canonical pattern strategy construction where available.
- No automatic parameter optimization is introduced; fold train data is context/history only.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Pattern WFO command works for supported pattern names.
- JSON schema documented.
- No-lookahead tests pass.
- Tests cover no-fills and failed fold behavior.

# Required Tests

## Unit Tests

- Pattern action builder for folds.
- Fold generation with pattern action history.

## Integration Tests

- Walk-forward CLI for FVG fixture.
- Walk-forward CLI for Order Block fixture if feasible.

## Contract Tests

- `docs/24_WALK_FORWARD_VALIDATION_SCHEMA.md` updated.

## Safety Tests

- No network calls or exchange endpoints.

# Verification

Default:

```bash
pytest tests/backtesting/test_walk_forward.py tests/patterns/test_no_lookahead_contract.py tests/backtesting/test_pattern_postgres_runner_cli.py
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
  - `quant_bitcoin/backtesting/walk_forward.py`
  - `quant_bitcoin/backtesting/walk_forward_cli.py`
  - `quant_bitcoin/backtesting/__init__.py`
  - `tests/backtesting/test_walk_forward.py`
  - `docs/24_WALK_FORWARD_VALIDATION_SCHEMA.md`
- Implementation summary:
  - Added offline pattern action-builder support for walk-forward validation using train plus current test-prefix signal detection and remaining-test-window exit simulation.
  - Extended WFO fold summaries with expectancy and read-only diagnostics, and aggregate output with expectancy distribution and pattern fold stability.
  - Extended CLI with `--strategy pattern`, `--pattern`, entry-mode, pattern-status, score-threshold, cost, and sizing arguments while preserving RSI mode.
  - Documented the pattern WFO schema and no-optimization/no-live-execution boundary.
- Tests added or updated:
  - Added WFO tests for FVG current-prefix action generation, pattern fixture validation, and CLI JSON for FVG and Order Block.
- Tests run:
  - `pytest tests/backtesting/test_walk_forward.py`
  - `pytest tests/backtesting/test_walk_forward.py tests/patterns/test_no_lookahead_contract.py tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `pytest`
  - `git diff --check`
- Codex self-review result:
  - Scope stayed within Task 182; no live trading, exchange endpoints, API keys, `.env`, or automatic parameter optimization were added.
- Known limitations:
  - Pattern WFO train windows are used as fixed historical context only; this task does not optimize parameters on train folds.
- Recommended next task:
  - Task 183.
