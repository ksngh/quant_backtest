# Goal

Refactor duplicated analytics/reporting code, reconcile documentation, and update STATUS/BACKLOG/PROJECT_HISTORY after Tasks 173-186, archiving ledgers if the fixed 50-task window rule requires it.

# Source Requirement

Owner instruction: the last task should be code refactoring, documentation consistency, status/backlog/history cleanup, and archiving if required by `AGENTS.md`.

Current repo rule:
- Agents must read state files before work.
- Every task must update status/history/backlog after execution.
- Ledger segmentation archives use fixed 50-task ranges.
- Current root window has Tasks 151-172, so Tasks 173-187 normally remain inside the 151-200 window and should not require fixed archive creation unless the window policy is changed or the root ledger becomes too noisy.

# Extracted Roles

- Owner role:
  - Project maintenance and ledger reconciliation owner.
- Supporting roles:
  - Backtest analytics role: identifies duplicated code.
  - Frontend/API docs role: reconciles displayed fields with API contract.
  - Ledger role: updates state files and archives when needed.
- Forbidden roles:
  - No new feature scope.
  - No live trading.
  - No behavior changes unless required to remove duplication safely.

# Context

After a batch of diagnostics/frontend/reporting tasks, code can become duplicated:
- metric extraction in frontend,
- backend diagnostics subset logic,
- JSON-safe metadata helpers,
- repeated explanation copy,
- docs/API mismatch,
- ledgers out of date.

This task closes the batch cleanly.

# Scope

- Inspect changed files from Tasks 173-186.
- Refactor duplicated helper logic:
  - frontend metric extraction/formatting helpers,
  - backend diagnostics/report helper composition,
  - shared schema constants if appropriate.
- Reconcile docs:
  - `README.md`,
  - `docs/api/API_CONTRACT.md`,
  - `docs/24_WALK_FORWARD_VALIDATION_SCHEMA.md`,
  - any new diagnostics/report docs,
  - frontend/backend status docs if applicable.
- Update ledgers:
  - `STATUS.md`,
  - `BACKLOG.md`,
  - `PROJECT_HISTORY.md`.
- Confirm whether archive is needed:
  - If root ledger remains current 151-200 window, do not create premature archive.
  - If task count crosses a fixed 50-task boundary later, create `*_task_151_200.md` archives.
- Run verification commands.
- Leave next task explicitly undecided or recommend a specific candidate.

# Out of Scope

- No new analytics features.
- No broad redesign.
- No live trading or execution behavior.
- No unrelated file changes.

# Requirements

- Documentation matches actual fields and behavior.
- Root ledgers accurately show active/completed task state.
- Archive pointers are correct.
- No stale references to outdated task windows.
- Refactor does not change public behavior unless tests prove equivalence.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:
- The current root ledger window remains Tasks 151-200; Task 187 does not cross a fixed 50-task archive boundary, so no `*_task_151_200.md` archive should be created.
- Refactoring is limited to low-risk duplication cleanup; broad dashboard decomposition or backend service redesign is deferred unless a clear equivalent helper extraction is small and covered by existing tests.
- This task remains read-only from a trading perspective and must not add live trading, order/account endpoints, API key handling, or `.env` behavior.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Reconciled README/API/status/backlog/history after the Tasks 173-186 analytics/reporting batch.
- Confirmed root ledgers remain in the active Tasks 151-200 window; no `*_task_151_200.md` archive is required yet.
- Extracted duplicated frontend value helpers into `frontend/src/lib/valueUtils.ts` and reused them from diagnostics/conclusion/explanation helpers without changing public behavior.
- Verification passed: `npm --prefix frontend run test:helpers`, `npm --prefix frontend run build`, `pytest`, and `git diff --check`.
- `npm --prefix frontend test` is not defined; the project helper test command is `npm --prefix frontend run test:helpers`.
- Codex self-review: scope respected, no live trading/order/account behavior added, no secrets hardcoded, docs/ledgers updated, and tests passed.
- Known limitation: no new visual regression/component harness was added because this task did not assign new test infrastructure.
- Recommended next task: undecided; candidate is dashboard visual/component regression coverage.

# Acceptance Criteria

- `STATUS.md` says no active task after completion unless a task is intentionally left active.
- `BACKLOG.md` includes completed Tasks 173-187 and follow-up candidates.
- `PROJECT_HISTORY.md` has concise completion notes.
- Docs match API/frontend fields.
- Full verification passes or blockers are documented.

# Required Tests

## Unit Tests

- No new unit tests required unless refactor moves logic; then preserve or add helper tests.

## Integration Tests

- Run backend/frontend/backtesting targeted tests affected by refactor.

## Contract Tests

- API docs and frontend types remain aligned.

## Safety Tests

- Confirm no live trading, order/account endpoints, API keys, or `.env` behavior.

# Verification

Default:

```bash
pytest
npm --prefix frontend run build
git diff --check
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are covered by deterministic regression tests.
- Frontend/API changes remain read-only and do not run backtests or place orders.

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
