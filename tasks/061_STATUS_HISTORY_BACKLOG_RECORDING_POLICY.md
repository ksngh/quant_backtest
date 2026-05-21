# Task 061: Status/History/Backlog Recording Policy

# Goal

Standardize when and how project state changes are recorded in `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md`, and explicitly codify the update obligations in `AGENTS.md`.

# Source Requirement

Owner request:
- Define recording criteria for `BACKLOG.md` (when/what to record).
- Define recording criteria for `PROJECT_HISTORY.md`.
- Explicitly state state-document update obligations in `AGENTS.md`.

# Scope

- Documentation/process updates only:
  - `AGENTS.md`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
  - this task file
- Clarify operational policy for status/history/backlog synchronization.

# Out of Scope

- Any runtime/code behavior changes.
- Any trading/backtest logic changes.
- Any persistence schema/runtime API changes.

# Requirements

- `AGENTS.md` must explicitly require completion-time updates to state docs.
- `BACKLOG.md` must document candidate-only semantics and reflect current candidate items.
- `PROJECT_HISTORY.md` must record completed-task outcomes succinctly.
- `STATUS.md` must remain the active pointer and reflect the current phase/step/active task state.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Confirm Task 061 is assigned as active for this documentation step.

## After Implementation

- [ ] Update `STATUS.md` for Task 061 progression.
- [ ] Record policy/result note in `PROJECT_HISTORY.md`.
- [ ] Ensure `BACKLOG.md` candidate list is synchronized.
- [ ] Verify formatting with `git diff --check`.

# Acceptance Criteria

- Policy expectations are explicit in `AGENTS.md`.
- `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` are internally consistent.
- No non-documentation files are modified.

# Verification

```bash
git diff --check
```

# Completion Summary Required

- files changed
- implementation summary
- tests/checks run
- self-review result
- known limitations
- recommended next task
