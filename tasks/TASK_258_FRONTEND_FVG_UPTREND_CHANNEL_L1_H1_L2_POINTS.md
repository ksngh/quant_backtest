# Task 258: Frontend FVG Uptrend Channel L1/H1/L2 Points

# Goal

Make the dashboard FVG v2 channel overlay clearly draw and label the three defining points for an upward channel:

- `L1`: first lower-anchor low.
- `H1`: intervening upper-touch high.
- `L2`: second lower-anchor low.

# Source Requirement

Owner clarified:

```text
아니 아까는 그림 잘 그려줬잖아.. 상승 추세선 같은 경우 L1,H1,L2 점 그리도록 해줘.
```

Clean requirement:

- For FVG v2 uptrend channel overlays, the chart must visibly mark the channel construction points as `L1`, `H1`, and `L2`.
- The points must come from saved channel geometry metadata, not from frontend recomputation.
- The labels must match the owner-facing terminology: `L1`, `H1`, `L2`.

# Extracted Roles

- Owner role:
  - Defines the visual/debugging expectation for upward FVG channel construction points.
- Supporting roles:
  - Frontend role: render the existing channel geometry points in the dashboard overlay.
  - API/metadata role: preserve and consume existing channel geometry fields such as `lower_anchor_1_index`, `upper_touch_index`, and `lower_anchor_2_index`.
  - Test role: add focused overlay helper/rendering tests for point ordering and labels.
- Forbidden roles:
  - Do not change channel detection math.
  - Do not recompute channel anchors from raw candles in the frontend.
  - Do not modify backend persistence unless existing metadata is proven insufficient.
  - Do not change FVG v2 entry/exit semantics, direction rules, target policy, cost filters, or backtest engine behavior.
  - Do not add live trading, order execution, credentials, signed requests, account endpoints, or exchange order endpoints.

# Context

FVG v2 channel metadata already records uptrend channel construction fields:

- `lower_anchor_1_index`
- `upper_touch_index`
- `lower_anchor_2_index`
- `lower_line`
- `upper_line`
- `channel_trend_direction`

The current frontend overlay helper already has point extraction logic, but the uptrend upper-touch point is labeled generically as `H` instead of the requested `H1`. This task should make the visual contract explicit and ensure tests protect it.

# Scope

- Update frontend FVG channel overlay point labeling for uptrend channels:
  - `lower_anchor_1_index` -> label `L1`.
  - `upper_touch_index` -> label `H1`.
  - `lower_anchor_2_index` -> label `L2`.
- Ensure the three points are included when the metadata exists.
- Preserve existing bounded multi-channel overlay behavior.
- Preserve existing entry/exit markers.
- Add or update frontend tests for the overlay helper/rendering behavior.
- Update API/frontend documentation only if the visible label contract needs to be documented.

# Out of Scope

- No backend channel detection changes.
- No strategy/backtest behavior changes.
- No new channel direction rules.
- No target/stop/cost-filter changes.
- No dashboard redesign.
- No downtrend point-label redesign unless needed to avoid regression.
- No live trading or exchange order behavior.

# Requirements

- Uptrend FVG v2 channel overlays must show all available defining points as `L1`, `H1`, and `L2`.
- The point positions must use saved channel metadata.
- `H1` must use `upper_touch_index` and the upper channel line value at that index.
- `L1` and `L2` must use the lower channel line values at their anchor indexes.
- Missing metadata must degrade gracefully without throwing.
- Existing channel line overlays, bounded segments, and trade markers must continue to render.
- Tests must prove the label sequence and point kinds for an uptrend channel.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Read `frontend/AGENTS.md` and `frontend/STATUS.md`.
- [x] Read `docs/api/API_CONTRACT.md` FVG channel metadata section.
- [x] Read `frontend/src/lib/fvgChannelOverlay.ts`.
- [x] Read `frontend/tests/fvgChannelOverlay.test.ts`.
- [x] Confirm no backend metadata change is needed before coding.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Update `frontend/STATUS.md` if frontend state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A saved uptrend channel with `lower_anchor_1_index`, `upper_touch_index`, and `lower_anchor_2_index` produces three visible point labels: `L1`, `H1`, `L2`.
- `H1` is not labeled as plain `H`.
- Point coordinates are derived from metadata line models and indexes.
- Existing multi-channel overlay behavior remains intact.
- Existing entry/exit markers remain intact.
- Frontend tests cover the uptrend `L1`/`H1`/`L2` labels.

# Required Tests

## Unit Tests

- Update or add `frontend/tests/fvgChannelOverlay.test.ts` coverage proving:
  - uptrend `lower_anchor_1_index` maps to `L1`,
  - uptrend `upper_touch_index` maps to `H1`,
  - uptrend `lower_anchor_2_index` maps to `L2`,
  - missing point metadata does not throw.

## Integration Tests

- Run the frontend typecheck/test command used by the repo for frontend helper tests.

## Contract Tests

- No backend contract test is required if existing metadata fields are sufficient.
- If any new field is introduced, update `docs/api/API_CONTRACT.md` and add appropriate contract coverage.

## Safety Tests

- Confirm no live trading controls, signed requests, exchange order endpoints, account endpoints, credentials, or real exchange order behavior are introduced.

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
npm --prefix frontend run test
npm --prefix frontend run typecheck
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

# Completion Summary

Completed on 2026-05-28.

- Files changed:
  - `frontend/src/lib/fvgChannelOverlay.ts`
  - `frontend/tests/fvgChannelOverlay.test.ts`
  - `tasks/TASK_258_FRONTEND_FVG_UPTREND_CHANNEL_L1_H1_L2_POINTS.md`
  - `STATUS.md`
  - `frontend/STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
- Implementation summary:
  - Changed the saved uptrend channel upper-touch marker label from `H` to `H1`.
  - Ordered construction point labels as `L1`, `H1`, `L2`.
  - Kept point coordinates sourced from saved channel geometry line models and indexes.
  - Did not change backend metadata, channel detection, strategy, backtest, entry/exit, target, stop, or cost-filter behavior.
- Tests added or updated:
  - Added frontend helper assertions for the uptrend `L1`, `H1`, `L2` label sequence.
  - Added regression assertion that the upper-touch point is not labeled plain `H`.
  - Added missing point metadata coverage to confirm graceful fallback without throwing.
- Tests run:
  - `npm --prefix frontend run test` (fails because `frontend/package.json` has no `test` script)
  - `npm --prefix frontend run test:helpers`
  - `npm --prefix frontend run typecheck`
  - `git diff --check`
- Codex self-review result:
  - Scope respected; implementation stayed within frontend overlay labeling and tests.
  - No backend behavior, trading behavior, signed requests, credentials, account endpoints, or exchange order endpoints were added.
  - No unnecessary abstraction was introduced.
- Known limitations:
  - The generic `npm --prefix frontend run test` command is unavailable in this package; the repo's actual helper test command is `npm --prefix frontend run test:helpers`.
  - Browser visual verification was not run in this task; helper tests verify the model consumed by the SVG chart.
- Recommended next task:
  - Run the owner FVG v2 channel command and inspect `COST_INFEASIBLE_TAKE_PROFIT` skips, projected targets, side distribution, total costs, equity curve, and the dashboard channel labels.
