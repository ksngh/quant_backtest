# Task 105: README_AND_API_CONTRACT_CANONICAL_BACKTEST_REFRESH

## Status

Planned

# Goal

Refresh README/API/backend warning docs so they describe canonical StrategyEngine-backed backtest behavior rather than legacy or placeholder paths.

# Source Requirement

Previous analysis showed README and API contract references can lag behind canonical CLI/persistence behavior, including legacy `BasicBacktester` wording and placeholder graph warning language.

# Extracted Roles

- Owner role: Project owner approves wording around deprecated aliases and whether old persisted-run warnings should remain visible.
- Supporting roles: Codex agent updates documentation and narrowly scoped backend warning text if required.
- Forbidden roles: Strategy implementation changes, DB schema changes, frontend rendering, live trading, or new API endpoints.

# Context

The repository has migrated toward canonical strategy-engine and persistence flows. Documentation should distinguish canonical commands from retained compatibility aliases and make old placeholder-run warnings precise.

# Scope

- Audit `README.md`, `docs/api/API_CONTRACT.md`, backend read-model service docs/comments, and CLI docs for legacy command/path language.
- Update canonical command examples to prefer `quant-bitcoin-strategy-backtest`.
- Document retained compatibility aliases as deprecated or compatibility-only.
- Clarify placeholder warning semantics as old-run compatibility warnings if canonical graph values now exist.
- Update `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md` as required by task completion.

# Out of Scope

- Do not change runtime behavior unless needed to align a misleading warning condition and covered by tests.
- Do not remove compatibility aliases.
- Do not add live trading or deployment instructions.

# Requirements

- Docs must match current canonical CLI ownership.
- Deprecated paths must be clearly labeled if retained.
- Warnings must not imply canonical runs are placeholder-only when they are not.

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

- README command examples no longer instruct active use of deprecated paths as primary path.
- API contract/backend warning text distinguishes canonical persisted results from old placeholder-neutral runs.
- Docs preserve safety boundary: no live trading, no real order execution, no API keys.

# Required Tests

## Unit Tests

- Not applicable unless warning helper behavior is changed.

## Integration Tests

- Run backend tests if backend warning logic changes.

## Contract Tests

- API contract text and backend read-model warning behavior remain aligned.

## Safety Tests

- No hardcoded secrets, no live execution instructions, no exchange order endpoint enablement.

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
grep -R "BasicBacktester\|placeholder-neutral\|quant-bitcoin-postgres-backtest\|quant-bitcoin-pattern-backtest" README.md docs backend quant_bitcoin || true
pytest -q backend/tests || true
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
