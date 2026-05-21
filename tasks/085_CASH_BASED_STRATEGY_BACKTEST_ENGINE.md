# Task 085: Cash-Based Strategy Backtest Engine

## Area

Backtest/Core + Quant Research

## Goal

Implement a strategy-level backtest engine that uses actual simulated capital, converts strategy actions into `BUY`/`SELL` cashflows, and reports final cash/equity like the existing RSI backtest.

This task must solve the discovered issue where pattern trades can exist without meaningful `BUY`/`SELL` accounting.

## Source Requirement

The owner wants strategy-level backtests to behave like the RSI backtest:

```text
starting_cash exists
strategy buys/sells
cash changes
position changes
final equity is calculated
remaining capital is shown
```

## Current Problems To Fix

Current pattern persistence/accounting can be misleading:

1. Pattern trades are stored as `ENTRY`, not execution-level `BUY`/`SELL`.
2. `buy_count` and `sell_count` can remain zero.
3. Entry quantity can be incorrectly derived from final `remaining_quantity_ratio`.
4. Fully exited trades can become `quantity = 0` during persistence.
5. Graph points can repeat final cash/position instead of representing time-varying portfolio state.

This task must fix these issues at the strategy backtest engine level.

## Required Reading

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- this task document
- Task 080 architecture doc
- Task 081 risk package
- Task 082 strategy classes
- `quant_bitcoin/backtesting/basic.py`
- `quant_bitcoin/backtesting/equity_curve.py`
- `quant_bitcoin/backtesting/costs.py`
- `quant_bitcoin/backtesting/pattern_postgres_runner_cli.py`
- `quant_bitcoin/patterns/exit_simulation.py`

## Scope

Create a reusable strategy backtest engine.

Recommended files:

```text
quant_bitcoin/backtesting/strategy_engine.py
quant_bitcoin/backtesting/strategy_models.py
tests/backtesting/test_strategy_engine.py
```

## Required Accounting Model

The engine must maintain:

```text
cash
position_quantity
position_average_price or active_position metadata
realized_pnl
unrealized_pnl
equity
drawdown
```

For spot long-only mode:

```text
ENTER_LONG -> BUY
EXIT_LONG / PARTIAL_EXIT_LONG -> SELL
```

## Required Output Models

Minimum output:

```text
StrategyBacktestResult
StrategyBacktestSummary
StrategyExecution
StrategyEquityPoint
```

Summary must include:

```text
starting_cash
ending_cash
ending_position
final_price
final_equity
total_return
trade_count
buy_count
sell_count
win_count
loss_count
max_drawdown
gross_pnl
net_pnl
average_net_r
metadata
```

Execution row must include:

```text
timestamp
side: BUY | SELL
action_type
price
quantity
notional
cash_after
position_after
equity_after
reason
pattern_event_id
exit_reason
gross_pnl
net_pnl
realized_r_multiple
metadata
```

## Quantity Rule

Do not use final `remaining_quantity_ratio` as entry quantity.

Correct model:

```text
entry_quantity = sizing_policy(...)
exit_quantity = entry_quantity * exit_event.quantity_ratio
remaining_quantity = entry_quantity - sum(exit_quantities)
```

For fixed quantity mode:

```text
entry_quantity = trade_quantity
```

For future risk-based sizing:

```text
entry_quantity = min(
    equity * risk_fraction / risk_per_unit,
    cash / effective_entry_price
)
```

Risk-based sizing can be stubbed or added if small, but fixed quantity must work now.

## Cost Accounting Rule

If costs are included, avoid double-counting.

Allowed models:

```text
Model A:
use effective price for spread/slippage
deduct fees separately

Model B:
use raw price
deduct fee/spread/slippage total cost separately
```

Do not apply both effective spread/slippage price and spread/slippage cost deduction.

## Intrabar / Exit Reason Requirement

The engine must preserve exit reasons from risk/exit simulation:

```text
HARD_STOP
TAKE_PROFIT
SOFT_INVALIDATION
TIME_STOP
NO_EXIT
```

These are research diagnostics and must not be lost when converting to `SELL`.

## Out of Scope

- No live trading.
- No real order execution.
- No exchange APIs.
- No strategy optimization.
- No walk-forward runner.
- No frontend/backend dashboard changes.
- No futures or leverage.
- No short selling unless future task explicitly enables paper-short mode.

## Execution Steps

1. Define strategy backtest result models.
2. Implement cash/position/equity accounting.
3. Convert strategy actions into execution rows.
4. Support partial exits.
5. Support exit reasons.
6. Generate equity points over the candle timeline.
7. Ensure completed exits still create non-zero entry and exit quantities.
8. Add deterministic synthetic tests.

## Acceptance Criteria

- A strategy backtest with `starting_cash=10000` reports actual ending cash and final equity.
- A synthetic strategy that enters and exits creates at least one `BUY` and one `SELL`.
- `buy_count` and `sell_count` reflect execution rows.
- Fully exited trades do not become `quantity=0`.
- Equity curve changes over time when trades occur.
- Exit reasons are preserved.
- No exchange endpoints are called.
- No live trading behavior exists.

## Verification

Run:

```bash
pytest -q tests/backtesting/test_strategy_engine.py
pytest -q tests/strategies
pytest -q
git diff --check
```

## Required State Updates

- Update `STATUS.md`.
- Append completion to `PROJECT_HISTORY.md`.
- Update `BACKLOG.md` if follow-up research metrics are discovered.

## Completion Summary Required

Include:

- engine files added
- accounting model used
- BUY/SELL conversion behavior
- tests added
- tests run
- known limitations
- recommended next task
