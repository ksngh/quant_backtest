# Task 228: FVG Detector Trend Score and EMA Filter Integration

# Goal

Wire EMA and multi-timeframe trend-score metadata into FVG detection so bullish/bearish FVG events can be diagnosed, scored, or optionally filtered by aligned 1m/5m/15m trend context.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - FVG detector owner for trend-aware event metadata and optional trend filter behavior.
- Supporting roles:
  - Indicator role from Task 227.
  - Pattern score metadata role.
  - Strategy/backtest role.
  - Test fixture role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

The existing FVG detector already uses ATR, displacement, volume ratio, pivots, support/resistance, and swing-structure features. It does not yet encode EMA or multi-timeframe trend agreement. This task integrates the trend primitive into FVG events without silently changing the existing baseline.

# Scope

- Extend `FairValueGapConfig` with trend-score options, for example `use_multitimeframe_trend_score`, `require_trend_alignment`, `minimum_bullish_trend_score`, and `maximum_bearish_trend_score`.
- Add optional `trend_score_config` or `ema_config` fields without breaking existing defaults.
- Attach event metadata such as `mtf_trend_score`, `mtf_trend_direction`, `mtf_trend_aligned`, `ema_fast`, `ema_slow`, and per-timeframe score components.
- Adjust executable/diagnostic pattern score components only when the trend feature is enabled or supplied.
- Support both diagnostic-only mode and hard-filter mode.
- Keep default behavior equivalent to current FVG detection when trend settings are not enabled.

# Out of Scope

- No Fibonacci confluence logic; that is Task 229.
- No entry-mode or retest trigger changes; that is Task 230.
- No liquidity target or exit-policy changes; those are Tasks 231 and 232.
- No live/paper trading behavior.

# Requirements

- Bullish FVG alignment should pass when the composite trend score is above the configured bullish threshold and fail when materially bearish.
- Bearish FVG alignment should pass when the composite trend score is below the configured bearish threshold and fail when materially bullish.
- Unavailable trend context must be represented explicitly and must not pass a required filter by accident.
- All new event fields must be serializable by existing metadata JSON helpers.
- Existing no-lookahead FVG tests must remain valid.
- Trend-related score components must include source labels and limitations consistent with existing score metadata conventions.

# Status Tracking

## Execution Notes

- Assumption: trend scoring remains default-off for FVG detection and only affects metadata/filtering when explicitly enabled or supplied.
- Assumption: `mtf_trend_score` stores the signed composite score, while the score component uses a bounded alignment-quality value for existing score metadata compatibility.
- Blockers: none for Task 228.
- Safety: no live trading, network, exchange, order/account, key, `.env`, or default strategy behavior changes were added.

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [x] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

## Completion Notes

- Extended FVG config/event metadata with opt-in multi-timeframe trend score diagnostics and hard-filter support.
- Added trend-aware score component metadata with default score weight `0.0` to preserve baseline FVG scoring unless later tasks explicitly change policy.
- Propagated trend metadata through canonical pattern action metadata.
- Updated FVG strategy documentation for default-off trend fields.
- Verification:
  - `pytest tests/patterns/test_fair_value_gap.py tests/backtesting/test_pattern_action_builder.py`
  - `pytest tests/indicators/test_ema.py tests/indicators/test_multitimeframe_trend_score.py`
  - `pytest tests/patterns/test_no_lookahead_contract.py`

# Acceptance Criteria

- FVG events include trend-score metadata when trend scoring is enabled.
- Trend filter can block bullish FVG in bearish multi-timeframe context and bearish FVG in bullish context.
- Diagnostic-only mode records trend data but does not filter events.
- Default FVG config emits the same events as before for deterministic fixture data.
- Skip/filter reasons are explainable in event metadata or diagnostics.

# Required Tests

## Unit Tests

- `tests/patterns/test_fair_value_gap.py` adds bullish aligned, bullish rejected, bearish aligned, bearish rejected, missing-trend, and default-unchanged cases.
- Pattern score metadata tests cover trend component presence and limitations.
- Serialization test confirms trend metadata is JSON-ready.

## Integration Tests

- Backtest action-building test confirms trend metadata propagates from raw event to canonical action metadata.
- Optional cache integration test if FVG detection cache carries trend features.

## Contract Tests

- Update FVG strategy docs or API metadata notes only for the added fields and default-off behavior.
- Confirm existing API contracts remain backward compatible when trend scoring is disabled.

## Safety Tests

- No exchange/order/account imports or API key handling.
- No default strategy behavior change without explicit config or CLI opt-in.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are deterministic and covered by tests.
- No look-ahead behavior is introduced.
- Documentation/API notes are updated when behavior or metadata changes.

# Verification

Default:

```bash
pytest tests/patterns/test_fair_value_gap.py tests/backtesting/test_pattern_action_builder.py
pytest tests/indicators/test_ema.py tests/indicators/test_multitimeframe_trend_score.py
pytest
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
