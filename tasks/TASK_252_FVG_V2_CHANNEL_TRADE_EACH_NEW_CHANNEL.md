# Task 252: FVG V2 Channel Trade Each New Channel

# Goal

Update opt-in FVG v2 channel mode so the strategy can trade whenever a new valid channel appears, instead of effectively producing only one channel-mode trade over the run.

# Source Requirement

Owner clarification:

- The intent is not repeated trading inside the same channel.
- The strategy should continue scanning and trade whenever a new channel becomes visible.
- Each valid newly formed channel should be eligible for its own retest entry and exit.

# Extracted Roles

- Owner role:
  - Defines channel-mode trade frequency semantics.
- Supporting roles:
  - Backtest strategy role: owns scanning for newly visible channels and generating independent trade candidates.
  - Deduplication role: owns avoiding duplicate trades for the same channel/event/timestamp.
  - Engine integration role: owns compatibility with open-position blocking and chronological action order.
  - Metadata role: owns channel identifiers and reasons for skipped/duplicate candidates.
  - Test role: owns fixtures with multiple distinct channels.
- Forbidden roles:
  - Do not implement same-channel repeated re-entry in this task.
  - Do not change baseline FVG or non-channel FVG v2 behavior.
  - Do not add live trading, order endpoints, account endpoints, credentials, or real exchange calls.
  - Do not bypass strategy-engine open-position safety without an explicit task.

# Context

Tasks 247-251 added FVG v2 channel geometry, channel retest entries/exits, frontend overlays, and LONG retest structure stops. Current action generation expands an FVG raw action into one channel candidate and the channel helper returns the first retest/exit for that candidate. In practice this can result in only one filled channel-mode trade for a run. The owner wants the system to continue evaluating later newly visible channels and trade those separately.

# Scope

- Define a stable channel identity for deduplication, for example based on:
  - lower anchor indices,
  - upper touch index,
  - window end index,
  - slope/intercept/width hash.
- Continue scanning across later FVG events / detection points so each new valid channel can generate a candidate trade.
- Ensure a new channel is not silently discarded because a previous channel already produced a trade.
- Preserve engine-level rule that entries are blocked while a position is open.
- Emit metadata for channel candidate identity and skip/duplicate reasons.
- Keep same-channel repeated entries out of scope.
- Preserve Task 251 LONG stop semantics:
  - LONG stop = retest structure low,
  - LONG target = upper channel line.

# Out of Scope

- No pyramiding or multiple simultaneous positions.
- No repeated trading of the same channel after one exit.
- No frontend layout redesign.
- No database schema migration unless existing metadata cannot carry channel identity.
- No live trading or order/account endpoints.

# Requirements

- Channel mode must remain explicitly opt-in.
- Existing FVG behavior must remain unchanged when channel mode is disabled.
- Multiple distinct channels in one candle range must be able to produce multiple trade action pairs, subject to chronological position constraints.
- Same channel must not generate duplicate trades from repeated FVG raw actions.
- Skipped duplicate/new-channel/open-position cases must be diagnosable from metadata or execution reasons.
- Channel identity metadata must be JSON-safe.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read this assigned task file before coding.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [x] Read `quant_bitcoin/patterns/fvg_channel.py`.
- [x] Confirm whether multi-channel scanning belongs in `_build_actions()`/dedupe state or the channel helper.

## After Implementation

- [x] Update `STATUS.md` if project state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- A deterministic fixture with two distinct valid channels produces two eligible channel trade candidates.
- A duplicate detection of the same channel does not produce a duplicate trade.
- If the first channel trade is still open when a later channel entry timestamp occurs, the engine blocks the overlapping entry with existing open-position behavior.
- If the first channel trade has exited before the later channel entry timestamp, the later channel can fill.
- Metadata includes channel identity and duplicate/skip reason where applicable.
- Task 251 LONG structure-stop behavior remains intact.

# Required Tests

## Unit Tests

- Channel identity metadata is stable for the same geometry.
- Multiple distinct channel fixture produces multiple candidate action pairs.
- Duplicate same-channel fixture emits one trade candidate and one duplicate skip/diagnostic.

## Integration Tests

- Strategy runner/action-builder test where two distinct channels generate two completed trades when non-overlapping.
- Engine test or existing engine regression verifying open-position blocking still applies.

## Contract Tests

- Verify metadata field names for channel identity and duplicate reason.

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
pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q
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
  - `tests/patterns/test_fvg_channel.py`
  - `tests/backtesting/test_pattern_action_builder.py`
  - `tasks/TASK_252_FVG_V2_CHANNEL_TRADE_EACH_NEW_CHANNEL.md`
  - `STATUS.md`
  - `PROJECT_HISTORY.md`
  - `BACKLOG.md`
- Implementation summary:
  - Added stable FVG channel identity and `channel_id` metadata.
  - Added channel-level dedupe so the same drawn channel emits one candidate and duplicate detections produce a diagnosable `FVG_CHANNEL_DUPLICATE` skip.
  - Updated the FVG channel runner path to keep scanning each visible candle prefix for new channel geometry instead of relying only on raw FVG events.
  - Preserved Task 251 LONG retest structure-low stop behavior and existing single-position engine blocking.
- Tests added or updated:
  - Stable channel identity coverage.
  - Duplicate channel skip metadata coverage.
  - Multi-channel scanner coverage.
  - Non-overlapping distinct-channel engine fill coverage.
- Tests run:
  - `pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py -q`
  - `pytest tests/backtesting/test_pattern_postgres_runner_cli.py -q`
  - `git diff --check`
- Codex self-review result:
  - Scope respected; no live trading, credentials, order endpoints, or unrelated architecture changes added.
- Known limitations:
  - Channel mode remains single-position at the engine level; overlapping new-channel entries are still blocked by existing `ENTRY_BLOCKED_OPEN_POSITION` / `OPPOSITE_ENTRY_BLOCKED` behavior.
  - Same-channel repeated re-entry after an exit remains out of scope.
- Recommended next task:
  - Run the 2026-05-20+ opt-in channel-mode backtest and inspect trade count, channel overlays, duplicate skips, and cost metadata end to end.
