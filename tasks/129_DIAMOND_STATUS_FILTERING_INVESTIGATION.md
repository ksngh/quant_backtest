# Task 129: Diamond Status Filtering Investigation

# Goal
Stabilize Diamond single-pattern strategy behavior by investigating and resolving the current default status-filtering mismatch causing failing unit tests.

# Source Requirement
- Owner request: "129번 task 진행해줘"
- Current project status pointer recommends this exact candidate: investigate Diamond strategy unit-test failures around default pattern status filtering.

# Extracted Roles

- Owner role: assign scope and approve behavioral contract.
- Supporting roles: strategy/backtest maintainer for `quant_bitcoin/strategies` and related tests.
- Forbidden roles: frontend/backend API feature expansion, live trading, exchange order execution.

# Context
`STATUS.md` currently reports two failing tests in `tests/strategies/test_single_pattern_strategies.py` tied to Diamond bullish/bearish entry expectations versus current status filtering behavior. Task 129 focuses only on this contract clarification/fix and regression validation.

# Scope

- Reproduce the reported Diamond status-filtering test failures.
- Confirm intended default pattern status policy for Diamond strategy path.
- Implement minimal code/test updates so default behavior and tests are aligned.
- Update task ledgers (`STATUS.md`, `PROJECT_HISTORY.md`, `BACKLOG.md`) after implementation.

# Out of Scope

- Any non-Diamond pattern behavior changes.
- Frontend/backend dashboard/API work.
- Live trading, exchange execution, credential/policy work.
- Performance optimization unrelated to Diamond status filtering.

# Requirements

- Keep changes limited to Diamond single-pattern strategy behavior and directly related tests/docs.
- Preserve architecture boundaries and existing canonical strategy interfaces.
- Add or update regression coverage for default status filtering semantics.
- Run targeted verification and report known limitations.

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

- Reported Diamond default status-filtering failures are reproduced and resolved.
- Diamond strategy default status-filtering behavior is explicit and test-backed.
- Targeted strategy test suite passes for updated Diamond expectations.
- Root ledgers are updated consistently for Task 129 completion state.

# Required Tests

## Unit Tests

- `pytest tests/strategies/test_single_pattern_strategies.py -k diamond`

## Integration Tests

- N/A unless required by discovered coupling.

## Contract Tests

- Any existing strategy contract tests impacted by Diamond default status filtering.

## Safety Tests

- Ensure no exchange order endpoints are introduced/called.

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

Task-focused minimum:

```bash
pytest tests/strategies/test_single_pattern_strategies.py -k diamond
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
