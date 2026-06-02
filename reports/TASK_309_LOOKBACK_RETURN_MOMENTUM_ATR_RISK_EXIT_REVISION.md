# Task 309: LOOKBACK_RETURN_MOMENTUM ATR Risk/Exit Revision

## Scope

Task 309 replaced the primary `LOOKBACK_RETURN_MOMENTUM` risk distance from a fixed entry-price percentage to ATR-based distance.

Assigned interpretation:

- `1R = ATR_at_entry`.
- ATR convention: `ATR(14)`, RMA smoothing, full-window required.
- ATR timing: completed candles through the signal candle are allowed; future entry-candle high/low/close is not used.
- Stop-loss distance: `1 ATR`.
- Take-profit distance: `1 ATR`.
- Task 305 cost-aware entry gate remains enabled for the primary validation.
- Task 308 lower-threshold grid is reused unchanged.

## Implementation Summary

- Updated `docs/strategy/lookback_return_momentum_v1.md` before code/backtest execution.
- Added ATR risk settings to `LookbackReturnMomentumConfig` and CLI metadata:
  - `risk_distance_mode=atr`
  - `atr_period=14`
  - `atr_smoothing=RMA`
  - `stop_loss_atr_multiple=1.0`
  - `take_profit_atr_multiple=1.0`
- Preserved explicit `fixed_pct` mode for backward-compatible tests and old geometry diagnostics.
- Added invalid ATR diagnostics via `INVALID_ATR_RISK_DISTANCE`.
- Updated cost-aware entry gating to use ATR-derived stop and target distance.
- Precomputed ATR once per action-building run so the 3-month `1m` validation is feasible while preserving no-lookahead signal-candle semantics.

## Validation Configuration

Shared configuration:

- Strategy: `LOOKBACK_RETURN_MOMENTUM` v1.
- Symbol: `BTCUSDT`.
- Window: `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`.
- Runner end-time convention: inclusive end-time using the last closed candle before `2026-05-01T00:00:00Z`.
- Cost profile: `conservative_crypto_1m`.
- Cost-aware entry gate: enabled.
- Gate thresholds: `min_net_reward_bps=0.0`, `min_net_rr=1.0`, `liquidity_role=TAKER`.
- Sizing/accounting:
  - `--starting-cash 1000000 --starting-cash-currency KRW --krw-per-usdt 1500`.
  - effective quote starting cash: `666.6666666666666 USDT`.
  - `--position-sizing-mode cash_fraction --position-sizing-value 0.10`.

Command template:

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
  --take-profit-atr-multiple 1.0 \
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
  --research-task-id TASK_309 \
  --research-variant-id <interval>_<label> \
  --research-window-id 20260201_20260501 \
  --research-run-group task_309_atr_risk_exit
```

Validation grid:

| Interval | Label | lookback_bars | holding_bars | entry_threshold | End time |
|---|---|---:|---:|---:|---|
| `1m` | comparator | 20 | 5 | 0.0010 | `2026-04-30T23:59:00Z` |
| `1m` | lower_20pct | 20 | 5 | 0.0008 | `2026-04-30T23:59:00Z` |
| `1m` | lower_40pct | 20 | 5 | 0.0006 | `2026-04-30T23:59:00Z` |
| `1m` | lower_60pct | 20 | 5 | 0.0004 | `2026-04-30T23:59:00Z` |
| `5m` | comparator | 12 | 6 | 0.0015 | `2026-04-30T23:55:00Z` |
| `5m` | lower_20pct | 12 | 6 | 0.0012 | `2026-04-30T23:55:00Z` |
| `5m` | lower_40pct | 12 | 6 | 0.0009 | `2026-04-30T23:55:00Z` |
| `5m` | lower_60pct | 12 | 6 | 0.0006 | `2026-04-30T23:55:00Z` |
| `15m` | comparator | 8 | 4 | 0.0020 | `2026-04-30T23:45:00Z` |
| `15m` | lower_20pct | 8 | 4 | 0.0016 | `2026-04-30T23:45:00Z` |
| `15m` | lower_40pct | 8 | 4 | 0.0012 | `2026-04-30T23:45:00Z` |
| `15m` | lower_60pct | 8 | 4 | 0.0008 | `2026-04-30T23:45:00Z` |

Raw outputs and manifest:

```text
reports/task_309_atr_risk_exit_raw_outputs/
  manifest.json
  1m_comparator_entry_threshold_0p0010.json
  1m_lower_20pct_entry_threshold_0p0008.json
  1m_lower_40pct_entry_threshold_0p0006.json
  1m_lower_60pct_entry_threshold_0p0004.json
  5m_comparator_entry_threshold_0p0015.json
  5m_lower_20pct_entry_threshold_0p0012.json
  5m_lower_40pct_entry_threshold_0p0009.json
  5m_lower_60pct_entry_threshold_0p0006.json
  15m_comparator_entry_threshold_0p0020.json
  15m_lower_20pct_entry_threshold_0p0016.json
  15m_lower_40pct_entry_threshold_0p0012.json
  15m_lower_60pct_entry_threshold_0p0008.json
```

## Results

| Interval | Label | Run id | Raw candidates | Cost-blocked | Invalid ATR | Accepted | Trades | Return |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `1m` | comparator | 1180 | 79,981 | 79,981 | 0 | 0 | 0 | 0.0000% |
| `1m` | lower_20pct | 1181 | 88,660 | 88,660 | 0 | 0 | 0 | 0.0000% |
| `1m` | lower_40pct | 1182 | 97,860 | 97,860 | 0 | 0 | 0 | 0.0000% |
| `1m` | lower_60pct | 1183 | 107,492 | 107,492 | 0 | 0 | 0 | 0.0000% |
| `5m` | comparator | 1184 | 17,171 | 17,170 | 1 | 0 | 0 | 0.0000% |
| `5m` | lower_20pct | 1185 | 18,723 | 18,722 | 1 | 0 | 0 | 0.0000% |
| `5m` | lower_40pct | 1186 | 20,372 | 20,371 | 1 | 0 | 0 | 0.0000% |
| `5m` | lower_60pct | 1187 | 22,097 | 22,096 | 1 | 0 | 0 | 0.0000% |
| `15m` | comparator | 1188 | 5,937 | 5,934 | 3 | 0 | 0 | 0.0000% |
| `15m` | lower_20pct | 1189 | 6,411 | 6,408 | 3 | 0 | 0 | 0.0000% |
| `15m` | lower_40pct | 1190 | 6,899 | 6,896 | 3 | 0 | 0 | 0.0000% |
| `15m` | lower_60pct | 1191 | 7,449 | 7,446 | 3 | 0 | 0 | 0.0000% |

Gross/net PnL, realized costs, exit mix, and expectancy:

| Metric | Result |
|---|---:|
| Completed trades | 0 |
| Exit count | 0 |
| Exit reasons | none |
| Gross PnL | 0 |
| Net PnL | 0 |
| Total realized cost | 0 |
| Average net R | N/A |
| Expectancy | N/A |

## Comparison Against Task 308

The raw momentum candidate counts match Task 308 for the same threshold grid. The change is how planned reward/risk is calculated after a signal appears.

| Interval | Lowest-threshold Task 308 candidates | Lowest-threshold Task 309 candidates | Task 308 accepted | Task 309 accepted |
|---|---:|---:|---:|---:|
| `1m` | 107,492 | 107,492 | 0 | 0 |
| `5m` | 22,097 | 22,097 | 0 | 0 |
| `15m` | 7,449 | 7,449 | 0 | 0 |

ATR did not reduce the signal-layer no-entry result under the assigned `1 ATR` stop and `1 ATR` target with `min_net_rr=1.0`.

The reason is structural:

- With stop distance `1 ATR` and target distance `1 ATR`, planned gross reward equals planned gross risk before costs.
- The cost-aware gate computes net reward after round-trip estimated cost and net risk after adding that cost.
- For any positive round-trip cost, `net_rr = (gross_reward_bps - cost_bps) / (gross_risk_bps + cost_bps)`.
- Because `gross_reward_bps == gross_risk_bps`, positive cost makes `net_rr < 1.0` regardless of ATR size.
- Therefore the configured gate cannot accept entries while `take_profit_atr_multiple` equals `stop_loss_atr_multiple` and `min_net_rr` remains `1.0`.

The few invalid ATR blocks on `5m` and `15m` are early warm-up candidates. They confirm the invalid-risk diagnostic path works; they are not the main no-entry driver.

## Interpretation

- ATR risk distance now works and is reproducible in output metadata.
- ATR warm-up is handled conservatively, with explicit `INVALID_ATR_RISK_DISTANCE` diagnostics.
- The no-entry result is not caused by missing raw momentum candidates or missing ATR values.
- Under the assigned 1:1 ATR stop/target geometry, the cost-aware entry gate correctly rejects all positive-cost candidates because the required net reward/risk cannot reach `1.0`.
- Positive gross performance cannot be evaluated in this primary validation because there are no accepted entries and no fills.

## Verification

- `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` -> `22 passed`.
- `python -m pytest tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_persists_reproducibility_metadata -q` -> `1 passed`.
- Persisted validation runs: `1180`-`1191`.
- Raw output JSON validation: each output passed `python -m json.tool`.

## Known Limitations

- Primary validation intentionally did not relax the cost-aware entry gate.
- Primary validation intentionally did not tune ATR period, ATR multiples, cost assumptions, holding bars, or entry thresholds beyond the Task 308 grid.
- Because the assigned target and stop are symmetric at `1 ATR`, the cost-aware `min_net_rr=1.0` gate mathematically prevents positive-cost acceptance.

## Recommended Next Task

Create a separate bounded reward/risk geometry diagnostic task if the owner wants filled trades under the same cost-aware gate. The next task should predeclare at least one asymmetric ATR target such as `take_profit_atr_multiple > stop_loss_atr_multiple`, or explicitly run a gross-vs-net diagnostic with the gate disabled or relaxed for comparison only.
