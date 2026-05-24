# Goal

Finish the remediation sequence by refactoring touched code for maintainability, reconciling documentation with implemented behavior, and updating STATUS, BACKLOG, PROJECT_HISTORY, and ledger archives according to `AGENTS.md`.

# Source Requirement

Owner requirement for the final task in this remediation task pack:

- The last task must cover code refactoring.
- The last task must align documentation consistency.
- The last task must organize `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- The last task must follow `AGENTS.md`, including archiving when needed.

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_TEMPLATE.md`
- all completed tasks in this remediation sequence, expected Tasks 152-170
- `docs/10_CODEX_COMMAND_GUIDE.md`
- `reviews/CODEX_SELF_REVIEW.md`
- `reviews/REVIEW_CHECKLIST.md`
- relevant README/docs/API docs touched by Tasks 152-170
- `docs/ledger_archives/`

# Extracted Roles

- Owner role:
  - Final remediation consistency owner.
  - Owns post-implementation cleanup, docs, and ledger reconciliation.
- Supporting roles:
  - Backtest/research role: confirms code behavior matches docs.
  - Documentation role: updates README, architecture, API, and task docs.
  - Ledger-maintenance role: updates status/backlog/history and archives fixed task ranges.
- Forbidden roles:
  - No new feature implementation except small refactors necessary to remove duplication or clarify completed behavior.
  - No live trading.
  - No exchange order/account endpoint calls.
  - No broad dashboard redesign unless a prior task explicitly created that scope.

# Context

Code-level hints:

- This task should run after the functional remediation tasks are complete.
- Refactoring targets may include duplication introduced across:
  - pattern action building;
  - sizing/quantity-mode handling;
  - intrabar policy wiring;
  - detector no-lookahead helpers;
  - metric/metadata serialization.
- Keep refactors small and behavior-preserving unless prior task acceptance criteria explicitly require behavior changes.
- Documentation to check:
  - `README.md` backtest/strategy-engine sections;
  - `docs/api/API_CONTRACT.md` if API/read models changed;
  - architecture/data-contract docs if candle validation or detection contracts changed;
  - task docs for completion checklists.
- Ledger archival:
  - Current root ledgers list Tasks 101-150.
  - If this pack creates/completes Tasks 152-171, create or update `docs/ledger_archives/backlog_task_101_150.md` and `docs/ledger_archives/project_history_task_101_150.md` if not already present.
  - Keep root `BACKLOG.md` and `PROJECT_HISTORY.md` focused on the latest active/recent window and include archive pointers.
  - Do not delete historical information; move it into fixed 50-task archives as required by `AGENTS.md`.

Functional intent:

- After the remediation sequence, code behavior, docs, task states, and ledgers should agree.

# Scope

- Review all code touched by Tasks 152-170 and remove unnecessary duplication.
- Align README/docs/API docs with actual implemented behavior.
- Update completed task checklists only where acceptance criteria and verification are satisfied.
- Update root `STATUS.md` with current phase, active task state, blockers, and recommended next step.
- Update `BACKLOG.md` with completed/blocked/follow-up status for Tasks 152-171.
- Append concise completion notes to `PROJECT_HISTORY.md`.
- Archive ledger windows according to the fixed 50-task range rule when needed.
- Run full verification and self-review.

# Out of Scope

- Adding new trading strategy behavior.
- Enabling live trading.
- Rewriting architecture beyond cleanup needed for consistency.
- Closing Task 138 or any live execution task without explicit owner approval.

# Requirements

- Code refactors must preserve behavior verified by prior tests.
- Docs must describe current implemented behavior, not planned future behavior.
- Any unsupported behavior must remain explicitly labeled as unsupported or blocked.
- `STATUS.md` must identify the current active task or no active task.
- `BACKLOG.md` must mark completed, blocked, deferred, and follow-up items accurately.
- `PROJECT_HISTORY.md` must include concise completion notes.
- Ledger archives must use fixed 50-task ranges as required by `AGENTS.md`.
- Task checkboxes must only be marked complete when verified.
- Task 138 live execution blocker must remain visible unless separately approved.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent task context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- No obvious duplicated remediation code remains where a small shared helper is appropriate.
- README/docs/API docs match actual backtest behavior after Tasks 152-170.
- `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md` are internally consistent.
- Ledger archives are created/updated if the root ledgers move from Tasks 101-150 to a newer window.
- Full test suite or documented feasible subset passes.
- `git diff --check` passes.
- Completion summary includes changed files, tests run, self-review result, known limitations, and recommended next task.

# Required Tests

## Unit Tests

- Run all unit tests affected by the remediation sequence.
- Add targeted regression tests only if refactoring exposes an uncovered behavior.

## Integration Tests

- Run canonical backtest CLI, persistence, backend service, and execution-safety test subsets relevant to changed behavior.
- Run frontend build/tests only if frontend/API docs/types were touched.

## Contract Tests

- Verify docs match current output contracts.
- Verify task template structure remains intact for newly created task documents.
- Verify ledger archive pointers are correct.

## Safety Tests

- Confirm no live trading is enabled.
- Confirm no real Binance order execution is enabled.
- Confirm no API keys or `.env` files are introduced.
- Confirm Task 138 remains blocked unless explicitly approved by owner.

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
npm --prefix frontend run build  # only if frontend/types were touched
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
