# Goal

Change the default FVG close-volume entry filter thresholds so the owner profile requires stronger completed-candle volume by default.

# Source Requirement

Owner requested:

1. Make the volume ratio default require at least `2.0x`.
2. Set the low-volume/거래량 기준 to `0.5x`.

# Extracted Roles

- Owner role: Defines default research thresholds for FVG close-volume entry filtering.
- Supporting roles:
  - Strategy CLI/profile: Applies the new owner default values.
  - Close-volume entry filter: Uses the configured threshold and records metadata.
  - Volume ratio diagnostics: Records low-volume threshold metadata where applicable.
  - Tests: Verify defaults, explicit overrides, and metadata.
- Forbidden roles:
  - Live trading or real order execution.
  - Exchange order/account endpoint calls.
  - Frontend/dashboard work unless a later task explicitly assigns it.
  - Changing unrelated pattern detector volume thresholds.

# Context

Tasks 261 and 262 added the FVG v2 close-volume entry filter and applied it to both LONG and SHORT entries. The current owner profile default uses:

- `enable_fvg_close_volume_filter = True`
- `fvg_close_volume_window = 20`
- `fvg_min_close_volume_ratio = 1.0`
- `fvg_close_volume_baseline_mode = prior_only`
- `fvg_close_volume_input_mode = base_volume`

The owner now wants a stricter default volume ratio threshold and a clear `0.5x` low-volume diagnostic threshold.

# Scope

- Change the owner/default FVG close-volume minimum ratio from `1.0` to `2.0`.
- Preserve explicit CLI override behavior:
  - `--fvg-min-close-volume-ratio <value>` must still override the default.
- Record the new default in owner-profile metadata and FVG v2 settings metadata.
- Add or update metadata so the low-volume diagnostic threshold is `0.5`.
- Keep the filter applied to both LONG and SHORT FVG v2/channel entries.
- Update tests that assert default close-volume settings.

# Out of Scope

- Live trading.
- Real Binance order execution.
- Changing Order Block volume thresholds.
- Changing Fair Value Gap detector middle-candle volume thresholds unless explicitly required by implementation tests.
- Changing market-regime volume thresholds.
- UI work.

# Requirements

- Default owner profile must set:
  - `fvg_min_close_volume_ratio = 2.0`
  - low-volume threshold/diagnostic 기준 = `0.5`
- `quant-bitcoin-strategy-backtest --pattern FAIR_VALUE_GAP` default owner profile should report the new values in metadata.
- Existing explicit CLI override must continue to work:
  - `--fvg-min-close-volume-ratio 1.0`
  - `--fvg-min-close-volume-ratio 5.0`
- The close-volume filter should still fail closed on invalid/missing volume data.
- Existing skip reason remains:
  - `LOW_CLOSE_VOLUME_ENTRY_FILTER`
- Metadata must make it clear that:
  - threshold `2.0` means current completed candle volume must be at least 2x the prior baseline;
  - threshold `0.5` marks/diagnoses low-volume status at half of the baseline.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read Tasks 261 and 262 and the current close-volume filter implementation before changing defaults.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Default FVG owner profile uses `fvg_min_close_volume_ratio=2.0`.
- Close-volume filter metadata reports the 2x threshold.
- Low-volume diagnostic/status threshold uses `0.5`.
- Explicit CLI overrides still win over the default.
- LONG and SHORT FVG v2/channel entries are still filtered consistently.
- No live trading behavior or exchange order endpoint usage is introduced.

# Required Tests

## Unit Tests

- Close-volume config builder default returns `minimum_volume_ratio=2.0`.
- Low-volume diagnostic threshold metadata is `0.5`.
- Explicit CLI override returns the requested ratio.

## Integration Tests

- Owner FAIR_VALUE_GAP parser/profile default records `fvg_min_close_volume_ratio=2.0`.
- A candle with ratio below 2.0 is blocked by default.
- A candle with ratio at or above 2.0 is allowed by default.
- Existing LONG and SHORT side coverage remains valid with updated thresholds.

## Contract Tests

- Runtime/FVG v2 metadata reports the new default threshold.
- Workflow settings or owner default profile metadata exposes the applied value.

## Safety Tests

- No real exchange order/account endpoint calls.
- No API keys required.

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

Default targeted verification:

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q
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

# Completion Notes

- Completed (2026-05-28): FVG close-volume defaults now require `minimum_volume_ratio=2.0` and record/use `low_volume_ratio_threshold=0.5`.
- Explicit CLI overrides such as `--fvg-min-close-volume-ratio 1.25` remain preserved by tests.
- Targeted verification passed:
  - `pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q`
