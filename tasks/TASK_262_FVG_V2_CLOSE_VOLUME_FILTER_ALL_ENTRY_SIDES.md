# Task 262: FVG V2 Close Volume Filter All Entry Sides

# Goal

Extend the Task 261 close-candle volume entry filter so it applies to both FVG v2 channel LONG and SHORT entries, not only LONG/buy entries.

# Source Requirement

Owner clarified after seeing trades still occur with a high volume-ratio threshold:

```text
아니 숏 매수도 막아줘야지..
```

Clean requirement:

- Treat both LONG and SHORT channel entries as entry signals that must pass the completed close-candle volume filter.
- A high `--fvg-min-close-volume-ratio` should block low-volume entries on either side.
- Preserve explicit disable and threshold overrides from Task 261.

# Extracted Roles

- Owner role:
  - Clarifies that the volume gate must block short-side entries too.
- Supporting roles:
  - Strategy/backtest role: applies the existing close-volume filter to both entry sides.
  - CLI role: updates metadata/defaults/help text if side scope changes.
  - Metadata role: records that the filter applies to all FVG v2 channel entry sides.
  - Test role: adds short-side low-volume blocked and adequate-volume pass coverage.
- Forbidden roles:
  - Do not add live trading, exchange order execution, signed requests, credentials, account endpoints, or exchange order endpoints.
  - Do not change FVG channel geometry, close-based retest confirmation, target/stop math, or cost-aware filtering.
  - Do not implement 15m/1h multi-timeframe alignment in this task.

# Context

Task 261 implemented a close-volume entry filter with default owner-profile settings:

- enabled by default for the FVG owner profile
- prior-only baseline
- window `20`
- minimum volume ratio `1.0`
- fail closed on invalid/missing volume
- currently scoped to `LONG`

The owner now clarified that SHORT entries should be blocked by the same volume condition. This is a narrow behavior correction to the side scope of the existing filter.

# Scope

- Change the default close-volume filter side scope from `LONG` to all FVG v2 channel entry sides.
- Apply the filter to both `ENTER_LONG` and `ENTER_SHORT` candidates.
- Preserve the existing CLI flags:
  - `--enable-fvg-close-volume-filter`
  - `--disable-fvg-close-volume-filter`
  - `--fvg-close-volume-window`
  - `--fvg-min-close-volume-ratio`
  - `--fvg-close-volume-input-mode`
  - `--fvg-close-volume-baseline-mode`
- Update metadata to make the all-side scope explicit.
- Update tests and docs.

# Out of Scope

- No live trading.
- No exchange account/order endpoints.
- No credentials or `.env` changes.
- No new volume indicator math beyond using the existing Task 261 filter.
- No 15m/1h multi-timeframe entry alignment.
- No frontend UI changes unless metadata contract text needs updating.
- No database schema migration.

# Requirements

- With the filter enabled, both LONG and SHORT channel entries must be evaluated by the same completed signal-candle volume ratio rule.
- If the side is LONG or SHORT and volume ratio is below threshold:
  - emit a non-executable `SKIP`
  - use deterministic reason `LOW_CLOSE_VOLUME_ENTRY_FILTER`
  - do not emit an entry execution for that candidate
- If the side is LONG or SHORT and volume ratio passes:
  - preserve the entry and include pass metadata.
- Metadata should indicate the filter applies to all entry sides, for example `applies_to_side=ALL` or `applies_to_sides=["LONG","SHORT"]`.
- Explicit disable flag must bypass both sides.
- Existing Task 261 default threshold/window behavior must remain unchanged.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Read `quant_bitcoin/backtesting/pattern_action_builder.py`.
- [x] Read `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`.
- [x] Read Task 261 tests that cover LONG volume filtering.
- [x] Record assumptions, blockers, or unclear status items before coding.

Implementation note: side scope is represented as `applies_to_side=ALL` and
`applies_to_sides=["LONG", "SHORT"]`; the same prior-only close-volume rule is
applied to both channel entry sides.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- [x] Low-volume LONG entry candidates are still blocked.
- [x] Low-volume SHORT entry candidates are blocked.
- [x] Adequate-volume LONG and SHORT entry candidates are allowed.
- [x] `--disable-fvg-close-volume-filter` bypasses both sides.
- [x] Metadata clearly states all-side application.
- [x] Existing Task 259 close-based retest behavior remains unchanged except for side scope of the volume gate.
- [x] Existing Task 260/261 owner defaults remain active.
- [x] No live trading behavior or exchange order/account endpoint behavior is introduced.

# Required Tests

## Unit Tests

- [x] SHORT low-volume candidate emits `LOW_CLOSE_VOLUME_ENTRY_FILTER`.
- [x] SHORT adequate-volume candidate passes.
- [x] Disable flag/config bypasses both LONG and SHORT filtering.
- [x] Metadata side scope is `ALL` or otherwise clearly includes both sides.

## Integration Tests

- [x] CLI default close-volume filter config reports all-side scope.
- [x] Existing FVG channel and CLI tests pass.

## Contract Tests

- [x] Update README/API contract if side-scope metadata text changes.
- [x] No database schema change expected.

## Safety Tests

- [x] Confirm no live trading controls, signed requests, exchange order endpoints, account endpoints, credentials, or real exchange order behavior are introduced.

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
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/patterns/test_fvg_channel.py tests/indicators/test_volume_ratio.py -q
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
