# Task 254: FVG V2 Multi Channel Overlay And Scan Semantics Review

# Goal

Fix and verify FVG v2 channel visualization and trading semantics so the dashboard draws each detected/traded channel as its own bounded segment, and the backtest behavior is clear about whether it trades only FVG-event channels or standalone newly visible channels.

# Source Requirement

Owner reported that the current frontend appears to draw only the first FVG trade channel, extends the channel lines too far left/right, and may make it look like later trades are still based on the first channel. Owner also observed that equity now drops repeatedly and suspects the strategy may be trading from the initially drawn channel rather than from each newly detected channel.

Owner requested:

- Explain why the line is based only on the first FVG trade.
- Do not extend channel lines left/right indefinitely.
- Draw each channel only until the next trade.
- Analyze whether the repeated equity drop is caused by trading from the first channel or by recent channel-scan behavior.
- Restore or separate behavior if the previous version was better because it only traded channels tied to actual FVG events.

# Extracted Roles

- Owner role:
  - Defines intended channel visualization and interpretable trading behavior.
- Supporting roles:
  - Frontend role: renders multiple FVG channel overlays and bounds each segment by trade timing.
  - Backend/API role: exposes enough per-trade channel identity, geometry, and timing fields for deterministic frontend rendering.
  - Backtest/research role: audits FVG v2 channel scan semantics, duplicate-channel handling, and equity impact.
  - Test role: adds deterministic helper/service/backtest tests covering multi-channel overlays and scan-mode semantics.
- Forbidden roles:
  - Do not add live trading, real exchange order execution, signed requests, credentials, or account/order endpoints.
  - Do not add pyramiding or simultaneous positions unless a later task explicitly requests it.
  - Do not redesign the whole dashboard beyond the channel overlay/trade interpretation issue.
  - Do not change unrelated strategy patterns.

# Context

Tasks 247-253 added opt-in FVG v2 parallel channel detection, channel retest entries/exits, metadata persistence/API exposure, frontend overlay rendering, structure-low stops for LONG retests, per-new-channel candidate generation, starting-cash display fixes, and broader channel metadata parsing.

Known current issues to verify from Task 253:

- `frontend/src/lib/fvgChannelOverlay.ts` builds and returns a single overlay from the first valid channel geometry candidate.
- `frontend/src/app/page.tsx` renders one `channelOverlay` object instead of multiple channel overlays.
- The chart projects the active channel from the current visible `fromIndex` to `toIndex`, which visually extends the line outside its actual channel/trade lifecycle.
- Task 252 introduced visible-prefix standalone FVG channel scanning in `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`; this may broaden trading beyond original FVG event-driven action expansion.
- `build_fvg_channel_trade_actions()` dedupes by `channel_id`, but the implementation must be reviewed to ensure no-fill or duplicate channels are not prematurely locked out in a way that distorts later trades.

# Scope

- Frontend:
  - Replace the single-channel overlay model with a multi-channel overlay list.
  - Derive each overlay segment from channel geometry plus trade timing.
  - Draw each channel segment only from its channel/trade start to the next trade boundary, not across the entire visible viewport.
  - Keep existing zoom/drag chart behavior intact.
- Backend/API:
  - Verify the saved-run detail response exposes per-trade `channel_id`, channel geometry, entry timing, exit timing, and enough candle index/time fields to segment overlays.
  - Add small serializer changes only if required by the frontend overlay contract.
- Backtest/research:
  - Audit whether trades are generated from FVG-event channel expansion, standalone visible-prefix channel scanning, or both.
  - Determine whether the equity degradation comes from broader standalone scanning, duplicate-channel handling, cost/slippage, or genuine strategy behavior.
  - If needed, separate scan semantics with explicit metadata or a flag so FVG-event-only and standalone-channel-scan behavior are distinguishable.
  - Review `seen_channel_ids` timing so a detected but unfilled channel is not incorrectly treated as a completed trade candidate unless that is the intended policy.
- Documentation/status:
  - Update task, status, backlog, and history files according to project workflow.

# Out of Scope

- No new pattern detector unrelated to FVG v2 channels.
- No full dashboard redesign.
- No database schema migration unless existing JSON/API fields are insufficient.
- No live trading or exchange order/account functionality.
- No hidden changes to default strategy economics outside the explicit FVG v2 channel scan semantics.

# Requirements

- The frontend must render multiple FVG v2 channel overlays when a run contains multiple channel geometries.
- The frontend must not stop at the first parsed channel geometry.
- Each channel line must be clipped to a deterministic segment ending at the next trade boundary or a documented fallback boundary.
- The UI must make it possible to visually connect each trade to its own `channel_id`.
- The backtest/API path must expose enough metadata to verify whether each trade came from:
  - FVG-event channel expansion,
  - standalone visible-prefix channel scanning,
  - duplicate skip,
  - no-fill skip,
  - open-position blocked skip.
- The implementation must determine whether standalone scanning changed trading behavior compared with the earlier FVG-event-only path.
- If scan behavior is changed, the change must be explicit, covered by tests, and reflected in run metadata or action metadata.
- Existing runs without channel metadata must continue to render safely.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read `frontend/src/lib/fvgChannelOverlay.ts`.
- [x] Read `frontend/src/app/page.tsx`.
- [x] Read `frontend/src/types/api.ts`.
- [x] Read `backend/quant_backtest_api/services/backtest_results.py`.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [x] Read `quant_bitcoin/patterns/fvg_channel.py`.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A frontend helper test proves multiple channel geometries produce multiple overlay segments.
- A frontend helper test proves a channel segment ends at the next trade boundary rather than at the chart viewport boundary.
- A frontend helper or render test proves legacy single/no-channel data remains safe.
- A backend/API test or fixture proves per-trade channel ID, geometry, and timing fields needed for segmentation are available.
- A backtest test or focused diagnostic fixture distinguishes FVG-event-only channel generation from standalone visible-prefix channel generation.
- The final implementation summary states whether the equity drop is caused by frontend-only display, standalone scan semantics, duplicate-channel handling, or confirmed strategy losses.
- No live trading, signed request, credential, account endpoint, or order endpoint behavior is added.

# Required Tests

## Unit Tests

- `buildFvgChannelOverlays()` or equivalent multi-overlay helper test with two or more channel geometries.
- Overlay segment boundary test where channel A ends at trade B and channel B ends at trade C or a documented fallback.
- Legacy/no-channel helper test.
- Focused channel dedupe/scan semantics test if `seen_channel_ids` behavior is changed.

## Integration Tests

- Backend saved-run service fixture with multiple channel trades and required channel timing/geometry fields.
- Strategy runner/action-builder fixture showing whether channel actions are FVG-event-based, standalone-scan-based, or both.

## Contract Tests

- Frontend/API type coverage for channel overlay array fields and per-trade `channel_id`.
- API contract update if response fields or metadata semantics change.

## Safety Tests

- Confirm no live trading controls, signed exchange requests, API-key handling, account endpoints, or real order endpoints are added.

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
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py backend/tests/test_backtest_results_service.py -q
npm --prefix frontend run typecheck
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

# Completion Summary

- Files changed:
  - `quant_bitcoin/patterns/fvg_channel.py`
  - `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
  - `backend/quant_backtest_api/services/backtest_results.py`
  - `backend/tests/test_backtest_results_service.py`
  - `docs/api/API_CONTRACT.md`
  - `frontend/src/lib/fvgChannelOverlay.ts`
  - `frontend/src/app/page.tsx`
  - `frontend/src/types/api.ts`
  - `frontend/tests/fvgChannelOverlay.test.ts`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `tasks/TASK_254_FVG_V2_MULTI_CHANNEL_OVERLAY_AND_SCAN_SEMANTICS_REVIEW.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
  - `frontend/STATUS.md`
  - `backend/STATUS.md`
- Implementation summary:
  - Replaced the frontend single FVG channel overlay path with multi-channel overlay segments.
  - Bounded each drawn channel segment to the channel start and the next trade boundary instead of projecting through the full visible viewport.
  - Preserved a legacy single-overlay helper while moving the dashboard chart to the multi-overlay helper.
  - Added `channel_candidate_source` and `channel_scan_source` metadata/API fields.
  - Split standalone rolling visible-prefix channel scan behind explicit `--fvg-channel-standalone-scan`; `--enable-fvg-v2-channel` now defaults to FVG-event expansion semantics.
  - Changed channel dedupe so a detected but unfilled channel is not marked as seen until a filled candidate is produced.
- Tests added or updated:
  - Frontend multi-channel overlay helper tests for multiple overlays, next-trade segment clipping, legacy no-channel behavior, nested exit metadata, and graph-point embedded metadata.
  - Backtest tests for standalone-scan opt-in behavior and unfilled-channel dedupe behavior.
  - CLI metadata tests for `standalone_scan_enabled` and scan semantics.
  - Backend service test for flattened channel source metadata.
- Tests run:
  - `python -m py_compile quant_bitcoin/backtesting/pattern_action_builder.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py quant_bitcoin/patterns/fvg_channel.py backend/quant_backtest_api/services/backtest_results.py`
  - `pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py backend/tests/test_backtest_results_service.py -q`
  - `npm --prefix frontend run typecheck`
  - `npm --prefix frontend run test:helpers`
  - `git diff --check`
- Codex self-review result:
  - Scope respected; no live trading, signed requests, credentials, account endpoints, or order endpoints added.
  - Frontend, backend API, and backtest changes stayed within Task 254.
- Known limitations:
  - Browser visual verification was not performed in this shell; helper/type tests verify the data model and chart compile path.
  - Equity degradation is now attributable as likely scan-semantics related when `--fvg-channel-standalone-scan` is enabled; final performance still requires re-running the owner dataset and comparing FVG-event-only versus standalone-scan modes.
- Recommended next task:
  - Re-run the owner 2026-05-20+ command once with default FVG-event-only channel mode and once with `--fvg-channel-standalone-scan`, then compare trade count, channel IDs, cost drag, and equity curve.
