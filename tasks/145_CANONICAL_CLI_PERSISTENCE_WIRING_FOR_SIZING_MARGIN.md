# Goal

Wire the new sizing, short buying-power, and simulated-margin options through the canonical strategy PostgreSQL runner CLI and persistence metadata.

CLI defaults must be safe and explicit. Users should not be surprised into `1 BTC` exposure when starting cash is `10_000`.

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
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/postgres_runner_cli.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/persistence/postgres.py`
- `docs/api/API_CONTRACT.md` if output contract is changed
- `tests/backtesting/test_strategy_postgres_runner_cli.py`
- `tests/persistence/`

# Extracted Roles

- Owner role:
  - Canonical CLI and persistence wiring owner.
  - Owns user-facing configuration flags and persisted metadata for sizing/margin policy.
- Supporting roles:
  - Strategy engine role: already implements behavior from Tasks 140-144.
  - Persistence role: stores additive policy metadata.
  - Documentation role: later reconciles user docs in Task 148.
- Forbidden roles:
  - No new live trading controls.
  - No real Binance order execution.
  - No margin/futures endpoint integration.
  - No frontend redesign.
  - No broad refactor. That is Task 147.

# Context

After engine behavior is corrected, users need an explicit way to choose sizing and simulated-margin behavior in the canonical CLI. The CLI currently exposes `--starting-cash` and `--trade-quantity`, and the pattern runner default can create misleading BTC-sized exposure if not guarded by the previous tasks.

This task wires configuration and metadata, not new accounting behavior.

# Scope

- Add CLI flags for sizing mode and sizing parameters.
- Add CLI flags for explicit short/margin simulation only if implemented by Tasks 142-143.
- Ensure CLI defaults align with safe behavior from Tasks 141-143.
- Include sizing/margin policy in JSON output metadata.
- Include sizing/margin policy in persistence metadata and run identity only if necessary for deterministic run-key semantics.
- Preserve backward-compatible use of `--trade-quantity` where appropriate.
- Update CLI tests.

# Out of Scope

- Implementing sizing/margin behavior in the engine.
- Adding account-state fields.
- Refactoring strategy runner internals beyond wiring.
- Documentation cleanup beyond minimal help text.
- Frontend/backend display changes.
- Real execution behavior.

# Requirements

- CLI help must describe sizing mode clearly.
- CLI defaults must not silently open oversized short exposure.
- `--trade-quantity` compatibility must be documented in parser behavior and tests.
- Invalid CLI combinations must fail deterministically.
- JSON stdout must include selected sizing and margin policy metadata.
- Persisted metadata must allow later inspection of the sizing and margin policy used for a backtest run.
- Existing no-persist and persist CLI paths must remain serializable.
- Task 138 live trading blocked state must remain unchanged.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Tasks 140-144 are completed or explicitly approved as dependencies.
- [x] Confirm this Task 145 is recorded as the current active implementation task before coding.
- [x] Confirm Task 146 is not started before this task is complete.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to Task 146 as next if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Canonical strategy runner accepts explicit sizing configuration.
- Canonical strategy runner accepts explicit simulated-margin configuration only when the engine supports it.
- Unsafe or ambiguous CLI combinations fail with stable errors.
- CLI JSON output includes sizing/margin policy metadata.
- Persistence metadata includes sizing/margin policy metadata additively.
- Existing CLI tests still pass after updates.
- No live trading behavior is added.

# Required Tests

## Unit Tests

- Test parser accepts valid sizing modes.
- Test parser rejects invalid sizing mode or invalid parameter combinations.
- Test parser preserves `--trade-quantity` compatibility.
- Test parser rejects simulated-margin flags when required parameters are missing.

## Integration Tests

- Test canonical strategy runner no-persist output includes sizing metadata.
- Test canonical strategy runner no-persist output includes simulated-margin metadata when explicitly configured.
- Test persistence payload includes policy metadata.
- Test default CLI does not silently open oversized short exposure in a fixture.

## Contract Tests

- Existing CLI output keys remain available.
- New metadata is additive.
- Run-key behavior is deterministic and documented when policy metadata affects identity.

## Safety Tests

- No live order endpoint is called.
- No account endpoint is called.
- No margin/futures endpoint is called.
- No API keys are required.
- No `ENABLE_LIVE_TRADING=true` default is introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- CLI flags do not imply real margin/futures behavior.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
pytest tests/persistence
pytest tests/backtesting/test_strategy_engine_accounting.py
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
