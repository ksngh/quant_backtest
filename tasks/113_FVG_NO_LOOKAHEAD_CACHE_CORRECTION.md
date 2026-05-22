# Goal

Remove look-ahead bias from the optimized Fair Value Gap detection/cache path.

At candle index `i`, FVG detection must depend only on candles up to and including index `i`. Future candles must not affect whether an FVG event is emitted, whether it is valid, or whether it is skipped at that historical point.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/pattern_detection_cache.py`
- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- existing FVG tests under `tests/patterns/` and `tests/backtesting/`

# Extracted Roles

- Owner role:
  - Pattern detection / backtesting correctness owner.
  - Owns no-look-ahead correctness for FVG detection in rolling backtests.
- Supporting roles:
  - Indicator cache role: precomputes indicator data without leaking future lifecycle state.
  - Pattern strategy role: evaluates events at current index only.
  - Test role: proves future candles cannot alter current event emission.
- Forbidden roles:
  - No strategy optimization.
  - No new FVG algorithm design beyond no-look-ahead correction.
  - No exchange calls.
  - No execution or position accounting changes.

# Context

The optimized FVG path builds `IndicatorCache.for_fvg(candles, ...)` over the full candle frame. `detect_fair_value_gap_at_index(...)` then calls `_evaluate_fair_value_gap(...)`, which can classify FVG lifecycle state by inspecting candles after the event candle. If the full frame is passed into this logic, future candles can suppress or alter a historical event.

This is a classic look-ahead bias. It can make a backtest unrealistically avoid FVGs that are later filled or broken.

# Scope

- Ensure FVG detection at `current_index` uses only candles through `current_index`.
- Preserve indicator caching where safe.
- Avoid recalculating all indicators unnecessarily if a safe cached implementation is possible.
- Add regression tests specifically targeting future-candle mutation.
- Keep detector output deterministic.

# Out of Scope

- Changing FVG economic rules.
- Adding liquidity or spread modules.
- Changing Order Block, Trendline, Cup and Handle, Diamond, or Adam and Eve logic unless tests reveal the same class of bug.
- Full lifecycle integration.
- Transaction-cost accounting.

# Requirements

- `detect_fair_value_gap_at_index(...)` must not pass future candles to lifecycle-sensitive evaluation logic.
- Future candles after `current_index` must not affect:
  - event existence;
  - event id;
  - direction;
  - pattern status;
  - entry reference;
  - stop reference;
  - target reference;
  - pattern score at that index.
- If FVG state classification requires later candles, it must be disabled or limited to the visible prefix during historical evaluation.
- The optimized path must produce the same event as the non-optimized rolling-prefix path for the same visible prefix.
- Add explicit tests for bullish and bearish FVG cases.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Modifying candles after index `i` does not change FVG event output at index `i`.
- A future fill does not remove a historical FVG event at the confirmation candle.
- A future break does not remove a historical FVG event at the confirmation candle.
- Optimized FVG evaluation and rolling-prefix FVG evaluation match for current-index detection.
- Existing FVG tests continue to pass.

# Required Tests

## Unit Tests

- Test bullish FVG event is emitted at confirmation candle even if future candle fills the gap.
- Test bearish FVG event is emitted at confirmation candle even if future candle fills the gap.
- Test bullish FVG event is emitted at confirmation candle even if future candle breaks the gap.
- Test event id remains stable when future candles are modified.
- Test optimized cache output equals rolling-prefix output at each evaluated index.

## Integration Tests

- Test canonical pattern action build for FVG does not change when future candles are appended after the event window.
- Test FVG backtest fixture can produce the expected event without requiring future candles.

## Contract Tests

- FVG detector remains pure and does not mutate input candles.
- Indicator cache does not expose future lifecycle state to current-index evaluation.
- Standard candle schema remains unchanged.

## Safety Tests

- No exchange calls are introduced.
- No external data is fetched for FVG detection.

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
pytest
```

# Additional Verification

```bash
pytest tests/backtesting/test_pattern_strategy_regressions.py
pytest tests/patterns/test_fair_value_gap.py
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
