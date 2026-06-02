# Task 311: LOOKBACK_RETURN_MOMENTUM ATR Reward/Cost Geometry Diagnostic

## Scope

Task 311 tested whether `LOOKBACK_RETURN_MOMENTUM` can produce cost-feasible entries when the stop stays at `1 ATR` and the take-profit is raised to `2.0`, `2.5`, and `3.0 ATR`.

The signal definition was not changed. The validation used the lowest Task 308 entry threshold per interval so the experiment isolates reward/cost geometry:

| Interval | lookback_bars | holding_bars | entry_threshold | End time |
|---|---:|---:|---:|---|
| `1m` | 20 | 5 | 0.0004 | `2026-04-30T23:59:00Z` |
| `5m` | 12 | 6 | 0.0006 | `2026-04-30T23:55:00Z` |
| `15m` | 8 | 4 | 0.0008 | `2026-04-30T23:45:00Z` |

Shared settings:

- Window: `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`.
- Symbol: `BTCUSDT`.
- Risk distance: `ATR(14)`, RMA, completed signal-candle timing.
- Stop: `1.0 ATR`.
- Take-profit candidates: `2.0`, `2.5`, `3.0 ATR`.
- Minimum ATR bps candidates: `0.0`, `20.0`.
- Cost profile: `conservative_crypto_1m`.
- Cost-aware gate: `min_net_reward_bps=0.0`, `min_net_rr=1.0`, `liquidity_role=TAKER`.
- Sizing/accounting: `1000000 KRW`, `krw_per_usdt=1500`, effective quote starting cash `666.6666666666666 USDT`, `cash_fraction=0.10`.

Raw outputs and the command manifest are saved under:

```text
reports/task_311_atr_reward_cost_geometry_raw_outputs/
  manifest.json
  1m_tp2p0_minatr0p0.json
  1m_tp2p0_minatr20p0.json
  1m_tp2p5_minatr0p0.json
  1m_tp2p5_minatr20p0.json
  1m_tp3p0_minatr0p0.json
  1m_tp3p0_minatr20p0.json
  5m_tp2p0_minatr0p0.json
  5m_tp2p0_minatr20p0.json
  5m_tp2p5_minatr0p0.json
  5m_tp2p5_minatr20p0.json
  5m_tp3p0_minatr0p0.json
  5m_tp3p0_minatr20p0.json
  15m_tp2p0_minatr0p0.json
  15m_tp2p0_minatr20p0.json
  15m_tp2p5_minatr0p0.json
  15m_tp2p5_minatr20p0.json
  15m_tp3p0_minatr0p0.json
  15m_tp3p0_minatr20p0.json
```

`manifest.json` includes the exact command array for each run.

## Command Template

```bash
quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --interval <interval> \
  --start-time 2026-02-01T00:00:00Z \
  --end-time <interval-specific-end-time> \
  --lookback-bars <lookback-bars> \
  --entry-threshold <entry-threshold> \
  --holding-bars <holding-bars> \
  --risk-distance-mode atr \
  --atr-period 14 \
  --atr-smoothing RMA \
  --stop-loss-atr-multiple 1.0 \
  --take-profit-atr-multiple <2.0|2.5|3.0> \
  --minimum-atr-bps <0.0|20.0> \
  --cost-profile conservative_crypto_1m \
  --enable-cost-aware-entry-filter \
  --min-net-reward-bps 0.0 \
  --min-net-rr 1.0 \
  --liquidity-role TAKER \
  --enforce-candle-continuity \
  --starting-cash 1000000 \
  --starting-cash-currency KRW \
  --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --research-task-id TASK_311 \
  --research-variant-id <variant-id> \
  --research-window-id 20260201_20260501 \
  --research-run-group task_311_atr_reward_cost_geometry
```

## Cost Geometry

For stop `1 ATR` and take-profit `k ATR`:

```text
gross_risk_bps = atr_bps
gross_reward_bps = k * atr_bps
net_rr = (gross_reward_bps - round_trip_cost_bps) / (gross_risk_bps + round_trip_cost_bps)
```

With `min_net_rr=1.0`, the candidate must satisfy:

```text
(k - 1) * atr_bps >= 2 * round_trip_cost_bps
```

This is why Task 309's `1 ATR` target could not pass any positive-cost gate. Raising the target multiple can make entries cost-feasible, but only when ATR is large enough relative to estimated round-trip cost. The `conservative_crypto_1m` cost profile also includes volatility-adjusted slippage, so the required ATR floor is not a fixed number.

## Results

| Interval | TP ATR | Min ATR bps | Run id | Candidates | ATR-small | Cost-blocked | Accepted | Completed | Net PnL | Avg net R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1m` | 2.0 | 0.0 | 1192 | 107,492 | 0 | 107,492 | 0 | 0 | 0.000 | N/A |
| `1m` | 2.0 | 20.0 | 1193 | 107,492 | 102,665 | 4,827 | 0 | 0 | 0.000 | N/A |
| `1m` | 2.5 | 0.0 | 1194 | 107,471 | 0 | 107,465 | 6 | 6 | -1.863 | 0.083876 |
| `1m` | 2.5 | 20.0 | 1195 | 107,471 | 102,665 | 4,800 | 6 | 6 | -1.863 | 0.083876 |
| `1m` | 3.0 | 0.0 | 1196 | 107,323 | 0 | 107,279 | 44 | 44 | -13.413 | -0.014311 |
| `1m` | 3.0 | 20.0 | 1197 | 107,323 | 102,665 | 4,614 | 44 | 44 | -13.413 | -0.014311 |
| `5m` | 2.0 | 0.0 | 1198 | 22,066 | 0 | 22,058 | 7 | 7 | -3.064 | -0.061178 |
| `5m` | 2.0 | 20.0 | 1199 | 22,066 | 12,128 | 9,930 | 7 | 7 | -3.064 | -0.061178 |
| `5m` | 2.5 | 0.0 | 1200 | 21,872 | 0 | 21,816 | 55 | 55 | -24.335 | -0.166667 |
| `5m` | 2.5 | 20.0 | 1201 | 21,872 | 12,128 | 9,688 | 55 | 55 | -24.335 | -0.166667 |
| `5m` | 3.0 | 0.0 | 1202 | 21,062 | 0 | 20,824 | 237 | 237 | -69.503 | 0.020107 |
| `5m` | 3.0 | 20.0 | 1203 | 21,062 | 12,128 | 8,696 | 237 | 237 | -69.503 | 0.020107 |
| `15m` | 2.0 | 0.0 | 1204 | 7,375 | 0 | 7,348 | 24 | 24 | -13.891 | -0.139272 |
| `15m` | 2.0 | 20.0 | 1205 | 7,375 | 734 | 6,614 | 24 | 24 | -13.891 | -0.139272 |
| `15m` | 2.5 | 0.0 | 1206 | 6,866 | 0 | 6,677 | 186 | 186 | -65.934 | -0.059231 |
| `15m` | 2.5 | 20.0 | 1207 | 6,866 | 734 | 5,943 | 186 | 186 | -65.934 | -0.059231 |
| `15m` | 3.0 | 0.0 | 1208 | 5,586 | 0 | 4,991 | 592 | 592 | -163.890 | -0.012777 |
| `15m` | 3.0 | 20.0 | 1209 | 5,586 | 734 | 4,257 | 592 | 592 | -163.890 | -0.012777 |

P&L detail for filled variants:

| Interval | TP ATR | Min ATR bps | Completed | Gross PnL | Cost | Net PnL | Return | Expectancy | Hit ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1m` | 2.5 | 0.0 | 6 | 0.019 | 1.882 | -1.863 | -0.2795% | -0.310501 | 16.67% |
| `1m` | 2.5 | 20.0 | 6 | 0.019 | 1.882 | -1.863 | -0.2795% | -0.310501 | 16.67% |
| `1m` | 3.0 | 0.0 | 44 | -0.202 | 13.211 | -13.413 | -2.0120% | -0.304848 | 15.91% |
| `1m` | 3.0 | 20.0 | 44 | -0.202 | 13.211 | -13.413 | -2.0120% | -0.304848 | 15.91% |
| `5m` | 2.0 | 0.0 | 7 | -0.420 | 2.644 | -3.064 | -0.4596% | -0.437715 | 42.86% |
| `5m` | 2.0 | 20.0 | 7 | -0.420 | 2.644 | -3.064 | -0.4596% | -0.437715 | 42.86% |
| `5m` | 2.5 | 0.0 | 55 | -5.831 | 18.504 | -24.335 | -3.6503% | -0.442457 | 20.00% |
| `5m` | 2.5 | 20.0 | 55 | -5.831 | 18.504 | -24.335 | -3.6503% | -0.442457 | 20.00% |
| `5m` | 3.0 | 0.0 | 237 | 0.733 | 70.236 | -69.503 | -10.4255% | -0.293263 | 24.05% |
| `5m` | 3.0 | 20.0 | 237 | 0.733 | 70.236 | -69.503 | -10.4255% | -0.293263 | 24.05% |
| `15m` | 2.0 | 0.0 | 24 | -3.984 | 9.907 | -13.891 | -2.0836% | -0.578781 | 16.67% |
| `15m` | 2.0 | 20.0 | 24 | -3.984 | 9.907 | -13.891 | -2.0836% | -0.578781 | 16.67% |
| `15m` | 2.5 | 0.0 | 186 | -5.967 | 59.967 | -65.934 | -9.8901% | -0.354484 | 22.58% |
| `15m` | 2.5 | 20.0 | 186 | -5.967 | 59.967 | -65.934 | -9.8901% | -0.354484 | 22.58% |
| `15m` | 3.0 | 0.0 | 592 | 0.398 | 164.288 | -163.890 | -24.5835% | -0.276842 | 20.44% |
| `15m` | 3.0 | 20.0 | 592 | 0.398 | 164.288 | -163.890 | -24.5835% | -0.276842 | 20.44% |

## Comparison Against Task 309

Task 309 used the same lowest thresholds with a symmetric `1 ATR` target. It produced no accepted entries. Task 311 confirms the reason was geometry: raising the take-profit multiple above the stop multiple allows some entries through the same cost-aware gate.

The comparison below uses Task 311's most permissive reward geometry, `3.0 ATR` target with `minimum_atr_bps=0.0`.

| Interval | Task | Candidates | ATR-small | Cost-blocked | Invalid ATR | Accepted | Completed | Gross PnL | Net PnL | Cost | Expectancy | Avg net R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1m` | Task 309, TP 1.0 | 107,492 | 0 | 107,492 | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | N/A | N/A |
| `1m` | Task 311, TP 3.0 | 107,323 | 0 | 107,279 | 0 | 44 | 44 | -0.202 | -13.413 | 13.211 | -0.304848 | -0.014311 |
| `5m` | Task 309, TP 1.0 | 22,097 | 0 | 22,096 | 1 | 0 | 0 | 0.000 | 0.000 | 0.000 | N/A | N/A |
| `5m` | Task 311, TP 3.0 | 21,062 | 0 | 20,824 | 1 | 237 | 237 | 0.733 | -69.503 | 70.236 | -0.293263 | 0.020107 |
| `15m` | Task 309, TP 1.0 | 7,449 | 0 | 7,446 | 3 | 0 | 0 | 0.000 | 0.000 | 0.000 | N/A | N/A |
| `15m` | Task 311, TP 3.0 | 5,586 | 0 | 4,991 | 3 | 592 | 592 | 0.398 | -163.890 | 164.288 | -0.276842 | -0.012777 |

Candidate counts fall in Task 311 because accepted entries open positions. The strategy is flat-only, so later momentum signals while a position is open are not counted as attempted entries in the runner diagnostics.

## Interpretation

- Raising the take-profit multiple did make candidates cost-feasible under the unchanged cost-aware gate.
- The first cost-feasible threshold differed by interval:
  - `1m`: no fills at `2.0 ATR`; fills start at `2.5 ATR`.
  - `5m`: fills start at `2.0 ATR`.
  - `15m`: fills start at `2.0 ATR`.
- The `20 bps` ATR floor did not change accepted entries or P&L in this grid. It reclassified many low-ATR candidates from cost-aware rejection to `ATR_TOO_SMALL_FOR_COST`, but every accepted trade already had ATR above the floor.
- Filled variants were not profitable after costs. Gross PnL was near flat or negative, while realized cost was large enough to dominate net PnL.
- The core failure changed from "no entry can pass cost geometry" to "some entries pass planned geometry, but realized hit rate/payoff after costs is still too weak."

## Known Limitations

- This task did not tune beyond the predeclared grid.
- `minimum_atr_bps=20.0` was only a diagnostic floor; it was too low to change the accepted-trade set.
- The validation uses the same February-April 2026 window and should not be treated as out-of-sample evidence.
- Short trades remain simulated backtest accounting and do not include borrow/funding/liquidation economics.

## Recommended Next Task

Use this result to define a stricter trade-quality diagnostic instead of raising target multiples further. The next bounded task should test whether accepted trades improve when the strategy requires a stronger realized-volatility or path-quality condition before entry, such as a higher ATR floor derived from the cost formula, directional continuation confirmation, or a time-of-day/liquidity filter.

The reason is that Task 311 already proved reward geometry can clear the cost gate. The remaining problem is not entry feasibility; it is that the filled trades do not produce enough realized gross edge to pay their costs.

## Verification

- `python -m py_compile quant_bitcoin/strategies/lookback_return_momentum.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py` -> passed.
- `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` -> `25 passed`.
- `python -m pytest tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q` -> `1 passed`.
- 18 raw JSON outputs plus `manifest.json` passed `python -m json.tool`.
- `git diff --check` -> passed.
- Code diff safety grep for API keys, secrets, `.env`, live order endpoints, signed endpoints, and `ENABLE_LIVE_TRADING` -> no matches.
