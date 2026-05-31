# Task 250: Frontend FVG V2 Channel Overlay Visualization

# Goal

Draw owner-specified FVG v2 channel lines on the saved-run dashboard chart, including anchor points, upper touch point, retest point, entry marker, stop boundary, and target boundary.

# Source Requirement

Owner requirement:

- The algorithm should draw the lines.
- The frontend should show those lines so the user can inspect the channel and verify entries/exits visually.

# Extracted Roles

- Owner role:
  - Frontend chart inspection owner.
- Supporting roles:
  - Frontend chart overlay role: owns line projection, SVG drawing, responsive layout, and legend labels.
  - API consumer role: consumes read-only channel geometry metadata from Task 249.
  - Test role: owns helper/type/build checks and visual sanity checks.
- Forbidden roles:
  - Do not implement channel detection here.
  - Do not implement trading logic here.
  - Do not query the database directly from frontend.
  - Do not add live trading controls, order/account endpoints, credentials, or strategy execution controls.

# Context

The dashboard now supports chart-first inspection. Once channel geometry is persisted and exposed by the API, the chart should render the same lower/upper channel lines used by the backtest so the user can verify that entries and exits came from the drawn boundaries.

# Scope

- Consume channel geometry from saved-run detail metadata.
- Project line equations into chart coordinates for visible viewport.
- Draw:
  - lower channel line,
  - upper channel line,
  - low anchor points,
  - intervening upper touch high,
  - retest touch/confirmation point when available,
  - entry/exit marker annotations tied to channel boundary metadata.
- Preserve existing price/equity chart behavior, trade markers, drag zoom, pan, and reset controls.
- Add a compact legend/toggle for channel overlay visibility.
- Render safely when metadata is absent or incomplete.

# Out of Scope

- Do not add backend fields here unless Task 249 is incomplete and explicitly included.
- Do not add a new charting library unless existing SVG implementation cannot reasonably support the overlay.
- Do not add order execution or live controls.
- Do not change strategy/backtest behavior.

# Requirements

- Overlay must align with the chart's current zoom/pan viewport.
- Lines must be computed from API-provided geometry, not recomputed from raw candles in the frontend.
- Missing metadata must show a clear unavailable state or omit overlay without crashing.
- Text labels must not overlap core chart controls on desktop or mobile.
- Overlay should be distinguishable from trade markers and existing price/equity lines.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `frontend/AGENTS.md`.
- [ ] Read `docs/api/API_CONTRACT.md`.
- [ ] Confirm Task 249 is completed or explicitly included.
- [ ] Read this assigned task file before coding.

## After Implementation

- [ ] Update `STATUS.md` if project state changed.
- [ ] Append a concise completion note to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- Price chart can show lower and upper FVG v2 channel lines for enriched runs.
- Anchor/touch/retest markers are visible and aligned with candle timestamps.
- Overlay remains aligned after drag zoom, pan, zoom in/out, and reset.
- Legacy runs without channel metadata do not crash.
- Frontend typecheck/build pass.

# Required Tests

## Unit Tests

- Test line-to-chart-coordinate helper if introduced.
- Test visible-range clipping/projection helper if introduced.
- Test metadata fallback parsing for legacy rows.

## Integration Tests

- Run frontend typecheck/build/helper tests.
- If browser tooling is available, verify overlay visibility and zoom/pan alignment on a fixture run.

## Contract Tests

- Verify frontend type names and field usage match `docs/api/API_CONTRACT.md`.

## Safety Tests

- Confirm no strategy execution, live trading controls, signed requests, account endpoints, or order endpoints are added.

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
npm --prefix frontend run test:helpers
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

# Completion Note

Completed on 2026-05-28.

- Added `frontend/src/lib/fvgChannelOverlay.ts` to parse saved channel metadata and project line values.
- Updated the price chart to draw lower/upper channel lines plus anchor, upper-touch, entry, and exit markers while preserving zoom/pan/reset behavior.
- Added TypeScript helper coverage and verified `typecheck`, `test:helpers`, and production build.
