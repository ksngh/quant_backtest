# Task 227: EMA Multi-Timeframe Trend Score Indicator

# Goal

Add EMA-based trend features and a configurable composite multi-timeframe trend score that can summarize 1m, 5m, 15m, and later higher-timeframe trend agreement for FVG research.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - Indicator owner for EMA and multi-timeframe trend-score computation.
- Supporting roles:
  - Multi-timeframe candle contract role from Task 226.
  - Pattern detector role.
  - Backtest diagnostics role.
  - Test fixture role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

The intended FVG retest strategy should not treat every FVG equally. Direction should be filtered or scored by trend context. This task adds the trend-score primitive but does not yet change FVG strategy behavior by default.

# Scope

- Add `quant_bitcoin/indicators/ema.py` or equivalent with deterministic EMA calculation and timing metadata.
- Add `MultiTimeframeTrendScoreConfig` with configurable timeframes, EMA fast/slow periods, slope lookback, and per-timeframe weights.
- Use Task 226 aligned higher-timeframe candles as input for 5m/15m features.
- Compute per-timeframe directional components: close-vs-EMA, fast-vs-slow, fast EMA slope, and optional slow EMA slope.
- Compute a composite score in a bounded range such as `[-1.0, 1.0]`, where positive favors long/FVG bullish context and negative favors short/FVG bearish context.
- Emit detailed score component metadata so diagnostics can explain why a score is bullish, bearish, neutral, or unavailable.

# Out of Scope

- No FVG filtering behavior in this task.
- No automatic strategy optimization or best-parameter selection.
- No higher-timeframe data fetching from external APIs.
- No frontend/API display unless metadata contracts are explicitly required by tests.

# Requirements

- EMA calculation must be deterministic, pandas-compatible, and safe for completed-candle research.
- The indicator must expose timing metadata: required warmup, current-candle inclusion semantics, and higher-timeframe availability caveat.
- Composite scoring must be transparent: output must include per-timeframe score, weight, direction, and missing-data reason.
- Default weights must be conservative and documented; proposed default is 1m=0.20, 5m=0.30, 15m=0.50 for FVG v2 research, but implementation must allow override.
- Neutral/unavailable scores must not be coerced into bullish or bearish alignment.
- The indicator must not import pattern strategy, risk, execution, persistence, or exchange modules.

# Status Tracking

## Execution Notes

- Assumption: EMA trend features are current-completed-candle indicators and are safe only after candle close.
- Assumption: higher-timeframe score components use Task 226 completed candle `close_time` availability, not duplicated aligned close values as new candles.
- Blockers: none for Task 227.
- Safety: implementation is offline indicator code only with no strategy behavior change, network access, exchange imports, order/account calls, keys, or `.env` behavior.

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

- Added deterministic EMA fast/slow, slope, warm-up, and timing metadata in `quant_bitcoin/indicators/ema.py`.
- Added diagnostic-only `multitimeframe_trend_score_v1` composite scoring with per-timeframe metadata in `quant_bitcoin/indicators/multitimeframe_trend_score.py`.
- Added tests for bullish, bearish, neutral, mixed, missing-context, weight validation, and Task 226 alignment integration.
- Updated `docs/26_INDICATOR_TIMING_CONTRACT.md`.
- Verification:
  - `pytest tests/indicators/test_ema.py tests/indicators/test_multitimeframe_trend_score.py`
  - `pytest tests/backtesting/test_multitimeframe_candles.py`

# Acceptance Criteria

- EMA fast/slow and slope fields are available for a single timeframe.
- Composite multi-timeframe score is available when aligned higher-timeframe candles are supplied.
- Missing 5m/15m context produces explicit missing metadata rather than false neutral agreement.
- Known bullish, bearish, and mixed synthetic datasets produce expected score signs and components.
- No existing pattern strategy behavior changes unless a later task opts in.

# Required Tests

## Unit Tests

- `tests/indicators/test_ema.py` covers EMA values, slope signs, warmup, invalid periods, and metadata.
- `tests/indicators/test_multitimeframe_trend_score.py` covers bullish, bearish, neutral, missing-context, and mixed-timeframe score cases.
- Weight validation tests reject negative weights and all-zero weight configs.

## Integration Tests

- Integration test with Task 226 alignment: 1m input produces 1m/5m/15m trend components without look-ahead.
- Optional shared indicator-cache test if the trend score is cached.

## Contract Tests

- Document trend-score metadata schema in indicator docs or API docs if exposed through strategy output later.
- Record that the score is diagnostic by default and not an auto-trading signal.

## Safety Tests

- Static safety test confirms no exchange/order/account imports.
- No external network call dependency.

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
pytest tests/indicators/test_ema.py tests/indicators/test_multitimeframe_trend_score.py
pytest tests/backtesting/test_multitimeframe_candles.py
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
