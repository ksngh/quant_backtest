# Goal

Persist and expose the new research diagnostics needed for serious backtest analysis, while keeping API/frontend behavior read-only and backward-compatible.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed gap:

- Several proposed improvements add diagnostics: sizing source, fill model, intrabar policy, attribution metrics, regime tags, score components, and cost assumptions.
- Persistence/API/dashboard must be kept consistent so saved runs remain analyzable without rerunning strategies.

Read and inspect:

- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/persistence/postgres.py`
- `backend/quant_backtest_api/routers/backtest_runs.py`
- backend read models/services
- `docs/api/API_CONTRACT.md`
- `frontend/src/types/api.ts`
- existing persistence/API tests

# Extracted Roles

- Owner role:
  - Read-only research diagnostics persistence/API owner.
- Supporting roles:
  - Backtest engine role: emits diagnostics.
  - Persistence role: saves completed simulated outputs.
  - Backend API role: exposes saved outputs read-only.
  - Frontend role: may consume fields later without running backtests.
- Forbidden roles:
  - No API endpoint that executes trades.
  - No frontend direct DB access.
  - No live trading controls.

# Context

Code-level hints:

- Prefer additive metadata fields first if schema changes are not necessary.
- Ensure `build_strategy_engine_persistence_payload()` carries new summary/execution metadata.
- If adding dedicated DB columns, add migration/SQL task notes and backward-compatible read behavior.
- Backend read models should preserve unknown metadata rather than dropping it.
- Frontend type updates should be additive and optional.

Functional intent:

- Backtest artifacts should be reproducible and explainable after persistence.

# Scope

- Carry diagnostics from engine output into persistence payload.
- Expose diagnostics through read-only backend API.
- Update API contract docs for new optional fields.
- Add or update frontend types only if fields are consumed or typed.
- Add tests for legacy runs missing new metadata.

# Out of Scope

- Running backtests from the backend API.
- Dashboard redesign.
- Live trading endpoints.
- Non-PostgreSQL storage.

# Requirements

- New diagnostics must be optional for legacy runs.
- Persistence writes must remain transactional.
- Read API must not synthesize misleading values when metadata is missing.
- API contract must clearly mark optional fields.
- Unknown metadata should remain JSON-safe and inspectable.

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

- Saved runs include diagnostics added by prior tasks.
- Backend read API returns diagnostics for new runs and handles missing diagnostics for old runs.
- API contract docs reflect optional fields.
- Existing dashboard/API tests still pass.

# Required Tests

## Unit Tests

- Test persistence adapter mapping for new metadata.
- Test JSON-safe serialization of diagnostics.

## Integration Tests

- Test save/load completed run with new diagnostics.
- Test backend service read model for new and legacy runs.

## Contract Tests

- Update and verify `docs/api/API_CONTRACT.md`.
- Ensure TypeScript API types remain backward-compatible if touched.

## Safety Tests

- Confirm backend remains read-only for saved results.
- Confirm no order/account endpoints or API keys are introduced.

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
pytest tests/backtesting/test_strategy_persistence_adapter.py backend/tests
pytest
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
