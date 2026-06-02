# Task 324: LOOKBACK_RETURN_MOMENTUM V2 No-Cost ATR-1 Validation

## Scope

Task 324 executed `Lookback Return Momentum V2` as a gross/no-cost diagnostic.

The signal family is unchanged from V1:

```text
momentum_return = close[t] / close[t - lookback_bars] - 1
```

The assigned V2 difference is execution geometry and cost handling:

- Strategy version metadata: `v2`.
- Cost-aware entry filter: disabled.
- Transaction costs: zero fee, zero spread, zero slippage via `--cost-profile zero`.
- Risk distance: `ATR(14, RMA)` at the completed signal candle.
- Stop-loss: `1.0 ATR`.
- Take-profit: `1.0 ATR`.
- Same-candle stop/take-profit ambiguity: existing stop-first policy preserved.
- Period: `2026-02-01T00:00:00Z <= candle time < 2026-05-01T00:00:00Z`.

This is not a cost-aware deployability result. It only asks whether the raw momentum signal and symmetric `1 ATR` exit path have positive gross behavior before real execution friction.

## Implementation Note

The existing runner could already express the no-cost ATR-1 mechanics with CLI options. Task 324 added only a small metadata/config path so `LOOKBACK_RETURN_MOMENTUM` runs can explicitly record `strategy_version = v2` without changing the existing default `v1` behavior.

Changed behavior:

- `--lookback-return-momentum-version v2` flows into:
  - strategy object version;
  - strategy config metadata;
  - action metadata;
  - reproducibility metadata;
  - persisted strategy config version.

Default behavior remains `v1` when the version flag is omitted.

## Data Coverage

The runner loads `--end-time` inclusively, so commands used the last included closed candle per interval to satisfy the task's exclusive `2026-05-01T00:00:00Z` boundary.

| Interval | Candles | First candle | Last included candle | Gaps | Duplicates |
|---|---:|---|---|---:|---:|
| `1m` | 128,160 | `2026-02-01T00:00:00Z` | `2026-04-30T23:59:00Z` | 0 | 0 |
| `5m` | 25,632 | `2026-02-01T00:00:00Z` | `2026-04-30T23:55:00Z` | 0 | 0 |
| `15m` | 8,544 | `2026-02-01T00:00:00Z` | `2026-04-30T23:45:00Z` | 0 | 0 |

No candle backfill was needed.

## Command Template

```bash
quant-bitcoin-strategy-backtest \
  --strategy LOOKBACK_RETURN_MOMENTUM \
  --lookback-return-momentum-version v2 \
  --interval <1m|5m|15m> \
  --start-time 2026-02-01T00:00:00Z \
  --end-time <interval-specific-last-included-candle> \
  --lookback-bars <20|12|8> \
  --entry-threshold <0.0004|0.0006|0.0008> \
  --holding-bars <5|6|4> \
  --risk-distance-mode atr \
  --atr-period 14 \
  --atr-smoothing RMA \
  --stop-loss-atr-multiple 1.0 \
  --take-profit-atr-multiple 1.0 \
  --minimum-atr-bps 0.0 \
  --cost-profile zero \
  --liquidity-role TAKER \
  --enforce-candle-continuity \
  --starting-cash 1000000 \
  --starting-cash-currency KRW \
  --krw-per-usdt 1500 \
  --position-sizing-mode cash_fraction \
  --position-sizing-value 0.10 \
  --research-task-id TASK_324 \
  --research-variant-id <variant-id> \
  --research-window-id 20260201_20260501 \
  --research-run-group task_324_v2_no_cost_atr1
```

Persisted runs:

| Interval | Variant id | Run id |
|---|---|---:|
| `1m` | `1m_v2_no_cost_atr1` | 1210 |
| `5m` | `5m_v2_no_cost_atr1` | 1211 |
| `15m` | `15m_v2_no_cost_atr1` | 1212 |

The full CLI JSON outputs were generated and JSON-validated locally. They are not committed because the `1m` raw output is about `386 MB`; the committed compact summary is `reports/task_324_v2_no_cost_atr1_summary.json`.

## Results

| Interval | Candidates | Accepted | Completed | Invalid ATR | Cost-blocked | Gross PnL | Net PnL | Cost | Return | Avg R | Hit ratio | Profit factor | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `1m` | 33,225 | 33,225 | 33,225 | 0 | 0 | -50.579 | -50.579 | 0.000 | -7.5868% | -0.030624 | 48.43% | 0.9389 | -7.6806% |
| `5m` | 6,222 | 6,221 | 6,220 | 1 | 0 | -0.896 | -0.896 | 0.000 | -0.1344% | -0.011771 | 49.13% | 0.9978 | -1.7357% |
| `15m` | 2,256 | 2,253 | 2,252 | 3 | 0 | -20.339 | -20.339 | 0.000 | -3.0509% | -0.031889 | 48.05% | 0.9174 | -3.2735% |

Notes:

- `5m` and `15m` each ended with one open position at the final candle. Completed-trade metrics exclude that still-open position, while portfolio return uses final mark-to-market equity.
- Candidate counts are lower than Task 309/311 raw-candidate counts because V2 accepts entries and the strategy remains flat-only. Momentum signals that occur while a position is open are not counted as attempted entries.
- Every run recorded `zero_transaction_cost_assumption`; total fee, spread, slippage, and total cost were all `0.0`.

## Exit Mix

| Interval | Stop loss | Take profit | Time exit |
|---|---:|---:|---:|
| `1m` | 15,128 | 14,222 | 3,875 |
| `5m` | 2,817 | 2,766 | 637 |
| `15m` | 854 | 809 | 589 |

The stop count is higher than the take-profit count in every interval. Because stop and target are symmetric at `1 ATR`, this directly pressures expectancy. Time exits also did not create enough positive offset.

## Side Attribution

| Interval | Side | Completed | Wins | Losses | Net PnL |
|---|---|---:|---:|---:|---:|
| `1m` | Long | 16,532 | 8,094 | 8,431 | -13.441 |
| `1m` | Short | 16,693 | 7,997 | 8,691 | -37.137 |
| `5m` | Long | 3,072 | 1,490 | 1,582 | -3.226 |
| `5m` | Short | 3,148 | 1,566 | 1,581 | 2.330 |
| `15m` | Long | 1,123 | 539 | 584 | -8.339 |
| `15m` | Short | 1,129 | 543 | 586 | -12.001 |

The only positive side bucket was `5m` short, but it was too small to offset the `5m` long loss. Both sides were negative in `1m` and `15m`.

## Comparison Against V1 Context

Task 309 used the same lowest-threshold symmetric `1 ATR` target geometry with positive transaction-cost assumptions and the cost-aware gate enabled. It produced no accepted entries:

| Interval | Task 309 candidates | Task 309 accepted | Main blocker |
|---|---:|---:|---|
| `1m` | 107,492 | 0 | `COST_INFEASIBLE_NET_RR` |
| `5m` | 22,097 | 0 | `COST_INFEASIBLE_NET_RR` plus 1 invalid ATR |
| `15m` | 7,449 | 0 | `COST_INFEASIBLE_NET_RR` plus 3 invalid ATR |

Task 324 removed that gate and removed costs. Entries therefore occurred, but the no-cost gross result was still negative in all three intervals.

This changes the diagnosis:

- Task 309 showed that symmetric `1 ATR` reward/risk cannot pass a positive-cost `min_net_rr = 1.0` gate.
- Task 324 shows that even after removing that gate and setting costs to zero, the tested V2 signal/exit configuration does not produce positive gross expectancy.
- Therefore this exact V2 configuration is weak before transaction costs are reintroduced.

## Interpretation

`Lookback Return Momentum V2` is not effective under the tested conditions. The strongest evidence is that costs are zero and no cost-aware entry filter is active, yet all three intervals have negative net/gross PnL and negative average R.

This does not reject momentum strategies generally. The conclusion is bounded because:

- The test covers one fixed February-April 2026 BTCUSDT window, not an out-of-sample or walk-forward validation.
- The signal is a simple close-to-close lookback return. It does not test other momentum definitions, acceleration measures, volume confirmation, regime filters, session filters, or higher-timeframe confirmation.
- The exit geometry is symmetric `1 ATR` stop and `1 ATR` take-profit. A different payoff structure can change the required hit rate and path sensitivity.
- Stop-first same-candle ambiguity is conservative and can matter in volatile candles.
- `5m` was close to flat before costs, so a broader judgment would require more windows before treating the result as stable.
- Short trades remain simulated backtest accounting without borrow, funding, margin, liquidation, or execution-friction economics.

The result is still meaningful: V2 did not fail only because of fees, spread, slippage, or the cost gate. The raw signal plus symmetric `1 ATR` exit path did not clear a no-cost baseline.

## Known Limitations

- This task did not tune thresholds, holding bars, ATR period, or ATR multiples after seeing results.
- The committed artifact is a compact summary rather than the full raw CLI JSON because full raw `1m` output is too large for practical PR storage.
- No daily/Tistory report artifact was generated; Task 324 only required a task report under `reports/`.
- No frontend/backend/API behavior was changed.

## Recommended Next Task

Create a separate bounded follow-up only if the owner wants to continue the momentum family. The next useful experiment should not simply disable costs again. It should predeclare one targeted change that addresses the observed gross-edge problem, such as:

- a stronger path-quality or continuation confirmation before entry;
- an ATR or volatility regime constraint justified by the no-cost exit mix;
- a different payoff geometry compared against the same no-cost baseline and then rechecked with costs.

The reason is that Task 324 already isolates the raw signal/exit path. Before asking whether a variant survives real costs, the next variant must first show a clearly positive gross/no-cost edge.

## Verification

- Strategy document existed before execution: `docs/strategy/lookback_return_momentum_v2.md`.
- Data preflight passed for `BTCUSDT` `1m`, `5m`, and `15m` with zero gaps and zero duplicates.
- Persisted runs: `1210`, `1211`, `1212`.
- Full CLI JSON outputs generated locally and passed `python -m json.tool`.
- `python -m pytest tests/strategies/test_lookback_return_momentum.py tests/backtesting/test_lookback_return_momentum_runner.py -q` -> `27 passed`.
- `python -m py_compile quant_bitcoin/strategies/lookback_return_momentum.py quant_bitcoin/backtesting/strategy_postgres_runner_core.py` -> passed.
- `python -m json.tool reports/task_324_v2_no_cost_atr1_summary.json` -> passed.
- `python -m pytest tests/strategies tests/backtesting` -> `627 passed, 2 failed`.
  - Failing tests:
    - `tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_outputs_position_signal_and_execution_side`
    - `tests/backtesting/test_strategy_cli_persistence.py::test_strategy_cli_accepts_equity_risk_fraction_sizing`
  - These are the existing `FAIR_VALUE_GAP` owner-default/profile expectation failures also noted by earlier momentum tasks; Task 324 did not modify the `FAIR_VALUE_GAP` path.
- `git diff --check` -> passed.
- Contract grep for `v2|no-cost|zero|cost_aware|1 ATR|ATR` over Task 324 docs/report/summary -> passed.
- Safety grep for live-trading/order/secret/`.env` terms over source and Task 324 artifacts returned only declarative safety text and pre-existing execution-client/redaction-test references; no new live order, account endpoint, secret, or `.env` behavior was introduced.
