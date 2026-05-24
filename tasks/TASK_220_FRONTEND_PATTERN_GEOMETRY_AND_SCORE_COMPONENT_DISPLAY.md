# Task 220: FRONTEND_PATTERN_GEOMETRY_AND_SCORE_COMPONENT_DISPLAY

# Goal

Show pattern-specific geometry and score-component reliability so users can understand why a pattern was detected.

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

- Each pattern event has geometry fields: FVG zone, OB zone, trendline pivots, Cup rims/bottom/handle, Diamond boundaries, Adam/Eve lows/neckline.
- Score metadata contains observed and placeholder components with limitations.
- Frontend should not present pattern_score as a calibrated probability.

# Scope

- frontend/
- docs/api/API_CONTRACT.md
- backend/
- quant_bitcoin/patterns/*.py
- tests/frontend/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Display geometry fields conditionally by pattern_type.
- Display score components with raw_score, weight, source, is_placeholder, and included_in_executable_score when available.
- Add explanation text: score is heuristic unless calibration report shows OOS lift.
- Display candidate-overfit diagnostics when available.
- Legacy runs without fields should show 'not available' rather than misleading defaults.

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
- This task is read-only frontend/API documentation work; no strategy, backtest, persistence, database schema, or execution behavior should change.
- Pattern geometry and score components will be extracted from saved trade metadata when present; legacy rows without metadata will render unavailable fallback text.
- Touched files are expected to be limited to `frontend/src/lib/patternGeometry.ts`, `frontend/src/app/page.tsx`, `frontend/src/styles/globals.css`, `frontend/tests/patternGeometry.test.ts`, `frontend/package.json`, `frontend/tsconfig.test.json`, `docs/api/API_CONTRACT.md`, and task/status/backlog/history ledgers.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- FVG/OB/Trendline/Cup/Diamond/Adam-Eve display pattern-specific fields.
- Placeholder components are visually separated from observed components.
- Calibrated probability wording is not used unless actual calibration metadata supports it.

# Required Tests

## Unit Tests

- Add unit tests appropriate to every changed pure function or data contract.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Frontend helper tests for each pattern_type geometry extraction.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Requires careful UI layout to avoid dense tables.

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
- `frontend/src/lib/patternGeometry.ts`
- `frontend/src/app/page.tsx`
- `frontend/src/styles/globals.css`
- `frontend/tests/patternGeometry.test.ts`
- `frontend/package.json`
- `frontend/tsconfig.test.json`
- `frontend/STATUS.md`
- `docs/api/API_CONTRACT.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_220_FRONTEND_PATTERN_GEOMETRY_AND_SCORE_COMPONENT_DISPLAY.md`

Implementation summary:
- Added a read-only pattern geometry extraction helper that conditionally maps FVG, Order Block, Trendline, Cup/Handle, Diamond, and Adam/Eve metadata from saved trade rows.
- Added a Pattern Geometry dashboard panel that separates observed score components from placeholder/diagnostic-only components and explains that `pattern_score` is heuristic rather than a calibrated probability.
- Rendered candidate-overfit diagnostics when `chart_pattern_candidate_diagnostics_v1` or score-calibration aggregate metadata is available.
- Documented the consumed metadata paths and frontend status.

Tests added or updated:
- Added `frontend/tests/patternGeometry.test.ts` with contract coverage for all six supported pattern types, placeholder component separation, candidate-overfit warnings, and legacy fallback behavior.
- Added the new helper/test file to frontend test configuration.

Tests run:
- `npm --prefix frontend run test:helpers`
- `npm --prefix frontend run build`
- `git diff --check`

Codex self-review result:
- Scope stayed within read-only frontend/API documentation and ledger updates.
- No strategy/backtest execution behavior, live trading path, signed request, secret handling, or database access was introduced.
- Tests and API documentation were updated for the new frontend contract.

Known limitations:
- The panel displays only metadata already preserved on saved runs; older rows without pattern geometry or score components intentionally show unavailable fallback text.
- No browser visual regression harness is assigned, so verification is helper tests plus Next production build.

Recommended next task:
- Task 221 `BACKEND_API_PATTERN_RISK_SCORE_SCHEMA_HARDENING`.
