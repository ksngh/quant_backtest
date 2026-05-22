# Task 097: CANONICAL_BACKTEST_REGRESSION_AND_RESEARCH_TEST_SUITE

## Status
Planned (created by Codex, implementation not started)

## Goal
Add regression and research-utility tests validating completed canonical backtest refactor outcomes across accounting, costs, pattern actions, optimization, and persistence.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/backtesting/pattern_detection_cache.py` (if present)
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/strategies/rsi_actions.py` (if present)
- `quant_bitcoin/backtesting/multiple_testing.py`
- `docs/15_RESEARCH_PROTOCOL.md`
- `docs/21_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md`

## Required Test Areas
### 1) Long/Short Accounting
- long win
- long loss
- short win
- short loss
- partial long exit
- partial short exit
- deterministic handling of opposite entry while open

### 2) Cost-Aware Accounting
- zero-cost net equals gross
- non-zero fee reduces net
- spread/slippage impact is not double-counted
- cost metadata preserved

### 3) RSI Canonical Path
- RSI strategy emits actions
- RSI CLI uses StrategyEngine
- RSI persistence uses canonical adapter

### 4) Pattern Long/Short Path
- bullish FVG creates long action sequence
- bearish FVG creates short action sequence
- bearish pattern is not skipped solely due to short-disabled behavior
- risk/exit plan produces actual exit actions

### 5) Entry Fill / No-Fill
- limit entry fill creates execution
- no-fill creates no trade or explicit diagnostic
- max wait bars respected

### 6) Intrabar Ambiguity
- conservative mode is not favorable vs optimistic
- optimistic mode can differ
- ambiguity count/metadata is exposed where available

### 7) Detection Optimization
- optimized FVG output matches prefix detector on fixtures
- no-look-ahead preserved

### 8) Persistence / API Readiness
- `StrategyBacktestResult` persists to graph tables
- graph points use non-placeholder equity when canonical equity exists
- trades preserve action type and position-side metadata

### 9) Multiple Testing Utility Smoke
- deterministic variant counts
- threshold helper behavior validation

## Out of Scope
- no new strategy feature implementation
- no live trading
- no dashboard UI changes
- no DB schema redesign

## Acceptance Criteria
- Test coverage includes all required areas or explicitly documents deferments.
- Full `pytest` passes.
- Regression tests fail when canonical guarantees regress (bearish skip regression, ignored costs, missing exits, optimized detector output drift, placeholder equity persistence regressions).
- `STATUS.md` and `PROJECT_HISTORY.md` are updated.

## Verification
- `pytest -q`
- `python -m compileall quant_bitcoin`
- `git diff --check`
