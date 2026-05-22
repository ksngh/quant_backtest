# Goal

Document the enriched pattern-strategy CLI output contract introduced in Task 110 and expand deterministic fixtures to cover short-side and no-fill paths.

# Source Requirement

- Candidate from `BACKLOG.md`: Task 111 `PATTERN_STRATEGY_OUTPUT_CONTRACT_DOCUMENTATION_AND_FIXTURE_EXPANSION` (document enriched stdout schema and broaden deterministic fixtures for short-side/no-fill cases).
- Owner prompt: "다음 task 진행" (proceed with the next task).

# Extracted Roles

- Owner role: Quant/backtest maintainer
- Supporting roles: Strategy CLI documentation and test fixture maintenance
- Forbidden roles: Live trading, exchange order execution, frontend/backend API redesign

# Context

Task 110 enriched strategy CLI output with executions/events/diagnostics and warning classifications. Follow-up work is needed to make the output contract explicit and ensure deterministic fixture coverage for short-side and no-fill scenarios.

# Scope

- Document enriched pattern-strategy stdout JSON fields (executions/events/diagnostics/warnings) in project docs.
- Add or expand deterministic fixtures for:
  - short-side pattern action/backtest output paths
  - no-fill warning/diagnostic output paths
- Add/update tests that lock contract behavior for these fixtures.

# Out of Scope

- Strategy-engine financial model redesign.
- Live trading or exchange API integration.
- Frontend/dashboard implementation changes.
- Persistence schema redesign beyond fixture-contract coverage explicitly needed by this task.

# Requirements

- Keep backward-compatible core JSON fields while documenting enriched metadata fields.
- Fixture data and tests must remain deterministic and non-networked.
- Contract-focused tests must assert warning classification and diagnostics presence/shape for short/no-fill cases.
- Do not modify unrelated modules.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions / notes:
- This task is now the relevant next task candidate and needs owner confirmation/assignment before implementation execution.
- No parallel batch is planned at task-definition stage.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Task documentation explicitly defines enriched output contract fields relevant to pattern strategy CLI.
- Deterministic fixtures include short-side and no-fill scenarios.
- Tests pass for documented contract/fixtures and guard warning + diagnostics schema.
- Status/history/backlog are updated at implementation completion.

# Required Tests

## Unit Tests

- Strategy CLI output schema tests for warning and diagnostics fields.

## Integration Tests

- Deterministic pattern strategy run fixture tests for short-side and no-fill outputs.

## Contract Tests

- JSON contract assertions for required enriched fields and backward-compatible base fields.

## Safety Tests

- Confirm no live order/account endpoint usage is introduced.

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
