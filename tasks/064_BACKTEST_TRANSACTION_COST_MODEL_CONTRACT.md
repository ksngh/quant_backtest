# Task 064: Backtest Transaction Cost Model Contract

## Purpose
Define a reusable, pure, deterministic transaction-cost model contract for historical backtests so future RSI and pattern workflows can move from gross to net evaluation without violating existing architecture and safety boundaries.

## Scope
- Add `quant_bitcoin/backtesting/costs.py` with:
  - `ExecutionSide` enum (`BUY`, `SELL`),
  - `LiquidityRole` enum (`MAKER`, `TAKER`),
  - `TransactionCostConfig` dataclass,
  - `TransactionCostBreakdown` dataclass,
  - pure helpers `basis_points_to_decimal(...)`, `effective_execution_price(...)`, and `calculate_transaction_cost(...)`.
- Add deterministic tests in `tests/backtesting/test_costs.py` covering validation and expected arithmetic.
- Keep change contract-only (no integration rewrite for current backtest engines).

## Out Of Scope
- No live trading or real order execution.
- No API keys, signed requests, or exchange order endpoint calls.
- No integration into `BasicBacktester` or pattern strategy backtest in this task.
- No market-data spread fetches or dynamic execution adapters.

## Required Deliverables
1. `quant_bitcoin/backtesting/costs.py` created with pure deterministic behavior.
2. `tests/backtesting/test_costs.py` created with focused coverage.
3. `STATUS.md` updated with completion summary and recommended next step.
4. `PROJECT_HISTORY.md` appended with a concise completion note.

## Acceptance Criteria
- Config rejects negative and non-finite values.
- Price and quantity validation reject non-positive or non-finite values.
- BUY effective execution price increases from spread/slippage.
- SELL effective execution price decreases from spread/slippage.
- Maker/taker fee selection is role-aware.
- Breakdown includes `gross_notional`, `fee_cost`, `spread_cost`, `slippage_cost`, `total_cost`, `effective_price`.
- Optional volatility-adjusted slippage multiplier works with a minimum slippage floor.
- Existing relevant tests continue to pass.

## Verification
- `pytest tests/backtesting/test_costs.py`
- `pytest tests/backtesting/test_basic_backtest.py tests/backtesting/test_pattern_strategy_backtest.py`
- `pytest` (if feasible)
- `git diff --check`

## Notes
This task creates only the reusable contract and pure helpers required for later net-backtest integration phases.
