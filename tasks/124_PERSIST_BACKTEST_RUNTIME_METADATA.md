# Persist Backtest Runtime Metadata

# Goal

Store measured backtest runtime in the database so users can inspect how long each run took.

Use existing JSONB metadata fields instead of adding new columns unless a schema change is clearly required.

Preferred storage:

- `backtest_runs.metadata.runtime` for run-level timing and phase timing;
- optionally `backtest_results.metadata.runtime_summary` for result-level timing summaries if useful.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `db/init/001_schema.sql`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/postgres_runner_cli.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/persistence/postgres.py`
- `backend/quant_backtest_api/services/backtest_results.py`
- `backend/quant_backtest_api/routers/backtest_runs.py`
- `frontend/src/types/api.ts`
- `frontend/src/app/page.tsx`
- related tests under `tests/backtesting/`, `tests/persistence/`, and `backend/tests/` if present

# Extracted Roles

- Owner role:
  - Persistence/backtest metadata owner.
  - Responsible for measuring and saving runtime metadata for completed backtest runs.

- Supporting roles:
  - Backtesting role:
    - Provides phase timing from canonical execution.
  - Persistence role:
    - Saves runtime metadata atomically with completed backtest results.
  - API role:
    - Exposes runtime metadata through existing run detail and list endpoints.
  - Test role:
    - Verifies metadata shape and serialization.

- Forbidden roles:
  - No frontend display work in this task unless required for minimal smoke verification.
  - No performance algorithm changes.
  - No live trading.
  - No order execution.
  - No API key handling.
  - No private exchange endpoints.

# Context

The database already has JSONB metadata fields:

- `strategy_configs.metadata`
- `backtest_runs.metadata`
- `backtest_results.metadata`
- `backtest_trades.metadata`
- `backtest_graph_points.metadata`

The run detail API already serializes `run.metadata` and `summary.metadata`. The frontend already has JSON panels for strategy parameters, run metadata, and result metadata.

Therefore, runtime can be saved without an immediate schema migration.

# Scope

- Add timing measurement to canonical backtest execution.
- Store timing payload in `backtest_runs.metadata.runtime`.
- Include at minimum:
  - `total_elapsed_ms`
  - `candle_load_elapsed_ms`
  - `action_build_elapsed_ms`
  - `engine_elapsed_ms`
  - `persistence_elapsed_ms` when measurable
  - `json_output_elapsed_ms` when measurable
  - `pattern_timings`
  - `candle_count`
  - `strategy_key`
  - `created_by`
  - `runtime_schema_version`
- Ensure metadata is JSON-serializable.
- Ensure deterministic run identity does not become unstable due to runtime data unless intentionally excluded from run key.
- Decide and document whether runtime metadata participates in `run_key`.
- Preferred: runtime metadata must not participate in deterministic `run_key`, because repeated identical strategy runs should map to the same logical run identity.

# Out of Scope

- Frontend UI panels.
- Runtime trend analytics.
- New database columns.
- New dashboard charts.
- Algorithm optimization.
- Pattern lifecycle implementation.

# Requirements

- Runtime measurement must be implemented in the canonical path.
- Runtime metadata must be saved for persisted runs.
- `--no-persist` output should still include runtime data in stdout JSON.
- Runtime metadata must not break existing persistence upsert behavior.
- Re-running the same deterministic backtest should not produce a different `run_key` solely because runtime changed.
- If current persistence payload cannot exclude runtime from run key, adjust identity construction so volatile metadata is excluded.
- Include pattern-level timing if available:
  - `pattern_key`
  - `elapsed_ms`
  - `events_detected`
  - `actions_emitted`
  - `candidate_count` if available.
- Include phase timing even when some phases are zero or unavailable.
- Store units explicitly in field names or metadata.

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

- Persisted `backtest_runs.metadata` includes `runtime`.
- Runtime payload contains total and phase timings.
- Runtime payload is available from `/api/backtest-runs/{id}` through existing run metadata serialization.
- `--no-persist` JSON includes runtime timing.
- Runtime metadata does not make deterministic run keys unstable.
- Existing saved result loading still works.
- Tests verify runtime metadata is saved and loaded.

# Required Tests

## Unit Tests

- Test timing payload builder.
- Test runtime metadata JSON serialization.
- Test run-key identity excludes volatile runtime metadata.
- Test persistence payload contains runtime metadata in run metadata.

## Integration Tests

- Run canonical CLI with mocked provider/repository.
- Assert repository receives payload with `run.metadata.runtime`.
- Run with `--no-persist`.
- Assert stdout JSON includes runtime.
- Persist and load a completed run.
- Assert loaded detail includes runtime metadata.

## Contract Tests

- Existing backtest result payload shape remains compatible.
- Existing list and detail APIs still return successful responses.
- Runtime metadata units are explicit.

## Safety Tests

- No exchange order/account endpoints.
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
- Runtime metadata does not affect deterministic run identity.
- Runtime metadata is visible through run detail API.

# Verification

Default:

```bash
pytest
```

Recommended targeted tests:

```bash
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
pytest tests/backtesting/test_strategy_persistence_adapter.py
pytest tests/persistence
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
- runtime fields saved
- selected DB metadata location
- run-key volatility decision
- Codex self-review result
- known limitations
- recommended next task
