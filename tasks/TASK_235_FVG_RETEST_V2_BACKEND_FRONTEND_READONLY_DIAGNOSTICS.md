# Task 235: FVG Retest V2 Backend and Frontend Read-Only Diagnostics

# Goal

Expose FVG v2 diagnostics through existing backend/frontend read-only research views so users can inspect trend score, Fibonacci confluence, retest fill quality, liquidity targets, and stop-mode outcomes without running trades from the UI.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - Read-only diagnostics presentation owner for backend API and frontend dashboard metadata.
- Supporting roles:
  - Backend API contract role.
  - Frontend dashboard role.
  - Research report role.
  - Type/schema role.
  - Test role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

Earlier pattern work added read-only dashboard/reporting surfaces. FVG v2 diagnostics will be hard to interpret if only raw JSON is available. This task is presentation-only and must not run backtests or place orders from frontend code.

# Scope

- Update backend schema/type extraction for FVG v2 diagnostic metadata if backend services surface saved backtest results.
- Extend frontend types for trend score, timeframe components, Fibonacci confluence, liquidity targets, entry trigger, bars waited, stop mode, and reaction-failure fields.
- Add read-only UI sections or research-report panels for FVG v2 diagnostics.
- Display caveats: OHLCV-derived proxies, completed-candle backtest only, not live/paper trading, and no order-book liquidity.
- Keep all frontend behavior passive; no route should start a backtest unless an existing assigned backend task already supports that read-only operation.
- Add tests for metadata parsing/rendering helpers.

# Out of Scope

- No new backend endpoint that runs backtests from the UI unless separately assigned.
- No trading controls, live execution buttons, API-key input, or order management UI.
- No chart rendering overhaul beyond displaying available metadata.
- No profitability recommendation or automated strategy promotion.

# Requirements

- Backend metadata handling must tolerate missing FVG v2 fields for old backtest runs.
- Frontend must degrade gracefully when a run has baseline FVG diagnostics only.
- Read-only labels must distinguish diagnostic filters from executed trade actions.
- Sensitive metadata redaction must remain active.
- Type definitions must match documented API/JSON output shape.
- UI tests or helper tests must cover missing and present metadata paths.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [x] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Saved or JSON-loaded FVG v2 runs can display trend/Fib/liquidity/entry/stop diagnostics.
- Baseline FVG runs still render without errors.
- No UI element can place orders, call exchange endpoints, or modify credentials.
- Backend/frontend tests cover new metadata paths and missing-field fallbacks.
- Documentation notes the read-only scope.

# Required Tests

## Unit Tests

- Backend service tests cover metadata schema extraction and redaction for FVG v2 fields.
- Frontend helper/type tests cover trend/Fib/liquidity diagnostics formatting.
- Research report formatting tests cover optional FVG v2 sections.

## Integration Tests

- Frontend build passes.
- Backend FastAPI-independent service tests pass; route tests are run only where dependencies are available.
- Fixture JSON from Task 234 renders through research-report path.

## Contract Tests

- Update `docs/api/API_CONTRACT.md` for read-only FVG v2 diagnostic fields.
- Update README or dashboard docs with the caveat that diagnostics are offline backtest metadata.

## Safety Tests

- Static check confirms no exchange/order/account endpoint imports in backend/frontend changes.
- No credential input or `.env` behavior is added.
- Frontend remains read-only for FVG diagnostics.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are deterministic and covered by tests.
- No look-ahead behavior is introduced.
- Documentation/API notes are updated when behavior or metadata changes.

# Verification

Default:

```bash
pytest backend tests/backtesting/test_performance_metrics.py || pytest tests/backtesting/test_performance_metrics.py
npm --prefix frontend run build
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

# Completion Notes

Completed on 2026-05-27.

Files changed:

- `backend/quant_backtest_api/services/backtest_results.py`
- `backend/quant_backtest_api/services/research_report.py`
- `backend/tests/test_backtest_results_service_runtime.py`
- `backend/tests/test_research_report.py`
- `frontend/src/app/page.tsx`
- `frontend/src/lib/fvgRetestDiagnostics.ts`
- `frontend/src/lib/researchReport.ts`
- `frontend/src/types/api.ts`
- `frontend/tests/fvgRetestDiagnostics.test.ts`
- `frontend/tests/researchReport.test.ts`
- `frontend/package.json`
- `frontend/tsconfig.test.json`
- `docs/api/API_CONTRACT.md`
- `README.md`

Implementation summary:

- Added `fvg_retest_v2` to backend read-only diagnostics extraction and metadata schema indexing.
- Added FVG v2 trend/Fibonacci/liquidity/entry/stop read-only summary into the research report note and markdown preview.
- Added frontend FVG retest v2 helper model, type coverage, dashboard panel, and helper tests with legacy fallback.
- Updated API/README documentation to clarify offline backtest metadata scope and OHLCV proxy limitations.

Tests added or updated:

- Backend service/research-report tests cover FVG v2 metadata exposure, schema indexing, and report redaction path.
- Frontend helper tests cover present FVG v2 metadata and missing legacy fallback.

Tests run:

- `pytest backend/tests/test_backtest_results_service_runtime.py backend/tests/test_research_report.py` (passed)
- `npm --prefix frontend run test:helpers` (passed)
- `pytest backend tests/backtesting/test_performance_metrics.py` (blocked during collection because `fastapi` is not installed)
- `pytest tests/backtesting/test_performance_metrics.py` (passed)
- `npm --prefix frontend run build` (passed)
- `rg "exchange|order endpoint|account endpoint|api_key|credential|\\.env|place order|signed" backend/quant_backtest_api frontend/src -n` (reviewed; only redaction/safety text and existing env-base URL references)
- `git diff --check` (passed)

Codex self-review result:

- Scope respected: presentation/API diagnostics only.
- No live trading, exchange order/account endpoint, API key, `.env`, or credential behavior added.
- Existing sensitive metadata redaction remains active.
- Backend/frontend missing-field fallbacks are covered.

Known limitations:

- Backend route tests requiring `fastapi` were not runnable in the current Python environment.
- The new dashboard panel is helper/build tested, not browser/component regression tested.

Recommended next task:

- Task 236 `FVG_RETEST_V2_WALK_FORWARD_AND_OOS_RESEARCH_PROTOCOL`.
