# Task 067: Portfolio Equity Curve Engine

## Goal
Implement a reusable, pure portfolio equity curve engine for historical backtests so research workflows can analyze candle-by-candle equity, drawdown, and mark-to-market exposure independently from strategy execution logic.

## Scope
- Add a generic backtesting equity-curve module under `quant_bitcoin/backtesting/`.
- Support standard candle data and generic trade-like rows.
- Keep compatibility with existing `BacktestTrade` from `quant_bitcoin.backtesting.basic`.
- Add focused unit tests for deterministic curve and drawdown behavior.

## Out of Scope
- Sharpe, Sortino, Calmar, or full performance metric suites.
- New transaction-cost modeling logic (only consume already supplied trade/cost values).
- Live trading, exchange APIs, persistence schema changes, or dashboard/report rendering.

## Requirements
1. Create `quant_bitcoin/backtesting/equity_curve.py` with reusable dataclasses:
   - `EquityCurvePoint`
   - `EquityCurveResult`
   - `EquityCurveConfig`
   - optional helper position state dataclass when useful
2. Implement pure functions:
   - `build_equity_curve_from_trades(candles, trades, starting_cash, mark_to_market=True, config=...)`
   - `calculate_drawdown_series(equity_points)`
3. Required behavior:
   - Validate standard candle schema and ascending timestamps.
   - Accept empty trade lists.
   - Support empty candle input when explicitly allowed by config.
   - Accept trade-like entries with timestamp, side/signal, price, quantity, optional cost.
   - Include per-point fields: timestamp, close_price, cash, position_quantity, position_market_value, equity, drawdown, trade_marker.
   - Mark-to-market uses candle close prices when enabled.
   - Do not mutate caller candle or trade inputs.
4. Compatibility:
   - Consume `BacktestTrade` directly when provided.
   - Keep pattern-trade conversion as a caller boundary and document it.
5. Tests:
   - Add `tests/backtesting/test_equity_curve.py`.
   - Cover no trades, one buy + one sell, long mark-to-market, close position, drawdown determinism, missing columns, unsorted timestamps, and non-mutation.

## Acceptance Criteria
- Deterministic equity curve is built for empty and non-empty trade scenarios.
- Drawdown series is deterministic and derived from equity high-water mark.
- Validation fails for missing standard columns and unsorted candles.
- Existing backtesting tests continue to pass.
- New tests pass for all required scenarios.

## Verification
- `pytest tests/backtesting/test_equity_curve.py`
- `pytest tests/backtesting/test_basic_backtest.py tests/backtesting/test_pattern_strategy_backtest.py`
- `pytest` (full suite if feasible)
- `git diff --check`
