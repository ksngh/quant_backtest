# Task 104: STRATEGY_POSTGRES_RUNNER_CLI_REFACTOR

## Status

Planned

# Goal

Split the compressed canonical strategy PostgreSQL CLI into focused parser, action orchestration, runner, persistence, and output-serialization units.

# Source Requirement

Repository verification showed `strategy_postgres_runner_cli.py` currently combines imports, parser setup, env defaults, candle loading, action construction, engine invocation, persistence, and JSON serialization in one compressed file.

# Extracted Roles

- Owner role: Project owner approves behavior-preserving refactor boundaries and whether module names should be public or internal.
- Supporting roles: Codex agent performs a behavior-preserving refactor with tests.
- Forbidden roles: Behavioral changes to strategy accounting, pattern semantics, persistence schema, Docker profile, or live trading.

# Context

The canonical CLI is central to RSI and pattern backtests. Its current single-file compressed structure makes later work difficult and increases risk of scope creep. This task should occur after the pattern action-builder integration to avoid merge conflicts.

# Scope

- Create focused helper modules or functions for CLI config parsing, action orchestration, persistence writing, and stdout serialization.
- Keep `quant_bitcoin.backtesting.strategy_postgres_runner_cli:main` as the entrypoint.
- Preserve `pattern_postgres_runner_cli` wrapper compatibility unless a later task removes it.
- Expand compressed imports/statements into normal readable Python style.
- Add focused tests for any extracted helpers.

# Out of Scope

- Do not change CLI option names or defaults except if documented as bug fixes.
- Do not modify Docker Compose or README in this task.
- Do not remove legacy CLI wrappers.

# Requirements

- Refactor must be behavior-preserving.
- New helper modules should not introduce unnecessary abstraction layers.
- Error logging and exit codes must remain compatible.

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

- Existing strategy CLI, pattern CLI, and RSI CLI tests pass.
- Entrypoint scripts in `pyproject.toml` still resolve.
- Code is more readable and module responsibilities are clear.

# Required Tests

## Unit Tests

- Add unit tests for extracted config/output/action helper functions where useful.

## Integration Tests

- Run existing CLI integration and persistence tests.

## Contract Tests

- CLI stdout JSON contract remains backward-compatible unless explicitly documented.

## Safety Tests

- No live trading, no exchange orders, no secrets.

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
pytest -q tests/backtesting/test_strategy_cli_persistence.py
pytest -q tests/backtesting/test_pattern_postgres_runner_cli.py
pytest -q tests/backtesting/test_postgres_runner_cli.py
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
