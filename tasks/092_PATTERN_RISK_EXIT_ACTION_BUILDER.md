# Task 092: PATTERN_RISK_EXIT_ACTION_BUILDER

## Status
Planned (created by Codex, implementation not started)

## Goal
Create a canonical adapter that converts detected pattern events and risk/exit plans into executable strategy actions.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/risk/exit_plan.py`
- `quant_bitcoin/risk/exit_simulation.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/patterns/fair_value_gap_risk_exit.py`
- pattern-specific risk/exit planner modules

## Problem Explanation
Current pattern strategy wrappers typically emit only entry actions (`ENTER_LONG`/`ENTER_SHORT`) and do not map simulated risk/exit outcomes into canonical exit actions.

## Required Implementation
Create module:
- `quant_bitcoin/backtesting/pattern_action_builder.py`

Suggested public function:
- `build_pattern_trade_actions(event, risk_plan, future_candles, *, entry_action_timestamp, position_side, soft_invalidation=None) -> list[StrategyAction]`

Expected behavior:
1. Emit entry action:
   - long: `ENTER_LONG`
   - short: `ENTER_SHORT`
2. Run `simulate_pattern_exit(...)` on future candles.
3. Convert each `PatternExitEvent`:
   - long partial -> `PARTIAL_EXIT_LONG`
   - long final -> `EXIT_LONG`
   - short partial -> `PARTIAL_EXIT_SHORT`
   - short final -> `EXIT_SHORT`
4. Preserve metadata:
   - `pattern_event_id`
   - `pattern_type`
   - `exit_reason`
   - `target_name`
   - `stop_price`
   - `realized_r_multiple` (if available)
   - `risk_per_unit`
   - `entry_price`
   - `exit_price`
   - `quantity_ratio`
   - `remaining_quantity_ratio`

## Quantity Semantics
If exit simulation returns quantity ratios, map to strategy action quantity using base trade quantity when supplied. Initial implementation may emit ratios directly with documented scaling expectations.

## Out of Scope
- No entry fill/no-fill simulation.
- No detector logic changes.
- No transaction cost implementation here.
- No live trading behavior.

## Tests
Add/update tests for:
- long event emits `ENTER_LONG` + `EXIT_LONG`
- long event emits partial exits when multiple exit events exist
- short event emits `ENTER_SHORT` + `EXIT_SHORT`
- exit metadata preservation
- no-exit simulation behavior (entry-only or explicit policy metadata)
- invalid risk plan rejection/skip behavior

## Acceptance Criteria
- Pattern risk/exit plans are converted into canonical `StrategyAction` sequences.
- Long and short conversion paths are both supported.
- StrategyEngine can consume generated actions.
- Tests pass.
- `STATUS.md` and `PROJECT_HISTORY.md` are updated.

## Verification
- `pytest -q tests/backtesting/test_pattern_action_builder.py`
- `pytest -q tests/backtesting/test_strategy_engine.py`
- `pytest -q`
- `git diff --check`
