# Task 088: STRATEGY_ACTION_LONG_SHORT_CONTRACT

## Status
Planned (created by Codex, implementation not started)

## Goal
Refactor the strategy action contract from long-only buy/sell-like semantics into explicit long/short position semantics while keeping execution-side semantics separate.

## Scope
- Update `quant_bitcoin/strategies/actions.py` to include:
  - `ENTER_SHORT`
  - `EXIT_SHORT`
  - `PARTIAL_EXIT_SHORT`
- Keep existing action types:
  - `ENTER_LONG`
  - `EXIT_LONG`
  - `PARTIAL_EXIT_LONG`
  - `SKIP`
- Add helper mappings/functions for action classification and side resolution:
  - `is_entry_action(action_type)`
  - `is_exit_action(action_type)`
  - `position_side_for_action(action_type)`  # LONG / SHORT / None
  - `execution_side_for_action(action_type)` # BUY / SELL / None
- Update `quant_bitcoin/backtesting/strategy_models.py` with compatibility-preserving side fields:
  - add `execution_side`
  - add `position_side`
  - keep `side` as compatibility alias where current tests rely on it
- Add/update tests for enum existence, helper mappings, and `SKIP` behavior.
- Ensure strategy engine tests continue to import and run.

## Out of Scope
- No short accounting implementation in `StrategyEngine` yet.
- No bearish pattern strategy behavior activation yet.
- No RSI strategy changes.
- No legacy cleanup/removal.
- No cost model implementation.
- No live trading behavior.

## Acceptance Criteria
- Long and short action contract exists.
- Existing long-only tests still pass (or are updated compatibly).
- No engine accounting behavior expansion beyond harmless compatibility fields.
- No exchange/order integration introduced.
- `STATUS.md` and `PROJECT_HISTORY.md` updated at completion.

## Verification Plan
- `pytest -q tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_engine_accounting.py`
- `pytest -q`
- `git diff --check`
