# Task 259: FVG V2 Channel Close-Based Retest And Trade-Bounded Overlay

# Goal

Change FVG v2 channel retest confirmation to use candle close semantics and make the dashboard channel overlay stop at the actual trade/retest point instead of extending beyond the intended visual boundary.

For an uptrend channel, the dashboard should visibly show the construction/trade points and draw the channel lines only across that meaningful span:

- `L1`: first lower-anchor low.
- `H1`: intervening upper-touch high.
- `L2`: second lower-anchor low.
- trade/retest point: the candle where the channel retest is confirmed and the simulated trade candidate is generated.

# Source Requirement

Owner clarified:

```text
리테스트를 확인하는 캔들은 종가기준이어야해.
선은 딱 매매지점까지만 그려달라니까..
가령 상승 추세선 같은경우는 점이 네개찍히고 딱 그 처음 점과 끝 점을 기준으로 선이 끝나겠지..
지금은 L1이나 L2 등의 점이 안찍히던데.. 이유가뭐야.
```

Clean requirement:

- FVG v2 channel retest confirmation must be close-based, not wick-touch-first.
- The dashboard must draw channel overlay lines from the first construction point to the trade/retest point only.
- Uptrend overlays must show `L1`, `H1`, `L2`, and the trade/retest point when the saved metadata is available.
- If points are missing, the implementation must expose why through tests/diagnostics rather than silently hiding them.

# Extracted Roles

- Owner role:
  - Defines that channel retest confirmation should use candle close.
  - Defines the visual boundary: draw channel lines only from the first construction point to the trade/retest point.
  - Defines the expected uptrend visual points: `L1`, `H1`, `L2`, and trade/retest point.
- Supporting roles:
  - Pattern/channel role: owns deterministic FVG v2 channel retest confirmation semantics.
  - Frontend role: renders saved channel geometry and trade/retest markers without recomputing channels from raw candles.
  - API/metadata role: preserves enough saved metadata for frontend point visibility and line clipping.
  - Test role: adds fixtures for close-based retest and bounded overlay behavior.
- Forbidden roles:
  - Do not add live trading, real exchange order execution, signed requests, credentials, account endpoints, or exchange order endpoints.
  - Do not change FVG v2 target/stop/cost-aware entry rules except where metadata references the retest/trade point.
  - Do not recompute channel geometry from raw candles in the frontend.
  - Do not expand into dashboard redesign, strategy optimization, or new parameter search.

# Context

Current channel retest logic in `quant_bitcoin/patterns/fvg_channel.py` uses a wick-touch plus close-back-inside rule:

- upper retest currently checks `high >= upper` and `close < upper`,
- lower retest currently checks `low <= lower` and `close > lower`.

This means a wick can trigger the retest candidate even if the owner expects the retest candle itself to be close-based.

Current frontend overlay logic in `frontend/src/lib/fvgChannelOverlay.ts`:

- extracts `L1`, `H1`, `L2` from saved uptrend channel geometry when `lower_anchor_1_index`, `upper_touch_index`, and `lower_anchor_2_index` exist,
- draws points in the SVG chart when those points fall inside the visible chart range,
- may extend the segment to the next trade boundary, which can be the exit point rather than the entry/retest point.

Likely reasons `L1`/`L2` may not be visible in the current dashboard include:

- the selected saved run was generated before channel geometry metadata was persisted or flattened,
- the selected run is not a channel run or does not include `channel_geometry`/`fvg_channel`,
- the visible chart range is zoomed/panned away from the construction points,
- the channel is downtrend geometry, whose construction points use `upper_anchor_1_index`, `lower_touch_index`, and `upper_anchor_2_index` rather than the uptrend `L1`/`H1`/`L2` fields,
- the overlay segment is clipped to a boundary that does not match the owner-expected trade/retest point.

# Scope

- Change FVG v2 channel retest confirmation to close-based semantics.
- Define exact close-based rules for upper and lower boundary retests in code and metadata.
- Preserve existing Task 256 direction mapping unless a test proves the close-based rule requires a documented adjustment:
  - upper-boundary retest -> LONG,
  - lower-boundary retest -> SHORT.
- Ensure wick-only touches no longer produce channel entries under the new close-based rule.
- Ensure the channel entry fill/trade point remains auditable in metadata.
- Update frontend overlay segment clipping so channel lines end at the trade/retest point, not the next exit boundary.
- Ensure uptrend overlays show `L1`, `H1`, `L2`, and the entry/retest point when metadata exists.
- Add diagnostic-friendly tests for missing point metadata and trade-bounded clipping.
- Update API contract documentation only if metadata fields or semantics change.

# Out of Scope

- No live trading.
- No exchange account/order endpoints.
- No new optimizer or profitability selection.
- No target/stop/cost-aware entry policy changes beyond compatibility with the new close-based retest point.
- No frontend recomputation of channel anchors from raw candles.
- No unrelated dashboard layout redesign.
- No database schema migration unless existing JSON metadata cannot carry required fields.

# Requirements

- A candle that only wicks to a channel boundary but does not satisfy the close-based retest rule must not generate a channel entry.
- A candle that satisfies the close-based upper-boundary retest rule must generate the expected LONG channel candidate under Task 256 semantics.
- A candle that satisfies the close-based lower-boundary retest rule must generate the expected SHORT channel candidate under Task 256 semantics.
- Retest metadata must clearly record that the confirmation basis is close-based.
- Frontend channel lines must start at the first construction point and end at the trade/retest point for the rendered channel candidate.
- For an uptrend channel with complete metadata, the overlay must include visible model points for `L1`, `H1`, `L2`, and entry/retest.
- The frontend must not silently drop point labels when metadata exists.
- If metadata is missing, tests must verify graceful fallback and document why labels cannot be drawn.
- Existing multi-channel dedupe, cost-aware target blocking, and saved-run API compatibility must remain intact.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Read `frontend/AGENTS.md` and `frontend/STATUS.md`.
- [x] Read `docs/api/API_CONTRACT.md` FVG channel metadata section.
- [x] Read `quant_bitcoin/patterns/fvg_channel.py`.
- [x] Read `tests/patterns/test_fvg_channel.py`.
- [x] Read `frontend/src/lib/fvgChannelOverlay.ts`.
- [x] Read `frontend/tests/fvgChannelOverlay.test.ts`.
- [x] Confirm whether API flattening already exposes all required geometry/trade fields.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Update `frontend/STATUS.md` if frontend behavior changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Wick-only upper/lower boundary tests do not produce channel entries.
- Close-confirmed upper/lower boundary tests do produce the expected channel entries.
- Channel entry metadata includes close-based retest semantics.
- Frontend overlay helper clips a channel segment to the entry/retest trade point, not to the later exit point.
- Uptrend overlay helper returns `L1`, `H1`, `L2`, and entry/retest point models when all metadata exists.
- Missing metadata fallback remains non-crashing and test-covered.
- Existing Task 256/257 channel behavior tests remain passing after semantic updates.

# Required Tests

## Unit Tests

- Add or update `tests/patterns/test_fvg_channel.py`:
  - wick-only upper retest is rejected,
  - wick-only lower retest is rejected,
  - close-based upper retest is accepted as LONG,
  - close-based lower retest is accepted as SHORT,
  - metadata records close-based confirmation semantics.
- Add or update `frontend/tests/fvgChannelOverlay.test.ts`:
  - segment end uses entry/retest point instead of exit point,
  - uptrend point labels include `L1`, `H1`, `L2`, and entry/retest,
  - missing point metadata gracefully returns available points only.

## Integration Tests

- Run targeted Python channel tests and frontend helper tests.

## Contract Tests

- If metadata shape changes, update `docs/api/API_CONTRACT.md` and related backend/frontend type tests.
- If no metadata shape changes are needed, document that existing fields are sufficient.

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
pytest tests/patterns/test_fvg_channel.py -q
npm --prefix frontend run test:helpers
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
  - `quant_bitcoin/patterns/fvg_channel.py`
  - `tests/patterns/test_fvg_channel.py`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `frontend/src/lib/fvgChannelOverlay.ts`
  - `frontend/tests/fvgChannelOverlay.test.ts`
  - `docs/api/API_CONTRACT.md`
  - `tasks/TASK_259_FVG_V2_CHANNEL_CLOSE_BASED_RETEST_AND_TRADE_BOUNDED_OVERLAY.md`
  - `STATUS.md`
  - `frontend/STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
- Implementation summary:
  - Changed FVG v2 channel retest confirmation from wick-touch plus close-back-inside to close-based boundary confirmation.
  - Upper-boundary channel retest now requires `close >= upper_channel_line` and maps to LONG under the existing Task 256 rule.
  - Lower-boundary channel retest now requires `close <= lower_channel_line` and maps to SHORT under the existing Task 256 rule.
  - Added `retest_confirmation_basis=CLOSE_BASED_CHANNEL_BOUNDARY_RETEST_V1` and related close-rule metadata to channel entries.
  - Changed frontend channel overlay clipping so line segments end at the saved entry/retest point instead of the later exit boundary.
  - Preserved metadata-sourced overlay points and frontend no-recompute boundary.
- Tests added or updated:
  - Added wick-only upper/lower rejection coverage.
  - Updated close-confirmed upper/lower channel entry fixtures and projected target expectations.
  - Updated channel action-builder fixtures for close-based retest semantics.
  - Updated frontend overlay helper tests for trade-bounded segment end, `L1`/`H1`/`L2`/entry labels, and partial/missing metadata fallback.
- Tests run:
  - `pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q`
  - `npm --prefix frontend run test:helpers`
  - `npm --prefix frontend run typecheck`
  - `python -m py_compile quant_bitcoin/patterns/fvg_channel.py`
  - `git diff --check`
- Codex self-review result:
  - Scope respected; changes stayed within Task 259 close-based retest and trade-bounded overlay behavior.
  - No live trading, signed requests, credentials, account endpoints, or exchange order endpoints were introduced.
  - No frontend channel recomputation from raw candles was added.
- Known limitations:
  - Existing saved runs generated before this task still carry old metadata/old retest behavior and must be rerun to show the updated close-based entries and bounded overlays.
  - Browser visual verification was not run; frontend helper tests verify the overlay model consumed by the SVG chart.
- Recommended next task:
  - Rerun the owner FVG v2 channel command and inspect trade count, skipped cost-infeasible candidates, projected targets, and dashboard `L1`/`H1`/`L2`/entry overlay behavior.
