# Task 248: FVG V2 Channel Retest Entry And Boundary Exit

# Goal

Use the Task 247 channel geometry to add opt-in FVG v2 channel retest entries and channel-boundary exits, with stops and take-profits based on the drawn channel lines instead of ATR.

# Source Requirement

Owner requirement:

- When price touches and retests the upper channel line, enter SHORT.
- When price touches and retests the lower channel line, confirm the close candle and enter LONG.
- Stop lines are the drawn channel lines.
- For LONG, exit at the upper line.
- For SHORT, exit at the lower line.
- Do not use ATR as the stop basis for this channel mode.

# Extracted Roles

- Owner role:
  - Strategy behavior owner for channel-based FVG v2.
- Supporting roles:
  - Backtest strategy role: owns entry action generation from channel retests.
  - Risk/exit role: owns line-based stop/target simulation.
  - Metadata role: owns entry/exit reason fields and boundary line diagnostics.
  - Test role: owns deterministic entry/exit fixtures and same-candle ambiguity tests.
- Forbidden roles:
  - Do not add frontend drawing here.
  - Do not add backend API/persistence changes here unless necessary metadata already flows through existing paths.
  - Do not add live trading, order endpoints, account endpoints, credentials, or real exchange calls.

# Context

Current FVG v2 risk planning can use ATR-buffered FVG boundaries or swing pivots. The owner now wants a separate channel mode where the drawn line itself is the risk boundary and the opposite line is the target. This should be opt-in and default-off so existing FVG and FVG v2 behavior remains unchanged.

# Scope

- Add a default-off channel mode for FVG v2.
- Consume valid channel geometry from Task 247.
- Define retest touch rules:
  - upper-line touch means candle high reaches or crosses `upper_line(index)`,
  - lower-line touch means candle low reaches or crosses `lower_line(index)`.
- Define close confirmation:
  - SHORT: after upper touch, close back below upper line confirms rejection.
  - LONG: after lower touch, close back above lower line confirms support.
- Generate entry actions only after confirmation, not before.
- For active positions, compute dynamic boundary prices per candle index:
  - LONG stop = lower line at that candle index,
  - LONG target = upper line at that candle index,
  - SHORT stop = upper line at that candle index,
  - SHORT target = lower line at that candle index.
- Replace ATR stop calculation for this mode only.
- Preserve explicit metadata:
  - `entry_boundary`,
  - `entry_retest_touch_index`,
  - `entry_confirmation_index`,
  - `stop_boundary`,
  - `target_boundary`,
  - `line_stop_price`,
  - `line_target_price`,
  - `channel_geometry`,
  - same-candle ambiguity reason when both boundary exit conditions occur.

# Out of Scope

- Do not remove existing ATR-buffered FVG stop modes.
- Do not make channel mode default.
- Do not add frontend overlays here.
- Do not persist new API fields here unless existing metadata persistence already carries them.
- Do not add market-order/live-order behavior.

# Requirements

- Channel mode must be explicitly enabled by configuration/CLI.
- Existing FVG v2 behavior must remain unchanged when channel mode is disabled.
- ATR must not determine stop or target in channel mode.
- Exit prices must be calculated from the channel lines at the evaluated candle index.
- Stop/target hit checks must use candle high-low against the dynamic line price.
- The same-candle stop/target policy must be explicit and deterministic.
- Metadata must make it clear that the stop/target came from channel lines, not ATR.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read Task 247 and confirm channel geometry is available.
- [ ] Read this assigned task file before coding.
- [ ] Confirm no frontend/API work is included.

## After Implementation

- [ ] Update `STATUS.md` if project state changed.
- [ ] Append a concise completion note to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- With channel mode enabled, LONG entries can be created from lower-line retest confirmation.
- With channel mode enabled, SHORT entries can be created from upper-line retest confirmation.
- LONG exits at upper line and stops at lower line.
- SHORT exits at lower line and stops at upper line.
- ATR does not set stop or target in channel mode.
- Existing FVG v2 tests pass with channel mode disabled.

# Required Tests

## Unit Tests

- LONG lower-line touch and close confirmation fixture.
- SHORT upper-line touch and close confirmation fixture.
- LONG target hit at upper line.
- LONG stop hit at lower line.
- SHORT target hit at lower line.
- SHORT stop hit at upper line.
- Same-candle boundary ambiguity fixture.
- Disabled-mode regression test.

## Integration Tests

- Run targeted FVG v2 backtest tests.
- Run strategy-engine tests that cover execution metadata and persistence payload generation if touched.

## Contract Tests

- Verify entry/exit metadata names are stable and JSON-serializable.

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
pytest tests/patterns tests/backtesting
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

- Added default-off `--enable-fvg-v2-channel` CLI wiring and channel config metadata.
- Added channel retest entries and dynamic line-boundary exits through `build_fvg_channel_trade_actions()` without ATR-derived channel-mode stop/target prices.
- Added LONG/SHORT entry, target, stop, same-candle ambiguity, CLI metadata, and action-builder tests.
