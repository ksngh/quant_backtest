# Task 094: PATTERN_DETECTION_PERFORMANCE_OPTIMIZATION

## Status
Planned (created by Codex, implementation not started)

## Goal
Reduce pattern detection complexity during strategy backtests by avoiding repeated full-prefix detector execution.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/patterns/order_block.py`
- `quant_bitcoin/patterns/trendline_break.py`
- indicator modules: ATR, volume ratio, displacement, pivots

## Problem
Current action generation often evaluates each strategy on full candle prefixes (`strategy.evaluate(candles.iloc[:i])`), causing O(n²)-like detector rework on long 1m histories.

## Required Design
Introduce optimized evaluation path components.

Suggested modules:
- `quant_bitcoin/backtesting/indicator_cache.py`
- `quant_bitcoin/backtesting/pattern_detection_cache.py`

Suggested structures:
- `IndicatorCache` (ATR, volume ratio, displacement, pivots)
- `PatternEvaluationContext` with:
  - `candles`
  - `current_index`
  - `indicator_cache`
  - `seen_event_ids`
  - `portfolio_state`

Optional strategy API extension:
- `evaluate_at(context) -> list[StrategyAction]`

Keep existing `evaluate(candles_so_far)` temporarily for compatibility.

## FVG Optimization
Implement FVG-first optimization path:
- Precompute ATR once.
- Precompute volume ratio once.
- Precompute displacement once.
- At each step, evaluate only local indices around `current_index` (`current_index-2`, `current_index-1`, `current_index`).

Suggested helper:
- `detect_fair_value_gap_at_index(candles, indicator_cache, current_index, config)`

If detector internals are too invasive, implement a backtesting-only optimized extractor first.

## Order Block Optimization
If feasible in scope:
- Precompute displacement once.
- At `current_index`, validate displacement candle locally.
- Bound source search by configured `source_search_lookback`.

## Complex Pattern Handling
For higher-complexity patterns (Trendline/Cup/Diamond/Adam):
- Use bounded lookback windows.
- Reuse precomputed pivots.
- Limit candidate counts.

If too large for this task, document deferments and deliver FVG optimization first.

## Out of Scope
- No untested semantic changes to pattern logic.
- No intentional strategy-result changes beyond equivalent optimization behavior.
- No removal of legacy `evaluate(...)` in this task.
- No live trading behavior.

## Tests
Add/update tests to compare deterministic outputs between:
- existing prefix-based FVG event/action path
- optimized FVG path

Use synthetic deterministic candles.

Add performance-oriented verification if feasible:
- assert optimized path avoids full-detector-per-prefix behavior (e.g., counter/fake detector instrumentation).

## Acceptance Criteria
- Optimized evaluation path exists.
- FVG optimized outputs match existing prefix outputs on fixtures.
- No-look-ahead behavior preserved.
- Complex-pattern status remains correct or explicitly deferred.
- Tests pass.
- `STATUS.md` and `PROJECT_HISTORY.md` are updated.

## Verification
- `pytest -q tests/backtesting/test_pattern_detection_optimization.py`
- `pytest -q tests/backtesting/test_pattern_strategy_regressions.py`
- `pytest -q`
- `git diff --check`
