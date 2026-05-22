# Task 099: LEDGER_SEGMENTATION_AND_TEMPLATE_ENFORCEMENT

## Status
Completed

# Goal
Reduce context overload by segmenting large ledger documents and enforce task-document template compliance for all newly created tasks.

# Source Requirement
Owner request (2026-05-22):
- keep only recent entries in root `BACKLOG.md` and `PROJECT_HISTORY.md`;
- move older entries into segmented files (example naming like `backlog_task1_50.md`);
- apply similar segmentation to `PROJECT_HISTORY.md`;
- add an explicit rule that every new task document must follow `tasks/TASK_TEMPLATE.md`.

# Extracted Roles
- Owner role: approve segmentation boundaries and naming convention.
- Supporting roles: Codex agent for markdown ledger restructuring and rule updates.
- Forbidden roles: source-code/strategy/backtest behavior changes.

# Context
Large root ledger files are increasing cognitive load and may cause missed constraints during task execution. The project needs a rolling-window approach for root ledgers and archival segment files for older entries.

# Scope
- Define and apply segmentation policy for `BACKLOG.md`:
  - keep latest ~15 task-related entries in root (exact count to be declared in execution notes);
  - archive older entries into 50-task chunk files under a deterministic naming scheme.
- Define and apply segmentation policy for `PROJECT_HISTORY.md` similarly.
- Add/update project rules (in `AGENTS.md` and/or process docs) requiring all new task docs to follow `tasks/TASK_TEMPLATE.md`.
- Update `STATUS.md` pointers to reflect where current vs archived ledger context should be read.

# Out of Scope
- Any trading/backtest/frontend/backend feature implementation.
- Any API/data-contract redesign.
- Deleting historical content without preserving it in archive files.

# Requirements
- No historical ledger content may be lost.
- Root ledger files must remain valid high-signal current pointers.
- Archive chunk naming must be explicit and stable (e.g., task ranges).
- New rule for template-required task docs must be unambiguous.

# Status Tracking

## Before Implementation
- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions/notes:
- This task is documentation/process restructuring only.
- Task numbering/range chunking policy will be documented in the task execution notes.

## After Implementation
- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria
- Root `BACKLOG.md` keeps only latest active/candidate window and points to archive chunk files.
- Root `PROJECT_HISTORY.md` keeps only recent window and points to archive chunk files.
- Archive files exist with deterministic task-range naming and complete migrated content.
- `AGENTS.md` includes explicit rule: task docs must follow `tasks/TASK_TEMPLATE.md`.
- `git diff --check` passes.

# Required Tests

## Unit Tests
- Not applicable (documentation/process task).

## Integration Tests
- Not applicable (documentation/process task).

## Contract Tests
- Not applicable.

## Safety Tests
- Verify no non-documentation source files were changed.

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

```bash
rg -n "Task 0(8[0-9]|9[0-9])|Task 09[0-9]" BACKLOG.md PROJECT_HISTORY.md STATUS.md
rg --files | rg "backlog_task|project_history_task|TASK_TEMPLATE"
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
