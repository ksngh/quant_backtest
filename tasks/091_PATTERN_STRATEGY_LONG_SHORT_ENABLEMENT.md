# Task 091: PATTERN_STRATEGY_LONG_SHORT_ENABLEMENT

## Status
Completed (2026-05-22)

## Goal
Enable bearish pattern events to emit short semantic strategy actions instead of default skip behavior.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/patterns/order_block.py`
- `quant_bitcoin/patterns/trendline_break.py`
- pattern risk/exit planners

## Problem
`PatternStrategyBase.evaluate(...)` currently skips bearish pattern events by emitting `SHORT_DISABLED` behavior rather than producing short semantic entries.

## Required Implementation
- Update pattern direction mapping to explicit position semantics:
  - `BULLISH -> LONG`
  - `BEARISH -> SHORT`
- Add helper:
  - `pattern_direction_to_position_side(direction: str) -> "LONG" | "SHORT" | None`
- Update `PatternStrategyBase.evaluate(...)` behavior:
  - BULLISH direction: build long risk plan, emit `ENTER_LONG`
  - BEARISH direction: build short risk plan, emit `ENTER_SHORT`
  - Unknown direction: emit `SKIP` or return `[]`
- Remove/disable default `emit_short_disabled_skip` behavior after tests are updated.
- Preserve risk-plan validation requirements.
- Ensure action metadata includes:
  - `pattern_event_id`
  - `pattern_type`
  - `pattern_direction`
  - `position_side`
  - `entry_reference`
  - `stop_reference`
  - `target_reference`
  - `risk_plan`

## Out of Scope
- No exit-action implementation.
- No entry-fill simulation.
- No detector optimization.
- No legacy file removal.
- No live trading behavior.

## Tests
Add/update tests for:
- bullish FVG emits `ENTER_LONG`
- bearish FVG emits `ENTER_SHORT`
- bearish events no longer emit default `SHORT_DISABLED`
- same long/short behavior for Order Block or Trendline Break when fixtures are straightforward
- invalid risk plan emits `SKIP` or `[]`
- StrategyEngine short-action processing compatibility (after Task 089)

## Acceptance Criteria
- Bearish pattern events are not skipped solely due to bearish direction.
- Pattern strategy outputs use long/short semantics.
- Existing bullish behavior remains compatible.
- Tests pass.
- Safety boundary unchanged.
- `STATUS.md` and `PROJECT_HISTORY.md` are updated.

## Verification
- `pytest -q tests/backtesting/test_pattern_strategy_regressions.py`
- `pytest -q tests/backtesting/test_strategy_engine.py`
- `pytest -q`
- `git diff --check`
