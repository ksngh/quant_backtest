# Goal

Create a saved-run research report artifact that summarizes strategy, risk, entry/exit timing, metrics, diagnostics, and recommended next experiments in a portable markdown/JSON format.

# Source Requirement

Owner wants detailed explanation and task-based iteration. After metrics and diagnostics are added, each run should be exportable as a research note for review without manually reading raw API JSON.

# Extracted Roles

- Owner role:
  - Research report artifact owner.
- Supporting roles:
  - Backend service role: serializes read-only report.
  - Frontend role: offers copy/download if appropriate.
  - Docs role: documents schema.
- Forbidden roles:
  - No live trading.
  - No order execution.
  - No frontend backtest runner.

# Context

A single selected run should produce a compact report:
- what strategy,
- market/data window,
- risk design,
- actual entry/exit behavior,
- performance metrics,
- diagnostics,
- charts reference links or data summary,
- limitations,
- next recommended tasks/experiments.

# Scope

- Add backend helper to build `BacktestResearchReport`.
- Include:
  - run identity,
  - reproducibility metadata,
  - strategy explanation,
  - risk settings,
  - performance metrics,
  - trade attribution,
  - cost summary,
  - timing diagnostics if available,
  - poor-performance diagnostics,
  - limitations and safety boundary.
- Output JSON and optional markdown string.
- Frontend can show a collapsible research-note preview and copy button if feasible.
- Keep report generation read-only.

# Out of Scope

- No PDF generation unless assigned later.
- No live execution controls.
- No strategy mutation.
- No external LLM summarization.

# Requirements

- Report can be generated from a saved run detail without running a backtest.
- Missing sections are clearly marked.
- The report includes enough context to reproduce and critique the result.
- No secrets or raw database URL are exposed.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read backend `AGENTS.md`.
- [x] Read backend `STATUS.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:
- Report generation uses already loaded saved-run detail data only; it must not rerun strategies or call databases beyond the existing detail load.
- Redaction must recursively mask obvious secret/database credential fields before JSON or markdown exposure.
- Frontend preview is read-only text and must not add export-triggered backtest execution or live controls.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added `backend.quant_backtest_api.services.research_report` to build read-only `backtest_research_report_v1` JSON plus markdown from already-loaded saved-run detail data.
- Exposed `research_report` on saved-run detail responses and added backend tests for report sections, legacy/minimal metadata, recursive redaction, and service integration.
- Added a read-only frontend Research Report preview and API contract schema notes.
- Verification passed: `pytest backend/tests/test_research_report.py backend/tests/test_backtest_results_service_runtime.py tests/backtesting/test_strategy_cli_persistence.py`, `npm --prefix frontend run build`, `pytest`, and `git diff --check`.
- Codex self-review: scope respected, no live trading/order/account behavior added, no secrets hardcoded, tests/docs/status ledgers updated.
- Known limitation: report markdown is a compact text preview, not a PDF/export workflow.
- Recommended next task: Task 187.

# Acceptance Criteria

- Backend service test verifies report sections.
- Report redacts sensitive metadata.
- Frontend build if preview added.
- Docs include schema.

# Required Tests

## Unit Tests

- Report builder with full metadata.
- Report builder with legacy/minimal metadata.
- Redaction test.

## Integration Tests

- Backend service endpoint/helper test.
- Frontend preview build if implemented.

## Contract Tests

- API contract for report schema.

## Safety Tests

- No API key or database password in report.

# Verification

Default:

```bash
pytest backend/tests/test_backtest_results_service_runtime.py tests/backtesting/test_strategy_cli_persistence.py
npm --prefix frontend run build
pytest
git diff --check
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are covered by deterministic regression tests.
- Frontend/API changes remain read-only and do not run backtests or place orders.

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
