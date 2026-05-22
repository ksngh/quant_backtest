# Task 093: ENTRY_FILL_INTRABAR_INTEGRATION

## Status
Planned (created by Codex, implementation not started)

## Goal
Integrate entry fill simulation and intrabar sequencing policy into pattern action generation so pattern backtests handle fill/no-fill outcomes and OHLC ambiguity more realistically.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `quant_bitcoin/patterns/entry_simulation.py`
- `quant_bitcoin/backtesting/intrabar_policy.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/risk/exit_simulation.py`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/backtesting/strategy_engine.py`

## Problem
Pattern entries currently tend to assume immediate execution at confirmation timestamp/close, while many pattern workflows require limit-style entry semantics and explicit handling of ambiguous OHLC path ordering.

## Required Implementation
Extend pattern action builder inputs to include:
- `entry_config: PatternEntryConfig`
- `entry_mode: PatternEntryMode`
- `intrabar_policy_config: IntrabarPolicyConfig`
- `max_wait_bars: int`

Flow requirements:
1. Pattern event confirmed.
2. Build entry plan.
3. Simulate entry fill on future candles.
4. If `NOT_FILLED` / `CANCELLED` / `INVALID`: emit policy-defined skip diagnostic or no trade.
5. If `FILLED`: emit `ENTER_LONG` / `ENTER_SHORT` at fill timestamp.
6. Start exit simulation after fill candle.
7. Resolve ambiguous same-candle entry/stop/target ordering with configured intrabar policy.
8. Emit exit actions.

## Required Metadata
No-fill diagnostics:
- `pattern_event_id`
- `entry_mode`
- `entry_status`
- `bars_waited`
- `reason`

Filled-trade metadata:
- `fill_price`
- `fill_timestamp`
- `fill_candle_index`
- `entry_mode`
- `intrabar_policy`

## Out of Scope
- No tick-level path reconstruction.
- No order book data integration.
- No live trading/order execution.
- No detector optimization.

## Tests
Add/update tests for:
- FVG midpoint limit fill emits entry action.
- FVG midpoint unfilled path emits no entry or explicit SKIP diagnostics per policy.
- `max_wait_bars` enforcement.
- Conservative intrabar policy resolves stop/target ambiguity against optimistic outcome.
- Short entry fill support.
- Entry metadata preservation.

## Acceptance Criteria
- Pattern backtests distinguish filled vs unfilled entries.
- Entry assumptions are explicit and test-covered.
- Intrabar policy is actively used in pattern action generation path.
- Tests pass.
- `STATUS.md` and `PROJECT_HISTORY.md` are updated.

## Verification
- `pytest -q tests/backtesting/test_pattern_action_builder.py`
- `pytest -q tests/patterns/test_entry_simulation.py`
- `pytest -q tests/backtesting/test_intrabar_policy.py`
- `pytest -q`
- `git diff --check`
