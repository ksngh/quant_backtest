# Task 299: LOOKBACK_RETURN_MOMENTUM Initial Validation

## Scope

- Strategy: `LOOKBACK_RETURN_MOMENTUM` v1.
- Strategy document read before execution: `docs/strategy/lookback_return_momentum_v1.md`.
- Code changes: none.
- Parameter tuning/search: none.
- Candle backfill or candle DB mutation: none.
- Interpretation: research-only.

## Verification Summary

- Focused tests: `13 passed`.
- Data preflight:
  - `BTCUSDT` `1m`: available, `216771` closed candles, `2026-01-01T00:00:00Z` to `2026-05-31T12:50:00Z`, `0` duplicate open-time groups, `0` gaps.
  - `BTCUSDT` `5m`: unavailable, `0` closed candles. Skipped as required.
  - `BTCUSDT` `15m`: available, `14452` closed candles, `2026-01-01T00:00:00Z` to `2026-05-31T12:45:00Z`, `0` duplicate open-time groups, `0` gaps.
- Validation window used for runs: `2026-05-20T00:00:00Z` to `2026-05-28T08:15:00Z`.
- Execution assumptions:
  - `--cost-profile conservative_crypto_1m`
  - `--enforce-candle-continuity`
  - `--starting-cash 1000000 --starting-cash-currency KRW --krw-per-usdt 1500`
  - effective quote starting cash: `666.6667` USDT
  - `--position-sizing-mode cash_fraction --position-sizing-value 0.10`
  - short results are simulated cash-bounded research accounting only.

## Default Parameters Tested

| Interval | lookback_bars | entry_threshold | holding_bars | risk_distance_pct | stop_loss_r | take_profit_r |
|---|---:|---:|---:|---:|---:|---:|
| `1m` | 20 | 0.001 | 5 | 0.002 | 1.0 | 1.5 |
| `15m` | 8 | 0.002 | 4 | 0.002 | 1.0 | 1.5 |

`5m` defaults were not run because local `BTCUSDT` `5m` closed candles are missing.

## Results

| Interval | Run ID | Candles | Trade rows | Completed trades | Gross PnL | Net PnL | Total return | Net win rate | Profit factor | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1m` | 1160 | 12016 | 2570 | 1285 | -0.7767 | -253.3047 | -37.9957% | 0.00% | 0.0000 | -37.9957% |
| `15m` | 1161 | 802 | 339 | 169 | -0.0390 | -45.6451 | -6.8468% | 0.00% | 0.0000 | -6.8468% |

## Cost Breakdown

| Interval | Fees | Spread | Slippage | Total cost |
|---|---:|---:|---:|---:|
| `1m` | 136.1029 | 40.8309 | 75.5942 | 252.5280 |
| `15m` | 21.7926 | 6.5378 | 17.2757 | 45.6061 |

## Exit Reason Breakdown

| Interval | Stop loss | Take profit | Time exit |
|---|---:|---:|---:|
| `1m` | 65 | 42 | 1178 |
| `15m` | 72 | 43 | 54 |

## Interpretation

This first bounded validation rejects any immediate profitability claim. Both runs are research-only diagnostics, and both are strongly cost-dominated under `conservative_crypto_1m` assumptions.

The `1m` run generated many trades, but nearly all completed trades exited by time exit and transaction costs drove net PnL to `-253.3047` USDT. The `15m` run traded less frequently but still finished negative after costs. The saved diagnostics also flagged negative expectancy, low hit rate, high cost drag, high turnover, drawdown weakness, and short-simulation-only limitations.

No strategy promotion is justified from these runs.

## Blockers And Limitations

- `5m` validation is blocked by missing local `BTCUSDT` `5m` candles.
- A full available `1m` run from `2026-01-01` to `2026-05-31` was started first but interrupted during payload preparation before persistence because the full-window output was unnecessarily large for this initial bounded task. No Task 299 full-window run was persisted.
- The selected bounded window is a first diagnostic window, not an out-of-sample or walk-forward protocol.
- The net win rate and profit factor are lifecycle net metrics after costs; take-profit exits still may be net-negative after costs in the persisted attribution.

## Commands Run

```bash
python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q
```

Validation was run through the existing `quant_bitcoin.backtesting.strategy_postgres_runner_cli` path with the parameters and assumptions listed above.

## Recommended Next Task

Execute Task 300 if the owner wants the daily-report template/style rule update next. If the owner wants to continue this momentum strategy, create a separate future task for either `5m` candle backfill execution or a locked OOS/WFO validation/diagnostic follow-up; do not tune this strategy inside Task 299.
