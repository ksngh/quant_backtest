# Task: Status Ledger Split (STATUS / PROJECT_HISTORY / BACKLOG)

## Goal
Split the current overloaded project status ledger into three lightweight project-management documents while preserving safety boundaries and avoiding application-code changes.

## Why This Task Is Needed
`STATUS.md` currently mixes multiple responsibilities:
- current project state,
- completed-task history,
- long checklists,
- follow-up candidate items,
- deferred verification notes,
- and broad historical narrative.

This makes day-to-day status reading slower and increases maintenance risk. The split keeps current-state reporting concise while retaining history and future candidate work in dedicated documents.

## In Scope
- Define the ledger split plan from current `STATUS.md` into:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Define clear ownership/responsibility boundaries for each document.
- Define migration mapping (what content category moves to which file).
- Define minimal verification for the documentation split change.

## Out of Scope (Explicit Exclusions)
- Do **not** perform application code changes.
- Do **not** change trading logic, live trading, exchange-order behavior, API-key handling, or `.env` handling.
- Do **not** introduce risk-management process changes.
- Do **not** create `RISK_REGISTER.md`.
- Do **not** add GitHub Actions, CI workflows, PR automation, review bots, or human approval workflows.
- Do **not** redesign architecture or contracts.

## Target Document Responsibilities

### 1) `STATUS.md` (Current State Only)
Keep this file concise and focused on active state only:
- Current phase
- Current step
- Current goal
- Current active task
- Last completed step (short summary only)
- Recommended next step
- Current blockers (short)
- Current safety boundary
- Pointers to `PROJECT_HISTORY.md` and `BACKLOG.md`

Constraint: remove long historical narratives, long completed checklists, and future-candidate lists from this file.

### 2) `PROJECT_HISTORY.md` (Completed/Historical Ledger)
Move historical and completed information here:
- Completed phases
- Completed tasks
- Long phase checklist history
- Previous completed-step details
- Historical implementation summaries
- Verification notes from completed work
- Archived status entries no longer part of current state

Constraint: this file is historical/reference oriented, not the active execution dashboard.

### 3) `BACKLOG.md` (Future Candidate Work)
Move non-active future work here:
- Recommended next tasks (that are not active)
- Deferred work
- Follow-up candidates
- Optional verification candidates
- Ideas not yet assigned as active tasks

Include or preserve candidate examples as backlog items:
- PR #64 retrospective review
- Non-FVG deterministic synthetic entry fixtures
- Docker runtime verification
- Liquidity indicator implementation
- Bid-Ask spread indicator implementation

Constraint: backlog items are candidates only; they are not approved implementation tasks until explicitly assigned.

## Migration Mapping (From Current `STATUS.md`)
- `Current Phase/Step/Goal/Active Task/Blockers/Immediate Next Step` -> remain in `STATUS.md`.
- `Long Phase Checklist` -> move to `PROJECT_HISTORY.md`.
- `Detailed previous completed-step narrative` -> move to `PROJECT_HISTORY.md`.
- `Open follow-up candidates / deferred optional work` -> move to `BACKLOG.md`.
- `Long historical open-question context` -> move to `PROJECT_HISTORY.md` unless it is actively blocking current execution.

## Acceptance Criteria
- `tasks/STATUS_LEDGER_SPLIT.md` exists.
- The document explains why splitting `STATUS.md` is necessary.
- The document defines target responsibility for:
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- The document explicitly excludes:
  - `RISK_REGISTER.md`
  - GitHub Actions / PR automation / CI additions
  - Human approval workflow additions
- The document does not require application code changes.
- The document includes a verification command.

## Verification
- `git diff --check`

## Implementation Notes For The Future Split Task
When this task is later implemented:
1. Create `PROJECT_HISTORY.md` and `BACKLOG.md` first.
2. Move content in small, reviewable chunks.
3. Keep `STATUS.md` readable in under ~1 screen for routine updates.
4. Preserve safety boundary language in `STATUS.md`.
5. Run verification and update status tracking accordingly.

## Completion Requirements (for the future implementation turn)
- files changed
- documentation summary
- verification run
- known limitations
- recommended next task
