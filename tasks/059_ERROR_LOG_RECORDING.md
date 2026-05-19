# Task 059: Error Logging on Runtime Failures

# Goal

Add a focused implementation task definition so runtime errors are recorded in logs during execution, without expanding into unrelated observability infrastructure.

# Source Requirement

"실행 중에 오류가 생기면 로그가 남기게 하고 싶어."

(Owner intent: When an error occurs while the program is running, preserve an error log for troubleshooting.)

# Extracted Roles

- Owner role:
  - Define where error logs should be written (console, file, or both) and acceptable verbosity.
  - Approve final logging behavior and format.
- Supporting roles:
  - Application entrypoint/runner modules configure logger initialization.
  - Runtime orchestration paths catch top-level exceptions and emit structured error logs.
  - Tests verify logging occurs for representative runtime exceptions.
- Forbidden roles:
  - No live trading behavior.
  - No exchange order execution.
  - No infrastructure expansion (dashboard, DB logging sink, scheduler, Docker-only logging stack).

# Context

The project already has backtesting and paper-trading workflows. The requested change is reliability-oriented: preserve diagnostic information when runtime failures occur. This task should remain minimal and compatible with current scope.

# Scope

- Define a single implementation target for runtime error logging in currently supported execution flows.
- Add deterministic logging behavior for uncaught/top-level runtime exceptions.
- Ensure stack trace or equivalent exception detail is preserved in emitted logs.
- Add/update tests validating that runtime exceptions generate logs.
- Update relevant usage docs only if runtime behavior/CLI expectations change.

# Out of Scope

- Live trading, real exchange order execution, risk-management redesign.
- External log aggregation platforms (ELK, CloudWatch, Datadog, etc.).
- Full observability overhaul (metrics/tracing frameworks).
- New database schema for logs.
- Background scheduler or service orchestration redesign.

# Requirements

- Introduce or reuse project logging configuration so runtime errors are recorded consistently.
- For supported CLI/runtime entrypoints, top-level exceptions must be logged with error severity.
- Error logs must include enough context to identify failing component and exception message.
- Error handling must not swallow failures silently; non-zero failure behavior should remain explicit.
- No secrets/API keys may be written intentionally by new code paths.
- Keep implementation incremental and limited to files required by this task.

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

- A concrete implementation PR can be produced from this task without requiring additional requirement decomposition.
- Runtime exception logging behavior is explicitly defined and testable.
- Scope and safety boundaries remain aligned with project rules.

# Required Tests

## Unit Tests

- Add/update tests for logger emission when representative runtime exceptions occur.

## Integration Tests

- Add/update entrypoint-level test(s) that assert runtime failure produces expected log output and explicit failure signaling.

## Contract Tests

- N/A unless existing public runner/CLI contract output changes.

## Safety Tests

- Verify no live exchange order API paths are introduced.
- Verify no secrets are intentionally logged by added code paths.

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

Task-focused suggested checks after implementation:

```bash
pytest -q
python -m quant_bitcoin.backtesting.pattern_postgres_runner_cli --help
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
