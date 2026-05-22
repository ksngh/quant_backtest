# Task 107: STRATEGY_EXECUTION_MAPPING_RETIREMENT

## Status

Planned

# Goal

Retire or absorb the long-only strategy execution mapping helper into the canonical long/short action helper API.

# Source Requirement

Current canonical action model supports long and short actions, while the older mapping helper appears long-only and may only be covered by its own test.

# Extracted Roles

- Owner role: Project owner approves whether to delete the helper or keep a deprecation shim.
- Supporting roles: Codex agent updates imports/tests and keeps canonical helper behavior stable.
- Forbidden roles: Core accounting changes, new action types, strategy semantic changes, or broad public API redesign.

# Context

`quant_bitcoin.strategies.actions` owns `StrategyActionType`, `execution_side_for_action`, and `position_side_for_action`. A separate long-only mapping helper can confuse ownership and may not support short-side semantics.

# Scope

- Search for active usage of `strategy_execution_mapping` and `map_long_only_action_to_execution_side`.
- If unused outside compatibility tests, remove the module or convert it to a clearly deprecated shim.
- Migrate tests to validate canonical `strategies.actions` helpers for both long and short actions.
- Update package exports if applicable.

# Out of Scope

- Do not change `StrategyEngine` execution behavior.
- Do not add new action types.
- Do not remove compatibility without documenting it.

# Requirements

- Canonical helper functions remain the single source of action-to-side mapping.
- Short-side mapping is tested.
- Long-only helper is removed or clearly deprecated.

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

- No active code depends on `strategy_execution_mapping`.
- Canonical action helper tests cover enter/exit/partial long and short mappings.
- `python -m compileall quant_bitcoin` passes.

# Required Tests

## Unit Tests

- Update or replace `tests/backtesting/test_strategy_execution_mapping.py`.

## Integration Tests

- Run strategy action and strategy engine tests.

## Contract Tests

- Canonical strategy action mapping contract is explicit and tested.

## Safety Tests

- No live trading, no secrets, no exchange calls.

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
grep -R "map_long_only_action_to_execution_side\|strategy_execution_mapping" . || true
pytest -q tests/backtesting/test_strategy_execution_mapping.py tests/backtesting/test_strategy_engine.py || true
python -m compileall quant_bitcoin
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
