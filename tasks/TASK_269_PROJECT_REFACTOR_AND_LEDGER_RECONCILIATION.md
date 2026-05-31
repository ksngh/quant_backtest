# Goal

Refactor and reconcile the project after the recent FVG research changes, then clean up `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` so they accurately reflect the current state and next tasks.

# Source Requirement

Owner requested:

- project refactoring;
- cleanup of `STATUS.md`;
- cleanup of `PROJECT_HISTORY.md`;
- cleanup of `BACKLOG.md`;
- then run Tasks 267, 268, and 269.

# Extracted Roles

- Owner role: Defines the desired cleanup/refactor boundary and confirms whether any follow-up task ordering should change.
- Supporting roles:
  - Refactor role: simplify recent FVG/volume/Order Block code without changing behavior.
  - Ledger role: reconcile `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`.
  - Verification role: run focused tests and `git diff --check`.
- Forbidden roles:
  - Live trading or real order execution.
  - Exchange order/account endpoint calls.
  - Large architecture redesign.
  - Frontend/backend API changes unless directly required by the cleanup.
  - Implementing Tasks 267 or 268 inside this task.

# Context

Recent work created or completed multiple FVG-related tasks:

- Task 267: local previous/current candle Order Block filter for FVG entry timing.
- Task 268: close-volume default threshold changes.
- Task 269 should be a cleanup/reconciliation task after those implementation tasks, not a place to silently add new trading behavior.

The root ledgers are intentionally recent high-signal windows and must remain aligned with the fixed 50-task archive rule.

# Scope

- Inspect recent strategy/backtest code touched by Tasks 266-268.
- Refactor only if it removes obvious duplication, improves naming, or makes the current behavior easier to verify.
- Keep public CLI behavior stable unless the ledger/task explicitly says otherwise.
- Reconcile root ledgers:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Confirm task pointers are accurate:
  - current active task;
  - completed work;
  - remaining work;
  - blockers;
  - next task.
- Remove stale or duplicated recent-window notes if they conflict with completed task state.
- Keep archive pointers accurate.
- Run focused verification.

# Out of Scope

- Implementing Task 267.
- Implementing Task 268.
- Live trading.
- Real Binance order placement.
- Database schema changes.
- UI redesign.
- Broad package/module restructuring.
- Changing strategy semantics except where required to preserve behavior after small refactors.

# Requirements

- Read the latest task state before editing.
- Only refactor code after Tasks 267 and 268 are complete, unless the owner explicitly assigns Task 269 first.
- Do not change FVG trading behavior in this task except as a consequence of behavior-preserving cleanup.
- If behavior-changing work is discovered, create a new task instead of silently implementing it.
- Keep ledger files concise and high-signal.
- If root ledger window grows beyond the expected range boundary, apply the fixed 50-task archive rule.
- The final state must clearly record:
  - Task 267 completion state;
  - Task 268 completion state;
  - Task 269 completion state;
  - next recommended task.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Confirm Tasks 267 and 268 are complete or explicitly record why Task 269 is running first.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Any refactor is behavior-preserving and focused.
- `STATUS.md` accurately reports phase, current step, active task, completed work, blockers, and next task.
- `PROJECT_HISTORY.md` contains a concise Task 269 completion note when done.
- `BACKLOG.md` marks completed/created/reprioritized tasks accurately.
- No stale “next task” pointer conflicts with the actual owner-assigned task order.
- Archive pointers remain correct.
- Focused tests pass or any blocker is recorded explicitly.

# Required Tests

## Unit Tests

- Run tests covering files touched by any refactor.

## Integration Tests

- Run recent FVG/backtesting tests if strategy/backtest code is touched.

## Contract Tests

- If CLI metadata is touched, verify CLI metadata tests still pass.

## Safety Tests

- Confirm no exchange order/account endpoint calls are introduced.
- Confirm no API keys or `.env` files are added.

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

Default targeted verification:

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q
git diff --check
```

If only ledgers/docs are changed and no code is touched, `git diff --check` is sufficient, but the final summary must say why tests were not run.

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

# Completion Notes

- Completed (2026-05-28): Recent FVG OB/volume code was reconciled after Tasks 267 and 268, with the historical OB detector path split behind explicit compatibility mode and root ledgers updated.
- Targeted verification passed:
  - `pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q`
