# Task 108: PATTERNS_PUBLIC_EXPORT_BOUNDARY_CLEANUP

## Status

Planned

# Goal

Clarify the public import boundary between pattern detectors, risk planning, and compatibility shims.

# Source Requirement

`quant_bitcoin.patterns.__init__` re-exports detector models, risk-exit planning contracts, and simulation compatibility items broadly. Compatibility shims under `quant_bitcoin.patterns` can obscure the canonical `quant_bitcoin.risk` ownership.

# Extracted Roles

- Owner role: Project owner approves the desired public API boundary and compatibility retention policy.
- Supporting roles: Codex agent migrates imports/docs/tests conservatively.
- Forbidden roles: Deleting externally required compatibility without approval, strategy behavior changes, DB/API/frontend work, or live trading.

# Context

Pattern detector modules and risk/exit simulation modules are related but have different responsibilities. Public exports should not make compatibility shims appear canonical if the canonical risk modules live under `quant_bitcoin.risk`.

# Scope

- Inventory imports from `quant_bitcoin.patterns.risk_exit` and `quant_bitcoin.patterns.exit_simulation`.
- Migrate active internal imports to `quant_bitcoin.risk` canonical paths where appropriate.
- Reduce or document broad `patterns.__init__` exports if owner approves.
- Keep compatibility shims only with explicit deprecation documentation.
- Update tests to validate canonical imports.

# Out of Scope

- Do not change detector algorithms or risk-plan calculations.
- Do not remove public compatibility used by tests/users without explicit documentation.
- Do not change CLI behavior.

# Requirements

- Detector API, risk API, and compatibility API ownership are clear.
- Active internal code prefers canonical risk module paths.
- Any retained broad exports are intentional.

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

- No active internal imports use deprecated pattern shim paths unless compatibility-only.
- Tests pass for patterns and risk modules.
- Documentation reflects canonical import paths.

# Required Tests

## Unit Tests

- Add import-boundary tests only if helpful.

## Integration Tests

- Run pattern and risk test suites.

## Contract Tests

- Public import contract is documented and intentional.

## Safety Tests

- No live trading, no API keys, no exchange order endpoints.

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
grep -R "quant_bitcoin.patterns.risk_exit\|quant_bitcoin.patterns.exit_simulation" quant_bitcoin tests docs || true
pytest -q tests/patterns tests/risk
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
