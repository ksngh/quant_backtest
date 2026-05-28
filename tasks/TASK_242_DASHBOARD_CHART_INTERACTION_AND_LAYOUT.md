# Task 242: Dashboard Chart Interaction And Layout

# Goal

Move the primary backtest chart experience to the top of the dashboard and replace date-input-first chart navigation with direct drag, pan, zoom, and reset controls.

# Source Requirement

Owner feedback:

1. The graph is hard to inspect.
2. Instead of `to/from` inputs as the main interaction, the chart should support zoom in/out and drag navigation.
3. The graph should be shown above the other dashboard sections.

# Extracted Roles

- Owner role:
  - Frontend dashboard UX owner.
- Supporting roles:
  - Frontend chart component role: owns chart viewport, interactions, layout, and responsive behavior.
  - Test role: owns frontend helper/type/build checks and any available visual or interaction tests.
- Forbidden roles:
  - Do not add backtest execution endpoints.
  - Do not mutate backend strategy/backtest logic.
  - Do not add live trading, order controls, account access, API keys, or `.env` changes.

# Context

The dashboard currently puts substantial controls/summary content before the chart, and chart range control relies on explicit date inputs. This is inefficient for trade/path inspection because the user wants to visually zoom into a time region, pan, and reset without manually typing a range.

# Scope

- Reorder the dashboard so the main price/equity chart area is near the top of the run detail view.
- Add direct chart interactions:
  - drag-select or drag-pan for time navigation,
  - zoom in,
  - zoom out,
  - reset viewport.
- Keep date/from-to controls only if useful as secondary exact controls, not the primary navigation path.
- Preserve trade markers and existing graph data contracts.
- Ensure chart interactions work on desktop and do not break mobile layout.

# Out of Scope

- Do not change backend API shape in this task.
- Do not add new persisted data fields.
- Do not implement run-list filtering here.
- Do not redesign the entire dashboard.
- Do not add charting libraries unless the existing code cannot reasonably support the required interactions.

# Requirements

- Primary chart section appears before indicator/diagnostics/detail panels.
- User can zoom and pan/drag through the chart without typing dates.
- Reset control restores the full run range.
- Trade markers remain visible and aligned after zoom/pan.
- Text and controls must not overlap on mobile or desktop.
- Existing run detail loading and chart data behavior remain read-only.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [ ] Read this assigned task file before coding.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm no backend strategy/backtest logic or live trading behavior is introduced.

## After Implementation

- [ ] Update `STATUS.md` if project state changed.
- [ ] Append a concise progress/completion note to `PROJECT_HISTORY.md` when completed.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- The graph appears above lower diagnostic/detail sections in the run detail page.
- Drag and zoom controls work on the visible chart data without requiring date input.
- Reset returns to the full chart domain.
- Existing marker/table behavior still works.
- Frontend build/type checks pass.

# Required Tests

## Unit Tests

- Test viewport/domain helper calculations if helpers are introduced.
- Test reset/zoom range calculations for boundary cases.

## Integration Tests

- Run frontend typecheck/build.
- If available, add or run frontend interaction/helper tests for chart viewport behavior.

## Contract Tests

- Confirm no backend API contract change is required.

## Safety Tests

- Confirm no live-trading controls, execution endpoints, or signed request behavior are added.

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
