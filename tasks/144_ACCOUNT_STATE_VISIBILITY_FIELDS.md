# Goal

Expose clear account-state fields so `cash_after` cannot be mistaken for free buying power when a short position is open.

This task should add additive, side-aware accounting visibility such as free cash, margin used, locked short proceeds, and cash semantics metadata while preserving existing `cash_after`, `position_after`, and `equity_after` fields.

# Source Requirement

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/117_SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS.md`
- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `tasks/142_SHORT_BUYING_POWER_POLICY.md`
- `tasks/143_SIMULATED_MARGIN_INITIAL_MARGIN_GUARD.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/persistence/postgres.py`
- `db/init/001_schema.sql`
- `frontend/src/types/api.ts` if backend/API fields are already exposed
- `docs/api/API_CONTRACT.md` if serialized API fields are changed
- `tests/backtesting/test_strategy_engine_accounting.py`
- `tests/persistence/`

# Extracted Roles

- Owner role:
  - Backtest account-state visibility owner.
  - Owns explicit cash/equity/free-cash/margin/locked-proceeds interpretation.
- Supporting roles:
  - Strategy engine role: computes execution/equity account-state snapshots.
  - Persistence role: stores or passes through additive metadata.
  - API/frontend role: may consume additive fields in later or scoped updates.
- Forbidden roles:
  - No breaking removal of existing result fields.
  - No real margin/futures implementation.
  - No live trading.
  - No frontend redesign beyond type-safe additive support if required.

# Context

The confusing symptom is not only that `cash_after` can increase after a short entry. It is also that users may read `cash_after` as free cash. For shorts, short-sale proceeds may be represented in the cash account, but they should not be presented as unrestricted buying power.

After Tasks 142 and 143 define short and simulated-margin guardrails, this task makes the account-state output explicit.

# Scope

- Add additive account-state fields to execution/equity/summary metadata where appropriate.
- Candidate fields:
  - `free_cash_after`
  - `margin_used_after`
  - `short_proceeds_locked_after`
  - `available_buying_power_after`
  - `cash_after_semantics`
- Compute fields consistently for flat, long, short, partial-exit, and full-exit states.
- Preserve existing `cash_after`, `position_after`, `equity_after`, summary fields, and persistence compatibility.
- Include clear metadata that `equity_after` is the primary net-asset value when positions are open.
- Update persistence payload metadata only additively unless a separate migration task is created.

# Out of Scope

- Changing core sizing behavior.
- Changing short buying-power policy.
- Changing margin/leverage requirements.
- CLI flags. Those are Task 145.
- Documentation cleanup. That is Task 148.
- Removing or renaming existing fields.
- Real exchange account state.

# Requirements

- Existing result fields remain available.
- For flat account state, free cash should equal cash/equity unless costs or existing model semantics require a documented difference.
- For long positions, free cash should not include position market value unless explicitly documented as buying power.
- For short positions, short-sale proceeds must not be represented as unrestricted free cash.
- For explicit simulated-margin shorts, margin used must be visible.
- Partial exits must update account-state fields consistently.
- Summary metadata must describe cash semantics clearly.
- Tests must prove `cash_after` and `free_cash_after` differ when short proceeds are locked.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Tasks 142 and 143 are completed or explicitly approved as dependencies.
- [x] Confirm this Task 144 is recorded as the current active implementation task before coding.
- [x] Confirm Task 145 is not started before this task is complete.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to Task 145 as next if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Account-state visibility fields are additive and serializable.
- `cash_after` is preserved but no longer the only cash-related field for short states.
- Short proceeds are not reported as free cash.
- `equity_after` remains available and is clearly represented as net account value.
- Persistence/API compatibility is preserved or explicitly documented with additive fields.
- Existing Task 117, 142, and 143 tests still pass.

# Required Tests

## Unit Tests

- Test flat account-state fields.
- Test long account-state fields.
- Test short account-state fields with locked proceeds or equivalent semantics.
- Test simulated-margin account-state fields with margin used.
- Test partial short exit updates free cash, margin used, and locked proceeds consistently.
- Test `cash_after_semantics` or equivalent metadata exists when short positions are present.

## Integration Tests

- Test persistence payload includes new metadata additively.
- Test API serialization remains backward-compatible if API fields are touched.
- Test canonical strategy runner JSON output remains serializable.

## Contract Tests

- Existing `StrategyExecution` fields remain available.
- New fields are optional/additive if added to dataclasses.
- Existing database schema remains compatible unless a migration is intentionally added and tested.

## Safety Tests

- No exchange account endpoint is called to populate these fields.
- No order endpoint is called.
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
- Account-state labels do not overpromise real exchange margin accuracy.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/persistence
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
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
