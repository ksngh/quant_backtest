# Task 221: BACKEND_API_PATTERN_RISK_SCORE_SCHEMA_HARDENING

# Goal

Harden backend/API schema for enriched pattern execution, risk, score, calibration, and diagnostics metadata.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P3**

# Extracted Roles

- Owner role: Project owner / quant research lead.
- Supporting roles:
  - Quant researcher: validate economic assumptions, score calibration, and OOS diagnostics.
  - System trading architect: maintain action, risk, sizing, cost, and execution contracts.
  - Backtest verification engineer: preserve no-lookahead, fill correctness, intrabar policy, and deterministic tests.
  - Code reviewer: enforce scope, safety, and architecture boundaries.
- Forbidden roles:
- Live trading implementation unless the task explicitly says otherwise.
- Real exchange order execution.
- Secret/key management changes outside documented safety scope.
- Unrelated frontend/backend/database changes unless listed in Scope.

# Context

- Pattern improvements add metadata fields for entry policies, fill alignment, target semantics, score components, intrabar policy, cost, and diagnostics.
- Saved-run consumers need stable read-only schemas.
- Legacy rows may not have new metadata.

# Scope

- backend/
- docs/api/API_CONTRACT.md
- quant_bitcoin/persistence/
- quant_bitcoin/backtesting/strategy_models.py
- backend/tests/
- tests/persistence/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Document metadata schemas: pattern_execution_policy_v1, target_semantics_v1, score_components_v1, risk_exit_audit_v2, intrabar_policy_v1.
- Ensure all new metadata is JSON-safe and redacted where necessary.
- Backend saved-run detail responses must expose metadata without crashing on legacy rows.
- Add schema validation helpers or typed extraction where appropriate.
- No live trading endpoints or controls.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for this task's historical context.
- [x] Confirm this task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Identify exact source files and tests touched by this task.
- [x] Confirm no live trading, real order execution, signed exchange request, or secret handling is introduced.

Assumptions:
- This task hardens read-only API serialization and documentation only; it must not rerun strategies, add execution endpoints, or change strategy/backtest behavior.
- Existing producer metadata remains backward-compatible. Backend response hardening should accept saved `risk_exit_audit_v1` rows while documenting the richer API-facing risk-exit audit contract expected by current consumers.
- Touched files are expected to be limited to `backend/quant_backtest_api/services/backtest_results.py`, `backend/tests/test_backtest_results_service_runtime.py`, `docs/api/API_CONTRACT.md`, and task/status/backlog/history ledgers.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- API contract documents all new metadata fields.
- Backend read-only service handles new and legacy metadata.
- Persistence preserves unknown JSON-safe metadata.

# Required Tests

## Unit Tests

- Add unit tests appropriate to every changed pure function or data contract.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Backend service test for full enriched metadata.
- Backend service test for legacy/minimal metadata.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.
- Safety: no API keys or live endpoints exposed.

# Side Effects / Risks

- API docs become longer.
- Frontend may need schema version branching.

# Review Checklist

- [x] Scope respected.
- [x] Requirement matched.
- [x] Role ownership respected.
- [x] Architecture boundaries respected.
- [x] Data contract respected where applicable.
- [x] No hardcoded secrets.
- [x] No real order execution unless explicitly requested by a future owner-approved live task.
- [x] No unnecessary abstractions.
- [x] No lookahead introduced.
- [x] Pattern/risk/indicator semantics are documented in metadata or docs.
- [x] Tests cover both success and failure/skip paths.

# Verification

Default:

```bash
pytest
```

Recommended targeted verification for this task:

```bash
pytest tests/patterns tests/risk tests/backtesting
pytest tests/strategies
git diff --check
```

If frontend files are changed:

```bash
cd frontend && npm run build
```

If backend/API files are changed and dependencies are available:

```bash
pytest backend/tests
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

# Completion Notes

Files changed:
- `backend/quant_backtest_api/services/backtest_results.py`
- `backend/tests/test_backtest_results_service_runtime.py`
- `docs/api/API_CONTRACT.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_221_BACKEND_API_PATTERN_RISK_SCORE_SCHEMA_HARDENING.md`

Implementation summary:
- Added direct backend response redaction for sensitive metadata keys while preserving read-only saved-run metadata shape.
- Added `diagnostics.summary.metadata_schema_index` schema discovery for `pattern_execution_policy_v1`, `target_semantics_v1`, `score_components_v1`, API-facing `risk_exit_audit_v2` with compatible saved `risk_exit_audit_v1`, and `intrabar_policy_v1`.
- Kept enriched metadata read-only and legacy-safe; missing metadata is reported as unavailable rather than false or zero.
- Expanded API contract documentation for pattern/risk/score/intrabar schema contracts and the metadata schema index.

Tests added or updated:
- Extended backend service runtime tests for enriched pattern metadata, schema index output, placeholder score-component counting, direct sensitive metadata redaction, and legacy/minimal metadata fallback.

Tests run:
- `pytest backend/tests/test_backtest_results_service_runtime.py`
- `pytest backend/tests` (blocked at collection by missing `fastapi` dependency for route tests)
- `git diff --check`

Codex self-review result:
- Scope stayed within backend read-only serialization/API docs and ledger updates.
- No strategy/backtest behavior, live trading path, signed request, API key handling, or exchange order/account endpoint was introduced.
- Contract tests cover enriched and legacy metadata behavior.

Known limitations:
- Full backend route test suite is still blocked in this environment because `fastapi` is not installed.
- `risk_exit_audit_v2` is documented as the API-facing contract while saved producer rows may still carry `risk_exit_audit_v1`; the schema index explicitly reports that compatibility.

Recommended next task:
- Task 222 `TEST_FIXTURE_EXPANSION_SYNTHETIC_PATTERNS`.
