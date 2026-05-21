# Task 080: Docker Compose Service Split (Backtest / Backend / DB / Frontend)

# Goal

Split the current all-in-one Docker Compose workflow into independently runnable service groups so developers can start only the services they need.

# Source Requirement

- User request (2026-05-21): "지금은 도커 컴포즈가 백테스트, 백엔드, db, 프론트 이렇게 한번에 띄우거든? 이거 다 분리해주는 task 만들어줘"

# Extracted Roles

- Owner role: Project owner requests local runtime decomposition for compose services.
- Supporting roles: Local environment orchestration, backend/frontend runtime boundaries, backtest runtime boundary.
- Forbidden roles: Live trading/order execution, API key handling, unrelated strategy/backtest logic changes.

# Context

- Task 079 completed one-command compose startup for dashboard-related local development.
- Current request changes startup ergonomics: avoid always booting all services together.
- Docker work is out-of-scope by default in root policy unless explicitly assigned; this task is that explicit assignment.

# Scope

- Redesign Docker Compose structure so backtest/backend/db/frontend can be started separately.
- Define clear service grouping strategy (for example multiple compose files, profiles, or both).
- Ensure each group has explicit startup commands and dependency behavior.
- Update local development docs for split workflows.

# Out of Scope

- Live trading or exchange order API integration.
- Strategy algorithm refactoring unrelated to runtime separation.
- Database schema redesign.
- Production deployment hardening.

# Requirements

- Developers can start backend+db without frontend/backtest.
- Developers can start frontend without forcing backtest startup.
- Developers can run backtest-oriented service path without forcing full dashboard stack.
- Existing host port accessibility remains documented.
- No secrets are committed.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if phase/step/goal/active-task/blockers changed.
- [ ] Append concise completion note to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` if follow-up work is created/reprioritized/completed.
- [ ] Confirm next task recommendation.

# Acceptance Criteria

- Compose strategy supports partial startup paths by role (backtest/backend/db/frontend).
- Commands for each startup path are documented and deterministic.
- `docker compose config` (or equivalent per split command) succeeds where environment permits.
- No accidental live-order or credential handling behavior is introduced.

# Required Tests

## Unit Tests

- N/A (runtime orchestration task).

## Integration Tests

- `docker compose config` for each supported startup path.
- smoke `docker compose up` for selected paths in Docker-capable environment.

## Contract Tests

- Existing backend/frontend API contract tests remain unchanged.

## Safety Tests

- Confirm no `.env` secrets committed.
- Confirm no exchange order/account endpoint behavior introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract unchanged unless explicitly planned.
- No hardcoded secrets.
- No real order execution behavior.

# Verification

Default:

```bash
pytest
```

Task-specific:

```bash
docker compose config
# and split-path config checks per chosen design
```

# Codex Self-Review Requirement

Before completion, run `reviews/CODEX_SELF_REVIEW.md` and include results in completion summary.

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
