# Task 079: Backend/Frontend Docker Compose Setup

# Goal

Provide a Docker Compose workflow so backend and frontend can be started together with one command for local development.

# Source Requirement

- User request (2026-05-21): "back이랑 front docker compose 파일로 바로 실행시킬 수 있게 끔 해줘."

# Extracted Roles

- Owner role: Project owner requests local developer runtime simplification.
- Supporting roles: Backend area, frontend area, local environment orchestration.
- Forbidden roles: Live trading/order execution, API key handling, unrelated strategy/backtest refactors.

# Context

- Task 078 completed integration and local workflow docs.
- Root `AGENTS.md` currently lists Docker as out-of-scope by default unless explicitly assigned by a task document.
- This document is the explicit assignment boundary for Docker Compose setup.

# Scope

- Add root-level `docker-compose.yml` (or equivalent) for backend + frontend local startup.
- Add/update backend/frontend Dockerfiles as needed for compose-based local run.
- Wire service networking/environment so frontend can call backend in containerized mode.
- Add concise run instructions and troubleshooting notes.

# Out of Scope

- Live trading or exchange order API integration.
- Database schema redesign.
- Strategy/backtest logic changes.
- Production-grade deployment hardening.

# Requirements

- `docker compose up` starts backend and frontend services without manual multi-terminal setup.
- Backend service exposes API port for host access.
- Frontend service exposes UI port for host access.
- Frontend API base configuration is compatible with compose network.
- No secrets are committed.

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

- Backend and frontend launch together via docker compose.
- Local host can access frontend and backend mapped ports.
- Basic smoke verification commands are documented and executed where environment permits.

# Required Tests

## Unit Tests

- N/A (task focus is runtime orchestration).

## Integration Tests

- `docker compose config`
- `docker compose up` smoke verification (environment permitting)

## Contract Tests

- Existing backend/frontend contract tests unchanged (no contract mutation).

## Safety Tests

- Confirm no live order endpoints, credentials, or `.env` secrets are introduced.

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
```

Task-specific:

```bash
docker compose config
docker compose up --build
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
