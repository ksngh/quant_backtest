# Task 219: FRONTEND_EXECUTION_RISK_ASSUMPTION_EXPLANATION

# Goal

Expose pattern execution assumptions in the read-only dashboard: entry mode, fill alignment, risk plan, cost profile, intrabar policy, and short limitations.

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

- Backtest metadata now includes many execution and risk assumptions.
- Users can misinterpret results if the UI shows PnL without fill/cost/short/intrabar context.
- Earlier frontend tasks added diagnostics panels, but this task should focus on explicit assumptions for pattern runs.

# Scope

- frontend/
- docs/api/API_CONTRACT.md
- backend/
- quant_bitcoin/backtesting/strategy_engine.py
- tests/frontend/
- backend/tests/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Display entry_mode, fill_assumption, fill_price_source, bars_waited, entry_reference, actual fill price, and risk_plan_aligned_to_fill.
- Display original versus fill-adjusted risk_per_unit when available.
- Display cost profile, zero-cost warning, effective_slippage_bps, and cost-to-gross-PnL ratio.
- Display intrabar policy and ambiguous stop/target counts.
- Display short economics limitation banner when short trades exist.
- Read-only only; do not add live controls.

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

Assumptions / notes:
- Implement this as a read-only frontend helper/panel consuming existing saved-run metadata paths; do not add execution, mutation, or live controls.
- Backend changes are only needed if required fields are absent from the already-exposed detail payload.
- Legacy rows should render unavailable/fallback text rather than zero-valued assumptions.
- Exact files expected: frontend helper/UI/tests and API contract notes; backend/source changes only if metadata exposure is missing.
- No live trading, real exchange order execution, signed exchange requests, credentials, or `.env` behavior are in scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added a read-only frontend Execution Assumptions panel for entry fill, fill-adjusted risk, cost, intrabar ambiguity, zero-cost warning, and short-simulation limitations.
- Added a pure frontend extraction helper with legacy fallback behavior and helper tests.
- Confirmed backend detail serialization preserves the metadata paths consumed by the panel.
- Updated API contract and frontend status notes for the consumed read-only fields.
- No live trading controls, backtest execution controls, real exchange calls, signed requests, credentials, or `.env` behavior were added.

# Acceptance Criteria

- Saved run detail page explains pattern entry/risk assumptions.
- Legacy runs without metadata degrade gracefully.
- Short limitation and zero-cost warnings are visible when applicable.

# Required Tests

## Unit Tests

- Add unit tests appropriate to every changed pure function or data contract.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Frontend helper tests: extract assumption fields from new and legacy metadata.
- Frontend component/snapshot tests if harness exists.
- Backend detail response test exposes required metadata paths.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.
- Safety: no live trading UI controls introduced.

# Side Effects / Risks

- UI complexity increases.
- Requires coordination with backend API schema if fields are missing.

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

Self-review summary:
- Implemented only the assigned read-only frontend assumption display and metadata-contract verification scope.
- Did not add execution, mutation, live trading, auth, database, or exchange controls to the frontend.
- Backend code was not changed; backend test coverage was extended to verify detail metadata pass-through.
- Verification passed with frontend helper tests, frontend production build, backend service test, and diff check.

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

Verification run:

```bash
npm --prefix frontend run test:helpers
npm --prefix frontend run build
pytest backend/tests/test_backtest_results_service_runtime.py
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
