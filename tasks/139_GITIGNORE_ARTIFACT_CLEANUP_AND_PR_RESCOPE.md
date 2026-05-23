# Goal

Create a clean pull request branch that contains only the work from the recent Tasks 130-137 execution pipeline, and add repository ignore rules for unrelated generated/local artifacts that are currently polluting the worktree.

# Source Requirement

User request on 2026-05-23:

- "이번에 작업한 내용만 브랜치 새로 따고 commit 하고 PR 올려줘."
- "그리고 나머지는 git ignore에 추가해줘."

# Extracted Roles

- Owner role:
  - Repository hygiene and PR scope owner.
  - Owns which files belong in the pull request and which local/generated artifacts should be ignored.
- Supporting roles:
  - Git workflow role: creates a clean branch, stages only intended files, commits, pushes, and opens a PR.
  - Ignore-policy role: updates `.gitignore` for generated/local artifacts.
  - Review role: confirms unrelated working-tree files are excluded from the PR.
- Forbidden roles:
  - No trading behavior changes.
  - No market-data, strategy, backtest, execution, risk, backend, or frontend feature changes.
  - No deletion or reset of user-created files unless explicitly approved.
  - No live trading.
  - No API keys or `.env` files.

# Context

The previous Tasks 130-137 work was committed and pushed to a draft PR branch, while unrelated local frontend/build artifacts remained in the working tree:

- `frontend/next-env.d.ts`
- `frontend/tsconfig.json`
- `frontend/.next/`
- `frontend/node_modules/`
- `frontend/package-lock.json`
- `quant_bitcoin.egg-info/`

Those unrelated files were not included in the prior PR, but the owner wants a clean branch/commit/PR containing only the intended recent task work and wants the remaining generated/local artifacts ignored.

# Scope

- Add focused `.gitignore` entries for local/generated artifacts that should not be tracked.
- Do not stage unrelated frontend source/config changes unless the task explicitly confirms they are generated and should be ignored.
- Create or reuse a clean branch for the intended PR scope.
- Stage only:
  - prior Tasks 130-137 implementation/state/test files,
  - `.gitignore`,
  - required task/status/history/backlog updates for this task.
- Commit the scoped changes.
- Push the branch.
- Open a draft PR or update an existing draft PR with the scoped commit.
- Leave unrelated working-tree changes uncommitted if they are not safely covered by ignore rules.

# Out of Scope

- Reverting user changes.
- Removing local directories such as `node_modules` or `.next`.
- Modifying frontend application behavior.
- Modifying execution/backtest behavior beyond the already completed Tasks 130-137 changes.
- Implementing Task 138 live execution.
- Creating live Binance order functionality.

# Requirements

- `.gitignore` must include generated/local artifacts currently polluting the worktree where appropriate.
- The PR must not include unrelated frontend config changes unless explicitly justified.
- The PR must include only intended task work and repository hygiene changes.
- Existing draft PR scope must be checked before opening a replacement PR.
- If a new PR is opened, record the new PR URL in the completion summary.
- Project state files must be updated after execution.
- Task 138 must remain blocked unless explicit live-order approval is provided separately.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `.gitignore` contains ignore rules for local/generated artifacts identified in the worktree.
- A clean branch exists with only intended scoped files staged/committed.
- A draft PR is opened or updated for that clean branch.
- Unrelated files are not silently committed.
- `git status --short` confirms no unrelated files are staged.
- Project ledgers record Task 139 completion and next task state.

# Required Tests

## Unit Tests

- Not applicable for ignore/PR hygiene unless implementation files are changed.

## Integration Tests

- Not applicable unless implementation files are changed.

## Contract Tests

- `git diff --check`
- `git status --short`
- Confirm PR changed-files list excludes unrelated local artifacts.

## Safety Tests

- Confirm no `.env` files are committed.
- Confirm no API keys or secrets are added.
- Confirm no live trading implementation is added.
- Confirm Task 138 remains blocked without explicit owner approval.

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
git diff --check
git status --short
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
