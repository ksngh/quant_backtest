# Dashboard Runtime Display

# Goal

Expose saved backtest runtime in the user-facing site so a user can see how long each backtest took.

Display runtime both:

- in the backtest run list;
- in the selected run detail panel.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `frontend/STATUS.md`
- `AGENTS.md`
- `backend/quant_backtest_api/services/backtest_results.py`
- `backend/quant_backtest_api/routers/backtest_runs.py`
- `backend/quant_backtest_api/schemas/backtest.py`
- `frontend/src/lib/api.ts`
- `frontend/src/types/api.ts`
- `frontend/src/app/page.tsx`
- `quant_bitcoin/persistence/postgres.py`
- related frontend/backend tests if present

# Extracted Roles

- Owner role:
  - Dashboard/API display owner.
  - Responsible for exposing persisted runtime metadata through API and rendering it clearly in the site.

- Supporting roles:
  - Persistence role:
    - Supplies `backtest_runs.metadata.runtime`.
  - API role:
    - Serializes runtime into list and detail responses.
  - Frontend role:
    - Displays runtime summary and phase breakdown.
  - Test role:
    - Verifies API and frontend display behavior.

- Forbidden roles:
  - No algorithm optimization in this task.
  - No DB schema changes unless runtime metadata cannot be read from existing metadata.
  - No live trading.
  - No exchange endpoint calls.
  - No API key handling.

# Context

The backend currently exposes:

- `/api/backtest-runs`
- `/api/backtest-runs/{backtest_run_id}`

The frontend currently renders:

- run list;
- selected run summary;
- close/equity charts;
- trades;
- strategy parameters JSON;
- run metadata JSON;
- result metadata JSON.

Runtime metadata can initially be displayed from run metadata, but a user-friendly UI should show summarized values without requiring users to inspect raw JSON.

# Scope

- Update repository list query or service serialization to expose runtime summary in list items.
- Update backend list item serialization to include:
  - `runtime.total_elapsed_ms`;
  - optionally `runtime.action_build_elapsed_ms`;
  - optionally `runtime.engine_elapsed_ms`.
- Update frontend API types.
- Update run list table with a runtime column.
- Update selected run summary with:
  - total runtime;
  - candle load time;
  - action build time;
  - engine time;
  - persistence time if available.
- Add a detailed runtime breakdown card.
- Preserve existing JSON metadata panels.

# Out of Scope

- Algorithm optimization.
- Runtime measurement implementation.
- New charts for runtime trends.
- Multi-run performance analytics.
- New DB columns.
- Pattern explanation rendering.

# Requirements

- Run list should show total runtime when available.
- Selected run detail should show phase timing.
- Missing runtime metadata should show `-` or a clear fallback, not crash.
- Runtime values should be formatted in human-readable units:
  - milliseconds for short phases;
  - seconds/minutes for total runtime when large.
- Frontend types must include optional runtime metadata.
- Backend response must remain backward-compatible for old runs without runtime metadata.
- Warnings may include a message for old runs missing runtime metadata only if useful and not noisy.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `/api/backtest-runs` returns runtime summary when run metadata contains runtime.
- `/api/backtest-runs/{id}` returns runtime in run metadata and frontend detail consumes it.
- Frontend run list displays runtime.
- Frontend selected run detail displays runtime phase breakdown.
- Old runs without runtime metadata render safely.
- Frontend build and tests pass.

# Required Tests

## Unit Tests

- Backend service serialization:
  - runtime present;
  - runtime absent;
  - malformed runtime ignored or safely serialized.
- Frontend formatting helper:
  - milliseconds;
  - seconds;
  - minutes;
  - missing value.

## Integration Tests

- Backend API detail response includes runtime metadata.
- Frontend page can render mocked detail response with runtime.
- Frontend page can render mocked detail response without runtime.

## Contract Tests

- API remains backward-compatible.
- Existing response fields remain available.
- Runtime field is optional.

## Safety Tests

- No exchange calls.
- No API key loading.
- No signed requests.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- UI handles old runs without runtime metadata.
- Runtime units are clear.

# Verification

Default:

```bash
pytest
```

Frontend verification if applicable:

```bash
cd frontend
npm test
npm run build
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
- frontend build result
- runtime display fields
- Codex self-review result
- known limitations
- recommended next task
