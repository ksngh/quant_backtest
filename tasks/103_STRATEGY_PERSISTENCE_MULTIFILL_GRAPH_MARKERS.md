# Task 103: STRATEGY_PERSISTENCE_MULTIFILL_GRAPH_MARKERS

## Status

Planned

# Goal

Preserve multiple executions that occur at the same timestamp when building persisted graph-point markers.

# Source Requirement

Pattern action integration can generate multiple executions around the same candle/timestamp. Current persistence-adapter behavior should be reviewed for timestamp-keyed overwrites and upgraded if needed.

# Extracted Roles

- Owner role: Project owner approves backward-compatible metadata shape for multi-execution graph markers.
- Supporting roles: Codex agent updates persistence adapter/tests and keeps schema compatibility.
- Forbidden roles: DB schema redesign, backend/frontend rendering changes unless strictly required by tests, strategy semantic changes, or live trading.

# Context

Canonical persistence now maps `StrategyBacktestResult` to persisted trades, graph points, and summaries. If graph point marker maps are keyed by timestamp to a single execution, same-timestamp partial/final exits or entry/exit combinations can lose marker detail. This task makes graph metadata multi-fill safe without requiring schema migration.

# Scope

- Inspect `quant_bitcoin/backtesting/strategy_persistence_adapter.py` for timestamp-to-single-execution assumptions.
- Change graph marker construction to preserve a list of executions per timestamp in metadata.
- Retain existing scalar marker fields where needed for backward compatibility.
- Add tests for same-timestamp multiple executions.
- Update API contract docs only if the serialized metadata shape is externally visible.

# Out of Scope

- Do not change database schema unless unavoidable and owner-approved.
- Do not change core accounting values.
- Do not implement frontend chart rendering.

# Requirements

- Persisted graph points must not drop same-timestamp executions.
- Existing consumers expecting scalar `signal` or `trade_sequence` must remain compatible.
- Metadata must be JSON-serializable and deterministic.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Same-timestamp execution fixture persists all relevant trade sequences/signals in graph-point metadata.
- Existing single-execution marker tests continue to pass.
- Persistence payload remains compatible with current repository schema.

# Required Tests

## Unit Tests

- Add/modify unit tests for `_build_graph_points` or equivalent adapter helper.

## Integration Tests

- Run persistence adapter and CLI persistence tests.

## Contract Tests

- Validate serialized metadata contract remains backward-compatible for backend read model.

## Safety Tests

- No secrets, no live trading, no exchange calls.

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
pytest
```

Task-specific:

```bash
pytest -q tests/backtesting/test_strategy_persistence_adapter.py
pytest -q tests/backtesting/test_strategy_cli_persistence.py
pytest -q backend/tests || true
python -m compileall quant_bitcoin backend
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
