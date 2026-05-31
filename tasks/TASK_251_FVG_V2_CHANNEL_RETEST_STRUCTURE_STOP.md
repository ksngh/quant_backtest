# Task 251: FVG V2 Channel Retest Structure Stop

# Goal

Update the opt-in FVG v2 channel mode so a LONG retest entry uses the pre-entry retest structure low as the stop, instead of the lower channel line. Preserve the channel upper line as the LONG target/exit line.

# Source Requirement

Owner clarification:

- If a LONG is entered after a retest, the stop line should be the local low immediately before/around the retest confirmation, not the channel lower line.
- The sell/take-profit line after a LONG entry should still be based on the drawn upper channel line.

# Extracted Roles

- Owner role:
  - Defines the trading semantics for FVG v2 channel retest risk.
- Supporting roles:
  - Backtest strategy role: owns changing channel-mode stop selection.
  - Exit simulation role: owns checking candle high/low against the new structure stop and existing channel target.
  - Metadata role: owns clear stop-source and stop-price fields for API/frontend inspection.
  - Test role: owns deterministic fixtures for retest structure-stop behavior.
- Forbidden roles:
  - Do not change baseline FVG or non-channel FVG v2 behavior.
  - Do not add live trading, order endpoints, account endpoints, credentials, or real exchange calls.
  - Do not add frontend execution controls.

# Context

Tasks 247-250 added opt-in FVG v2 parallel-channel detection, channel retest entries, dynamic channel-boundary exits, saved metadata, and frontend overlays. Task 248 originally defined LONG stop as the lower channel line and SHORT stop as the upper channel line. The owner has now refined the LONG stop rule: after a lower-line retest confirms a LONG, the stop should be the retest structure low immediately before/around confirmation.

# Scope

- Add a deterministic retest structure-stop resolver for channel-mode LONG entries.
- For a LONG retest entry:
  - identify the local retest low from the candle sequence immediately before and/or including the retest confirmation candle,
  - set `line_stop_price` or equivalent executable stop price to that structure low,
  - set metadata such as `stop_source=RETEST_STRUCTURE_LOW` and `retest_structure_low`.
- Keep LONG target/exit as the upper channel line at each evaluated candle index.
- Keep channel geometry metadata available for frontend drawing.
- Clarify metadata so the frontend can display:
  - channel lower/upper lines,
  - retest structure stop price,
  - upper-line target price.
- Decide and document whether SHORT should analogously use a retest structure high as stop. If implemented, it must be explicit and tested.

# Out of Scope

- Do not change channel detection geometry.
- Do not change cost/slippage/fee logic.
- Do not change persistence schema unless existing JSON metadata cannot carry the new fields.
- Do not add live trading behavior.
- Do not change the dashboard layout beyond consuming metadata already exposed by channel mode, unless a frontend task explicitly requires a visual stop marker refinement.

# Requirements

- Channel mode must remain explicitly opt-in.
- Existing FVG behavior must remain unchanged when channel mode is disabled.
- ATR must not determine the channel-mode retest structure stop.
- LONG stop hit checks must use the resolved retest structure low.
- LONG target hit checks must continue to use the upper channel line at the evaluated candle index.
- Stop metadata must be explicit enough to distinguish:
  - `CHANNEL_LOWER_LINE`,
  - `RETEST_STRUCTURE_LOW`.
- If no valid retest structure low can be resolved, the trade must be skipped or marked invalid with a deterministic reason.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read this assigned task file before coding.
- [ ] Read `quant_bitcoin/patterns/fvg_channel.py`.
- [ ] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [ ] Confirm whether SHORT gets an analogous structure-high stop or remains channel-line stop.

## After Implementation

- [ ] Update `STATUS.md` if project state changed.
- [ ] Append a concise completion note to `PROJECT_HISTORY.md`.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- LONG channel-mode entries use the retest structure low as stop.
- LONG channel-mode target/exit still uses the upper channel line.
- Metadata exposes stop source and retest structure low.
- Existing channel geometry overlay metadata remains backward compatible.
- Existing non-channel FVG tests continue to pass.

# Required Tests

## Unit Tests

- LONG lower-line retest fixture where stop equals retest structure low, not lower channel line.
- LONG stop hit fixture using structure low.
- LONG target hit fixture using upper channel line.
- Missing/invalid structure-low fixture emits deterministic skip/invalid reason.
- If SHORT structure-high stop is implemented, add symmetric SHORT tests.

## Integration Tests

- Run targeted FVG channel action-builder tests.
- Run strategy-engine execution metadata tests if action metadata changes.

## Contract Tests

- Verify metadata field names for `stop_source`, `retest_structure_low`, executable stop price, and upper-line target price.

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
pytest tests/patterns/test_fvg_channel.py tests/backtesting/test_pattern_action_builder.py -q
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

- LONG channel retest entries now resolve `retest_structure_low` from the retest sequence and use it as the executable stop.
- LONG target/exit remains the upper channel line at the evaluated candle index.
- Metadata now distinguishes `stop_source=RETEST_STRUCTURE_LOW` from channel-line geometry and exposes structure-stop fields through the saved-run trade API.
- SHORT stop behavior intentionally remains the existing upper channel line; create a follow-up task if symmetric retest structure-high stops are desired.
