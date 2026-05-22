# Task 109: FVG_CACHE_NAMING_OR_PATTERN_CACHE_REGISTRY

## Status

Completed (2026-05-22)

# Goal

Resolve the mismatch between generic pattern-cache naming and FVG-specific implementation.

# Source Requirement

Current optimization module naming suggests general pattern detection caching, but implementation is centered on `IndicatorCache.for_fvg(...)` and `detect_fair_value_gap_at_index(...)`.

# Extracted Roles

- Owner role: Project owner chooses rename-only vs generalized registry strategy.
- Supporting roles: Codex agent applies the chosen naming/registry design and updates imports/tests.
- Forbidden roles: New pattern detector implementations, behavior changes to FVG detection, CLI integration changes, or performance rewrites outside cache ownership.

# Context

FVG detection has an optimized cache path, while other patterns still use prefix detector evaluation. The module should either honestly be named FVG-specific or be extended into a real pattern cache registry.

# Scope

- Document two options before implementation: rename-only or generalized registry.
- If rename-only: move/alias `pattern_detection_cache.py` to FVG-specific naming and update imports.
- If generalized: introduce minimal registry/context abstractions without changing detector outputs.
- Preserve optimized FVG parity and no-look-ahead guarantees.
- Update tests and docs/import paths.

# Out of Scope

- Do not change FVG detection results.
- Do not optimize all non-FVG patterns unless owner explicitly chooses registry expansion and scope is bounded.
- Do not change CLI semantics.

# Requirements

- Module name matches actual responsibility.
- FVG cache behavior remains deterministic and parity-tested.
- No-look-ahead behavior remains protected.

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

- FVG optimized output matches prefix detector fixtures.
- Imports remain clear and stable.
- No hidden behavior change to pattern strategy evaluation.

# Required Tests

## Unit Tests

- Update cache unit tests or add rename/import tests.

## Integration Tests

- Run pattern detection optimization and strategy tests.

## Contract Tests

- No-look-ahead/data contract for candle prefixes remains intact.

## Safety Tests

- No live trading, no exchange calls, no secrets.

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
pytest -q tests/backtesting/test_pattern_detection_optimization.py
pytest -q tests/strategies
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
