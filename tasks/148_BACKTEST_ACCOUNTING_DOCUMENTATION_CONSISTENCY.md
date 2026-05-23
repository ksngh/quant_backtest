# Goal

Reconcile all documentation and project ledgers after the cash-bounded sizing, short buying-power, simulated-margin, account-state, CLI/persistence, display/API, and refactor tasks are complete.

This is the final task in this work window. It must make the repository documentation consistent with the implemented behavior and remove or revise stale descriptions that imply `cash_after` is free cash or that simulated shorts are real margin/futures shorts.

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
- `tasks/147_BACKTEST_ACCOUNTING_REFACTOR_AFTER_CASH_AND_MARGIN.md`
- `README.md`
- `docs/api/API_CONTRACT.md`
- `docs/`
- `backend/STATUS.md` if backend docs/status changed
- `frontend/STATUS.md` if frontend docs/status changed
- CLI help text and docstrings in relevant backtesting modules
- `reviews/CODEX_SELF_REVIEW.md`
- `reviews/REVIEW_CHECKLIST.md`

# Extracted Roles

- Owner role:
  - Documentation consistency owner.
  - Owns final written contract for cash, equity, free cash, margin used, short simulation, and unsupported economics.
- Supporting roles:
  - Backtest role: provides implemented semantics from Tasks 140-147.
  - API/frontend role: provides display/read-model terms if touched.
  - Ledger role: records completion state and next step accurately.
- Forbidden roles:
  - No new implementation behavior.
  - No refactor beyond typo-level cleanup.
  - No live trading approval or implementation.
  - No exchange endpoint behavior.

# Context

The repository already documents limitations from Task 117 and product boundaries from Task 135. After Tasks 140-147, docs must be updated so users understand:

- `cash_after` is not always free buying power.
- `equity_after`/`final_equity` represent net account value.
- Long entries are cash-bounded.
- Default short policy prevents silent oversized short exposure.
- Simulated margin/leverage is opt-in and backtest-only.
- Borrow fees, futures funding, maintenance margin, and liquidation are still unsupported unless a future task implements them.
- Spot paper/testnet/live behavior remains distinct from backtest simulation.

# Scope

- Update README and docs that describe backtest cash/equity/trade behavior.
- Update API contract docs if new fields or metadata were added.
- Update CLI usage docs/examples to show safe sizing configuration.
- Update warnings/limitations docs around short simulation and simulated margin.
- Update backend/frontend status docs only if those areas changed.
- Update `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` to reflect completed task sequence and next task pointer.
- Remove stale references that conflict with implemented behavior.
- Keep documentation concise and directly tied to current code.

# Out of Scope

- Implementing new code behavior.
- Renaming public fields.
- Adding new API fields.
- Refactoring source code.
- Live trading work.
- Approving Task 138.
- Exchange integration.

# Requirements

- Documentation must match implemented code after Tasks 140-147.
- `cash_after`, `ending_cash`, `equity_after`, `final_equity`, free cash, margin used, and locked proceeds must be defined consistently wherever they appear.
- Short simulation docs must clearly distinguish backtest simulation from spot execution and real margin/futures products.
- CLI examples must avoid unsafe or misleading default assumptions.
- Unsupported economics limitations must remain explicit:
  - no borrow fees modeled,
  - no futures funding modeled,
  - no maintenance margin or liquidation model.
- Ledger files must point to the correct next task or explicitly state no active implementation task.
- Task 138 live trading blocked state must remain visible unless explicit owner approval exists.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Tasks 140-147 are completed or explicitly skipped with owner approval.
- [x] Confirm this Task 148 is recorded as the current active documentation task before editing docs.
- [x] Confirm no implementation changes are required; if implementation gaps are found, stop and create a follow-up task instead of patching behavior here.
- [x] Record assumptions, blockers, or unclear status items before editing.

## After Implementation

- [x] Update `STATUS.md` to reflect completion or any blocker.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete and record the next candidate task.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- README/docs/API contract text matches current cash/equity/sizing/short/margin behavior.
- Stale or contradictory docs are removed or corrected.
- CLI examples and help references are consistent with safe defaults.
- Ledger files accurately record Tasks 140-148 completion or blockers.
- No code behavior is changed.
- Documentation clearly states remaining limitations and Task 138 live-trading blocker.

# Required Tests

## Unit Tests

- No new unit tests required unless documentation examples are executable snippets.

## Integration Tests

- Run targeted tests for any executable examples or generated docs checks if present.
- Re-run smoke tests for CLI help if docs depend on parser output.

## Contract Tests

- Verify API contract docs match serialized fields if API fields changed.
- Verify frontend type documentation matches API field names if frontend docs changed.

## Safety Tests

- No exchange endpoint calls.
- No API keys required.
- No `.env` files created or modified.
- No live trading approval or implementation introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Documentation does not claim unsupported margin/futures realism.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
```

If documentation-only changes make full pytest unnecessary in the execution environment, run the targeted smoke tests above and document the reason.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- documentation summary
- tests run
- Codex self-review result
- known limitations
- recommended next task
