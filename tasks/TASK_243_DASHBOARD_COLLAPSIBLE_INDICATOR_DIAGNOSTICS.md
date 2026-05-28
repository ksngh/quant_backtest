# Task 243: Dashboard Collapsible Indicator Diagnostics

# Goal

Make indicator, diagnostics, and metadata sections easier to scan by showing compact headers first and expanding details only when the user clicks.

# Source Requirement

Owner feedback:

3. Indicators are hard to read because too much is shown at once. The dashboard should not show every indicator simultaneously; each indicator/diagnostic group should open on click.

# Extracted Roles

- Owner role:
  - Frontend dashboard information-architecture owner.
- Supporting roles:
  - Frontend component role: owns disclosure/accordion UI, state, layout, and accessibility.
  - Test role: owns frontend type/build and helper checks.
- Forbidden roles:
  - Do not change backend persistence/API unless a missing field blocks display.
  - Do not change backtest/strategy logic.
  - Do not add live trading behavior or execution controls.

# Context

The current dashboard exposes many diagnostics and indicator-derived panels at once. That creates visual noise and makes the important graph/trade review harder to inspect. The desired behavior is progressive disclosure: show section titles and high-signal summaries, then expand on demand.

# Scope

- Convert indicator and diagnostic-heavy panels into click-to-open sections.
- Use stable section groups such as:
  - Strategy parameters,
  - Execution assumptions,
  - Pattern geometry,
  - Risk exit audit,
  - FVG v2 diagnostics,
  - Research report/debug JSON.
- Keep the most important summary rows visible where helpful.
- Persist no UI state unless existing app patterns already support it.
- Keep keyboard and screen-reader basic accessibility for toggles.

# Out of Scope

- Do not remove diagnostics from the API.
- Do not change indicator calculations.
- Do not add backend filtering.
- Do not add new chart interactions; Task 242 owns chart interactions.

# Requirements

- Indicator/diagnostic sections render collapsed by default unless there is a clear existing UX reason to keep one open.
- User can expand/collapse each section independently.
- Section headers show enough context to decide whether to open the section.
- Expanded content preserves existing data and legacy fallbacks.
- Layout remains readable on mobile and desktop.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read this assigned task file before coding.
- [ ] Confirm no backend or backtest logic changes are needed.

## After Implementation

- [ ] Update `STATUS.md` if project state changed.
- [ ] Append a concise progress/completion note to `PROJECT_HISTORY.md` when completed.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- Indicator/diagnostic panels are no longer all fully expanded at once.
- Each relevant group can be opened and closed by click.
- Existing information remains accessible.
- Frontend build/type checks pass.

# Required Tests

## Unit Tests

- Add helper/component tests if disclosure state is factored into testable helpers.

## Integration Tests

- Run frontend typecheck/build.
- If browser tooling is available, verify a saved run page can expand and collapse major sections.

## Contract Tests

- Confirm no API contract changes are required.

## Safety Tests

- Confirm no live trading controls or backend execution behavior are introduced.

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
npm --prefix frontend run typecheck
npm --prefix frontend run build
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
