# Task 089: STRATEGY_ENGINE_LONG_SHORT_COST_ACCOUNTING

## Status
Planned (created by Codex, implementation not started)

## Goal
Upgrade `StrategyEngine` into the canonical long/short accounting engine and integrate transaction costs.

## Required Context
- `AGENTS.md`
- `STATUS.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/costs.py`
- `quant_bitcoin/strategies/actions.py`
- `tests/backtesting/test_strategy_engine.py`
- `tests/backtesting/test_strategy_engine_accounting.py`
- `tests/backtesting/test_costs.py`

## Problem
Current `StrategyEngine` is long-only and does not apply transaction-cost helpers.

## Required Design
Research-only linear signed-position accounting:
- LONG position -> positive quantity
- SHORT position -> negative quantity
- equity = cash + signed_position * mark_price

Document limitation explicitly:
- no borrow fees
- no futures funding
- no maintenance margin / liquidation model

## Required Implementation
- Extend `StrategyEngineConfig` with:
  - `transaction_cost_config: TransactionCostConfig | None = None`
  - `default_liquidity_role: LiquidityRole = LiquidityRole.TAKER`
  - `allow_short: bool = True`
- Update strategy execution/summaries with compatibility-preserving fields:
  - `raw_price`, `effective_price`
  - `fee_cost`, `spread_cost`, `slippage_cost`, `total_cost`
  - `gross_pnl`, `net_pnl`
  - `position_side`, `execution_side`
- Preserve backward-compatible fields where tests depend on them (`price`, `side`, `gross_pnl`, `net_pnl`).

## Cost Semantics
- `effective_price` includes spread/slippage impact.
- `fee_cost` is separately deducted from cash.
- `spread_cost` and `slippage_cost` are reporting metadata only and must not be deducted again.

## Engine Behavior
- Implement deterministic long + short open/close/partial-close behavior.
- Prevent automatic reversal by default.
- If opposite entry is received while position is open, skip deterministically with reason metadata.

## Out of Scope
- margin/funding/liquidation modeling
- live trading or exchange order calls
- pattern risk/exit action builder changes
- legacy cleanup

## Tests
Add/update tests for:
- long + short accounting at zero cost
- long + short profit/loss
- partial long + partial short exits
- deterministic opposite-entry skip behavior
- cost impacts: net PnL < gross PnL where costs apply
- fee deducted exactly once
- spread/slippage not double-counted
- drawdown behavior with short positions

## Acceptance Criteria
- `StrategyEngine` supports long + short semantic actions.
- Cost model integrated with clear non-double-counted semantics.
- Existing long tests still pass (or compatible updates made).
- Short tests pass.
- No live trading behavior added.
- `STATUS.md` and `PROJECT_HISTORY.md` updated.

## Verification
- `pytest -q tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_engine_accounting.py tests/backtesting/test_costs.py`
- `pytest -q`
- `git diff --check`
