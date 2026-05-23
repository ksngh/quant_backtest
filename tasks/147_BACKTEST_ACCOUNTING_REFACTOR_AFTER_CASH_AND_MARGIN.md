# Goal

Refactor the backtest accounting, sizing, and margin-simulation code after Tasks 140-146 have locked behavior with tests.

This task must not introduce new business behavior. It exists to reduce duplication, clarify naming, isolate account-state calculations, and make future maintenance safer.

# Source Requirement

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `tasks/141_LONG_CASH_BOUNDED_ENTRY_EXECUTION.md`
- `tasks/142_SHORT_BUYING_POWER_POLICY.md`
- `tasks/143_SIMULATED_MARGIN_INITIAL_MARGIN_GUARD.md`
- `tasks/144_ACCOUNT_STATE_VISIBILITY_FIELDS.md`
- `tasks/145_CANONICAL_CLI_PERSISTENCE_WIRING_FOR_SIZING_MARGIN.md`
- `tasks/146_BACKTEST_CASH_EQUITY_DISPLAY_AND_API_SEMANTICS.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- related sizing/accounting modules added by Tasks 140-146
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- all tests added or modified by Tasks 140-146

# Extracted Roles

- Owner role:
  - Backtest accounting refactor owner.
  - Owns code organization and internal naming without changing external behavior.
- Supporting roles:
  - Test suite role: guards behavior before and after refactor.
  - Persistence/API role: verifies no external contract regression.
  - Documentation role: receives final consistency updates in Task 148.
- Forbidden roles:
  - No new sizing behavior.
  - No new margin behavior.
  - No new CLI flags.
  - No documentation rewrite beyond tiny comments/docstrings.
  - No live trading behavior.
  - No exchange endpoint behavior.

# Context

Tasks 140-146 intentionally prioritize behavior and user-visible correctness. Once those changes are tested, the implementation may contain duplicated calculations, long helper functions, or unclear naming around cash, equity, free cash, margin used, and locked short proceeds.

This task is intentionally placed after feature tasks and before documentation consistency.

# Scope

- Extract focused helpers for account-state calculation if needed.
- Extract focused helpers for sizing quantity resolution if needed.
- Extract focused helpers for margin requirement calculation if needed.
- Reduce duplication between long and short execution paths without changing semantics.
- Improve type names, docstrings, and internal comments where they clarify accounting responsibilities.
- Keep public dataclass fields and CLI/API contracts stable.
- Keep all tests from Tasks 117 and 140-146 passing.

# Out of Scope

- New behavior.
- New user-facing fields.
- New CLI flags.
- New persistence schema.
- Frontend/backend feature changes.
- Live trading or exchange integration.
- Large package reshuffle.

# Requirements

- Refactor must be behavior-preserving.
- Any moved functions/classes must have compatibility imports if they were public.
- Existing tests must pass without changing expectations except for import path updates justified by internal move.
- Account-state calculation must be easier to audit than before refactor.
- Sizing and margin checks must remain deterministic.
- Summary metadata and result serialization must remain compatible.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Tasks 140-146 are completed or explicitly skipped with owner approval.
- [x] Confirm this Task 147 is recorded as the current active implementation task before coding.
- [x] Confirm Task 148 is not started before this refactor is complete.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to Task 148 as next if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Refactor introduces no intended behavior change.
- Account-state, sizing, and margin calculation code is more localized and auditable.
- Existing external fields, CLI output, and persistence/API contracts remain compatible.
- Full targeted backtest/accounting test suite passes.
- Codex self-review explicitly confirms no scope expansion.

# Required Tests

## Unit Tests

- Re-run all account-state, sizing, long, short, and margin tests from Tasks 140-146.
- Add small helper-level tests only if helpers contain non-trivial logic not already covered.

## Integration Tests

- Re-run canonical strategy runner tests.
- Re-run persistence metadata tests.
- Re-run backend/frontend serialization tests if touched.

## Contract Tests

- Verify public imports remain compatible or documented migration aliases exist.
- Verify existing dataclass fields remain available.
- Verify CLI JSON keys remain stable.

## Safety Tests

- No order endpoint is called.
- No account endpoint is called.
- No margin/futures endpoint is called.
- No API keys are required.
- No live trading behavior is introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Refactor does not smuggle in feature changes.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
pytest tests/persistence
pytest tests/execution
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
