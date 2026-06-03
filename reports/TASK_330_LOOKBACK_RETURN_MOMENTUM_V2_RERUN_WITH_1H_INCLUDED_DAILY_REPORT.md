# Task 330: LOOKBACK_RETURN_MOMENTUM V2 Rerun With 1h Included Daily Report

## Scope

Reran the active V2 higher-timeframe validation with `1h`, `4h`, and `1d` all included. The preferred full window still had native `1h` continuity gaps after bounded public backfill attempts, so the selected execution window is the predeclared common continuous fallback:

```text
2023-03-25T00:00:00Z <= candle time < 2026-06-01T00:00:00Z
```

## Data Coverage

Full-window `1h` still has 7 internal gaps / 14 missing open times. The selected fallback window has zero gaps for `1h`, `4h`, and `1d`.

| interval | selected expected | selected rows | selected gaps | selected missing | first | last |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 1h | 27936 | 27936 | 0 | 0 | 2023-03-25T00:00:00Z | 2026-05-31T23:00:00Z |
| 4h | 6984 | 6984 | 0 | 0 | 2023-03-25T00:00:00Z | 2026-05-31T20:00:00Z |
| 1d | 1164 | 1164 | 0 | 0 | 2023-03-25T00:00:00Z | 2026-05-31T00:00:00Z |


## Backfill Attempt

Attempted bounded Binance public `1h` backfill for the 7 full-window missing ranges. Each attempt returned `stored_candles=0`, so no full-window repair occurred. No synthetic candles or derived intervals were created.

## Command Shape

All runs used zero fee/spread/slippage, disabled cost-aware entry filtering, `ATR(14, RMA)`, `1 ATR` stop, `1 ATR` take-profit, signal-close entry, next-candle exit checks, and `--enforce-candle-continuity`.

## Variant Label Guide

Variant labels use this order:

```text
candle interval / lookback horizon / maximum holding horizon
```

For example, `1h_1d_to_6h` means the backtest uses `1h` candles, computes the signal from the last `1d` close-to-close return, and exits no later than `6h` after entry if neither the `1 ATR` stop nor the `1 ATR` take-profit is reached first.

| variant | meaning | lookback bars | holding bars |
| --- | --- | ---: | ---: |
| 1h_1d_to_6h | 1h candles, last 1 day return -> next max 6 hours | 24 | 6 |
| 1h_3d_to_1d | 1h candles, last 3 days return -> next max 1 day | 72 | 24 |
| 4h_1d_to_12h | 4h candles, last 1 day return -> next max 12 hours | 6 | 3 |
| 4h_3d_to_1d | 4h candles, last 3 days return -> next max 1 day | 18 | 6 |
| 1d_1w_to_1d | 1d candles, last 1 week return -> next max 1 day | 7 | 1 |
| 1d_1m_to_1w | 1d candles, last 1 month return -> next max 1 week | 30 | 7 |

## Results

| interval | variant | run | candles | lookback | holding | threshold | candidates | accepted | completed | invalid ATR | gross PnL | net PnL | cost | return | max DD | avg R | hit | PF |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1h | 1h_1d_to_6h | 1217 | 27936 | 24 | 6 | 0.005 | 5783 | 5783 | 5783 | 0 | -82.40 | -82.40 | +0.00 | -12.36% | -13.15% | -0.031 | +47.95% | 0.928 |
| 1h | 1h_3d_to_1d | 1218 | 27936 | 72 | 24 | 0.015 | 4112 | 4112 | 4112 | 0 | -60.58 | -60.58 | +0.00 | -9.09% | -10.44% | -0.035 | +48.05% | 0.939 |
| 4h | 4h_1d_to_12h | 1219 | 6984 | 6 | 3 | 0.01 | 1521 | 1517 | 1517 | 4 | -29.63 | -29.63 | +0.00 | -4.44% | -7.39% | -0.013 | +47.99% | 0.946 |
| 4h | 4h_3d_to_1d | 1220 | 6984 | 18 | 6 | 0.03 | 845 | 845 | 845 | 0 | +10.68 | +10.68 | +0.00 | +1.60% | -4.96% | 0.023 | +51.24% | 1.026 |
| 1d | 1d_1w_to_1d | 1221 | 1164 | 7 | 1 | 0.03 | 365 | 363 | 363 | 2 | +51.48 | +51.48 | +0.00 | +7.72% | -2.07% | 0.057 | +51.52% | 1.276 |
| 1d | 1d_1m_to_1w | 1222 | 1164 | 30 | 7 | 0.1 | 137 | 137 | 137 | 0 | +22.54 | +22.54 | +0.00 | +3.38% | -3.57% | 0.061 | +52.55% | 1.145 |

## Exit Mix

| variant | stop loss | take profit | time exit | time exit share |
| --- | ---: | ---: | ---: | ---: |
| 1h_1d_to_6h | 2473 | 2354 | 956 | +16.53% |
| 1h_3d_to_1d | 2106 | 1967 | 39 | +0.95% |
| 4h_1d_to_12h | 460 | 484 | 573 | +37.77% |
| 4h_3d_to_1d | 353 | 379 | 113 | +13.37% |
| 1d_1w_to_1d | 36 | 61 | 266 | +73.28% |
| 1d_1m_to_1w | 57 | 67 | 13 | +9.49% |

## Side Attribution

| variant | long trades | long PnL | long hit | short trades | short PnL | short hit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1h_1d_to_6h | 3011 | -33.44 | +48.06% | 2772 | -48.95 | +47.84% |
| 1h_3d_to_1d | 2186 | -9.86 | +48.67% | 1926 | -50.72 | +47.35% |
| 4h_1d_to_12h | 782 | -0.50 | +49.74% | 735 | -29.14 | +46.12% |
| 4h_3d_to_1d | 463 | +13.50 | +52.48% | 382 | -2.82 | +49.74% |
| 1d_1w_to_1d | 200 | +29.18 | +53.50% | 163 | +22.30 | +49.08% |
| 1d_1m_to_1w | 88 | +14.84 | +52.27% | 49 | +7.71 | +53.06% |

## Yearly Attribution

| variant | year | trades | return | net PnL | avg R | hit | PF | max DD | SL/TP/Time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1h_1d_to_6h | 2023 | 1261 | -3.46% | -23.05 | -0.051 | +47.42% | 0.895 | -4.55% | 540/488/233 |
| 1h_1d_to_6h | 2024 | 1914 | -2.76% | -18.40 | -0.015 | +48.54% | 0.958 | -4.43% | 802/795/317 |
| 1h_1d_to_6h | 2025 | 1834 | -4.89% | -32.63 | -0.046 | +47.00% | 0.905 | -6.05% | 807/747/280 |
| 1h_1d_to_6h | 2026 | 774 | -1.25% | -8.31 | -0.005 | +49.61% | 0.944 | -2.56% | 324/324/126 |
| 1h_3d_to_1d | 2023 | 807 | -2.08% | -13.85 | -0.061 | +46.72% | 0.920 | -3.92% | 424/376/7 |
| 1h_3d_to_1d | 2024 | 1399 | +0.98% | +6.54 | 0.013 | +50.54% | 1.018 | -2.20% | 681/702/16 |
| 1h_3d_to_1d | 2025 | 1328 | -3.57% | -23.83 | -0.049 | +47.29% | 0.922 | -3.93% | 688/625/15 |
| 1h_3d_to_1d | 2026 | 578 | -4.42% | -29.45 | -0.086 | +45.67% | 0.798 | -5.50% | 313/264/1 |
| 4h_1d_to_12h | 2023 | 315 | -1.68% | -11.19 | -0.033 | +45.71% | 0.888 | -2.41% | 106/104/105 |
| 4h_1d_to_12h | 2024 | 527 | +2.74% | +18.29 | 0.046 | +49.91% | 1.091 | -1.86% | 139/180/208 |
| 4h_1d_to_12h | 2025 | 467 | -5.33% | -35.54 | -0.086 | +46.90% | 0.796 | -6.54% | 156/130/181 |
| 4h_1d_to_12h | 2026 | 208 | -0.18% | -1.19 | 0.032 | +49.04% | 0.984 | -2.63% | 59/70/79 |
| 4h_3d_to_1d | 2023 | 146 | +2.01% | +13.41 | 0.110 | +55.48% | 1.262 | -1.20% | 53/71/22 |
| 4h_3d_to_1d | 2024 | 330 | +2.97% | +19.78 | 0.063 | +53.03% | 1.119 | -1.78% | 131/155/44 |
| 4h_3d_to_1d | 2025 | 248 | -2.48% | -16.50 | -0.051 | +47.18% | 0.864 | -3.11% | 113/102/33 |
| 4h_3d_to_1d | 2026 | 121 | -0.90% | -6.00 | -0.039 | +49.59% | 0.906 | -2.77% | 56/51/14 |
| 1d_1w_to_1d | 2023 | 69 | -0.60% | -4.01 | -0.027 | +44.93% | 0.890 | -1.47% | 11/10/48 |
| 1d_1w_to_1d | 2024 | 132 | +4.18% | +27.89 | 0.086 | +53.79% | 1.415 | -1.31% | 11/23/98 |
| 1d_1w_to_1d | 2025 | 112 | +2.26% | +15.06 | 0.066 | +50.89% | 1.250 | -1.85% | 11/21/80 |
| 1d_1w_to_1d | 2026 | 50 | +1.88% | +12.55 | 0.080 | +56.00% | 1.561 | -1.06% | 3/7/40 |
| 1d_1m_to_1w | 2023 | 29 | +1.44% | +9.63 | 0.154 | +55.17% | 1.415 | -1.04% | 9/15/5 |
| 1d_1m_to_1w | 2024 | 53 | +2.34% | +15.62 | 0.086 | +54.72% | 1.248 | -3.21% | 23/27/3 |
| 1d_1m_to_1w | 2025 | 37 | +1.22% | +8.15 | 0.086 | +54.05% | 1.197 | -1.71% | 15/19/3 |
| 1d_1m_to_1w | 2026 | 18 | -1.63% | -10.85 | -0.212 | +38.89% | 0.609 | -1.97% | 10/6/2 |


## V1 / V2 Interpretation

V1 tested whether minute-level close-to-close pressure could survive cost-aware ATR reward/cost geometry. V2 changes the comparison group because the economic premise is delayed information diffusion and slower position adjustment. Minute bars can be dominated by microstructure noise, liquidation bursts, spread crossing, and local order-flow pressure. The selected V2 window therefore tests whether the same signal family looks more coherent at `1h`, `4h`, and `1d`.

## Interpretation

The rerun changes the previous 1h-blocked interpretation. `1h` is now executed and both `1h` variants are negative no-cost. `4h` is mixed: `4h_1d_to_12h` is negative and `4h_3d_to_1d` is modestly positive. `1d` variants are positive no-cost, but the stronger `1d_1m_to_1w` result is smaller on this fallback window than it was in the earlier full-window 4h/1d-only artifact.

This supports a bounded statement: the evidence is better for daily-horizon momentum than for `1h` momentum under the tested close-to-close proxy and symmetric ATR-1 exits. It does not establish cost-aware profitability and does not validate or reject all momentum mechanisms.

## Time Exit Interpretation

`holding_bars` defines the forward validation horizon. Without time exit, stale positions could remain open until stop or target much later, which would turn this into an indefinite trend-following test. Time exits are therefore part of the experimental design, not a technical afterthought.

High time-exit share means the price often failed to reach either `1 ATR` stop or `1 ATR` target inside the declared horizon. That can mean the holding horizon is too short, the ATR target is too wide, or the signal direction is weak. A follow-up should predeclare holding-horizon variants and report average R by exit reason before adding new filters.

## Regime Boundary

Yearly attribution is a coarse regime proxy only. The task did not condition entries on bull/bear state, volatility percentile, liquidity, drawdown/recovery state, macro, ETF flow, DXY, or broader risk-on/risk-off context. A later task should predeclare objective regime labels and evaluate the same variants within those labels before tuning.

## Artifacts

- Compact summary JSON: `reports/task_330_v2_1h_included_no_cost_atr1_summary.json`
- Raw CLI JSON: omitted from the report artifact because the six raw outputs
  exceeded 150MB. Persisted run ids and compact summary JSON are saved instead.
- Daily report artifact: `reports/blog_payloads/lookback-return-momentum/v2/20230325-20260601-htf-no-cost-atr1-1h-included/`
- Report HTML: `reports/blog_payloads/lookback-return-momentum/v2/20230325-20260601-htf-no-cost-atr1-1h-included/report-ko.html`

## Verification

- `python -m json.tool reports/task_330_v2_1h_included_no_cost_atr1_summary.json >/dev/null`
- `python -m json.tool reports/blog_payloads/lookback-return-momentum/v2/20230325-20260601-htf-no-cost-atr1-1h-included/payload.json >/dev/null`
- Verified all nine PNG files exist and are `1800 x 1000`.
- Verified `1h` appears in the compact summary, payload, and `report-ko.html`.
- Verified `report-ko.html` has no forbidden wording matches for `봅니다.`, `그것은`, `강한 결론`, `기본값`, or standalone hypothesis labels.
- Verified `report-ko.html` and report-facing payload fields do not expose run/task IDs.
- Verified same-folder PNG references in `report-ko.html`.
- `python -m py_compile quant_bitcoin/strategies/lookback_return_momentum.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` passed: `25 passed`.
- `git diff --check` passed.
- Safety grep produced only pre-existing/declarative safety-policy matches and existing non-order backtest environment reads; no live trading, order/account/private endpoint, secret, or `.env` behavior was added by this task.

## Codex Self-Review

- Scope stayed inside Task 330: V2 rerun, summary/report artifacts, strategy/task documentation, and state tracking.
- No frontend/backend/API work was added.
- No strategy signal, risk, cost, or execution code was changed.
- No post-result tuning was performed; the predeclared primary grid was rerun.
- No synthetic `1h` candles were created.
- No live trading, real order execution, signed exchange requests, exchange order/account/private endpoint calls, secrets, or `.env` changes were introduced.

## Recommended Next Task

Create a predeclared follow-up that tests the positive daily-horizon V2 variants under transaction costs and explicit regime labels. The regime labels should be defined before execution, for example trend state, volatility percentile, drawdown/recovery state, liquidity, and broad risk-on/risk-off proxy, so the next result does not become post-result tuning.
