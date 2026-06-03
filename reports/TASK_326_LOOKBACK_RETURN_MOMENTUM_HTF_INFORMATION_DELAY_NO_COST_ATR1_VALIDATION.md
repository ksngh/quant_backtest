# Task 326: LOOKBACK_RETURN_MOMENTUM Higher-Timeframe Information-Delay No-Cost ATR-1 Validation

## Scope

This report executes the Task 326 higher-timeframe diagnostic for `LOOKBACK_RETURN_MOMENTUM` where data continuity allows it. The intended window is `2021-01-01T00:00:00Z <= candle time < 2026-06-01T00:00:00Z`. Because the current PostgreSQL runner loads `open_time <= --end-time`, executed runs used the last open time before the preferred exclusive end: `2026-05-31T20:00:00Z` for `4h` and `2026-05-31T00:00:00Z` for `1d`.

`1h` was not executed. Native Binance public `1h` candles in the fixed window have internal continuity gaps totaling 14 missing open times, and bounded public kline backfill attempts returned no candles for those open times. No synthetic candles were created and no candles were derived from another interval.

## Hypothesis

The tested hypothesis is that the same close-to-close lookback-return signal may align better with information-delay momentum on `1h`, `4h`, and `1d` than on prior minute-level windows. The validation is gross/no-cost only: fees, spread, slippage, and cost-aware entry filtering are all disabled.

## Theory and References

The theory follows `docs/strategy/lookback_return_momentum_v2.md`: delayed information diffusion, underreaction, slower position adjustment, order-flow continuation, and trend-following participation can unfold over hours or days. Jegadeesh and Titman (1993) and Moskowitz, Ooi, and Pedersen (2012) are used only as general momentum background, not as proof that this BTCUSDT implementation should work.

Internal references:

- `docs/strategy/lookback_return_momentum_v1.md`: original signal and no-lookahead mechanics.
- `docs/strategy/lookback_return_momentum_v2.md`: HTF V2 hypothesis, no-cost boundary, and predeclared grid.
- `tasks/TASK_324_LOOKBACK_RETURN_MOMENTUM_V2_NO_COST_ATR1_EXIT_VALIDATION.md`: short-timeframe V2 plan. The local V2 strategy doc/report/summary artifacts are still absent, so Task 324 numeric comparison remains owner-provided context rather than repository-backed stored metrics.

## Data Coverage

| interval | expected | rows | dup extra | gaps | missing | first | last | fixed window ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1h | 47448 | 47434 | 0 | 7 | 14 | 2021-01-01T00:00:00Z | 2026-05-31T23:00:00Z | no |
| 4h | 11862 | 11862 | 0 | 0 | 0 | 2021-01-01T00:00:00Z | 2026-05-31T20:00:00Z | yes |
| 1d | 1977 | 1977 | 0 | 0 | 0 | 2021-01-01T00:00:00Z | 2026-05-31T00:00:00Z | yes |

`1h` missing ranges: `2021-02-11T04:00:00Z`, `2021-03-06T02:00:00Z`, `2021-04-20T02:00:00Z`-`03:00:00Z`, `2021-04-25T05:00:00Z`-`07:00:00Z`, `2021-08-13T02:00:00Z`-`05:00:00Z`, `2021-09-29T07:00:00Z`-`08:00:00Z`, and `2023-03-24T13:00:00Z`.

## Command Template

Executed variants used this shape:

```bash
quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --source binance_spot --symbol BTCUSDT --interval <4h|1d> \
  --start-time 2021-01-01T00:00:00Z --end-time <last-open-before-exclusive-end> \
  --lookback-bars <grid> --holding-bars <grid> --entry-threshold <grid> \
  --risk-distance-mode atr --atr-period 14 --atr-smoothing RMA \
  --stop-loss-atr-multiple 1.0 --take-profit-atr-multiple 1.0 --minimum-atr-bps 0.0 \
  --maker-fee-bps 0 --taker-fee-bps 0 --spread-bps 0 --slippage-bps 0 \
  --minimum-slippage-bps 0 --volatility-slippage-multiplier 0 \
  --starting-cash 1000000 --starting-cash-currency KRW --quote-currency USDT --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction --position-sizing-value 0.10 \
  --research-task-id TASK_326 \
  --research-run-group lookback_return_momentum_v2_htf_no_cost_atr1 \
  --research-variant-id <variant_id> \
  --enforce-candle-continuity
```

## Predeclared Parameter Grid

| interval | variant | lookback | holding | threshold | status | run id |
| --- | --- | --- | --- | --- | --- | --- |
| 1h | 1h_1d_to_6h | 24 | 6 | 0.005 | blocked | blocked |
| 1h | 1h_3d_to_1d | 72 | 24 | 0.015 | blocked | blocked |
| 4h | 4h_1d_to_12h | 6 | 3 | 0.01 | executed | 1213 |
| 4h | 4h_3d_to_1d | 18 | 6 | 0.03 | executed | 1214 |
| 1d | 1d_1w_to_1d | 7 | 1 | 0.03 | executed | 1215 |
| 1d | 1d_1m_to_1w | 30 | 7 | 0.1 | executed | 1216 |

## Results

PnL and expectancy are reported in the engine quote-cash accounting unit after the configured `KRW -> USDT` conversion (`1,000,000 KRW / 1,500 = 666.6667 USDT` starting cash).

| interval | variant | run | candles | lookback | holding | threshold | candidates | accepted | completed | invalid ATR | net PnL | return | max DD | expectancy | PF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1h | 1h_1d_to_6h | blocked | 47434 | 24 | 6 | 0.005 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 1h | 1h_3d_to_1d | blocked | 47434 | 72 | 24 | 0.015 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 4h | 4h_1d_to_12h | 1213 | 11862 | 6 | 3 | 0.01 | 2752 | 2746 | 2746 | 6 | -69.33 | -10.40% | -13.25% | -0.0252 | 0.942 |
| 4h | 4h_3d_to_1d | 1214 | 11862 | 18 | 6 | 0.03 | 1621 | 1621 | 1621 | 0 | 98.83 | 14.82% | -4.96% | 0.0610 | 1.094 |
| 1d | 1d_1w_to_1d | 1215 | 1977 | 7 | 1 | 0.03 | 667 | 663 | 663 | 4 | 56.45 | 8.47% | -6.04% | 0.0851 | 1.125 |
| 1d | 1d_1m_to_1w | 1216 | 1977 | 30 | 7 | 0.1 | 271 | 271 | 271 | 0 | 144.29 | 21.64% | -3.57% | 0.5324 | 1.380 |

## Exit Mix

| variant | stop loss | take profit | time exit |
| --- | --- | --- | --- |
| 1h_1d_to_6h | n/a | n/a | n/a |
| 1h_3d_to_1d | n/a | n/a | n/a |
| 4h_1d_to_12h | 811 | 848 | 1087 |
| 4h_3d_to_1d | 663 | 735 | 223 |
| 1d_1w_to_1d | 63 | 104 | 496 |
| 1d_1m_to_1w | 101 | 134 | 36 |

## Side Attribution

| variant | long trades | long net PnL | long hit | short trades | short net PnL | short hit |
| --- | --- | --- | --- | --- | --- | --- |
| 1h_1d_to_6h | n/a | n/a | n/a | n/a | n/a | n/a |
| 1h_3d_to_1d | n/a | n/a | n/a | n/a | n/a | n/a |
| 4h_1d_to_12h | 1390 | -22.01 | 49.35% | 1356 | -47.32 | 46.68% |
| 4h_3d_to_1d | 850 | 45.24 | 52.35% | 771 | 53.58 | 51.49% |
| 1d_1w_to_1d | 352 | 10.47 | 49.43% | 311 | 45.97 | 51.45% |
| 1d_1m_to_1w | 156 | 50.05 | 53.21% | 115 | 94.23 | 57.39% |

## Yearly Attribution

| variant | year | trades | return | net PnL | avg R | hit | PF | max DD | SL/TP/Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1h_1d_to_6h | blocked | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 1h_3d_to_1d | blocked | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| 4h_1d_to_12h | 2021 | 591 | -4.10% | -27.34 | -0.0200 | 47.55% | 0.931 | -7.82% | 169/170/252 |
| 4h_1d_to_12h | 2022 | 525 | -2.20% | -14.86 | -0.0185 | 48.19% | 0.940 | -3.55% | 154/155/216 |
| 4h_1d_to_12h | 2023 | 428 | -1.58% | -9.84 | -0.0078 | 46.96% | 0.926 | -3.81% | 134/143/151 |
| 4h_1d_to_12h | 2024 | 527 | 2.79% | 17.15 | 0.0459 | 49.91% | 1.091 | -1.86% | 139/180/208 |
| 4h_1d_to_12h | 2025 | 467 | -5.24% | -33.32 | -0.0860 | 46.90% | 0.796 | -6.54% | 156/130/181 |
| 4h_1d_to_12h | 2026 | 208 | -0.20% | -1.12 | 0.0325 | 49.04% | 0.984 | -2.63% | 59/70/79 |
| 4h_3d_to_1d | 2021 | 402 | 5.72% | 38.89 | 0.0370 | 51.99% | 1.110 | -4.19% | 168/183/51 |
| 4h_3d_to_1d | 2022 | 308 | 6.09% | 41.37 | 0.0745 | 53.25% | 1.206 | -2.37% | 117/142/49 |
| 4h_3d_to_1d | 2023 | 212 | 2.90% | 21.65 | 0.1054 | 55.19% | 1.227 | -1.28% | 78/102/32 |
| 4h_3d_to_1d | 2024 | 330 | 2.91% | 22.35 | 0.0634 | 53.03% | 1.119 | -1.78% | 131/155/44 |
| 4h_3d_to_1d | 2025 | 248 | -2.36% | -18.65 | -0.0505 | 47.18% | 0.864 | -3.11% | 113/102/33 |
| 4h_3d_to_1d | 2026 | 121 | -0.88% | -6.79 | -0.0388 | 49.59% | 0.906 | -2.77% | 56/51/14 |
| 1d_1w_to_1d | 2021 | 145 | -4.50% | -29.99 | -0.0258 | 46.21% | 0.812 | -6.04% | 14/16/115 |
| 1d_1w_to_1d | 2022 | 120 | 5.47% | 32.65 | 0.0647 | 49.17% | 1.392 | -3.30% | 8/20/92 |
| 1d_1w_to_1d | 2023 | 104 | -0.31% | -2.10 | 0.0078 | 50.00% | 0.964 | -2.22% | 16/17/71 |
| 1d_1w_to_1d | 2024 | 132 | 4.21% | 28.08 | 0.0856 | 53.79% | 1.415 | -1.31% | 11/23/98 |
| 1d_1w_to_1d | 2025 | 112 | 2.29% | 15.17 | 0.0660 | 50.89% | 1.250 | -1.85% | 11/21/80 |
| 1d_1w_to_1d | 2026 | 50 | 1.78% | 12.64 | 0.0801 | 56.00% | 1.561 | -1.06% | 3/7/40 |
| 1d_1m_to_1w | 2021 | 60 | 10.79% | 71.53 | 0.1632 | 55.00% | 1.749 | -2.13% | 20/30/10 |
| 1d_1m_to_1w | 2022 | 53 | 3.98% | 27.32 | 0.1081 | 56.60% | 1.325 | -2.61% | 18/24/11 |
| 1d_1m_to_1w | 2023 | 50 | 3.99% | 30.24 | 0.2200 | 60.00% | 1.674 | -1.04% | 15/28/7 |
| 1d_1m_to_1w | 2024 | 53 | 1.95% | 18.37 | 0.0863 | 54.72% | 1.248 | -3.21% | 23/27/3 |
| 1d_1m_to_1w | 2025 | 37 | 1.18% | 9.59 | 0.0862 | 54.05% | 1.197 | -1.71% | 15/19/3 |
| 1d_1m_to_1w | 2026 | 18 | -1.55% | -12.77 | -0.2118 | 38.89% | 0.609 | -1.97% | 10/6/2 |

## Comparison Against Task 324

Task 324 local report artifacts are absent, so this report does not fabricate `1m`/`5m`/`15m` stored metrics. Using the owner-provided prior context, the earlier short-timeframe no-cost symmetric `1 ATR` family was weak or negative. In this Task 326 execution, the available `4h`/`1d` variants are materially different: three of four executed variants are positive gross/no-cost, and the best executed variant is `1d_1m_to_1w` with `21.64%` total return.

The comparison is incomplete because `1h` could not be executed over the fixed continuous native-candle window.

## Interpretation

The available `4h` and `1d` evidence supports the idea that the information-delay premise is better aligned with slower horizons than the prior minute-level tests. The strongest result is `1d_1m_to_1w`, where a one-month lookback and one-week hold returned `21.64%` gross/no-cost with `0` transaction cost.

This should be interpreted narrowly. The result is not a deployability claim because it ignores fees, spread, slippage, and cost-aware entry feasibility. It is also not a claim that all momentum strategies work. It says that, among the executed native-continuity variants, higher-timeframe close-to-close momentum is not rejected at the gross/no-cost diagnostic stage.

The side attribution is not perfectly symmetric. The positive variants have both long and short contribution, but the balance differs by variant, and the yearly table shows regime dependence. The result needs a cost-aware follow-up and then an OOS/WFO protocol before any stronger strategy decision.

## What This Can Reject

- `4h_1d_to_12h` is weak under the tested geometry: it produced `-10.40%` gross/no-cost and a negative average R.
- A blanket claim that higher timeframe is automatically better is not supported, because one executed `4h` variant was negative and `1h` was blocked.

## What This Cannot Reject

- It cannot reject `1h` momentum because the fixed native `1h` data window failed continuity preflight.
- It cannot reject all momentum strategies, because no volume, order-flow, risk-flow, macro synchronization, regime filter, or alternative momentum definition was tested.
- It cannot establish cost-aware profitability, because all transaction costs were deliberately set to zero.

## Known Limitations

- `1h` was blocked by native candle continuity gaps and was not executed.
- The persisted strategy metadata still records `strategy_version=v1`; Task 326 V2 identity is recorded through the V2 strategy document plus `research.task_id`, `research.run_group`, and `research.variant_id` metadata.
- The test is gross/no-cost only.
- The test uses one fixed historical window and no OOS/WFO split.
- Same-candle stop/take-profit ambiguity remains stop-first.

## Recommended Next Task

Create a cost-aware follow-up for only the positive `4h`/`1d` V2 variants, starting with `1d_1m_to_1w` and `4h_3d_to_1d`. The follow-up should reintroduce realistic fee/spread/slippage, preserve the same no-lookahead ATR logic, and then add an OOS/WFO or predeclared year-split validation before interpreting viability.

A separate data task is also needed if the owner wants a continuous `1h` 2021-2026 validation. It should decide whether official missing Binance `1h` periods are acceptable as gaps, whether to use a later continuous subwindow, or whether a tested lower-timeframe aggregation path is allowed.

## Verification

- `1h` data preflight: failed due 7 internal gaps / 14 missing native public kline open times.
- `4h` data preflight: passed, 11,862 continuous candles.
- `1d` data preflight: passed, 1,977 continuous candles.
- Persisted run IDs: `1213`, `1214`, `1215`, `1216`.
- No cost-aware entry filter was passed.
- All executed runs used zero fee, zero spread, zero slippage, and `--enforce-candle-continuity`.
- Compact summary JSON: `reports/task_326_htf_no_cost_atr1_summary.json`.
