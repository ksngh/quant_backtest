# Task 106: LEGACY_PUBLIC_API_PRUNING

## Status

Planned

# Goal

Reduce deprecated backtesting APIs exposed through package-level public imports after canonical behavior is verified.

# Source Requirement

Task 096 marked legacy cleanup completed by adding deprecation guidance, but deprecated modules may still be exported through `quant_bitcoin.backtesting.__init__` and validated by legacy-focused tests.

# Extracted Roles

- Owner role: Project owner approves whether retained legacy modules should be removed, moved to compatibility-only namespace, or left as explicit shims.
- Supporting roles: Codex agent inventories imports, updates tests/docs, and prunes public exports conservatively.
- Forbidden roles: Pattern action integration, CLI refactor, strategy semantic changes, or deleting compatibility required by users without approval.

# Context

Deprecated modules such as `basic.py` and `pattern_strategy.py` can remain useful as compatibility references, but package-level public exports make them look canonical. This task prunes the import surface only after canonical tests are stable.

# Scope

- Inventory active imports of `BasicBacktester`, `BacktestResult`, `PatternStrategyBacktestConfig`, and `run_pattern_strategy_backtest`.
- Remove deprecated symbols from `quant_bitcoin.backtesting.__all__` unless owner approves keeping them.
- Move legacy-focused tests to compatibility-only tests or rewrite them to canonical StrategyEngine paths.
- Add explicit compatibility/deprecation comments where retained.
- Update docs that expose deprecated APIs as primary usage.

# Out of Scope

- Do not remove modules that are still required by active tests or compatibility without documenting the decision.
- Do not change canonical strategy-engine accounting behavior.
- Do not touch Docker/backend/frontend unless imports require it.

# Requirements

- Every deprecated symbol has one explicit decision: remove export, keep as compatibility, or migrate test.
- Active docs and active CLI paths do not rely on deprecated public API.
- Compatibility behavior remains intentional if retained.

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

- `quant_bitcoin.backtesting` public export surface is canonical-first.
- Active code no longer imports deprecated backtest modules unless compatibility-only.
- Tests verify canonical paths rather than expanding legacy behavior.

# Required Tests

## Unit Tests

- Add/update import-surface or compatibility tests if useful.

## Integration Tests

- Run full backtesting test suite.

## Contract Tests

- Package import contract remains stable for canonical symbols.

## Safety Tests

- No live trading, no secrets, no exchange order endpoints.

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
grep -R "BasicBacktester\|run_pattern_strategy_backtest\|PatternStrategyBacktestConfig" quant_bitcoin tests README.md docs || true
pytest -q tests/backtesting
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
