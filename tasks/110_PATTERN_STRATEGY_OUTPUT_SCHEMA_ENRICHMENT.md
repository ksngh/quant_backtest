# Task 110: PATTERN_STRATEGY_OUTPUT_SCHEMA_ENRICHMENT

## Status

Completed (2026-05-22)

# Goal

Enrich strategy-backtest CLI JSON output so pattern events, actions, executions, and diagnostics are inspectable from stdout.

# Source Requirement

Current `strategy_postgres_runner_cli.py` serializes executions minimally and emits `events: []`, even though pattern action metadata can contain pattern-event and exit details.

# Extracted Roles

- Owner role: Project owner approves the stdout JSON fields and compatibility requirements for scripts consuming CLI output.
- Supporting roles: Codex agent updates serializer/tests after canonical action integration is complete.
- Forbidden roles: Backend API schema migration, frontend dashboard rendering, persistence schema redesign, or strategy semantic changes.

# Context

Once canonical pattern action builder integration is complete, CLI stdout should expose enough information to debug pattern detection, entry fill, exits, and skipped actions without opening the database.

# Scope

- Extend CLI output serialization to include action type, position side, execution side, pattern event id, exit reason, cost fields, and relevant metadata.
- Populate `events` or `diagnostics` with concise pattern/event summaries derived from actions/executions.
- Keep backward-compatible core fields: `strategy`, `portfolio`, `summary`, `executions`, `warnings`.
- Add tests for no-event, skipped-entry, entry+exit, and short-side cases where fixtures exist.

# Out of Scope

- Do not change persistence schema.
- Do not implement backend/frontend rendering.
- Do not change strategy accounting or detector outputs.

# Requirements

- Output must remain deterministic JSON.
- Sensitive data must never be emitted.
- Warnings must clearly distinguish no events, no fills, invalid risk plan, and open-position limitations.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- CLI stdout can explain pattern action flow without DB inspection.
- Existing consumers can still read old core fields.
- Tests cover enriched output for representative scenarios.

# Required Tests

## Unit Tests

- Add serializer unit tests if output logic is extracted.

## Integration Tests

- Run CLI integration tests for strategy and pattern backtests.

## Contract Tests

- CLI JSON contract remains backward-compatible for core fields.

## Safety Tests

- No secrets, no live trading, no exchange orders.

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
