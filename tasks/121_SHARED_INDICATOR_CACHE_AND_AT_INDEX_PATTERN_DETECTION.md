# Shared Indicator Cache And At-Index Pattern Detection

# Goal

Optimize the canonical pattern backtest path by eliminating repeated full-prefix indicator and pattern recalculation.

This is the highest-priority implementation task after profiling. The canonical pattern backtest must evaluate only events confirmed at the current candle index and must reuse shared indicators computed once per candle set.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/pattern_detection_cache.py`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/patterns/order_block.py`
- `quant_bitcoin/patterns/trendline_break.py`
- `quant_bitcoin/patterns/cup_and_handle.py`
- `quant_bitcoin/patterns/diamond.py`
- `quant_bitcoin/patterns/adam_and_eve.py`
- `quant_bitcoin/indicators/atr.py`
- `quant_bitcoin/indicators/volume_ratio.py`
- `quant_bitcoin/indicators/displacement_candle.py`
- `quant_bitcoin/indicators/pivots.py`
- related tests in `tests/backtesting/`, `tests/patterns/`, and `tests/indicators/`

# Extracted Roles

- Owner role:
  - Pattern backtest optimization owner.
  - Responsible for the canonical in-memory detection loop and shared indicator reuse.

- Supporting roles:
  - Indicator role:
    - Provides reusable ATR, volume-ratio, displacement, and pivot data.
  - Pattern detection role:
    - Provides at-index event detection for each pattern.
  - Strategy role:
    - Converts current-index events into semantic strategy actions.
  - Test role:
    - Verifies behavior equivalence and no-look-ahead behavior.

- Forbidden roles:
  - No persistence changes in this task.
  - No frontend changes.
  - No live trading.
  - No exchange order/account endpoints.
  - No API keys.
  - No broad rewrite of unrelated strategy code.

# Context

Current likely bottleneck is repeated evaluation of each candle prefix:

```text
for i in range(1, len(candles) + 1):
    strategy.evaluate(candles.iloc[:i])
```

This causes repeated calculation of:

- ATR;
- volume ratio;
- displacement candles;
- pivots;
- pattern candidates.

For 400 candles this can still become slow, especially for pivot-heavy patterns. For larger runs it will scale poorly.

The canonical path should shift from full-prefix batch detection to at-index detection:

```text
build shared indicator cache once
for current_index in range(candle_count):
    detect events confirmed at current_index only
    emit actions
```

# Scope

- Build a shared indicator cache for canonical pattern backtests.
- Reuse precomputed:
  - normalized candles;
  - ATR rows;
  - volume-ratio rows;
  - displacement rows;
  - pivot rows.
- Add or extend a context object that all pattern strategies can use.
- Implement at-index detection for lightweight patterns first:
  - Fair Value Gap;
  - Order Block.
- Extend canonical pattern strategy evaluation to prefer at-index detection.
- Preserve existing batch detectors for research and compatibility.
- Ensure no future candles are used for current-index decisions.
- Ensure duplicate event ids are filtered early.

# Out of Scope

- Pivot-heavy deep candidate pruning beyond basic at-index path.
- Runtime persistence.
- Frontend/API display.
- S/L and T/P lifecycle changes.
- Cost accounting changes.
- New pattern types.
- DB schema changes.

# Requirements

- Create or extend a shared cache type, for example:

```python
@dataclass
class PatternIndicatorCache:
    candles: pd.DataFrame
    atr_rows: pd.DataFrame
    volume_ratio_rows: pd.DataFrame
    displacement_rows: pd.DataFrame
    pivot_rows: pd.DataFrame
```

- The cache must be built once per candle set.
- The cache must not mutate caller data.
- Canonical pattern backtest must not recalculate full indicators for every candle.
- At-index detection must emit only events whose confirmation/end/breakout index is the current index.
- Fair Value Gap at-index detection must evaluate only the current 3-candle window and cached indicators.
- Order Block at-index detection must evaluate only current displacement candle and bounded source lookback.
- Preserve stable event ids.
- Preserve deterministic event ordering.
- Add early duplicate suppression via `seen_event_ids`.
- Existing batch detectors must continue to work unless explicitly replaced by tests.

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

- Canonical pattern backtest builds shared indicator cache once per run.
- Fair Value Gap canonical evaluation no longer recalculates ATR/volume/displacement per prefix.
- Order Block canonical evaluation no longer recalculates ATR/volume/displacement per prefix.
- Current-index event detection emits only current-index events.
- Previously detected event ids are not recomputed and then filtered late when avoidable.
- Representative fixtures produce the same valid events as batch detection for the same confirmation index.
- Runtime for 400-candle FVG and Order Block backtests is materially reduced.
- No-look-ahead behavior is preserved.

# Required Tests

## Unit Tests

- Test shared indicator cache construction.
- Test cache construction does not mutate source candles.
- Test FVG at-index detection emits expected event at current index.
- Test FVG at-index detection emits no event before confirmation index.
- Test Order Block at-index detection emits expected event at current displacement index.
- Test Order Block at-index detection respects source search lookback.
- Test duplicate event ids are not emitted twice.

## Integration Tests

- Run canonical `FAIR_VALUE_GAP` pattern backtest on fixture candles.
- Run canonical `ORDER_BLOCK` pattern backtest on fixture candles.
- Confirm action count and event ids match expected fixture output.
- Confirm runtime metadata or profiling output shows cache is used once.

## Contract Tests

- Standard candle contract remains:
  - `timestamp`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`
- Batch detectors remain usable.
- At-index detectors do not fetch market data.
- At-index detectors do not execute trades.
- At-index detectors do not persist results.

## Safety Tests

- Confirm no exchange order/account/private endpoints are called.
- Confirm no API keys are loaded.
- Confirm no signed requests are made.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Indicators are computed once per run where intended.
- At-index detector does not inspect future candles.
- Existing batch detector behavior remains covered.

# Verification

Default:

```bash
pytest
```

Recommended targeted tests:

```bash
pytest tests/backtesting/test_pattern_detection_cache.py
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
pytest tests/patterns/test_fair_value_gap.py
pytest tests/patterns/test_order_block.py
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
- runtime before
- runtime after
- cache design summary
- no-look-ahead confirmation
- Codex self-review result
- known limitations
- recommended next task
