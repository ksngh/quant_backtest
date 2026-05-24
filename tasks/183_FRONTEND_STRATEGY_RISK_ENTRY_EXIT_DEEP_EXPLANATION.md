# Goal

Upgrade the frontend explanation area to explicitly show what strategy ran, how risk management works, and how entry/exit timing works for the selected run using actual run metadata.

# Source Requirement

Owner request:
1. Frontend should explain what the current strategy is and describe it in detail.
2. Frontend should explain risk management.
3. Frontend should explain entry timing and sell/exit timing.
4. Explanations should reflect the actual selected run and current repo behavior, not generic marketing text.

Current repo findings:
- `frontend/src/app/page.tsx` has `StrategyExplanation`, `AccountStatePanel`, `TradeTable`, `ParametersPanel`, and `RuntimePanel`.
- `pattern_explanations.py` provides algorithm, detection, entry, stop, take-profit, partial exit, soft invalidation, time stop, rationale, and limitations.
- Frontend currently shows generic rule cards, but it does not fully distinguish configured strategy, actual fill model, risk plan alignment, realized exit distribution, and performance diagnosis.

# Extracted Roles

- Owner role:
  - Frontend strategy explanation owner.
- Supporting roles:
  - Strategy explanation metadata role.
  - Backtest diagnostics role.
  - API contract role.
- Forbidden roles:
  - No frontend ability to run strategies.
  - No live trading controls.
  - No direct DB access.

# Context

The dashboard should be understandable without reading code. A user should be able to select a run and answer:
- What strategy did this run use?
- What economic hypothesis does it test?
- What indicators and pattern fields does it use?
- How was risk sized?
- Where was stop loss placed?
- Where were targets placed?
- What caused exits in this run?
- Was entry a market confirmation entry or retest/limit entry?
- Did the realized behavior match the intended design?

# Scope

- Replace or extend `StrategyExplanation` with structured subpanels:
  - `Strategy Overview`,
  - `Economic Hypothesis`,
  - `Indicators Used`,
  - `Risk Management Design`,
  - `Actual Risk Behavior`,
  - `Entry Timing`,
  - `Exit Timing`,
  - `Known Limitations`,
  - `Bad Performance Clues` if diagnostics exist.
- Use persisted explanation metadata first.
- Use strategy parameters and execution metadata to show:
  - selected pattern,
  - entry mode,
  - fill price source,
  - risk sizing mode,
  - stop/target design,
  - soft invalidation rule,
  - partial exit rule,
  - time stop rule,
  - cost assumptions.
- Mark fallback content clearly if metadata is missing.
- Keep raw JSON behind debug details only.

# Out of Scope

- No backend execution endpoint.
- No strategy changes.
- No live trading controls.
- No excessive static text that contradicts actual metadata.

# Requirements

- Frontend must show strategy/risk/entry/exit explanation for a run with full metadata.
- Legacy runs must show fallback sections safely.
- Text must not imply live trading readiness.
- Risk and entry/exit sections must use actual metadata when present.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read frontend `AGENTS.md`.
- [x] Read frontend `STATUS.md`.
- [x] Read `docs/api/API_CONTRACT.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:
- Frontend changes are read-only and must consume existing detail/diagnostics payloads only.
- Fallback text is acceptable for legacy rows, but it must be explicitly labeled as fallback/unavailable.
- No backend execution endpoint or strategy-running UI is introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- The dashboard has dedicated strategy, risk, entry, and exit explanation sections.
- FVG run shows whether entry was confirmation close, next open, midpoint, boundary, or custom limit.
- Risk panel shows sizing mode, risk per unit, stop/target/partial exit semantics where available.
- Exit panel shows realized exit reasons if diagnostics/attribution exist.
- Frontend build passes.

# Required Tests

## Unit Tests

- Helper tests for extracting strategy/risk/entry/exit metadata if harness exists.
- Fallback text tests.

## Integration Tests

- Render fixture with FVG Task 172-style metadata showing original entry reference and fill-adjusted risk plan.

## Contract Tests

- API contract documents fields consumed by explanation panels.

## Safety Tests

- Confirm frontend does not call execution endpoints or run backtests.

# Verification

Default:

```bash
npm --prefix frontend run build
pytest backend/tests/test_backtest_results_service_runtime.py
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

# Completion Summary

- Files changed:
  - `frontend/src/lib/strategyExplanation.ts`
  - `frontend/src/app/page.tsx`
  - `frontend/tests/strategyExplanation.test.ts`
  - `frontend/package.json`
  - `frontend/tsconfig.test.json`
  - `frontend/STATUS.md`
  - `docs/api/API_CONTRACT.md`
- Implementation summary:
  - Replaced the generic Strategy Logic area with structured Strategy Overview, Economic Hypothesis, Indicators Used, Risk Management Design, Actual Risk Behavior, Entry Timing, Exit Timing, Known Limitations, and Bad Performance Clues sections.
  - Added a typed frontend extraction helper that consumes actual run metadata, diagnostics, and trade metadata first, with clearly marked fallback behavior for legacy rows.
  - Added helper coverage for FVG fill-adjusted risk metadata, entry mode, exit reason, diagnostics clues, and legacy fallback text.
  - Documented the metadata fields consumed by the explanation panels.
- Tests added or updated:
  - Added `frontend/tests/strategyExplanation.test.ts`.
  - Updated frontend helper test script and TypeScript test config.
- Tests run:
  - `npm --prefix frontend run test:helpers`
  - `npm --prefix frontend run build`
  - `pytest backend/tests/test_backtest_results_service_runtime.py`
  - `pytest`
  - `git diff --check`
- Codex self-review result:
  - Scope stayed within Task 183; frontend remains read-only and no execution endpoint, live trading control, direct DB access, API key, or `.env` behavior was added.
- Known limitations:
  - Legacy runs can only show fallback explanation where persisted strategy explanation and execution metadata are absent.
- Recommended next task:
  - Task 184.
