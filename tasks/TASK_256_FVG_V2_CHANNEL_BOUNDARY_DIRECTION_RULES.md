# Task 256: FVG V2 Channel Boundary Direction Rules

# Goal

Update the opt-in FVG v2 channel strategy so channel-boundary retest entries follow the owner-defined direction rules:

- In an uptrend channel, lower-boundary retest confirms SHORT.
- In an uptrend channel, upper-boundary retest confirms LONG.
- In a downtrend channel, upper-boundary retest confirms LONG.
- In a downtrend channel, lower-boundary retest confirms SHORT.

In practical entry-side terms, this means upper-boundary retests enter LONG and lower-boundary retests enter SHORT, with channel trend direction preserved as explicit metadata and tested behavior.

# Source Requirement

Owner clarified:

```text
상승 추세선에서 밑부분에 닿으면 리테스트 확인하고 숏치는게 맞아.
상승 추세선에서 윗부분에 닿으면 리테스트 확인하고 롱치는게 맞고,
하락 추세선에서 윗 선에 닿으면 리테스트 확인하고 롱치는 게 맞고,
하락 추세선에서 밑 부분에 닿으면 리테스트 확인하고 숏치도록 전략을 수정해줘.
내 생각엔 그냥 반대로 하면 될 거 같고, 지금 한 작업이 그렇게 한 작업인지 확인해봐
```

Current finding before implementation:

- Task 255 did not implement this channel-boundary rule.
- Task 255 only added baseline FVG inverse direction mode behind `--fvg-inverse-direction`.
- Task 255 deliberately blocks FVG channel inverse mode with `FVG_INVERSE_DIRECTION_CHANNEL_UNSUPPORTED`.
- Existing Task 248 channel behavior is the opposite of this new requirement:
  - upper-boundary retest -> SHORT,
  - lower-boundary retest -> LONG.

# Extracted Roles

- Owner role:
  - Defines channel-boundary direction semantics for FVG v2 channel retest entries.
- Supporting roles:
  - Strategy/backtest role: changes channel retest entry-side selection.
  - Channel geometry role: records whether detected channel geometry is uptrend or downtrend when supported.
  - Risk/exit role: keeps stop/target behavior internally consistent after the entry-side change.
  - Metadata role: exposes entry boundary, channel trend direction, effective side, and rule version.
  - Test role: proves upper/lower boundary direction rules with deterministic fixtures.
- Forbidden roles:
  - Do not change baseline FVG behavior.
  - Do not change default disabled behavior for FVG v2 channel mode.
  - Do not add live trading, exchange order endpoints, account endpoints, signed requests, credentials, or real order execution.
  - Do not add frontend UI changes unless channel metadata contract changes require a narrow compatibility update.

# Context

Tasks 247-254 added FVG v2 channel geometry, channel retest entries/exits, saved metadata, dashboard overlays, multi-channel overlay semantics, and explicit standalone scan behavior.

Task 248 originally defined:

- upper-line touch/retest -> SHORT,
- lower-line touch/retest -> LONG,
- LONG target upper line,
- SHORT target lower line,
- channel-line stops instead of ATR.

Task 251 refined only the LONG stop to use the retest structure low.

Task 255 added `--fvg-inverse-direction`, but it applies only to baseline FVG action expansion and intentionally skips FVG channel inverse behavior. The new owner rule is not simply the existing baseline inverse flag; it is a specific channel-boundary direction contract.

The current implementation surface includes:

- `quant_bitcoin/patterns/fvg_channel.py`
  - `simulate_channel_retest_entry()`
  - `simulate_channel_boundary_exit()`
  - channel geometry models and metadata.
- `quant_bitcoin/backtesting/pattern_action_builder.py`
  - `build_fvg_channel_trade_actions()`
  - metadata assembly and action type conversion.
- tests:
  - `tests/patterns/test_fvg_channel.py`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `tests/backtesting/test_pattern_postgres_runner_cli.py`

# Scope

- Confirm current channel behavior and document that Task 255 did not implement the owner-defined channel-boundary rule.
- Change FVG v2 channel retest entry direction mapping to:
  - upper-boundary touch and retest confirmation -> LONG,
  - lower-boundary touch and retest confirmation -> SHORT.
- Preserve the retest confirmation concept:
  - upper-boundary LONG must be confirmed by a close condition that is explicit and deterministic.
  - lower-boundary SHORT must be confirmed by a close condition that is explicit and deterministic.
- Review and update stop/target semantics for the new entry sides:
  - LONG entries from upper-boundary retest must have a clear stop and exit/target policy.
  - SHORT entries from lower-boundary retest must have a clear stop and exit/target policy.
- Add or update metadata fields, such as:
  - `channel_direction_rule`,
  - `channel_trend_direction`,
  - `entry_boundary`,
  - `original_channel_entry_side`,
  - `effective_channel_entry_side`,
  - `channel_boundary_direction_mode`.
- If downtrend channel detection is not currently supported, either:
  - implement symmetric downtrend channel detection with deterministic tests, or
  - keep geometry detection unchanged and record the limitation explicitly in metadata/task completion.
- Ensure `--fvg-inverse-direction` channel-mode behavior is reconciled with this rule:
  - either channel mode no longer needs the baseline inverse flag, or
  - the flag remains rejected for channel mode with a reason that points to this explicit channel-boundary rule.

# Out of Scope

- No baseline FVG inverse-mode changes beyond preserving Task 255 behavior.
- No frontend redesign.
- No database schema migration unless existing JSON metadata paths cannot carry the required fields.
- No automatic profitability selection or strategy optimization.
- No live trading, real exchange orders, account endpoints, signed requests, credentials, or order endpoint calls.

# Requirements

- Existing FVG v2 channel mode must remain opt-in.
- Existing non-channel FVG behavior must remain unchanged.
- New channel entry side mapping must be deterministic:
  - upper boundary -> LONG,
  - lower boundary -> SHORT.
- Tests must cover the four owner-described cases:
  - uptrend lower-boundary retest -> SHORT,
  - uptrend upper-boundary retest -> LONG,
  - downtrend upper-boundary retest -> LONG,
  - downtrend lower-boundary retest -> SHORT.
- If downtrend channel geometry is deferred, the task completion must clearly state which downtrend cases are not executable yet and why.
- Stop/target hit checks must still use candle high-low against executable raw line/structure prices.
- Same-candle ambiguity behavior must remain explicit.
- Metadata must make it clear which channel boundary created the entry and which direction rule version was applied.
- No ATR-based stop must be introduced for this channel-boundary mode.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read this assigned task file before coding.
- [x] Read Task 248, Task 251, Task 254, and Task 255.
- [x] Read relevant channel strategy source and tests.
- [x] Confirm whether current channel geometry supports downtrend channels.
- [x] Record assumptions, blockers, or unclear exit semantics before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Current Task 255 behavior is verified as not equivalent to the new owner rule.
- With FVG v2 channel mode enabled:
  - upper-boundary retest can produce a LONG entry,
  - lower-boundary retest can produce a SHORT entry.
- Uptrend and downtrend channel-direction metadata is present where geometry supports it.
- Downtrend support is either implemented and tested or explicitly documented as deferred.
- Entry action metadata includes boundary-side and direction-rule fields.
- Exit/stop metadata remains internally consistent with the new entry side.
- Existing baseline FVG inverse tests still pass.
- Existing default-off channel behavior remains unchanged.
- No live trading or exchange endpoint behavior is added.

# Required Tests

## Unit Tests

- `simulate_channel_retest_entry()` upper-boundary retest emits LONG.
- `simulate_channel_retest_entry()` lower-boundary retest emits SHORT.
- Uptrend lower-boundary owner case fixture.
- Uptrend upper-boundary owner case fixture.
- Downtrend upper-boundary owner case fixture, if downtrend geometry is supported.
- Downtrend lower-boundary owner case fixture, if downtrend geometry is supported.
- Same-candle ambiguity remains deterministic.

## Integration Tests

- `build_fvg_channel_trade_actions()` emits `ENTER_LONG` for upper-boundary retest.
- `build_fvg_channel_trade_actions()` emits `ENTER_SHORT` for lower-boundary retest.
- Baseline `--fvg-inverse-direction` tests remain unchanged.
- CLI metadata remains stable for FVG channel configuration.

## Contract Tests

- Verify new metadata fields are JSON-serializable through existing action/run metadata paths.
- Verify existing frontend overlay metadata still has `channel_geometry` / `fvg_channel` fields.

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
pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q
git diff --check
```

If frontend/API metadata parsing is touched:

```bash
npm --prefix frontend run typecheck
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
  - `backend/quant_backtest_api/services/backtest_results.py`
  - `backend/tests/test_backtest_results_service.py`
  - `frontend/src/types/api.ts`
  - `docs/api/API_CONTRACT.md`
  - `tasks/TASK_256_FVG_V2_CHANNEL_BOUNDARY_DIRECTION_RULES.md`
  - `STATUS.md`
  - `BACKLOG.md`
  - `PROJECT_HISTORY.md`
- Implementation summary:
  - Confirmed Task 255 was not equivalent to this channel-boundary rule; baseline FVG inverse mode remains separate.
  - Changed FVG v2 channel retest entry mapping to upper-boundary retest -> LONG and lower-boundary retest -> SHORT.
  - Kept the existing close-back-inside retest confirmation semantics and existing channel-mode exit policy: LONG targets the upper line with retest-structure-low stop, SHORT targets the lower line with upper-line stop.
  - Added symmetric downtrend channel detection using high anchors and an intervening lower touch.
  - Added channel trend/direction-rule metadata, including `channel_trend_direction`, `channel_boundary_direction_mode`, `original_channel_entry_side`, and `effective_channel_entry_side`.
  - Exposed the new channel metadata through the saved-run service flattening path and frontend API type.
- Tests added or updated:
  - Uptrend upper-boundary LONG and lower-boundary SHORT unit tests.
  - Downtrend channel detection, upper-boundary LONG, and lower-boundary SHORT unit tests.
  - Action-builder integration tests for upper-boundary LONG and lower-boundary SHORT actions.
  - Backend service flattening test for the new channel direction metadata.
- Tests run:
  - `python -m py_compile quant_bitcoin/patterns/fvg_channel.py quant_bitcoin/backtesting/pattern_action_builder.py backend/quant_backtest_api/services/backtest_results.py`
  - `pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py backend/tests/test_backtest_results_service.py -q`
  - `npm --prefix frontend run typecheck`
  - `git diff --check`
- Codex self-review result:
  - Scope respected; no live trading, signed requests, credentials, account endpoints, or exchange order endpoints added.
  - Strategy changes stayed inside the assigned FVG v2 channel boundary rule.
- Known limitations:
  - The retest confirmation remains the existing close-back-inside rule; no new breakout/retest policy was introduced.
  - SHORT stop remains the upper channel line; symmetric retest-structure-high stop remains a separate follow-up candidate.
- Recommended next task:
  - Re-run the owner 2026-05-20+ FVG v2 channel backtest and inspect trade count, channel IDs, long/short side distribution, costs, and equity curve under the new channel-boundary rule.
