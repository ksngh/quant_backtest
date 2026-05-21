# Task: Status Ledger Split (STATUS / PROJECT_HISTORY / BACKLOG)

## Mode
Document

## Goal
Implement the status-ledger split now so active work uses concise, area-aware context while preserving project history and future candidate tracking.

## Why This Task Is Needed
`STATUS.md` had become an overloaded mixed ledger (active state + historical details + backlog candidates). This caused unnecessary context loading for backend/frontend tasks in a monorepo. The split enables focused context routing:
- active execution state in `STATUS.md`
- historical archive in `PROJECT_HISTORY.md`
- future/deferred candidates in `BACKLOG.md`

## In Scope
- Implement document split:
  - `STATUS.md` (short current-state pointer)
  - `PROJECT_HISTORY.md` (historical/completed archive)
  - `BACKLOG.md` (future/deferred candidates)
- Update project rules in `AGENTS.md` for focused-context reading.
- Update `docs/10_CODEX_COMMAND_GUIDE.md` to align command behavior with focused-context workflow.
- Keep backend/frontend context-load reduction as a first-class outcome.

## Out of Scope (Explicit Exclusions)
- Backend implementation
- Frontend implementation
- API contract implementation
- Application code changes
- Trading logic changes
- Live trading behavior
- API keys / `.env` workflow changes
- Exchange order/account endpoint additions
- Database schema changes
- GitHub Actions / CI additions
- PR automation / review bot automation
- Human approval workflow additions
- Risk-management process additions
- `RISK_REGISTER.md` creation
- AI agent role-separation redesign
- AX metrics process additions

## Focused Context Rule Target
- Future backend tasks should not read full `PROJECT_HISTORY.md` by default.
- Future frontend tasks should not read full `PROJECT_HISTORY.md` by default.
- Backend/frontend tasks should start from root `STATUS.md` plus focused task/API/area docs.
- If backend/frontend status files are introduced later, they should be concise and area-specific.
- Monorepo structure may remain unchanged; context loading must be area-routed.

## Acceptance Criteria
- `STATUS.md` is short and current-state only.
- `PROJECT_HISTORY.md` exists and preserves completed/historical information.
- `BACKLOG.md` exists and preserves future/deferred candidate work.
- Useful historical information is moved, not deleted.
- `STATUS.md` points to `PROJECT_HISTORY.md` and `BACKLOG.md`.
- `STATUS.md` includes current safety boundary.
- `BACKLOG.md` includes backend/frontend candidate work.
- `AGENTS.md` includes focused-context rule.
- `docs/10_CODEX_COMMAND_GUIDE.md` includes focused-context guidance.
- No application code is modified.
- No `RISK_REGISTER.md` is created.
- No GitHub Actions, PR automation, or human approval workflow additions are introduced.

## Verification
- `git diff --check`

## Completion Requirements
- files changed
- documentation summary
- what moved from `STATUS.md` to `PROJECT_HISTORY.md`
- what moved from `STATUS.md` to `BACKLOG.md`
- what changed in `AGENTS.md`
- what changed in `docs/10_CODEX_COMMAND_GUIDE.md`
- verification run
- known limitations
- recommended next task
