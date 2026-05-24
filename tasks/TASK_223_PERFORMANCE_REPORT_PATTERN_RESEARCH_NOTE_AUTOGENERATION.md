# Task 223: PERFORMANCE_REPORT_PATTERN_RESEARCH_NOTE_AUTOGENERATION

# Goal

Generate a structured research note for pattern backtest runs summarizing alpha hypothesis, entry/exit policy, risk assumptions, diagnostics, and recommended next experiments.

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

- Task 186 added saved-run research report artifacts.
- Pattern-specific diagnostics now need to be summarized in a way that separates detector quality, entry timing, risk behavior, costs, and regime dependence.
- Reports should make clear that current pattern scores are heuristic unless calibrated.

# Scope

- quant_bitcoin/backtesting/
- backend/
- frontend/
- docs/api/API_CONTRACT.md
- tests/backtesting/
- backend/tests/
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

- Add pattern-specific report sections: hypothesis, detector conditions, windows/candles observed, entry mode, risk plan, cost profile, score reliability, no-lookahead status, regime dependence, and limitations.
- Include top failure reasons from diagnostics.
- Include recommended next analyses based on poor-performance classification.
- Render both JSON and markdown variants.
- Redact secrets and avoid live-trading language.

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
- This task extends the existing saved-run research report artifact; it must not rerun strategies, mutate parameters, or add execution endpoints.
- Pattern research notes are generated from already-loaded report inputs, saved summary metadata, diagnostics, and trade metadata only.
- Touched files are expected to be limited to `backend/quant_backtest_api/services/research_report.py`, `backend/tests/test_research_report.py`, `frontend/src/lib/researchReport.ts`, `frontend/src/app/page.tsx`, `frontend/tests/researchReport.test.ts`, frontend test config/package files, `docs/api/API_CONTRACT.md`, and task/status/backlog/history ledgers.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Saved pattern run produces a research note with all required sections.
- Legacy run produces a partial report with unavailable fields clearly marked.
- Report distinguishes research-grade from production/live readiness.

# Required Tests

## Unit Tests

- Unit: report builder maps enriched metadata into pattern sections.
- Unit: legacy metadata fallback.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Backend: saved-run detail exposes report.
- Frontend: preview renders key sections.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Report artifacts can become lengthy.
- Requires keeping schema versions stable.

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
- `backend/quant_backtest_api/services/research_report.py`
- `backend/tests/test_research_report.py`
- `frontend/src/lib/researchReport.ts`
- `frontend/src/app/page.tsx`
- `frontend/tests/researchReport.test.ts`
- `frontend/package.json`
- `frontend/tsconfig.test.json`
- `frontend/STATUS.md`
- `docs/api/API_CONTRACT.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_223_PERFORMANCE_REPORT_PATTERN_RESEARCH_NOTE_AUTOGENERATION.md`

Implementation summary:
- Extended `backtest_research_report_v1` with `pattern_research_note_v1` for hypothesis, detector conditions, windows/candles observed, entry mode, risk plan, cost profile, score reliability, no-lookahead status, regime dependence, top failure reasons, limitations, and recommended next analyses.
- Added markdown output for the pattern research note and preserved secret redaction.
- Added frontend research-report preview extraction and rendered key pattern-note sections as read-only summary rows and section chips.
- Updated API/frontend docs for the new report section.

Tests added or updated:
- Extended backend research report tests for enriched pattern notes, legacy partial fallback, failure reasons, score reliability, and redaction.
- Added frontend helper tests for pattern research report preview rows and section labels.

Tests run:
- `pytest backend/tests/test_research_report.py backend/tests/test_backtest_results_service_runtime.py`
- `npm --prefix frontend run test:helpers`
- `npm --prefix frontend run build`
- `git diff --check`

Codex self-review result:
- Scope stayed within saved-run report generation, read-only frontend preview, docs, and ledgers.
- No backtest rerun, strategy mutation, live trading path, signed request, exchange order/account endpoint, API key handling, or `.env` mutation was introduced.
- Legacy rows produce partial report fields rather than misleading defaults.

Known limitations:
- Full backend route tests remain environment-blocked by missing `fastapi`.
- Pattern research notes summarize saved metadata; missing legacy fields remain unavailable.

Recommended next task:
- Task 224 `LIVE_READINESS_BOUNDARY_NON_EXECUTION_AUDIT_FOR_PATTERNS`.
