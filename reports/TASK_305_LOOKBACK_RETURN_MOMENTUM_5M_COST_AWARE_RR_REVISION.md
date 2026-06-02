# Task 305: LOOKBACK_RETURN_MOMENTUM 5m Cost-Aware RR Revision

## Summary

- Strategy: `LOOKBACK_RETURN_MOMENTUM` v1, research-only.
- Entry gate: `cost_aware_entry_filter_v1`.
- Validation window: `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`.
- Cost profile: `conservative_crypto_1m`.
- Gate thresholds: `min_net_reward_bps=0.0`, `min_net_rr=1.0`, `liquidity_role=TAKER`.
- Result: `1m`, `5m`, and `15m` all produced momentum entry candidates, but every candidate was blocked by the cost-aware reward/risk gate. No fills were produced.

This is not a live-trading result and does not imply deployability. It shows that the current fixed `0.2%` risk distance and `1.5R` take-profit geometry does not survive the predeclared cost gate under the selected cost profile.

## Implementation Notes

- Updated `docs/strategy/lookback_return_momentum_v1.md` before implementation/backtest execution.
- Added cost-aware net reward/risk gating to the `LOOKBACK_RETURN_MOMENTUM` action builder.
- Reused the existing runner CLI concepts: `--enable-cost-aware-entry-filter`, `--min-net-reward-bps`, `--min-net-rr`, active transaction-cost profile, and taker/maker role selection.
- Accepted entries attach cost-aware metadata; blocked candidates emit `SKIP` actions with `COST_INFEASIBLE_NET_RR`.
- Runner diagnostics now count attempted, accepted, and cost-blocked entries.
- Saved run metadata now includes the cost-aware gate config, cost profile, workflow settings, and momentum config.

## Data Preflight

No new backfill was performed. Local closed candles already covered the required window.

| Interval | Expected candles | Found candles | First candle | Last included candle | Duplicate open-time groups | Missing expected opens |
|---|---:|---:|---|---|---:|---:|
| `1m` | 128,160 | 128,160 | `2026-02-01 00:00:00+00:00` | `2026-04-30 23:59:00+00:00` | 0 | 0 |
| `5m` | 25,632 | 25,632 | `2026-02-01 00:00:00+00:00` | `2026-04-30 23:55:00+00:00` | 0 | 0 |
| `15m` | 8,544 | 8,544 | `2026-02-01 00:00:00+00:00` | `2026-04-30 23:45:00+00:00` | 0 | 0 |

Runner end-time note: the current candle loader treats `--end-time` as inclusive. To preserve the task's end-exclusive `2026-05-01T00:00:00Z` window, validation used each interval's last candle before that timestamp.

## Validation Config

| Interval | Run id | lookback_bars | holding_bars | entry_threshold | CLI end-time used |
|---|---:|---:|---:|---:|---|
| `1m` | 1162 | 20 | 5 | 0.0010 | `2026-04-30T23:59:00Z` |
| `5m` | 1163 | 12 | 6 | 0.0015 | `2026-04-30T23:55:00Z` |
| `15m` | 1164 | 8 | 4 | 0.0020 | `2026-04-30T23:45:00Z` |

Shared sizing/accounting config:

- `--starting-cash 1000000 --starting-cash-currency KRW --krw-per-usdt 1500`
- effective quote starting cash: `666.6666666666666 USDT`
- `--position-sizing-mode cash_fraction --position-sizing-value 0.10`
- `--enforce-candle-continuity`
- `--research-task-id TASK_305`
- `--research-variant-id lookback_return_momentum_cost_aware_rr`
- `--research-run-group cost_aware_rr_validation`

Cost assumptions from `conservative_crypto_1m`:

- taker fee: `10.0 bps`
- spread: `3.0 bps`
- base slippage: `5.0 bps`
- minimum slippage: `1.0 bps`
- volatility slippage multiplier: `0.1`

The current default target geometry has gross reward of `30 bps` and gross risk of `20 bps`. The minimum round-trip cost under this profile is already `36 bps` before volatility adjustment, so the net reward is at most `-6 bps`. That is why every candidate fails the predeclared `net_reward_bps >= 0` and `net_rr >= 1.0` gate.

## Results

| Interval | Candidates | Accepted | Blocked | Blocked long | Blocked short | Completed trades | Gross PnL | Net PnL | Total return | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1m` | 79,981 | 0 | 79,981 | 39,961 | 40,020 | 0 | 0 | 0.0 | 0.0% | 0.0% |
| `5m` | 17,171 | 0 | 17,171 | 8,554 | 8,617 | 0 | 0 | 0.0 | 0.0% | 0.0% |
| `15m` | 5,937 | 0 | 5,937 | 2,941 | 2,996 | 0 | 0 | 0.0 | 0.0% | 0.0% |

Common block reason: `COST_INFEASIBLE_NET_RR`.

| Interval | Win rate | Profit factor | Fee cost | Spread cost | Slippage cost | Exit reasons |
|---|---:|---:|---:|---:|---:|---|
| `1m` | n/a | n/a | 0 | 0 | 0 | none |
| `5m` | n/a | n/a | 0 | 0 | 0 | none |
| `15m` | n/a | n/a | 0 | 0 | 0 | none |

Costs are zero in the realized result because no entries passed the pre-trade gate and therefore no simulated fills occurred.

## Historical Context

Task 299 used a shorter May window and did not apply this cost-aware pre-entry gate. It saved `1m` and `15m` runs with negative returns and skipped `5m` because local closed `5m` candles were missing at that time. Task 305 is not a tuned comparison against Task 299: it uses a longer February-to-May window, includes `5m`, and changes the entry admissibility rule before validation.

## Verification

- `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` -> `19 passed`
- `python -m pytest tests/market_data/test_binance_backfill.py tests/market_data/test_binance_backfill_cli.py tests/market_data/test_binance_downloader.py tests/market_data/test_candle_validation.py -q` -> `64 passed`
- `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q` -> `20 passed`
- Persisted run metadata verified for runs `1162`, `1163`, and `1164`: each run row includes enabled `cost_aware_entry_filter`, `conservative_crypto_1m` cost profile, workflow settings, and the matching momentum config.

## Known Limitations

- This task did not tune parameters after seeing results.
- Because every entry candidate was blocked, the result cannot estimate realized win rate, profit factor, or exit behavior under the revised gate.
- The result indicates that the current fixed target/risk geometry is infeasible under the selected cost assumptions; a separate task is required before testing any alternative risk distance, target multiple, timeframe-specific cost profile, or gross-vs-net diagnostic variant.
