# Task 253: Backtest Run Starting Cash And Channel Overlay Visibility Fix

# Goal

Fix the saved-run dashboard path so a strategy backtest executed with `--starting-cash 1000000` displays 1,000,000 consistently, and FVG v2 channel lines are visible in the frontend for runs that contain channel metadata.

# Source Requirement

Owner reported after running the FVG v2 channel workflow with backend and frontend already running:

- `--starting-cash 1000000` is provided, but the UI keeps showing 10,000.
- The drawn channel lines do not appear in the frontend.

# Extracted Roles

- Owner role:
  - Defines the observed correctness issue and expected visible dashboard behavior.
- Supporting roles:
  - CLI/backtest runner role: verifies parsed starting cash reaches engine config, stdout JSON, persistence payload, and run key inputs.
  - Persistence/API role: verifies saved run and detail API expose the actual configured starting cash and channel metadata.
  - Frontend role: verifies the dashboard selects/displays the correct run fields and renders channel overlay lines when metadata exists.
  - Test role: adds deterministic regression coverage for starting-cash propagation and channel overlay visibility.
- Forbidden roles:
  - Do not add live trading, real exchange order execution, signed requests, credentials, or account/order endpoints.
  - Do not change strategy economics or channel detection rules unless needed to fix metadata propagation/display.
  - Do not add pyramiding or same-channel repeated entries.

# Context

Tasks 247-252 added opt-in FVG v2 channel detection, retest entries/exits, channel metadata persistence/API fields, frontend overlay rendering, LONG structure-low stops, and per-new-channel candidate generation. The owner now reports that the end-to-end saved-run dashboard does not reflect the requested starting cash and does not show channel lines despite the backend and frontend being active.

Likely failure surfaces to verify:

- CLI argument parsing or run invocation may not be using the edited package/entry point.
- `StrategyEngineConfig.starting_cash`, summary metadata, persistence payload, and `backtest_runs.starting_cash` may diverge.
- API serializers may return a default/legacy 10,000 value instead of saved run detail values.
- Frontend may display a default, list value, stale selected run, or summary fallback instead of detail data.
- Channel metadata may exist in trade metadata but not be flattened into the API fields consumed by `frontend/src/lib/fvgChannelOverlay.ts`.
- Overlay may be built only from completed trades, while current run metadata is attached to skipped/blocked entries or diagnostics.
- SVG overlay may render behind candles, outside clipped viewport, disabled by a toggle state, or filtered by missing field names.

# Scope

- Reproduce or inspect the saved-run path for the owner command shape:
  - `--pattern FAIR_VALUE_GAP`
  - `--start-time 2026-05-20T00:00:00Z`
  - `--starting-cash 1000000`
  - `--position-sizing-mode cash_fraction`
  - `--position-sizing-value 0.10`
  - `--enable-fvg-v2-channel`
- Trace starting cash through:
  - CLI args,
  - strategy engine config,
  - stdout JSON summary/config,
  - persistence payload,
  - backend list/detail API,
  - frontend summary/list/detail display.
- Trace FVG channel metadata through:
  - action metadata,
  - execution/trade metadata,
  - persistence payload,
  - backend flattened response fields,
  - frontend API types,
  - overlay builder,
  - chart SVG render path.
- Fix the smallest code path that causes the mismatch or missing overlay.
- Preserve existing default behavior for runs without channel metadata.
- Preserve Task 251 and Task 252 strategy semantics.

# Out of Scope

- No new trading strategy rules.
- No same-channel repeated trading.
- No multiple simultaneous positions.
- No database schema migration unless existing JSON metadata cannot safely carry the required fields.
- No live trading/order/account features.
- No unrelated dashboard redesign.

# Requirements

- `--starting-cash 1000000` must be visible as 1,000,000 in saved-run list/detail/frontend summary for the newly created run.
- The detail API must expose starting cash from the saved run/result, not an unrelated default fallback.
- FVG channel metadata must be available in the API response for runs that generated channel-mode entries/exits or diagnosable channel candidates.
- The frontend must render lower/upper channel lines when channel geometry metadata exists.
- If no channel metadata exists for a selected run, the frontend must omit the overlay cleanly or show a clear unavailable state without crashing.
- The UI must not silently look like it selected the new run while actually showing an older 10,000 starting-cash run.
- Tests must distinguish stale-run selection from value propagation failures where feasible.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read `quant_bitcoin/backtesting/strategy_persistence_adapter.py`.
- [x] Read `quant_bitcoin/persistence/postgres.py`.
- [x] Read `backend/quant_backtest_api/services/backtest_results.py`.
- [x] Read `frontend/src/app/page.tsx`.
- [x] Read `frontend/src/lib/fvgChannelOverlay.ts`.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A deterministic CLI/runner or persistence test proves configured `starting_cash=1000000` is carried into the engine result and saved payload/API-facing value.
- A backend service/API test proves saved run detail returns the configured starting cash rather than the 10,000 default.
- A frontend helper or component-level test proves the displayed selected-run starting cash is sourced from the selected run/detail data.
- A channel metadata fixture produces frontend overlay line segments with non-empty lower/upper lines.
- A saved-run API fixture with channel metadata exposes the fields required by the frontend overlay builder.
- Legacy runs without channel metadata remain safe and do not crash the frontend.

# Required Tests

## Unit Tests

- Starting-cash propagation helper or serializer test for 1,000,000.
- `buildFvgChannelOverlay()` test with enriched channel metadata that produces visible lower/upper line segments.
- Legacy/no-channel overlay helper test returns no overlay safely.

## Integration Tests

- Strategy runner/persistence payload test with `starting_cash=1000000`.
- Backend saved-run detail service test for starting cash and channel metadata fields.

## Contract Tests

- API contract/type expectations for starting cash and FVG channel overlay fields.
- Frontend type/helper coverage for channel metadata names used by the backend.

## Safety Tests

- Confirm no live trading controls, signed requests, exchange order endpoints, or credential handling are added.

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
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_strategy_engine.py backend/tests/test_backtest_results_service.py -q
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
  - `quant_bitcoin/persistence/postgres.py`
  - `backend/quant_backtest_api/services/backtest_results.py`
  - `docs/api/API_CONTRACT.md`
  - `frontend/src/app/page.tsx`
  - `frontend/src/lib/fvgChannelOverlay.ts`
  - `frontend/src/lib/runDisplay.ts`
  - `frontend/src/types/api.ts`
  - `frontend/package.json`
  - `frontend/tsconfig.test.json`
  - `.gitignore`
  - `frontend/tests/fvgChannelOverlay.test.ts`
  - `frontend/tests/runDisplay.test.ts`
  - `backend/tests/test_backtest_results_service.py`
  - `tests/backtesting/test_pattern_postgres_runner_cli.py`
  - `tests/backtesting/test_strategy_persistence_adapter.py`
  - `tasks/TASK_253_BACKTEST_RUN_STARTING_CASH_AND_CHANNEL_OVERLAY_VISIBILITY_FIX.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
- Implementation summary:
  - Exposed configured `starting_cash` in saved-run list API summary.
  - Made the frontend display configured run starting cash (`run.starting_cash`) as the primary Starting Cash value and show a mismatch note if result summary differs.
  - Added run-list starting cash text so stale/older run selection is visible.
  - Made channel overlay discovery robust across trade top-level fields, trade metadata, nested `exit_metadata`, and graph-point embedded trade metadata.
  - Flattened channel ID/identity and nested exit channel geometry in the backend trade serializer.
  - Documented starting cash and channel ID/identity API fields.
- Tests added or updated:
  - Million starting-cash CLI/persistence propagation tests.
  - Backend list starting-cash and nested channel metadata serialization tests.
  - Frontend starting-cash display helper test.
  - Frontend channel overlay nested/graph metadata tests.
- Tests run:
  - `pytest tests/backtesting/test_strategy_persistence_adapter.py tests/backtesting/test_pattern_postgres_runner_cli.py backend/tests/test_backtest_results_service.py -q`
  - `pytest tests/backtesting/test_strategy_engine.py -q`
  - `npm --prefix frontend run typecheck`
  - `npm --prefix frontend run test:helpers`
  - `git diff --check`
- Codex self-review result:
  - Scope respected; no live trading, signed requests, credentials, account endpoints, or order endpoints added.
- Known limitations:
  - Local API was not reachable from this shell during inspection, so live browser/API visual verification was not performed here.
  - The overlay still draws the first available channel model; richer multi-channel overlay selection can be a later frontend task.
- Recommended next task:
  - Re-run the 2026-05-20+ command, select the newest run, and verify the list row shows `Start cash 1,000,000` and the Close Price chart reports/draws the FVG channel overlay.
