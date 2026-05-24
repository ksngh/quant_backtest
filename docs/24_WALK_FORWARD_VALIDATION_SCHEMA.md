# Walk-Forward Validation Schema

Task 166 adds an offline validation payload for fixed-parameter walk-forward checks.
Task 182 extends the same schema to supported pattern strategies.

Safety boundary:

- Uses supplied candle data only.
- Calls the simulated strategy backtest engine only.
- Does not place orders, read account endpoints, read API keys, or make live deployment decisions.

Top-level payload:

```json
{
  "schema_version": "walk_forward_validation_v1",
  "config": {
    "train_window": "0 days 00:30:00",
    "test_window": "0 days 00:10:00",
    "step_size": "0 days 00:10:00"
  },
  "folds": [],
  "aggregate": {},
  "monte_carlo": {}
}
```

Fold rows include UTC `train_start`, `train_end`, `test_start`, `test_end`, candle counts, action count, status, strategy parameters, summary metrics, and optional diagnostics copied from the simulated strategy-engine result. Status values are:

- `OK`: at least one filled execution.
- `NO_FILLS`: fold ran but no fills occurred.
- `FAILED`: fold could not run; `reason` is present.

Aggregate metrics include fold count, failure count, no-fill fold count, positive-fold ratio, pattern fold stability, and distribution summaries for total return, net PnL, expectancy, trade count, and max drawdown.

Pattern strategy mode:

```bash
python -m quant_bitcoin.backtesting.walk_forward_cli \
  --csv candles.csv \
  --train-window 7D \
  --test-window 1D \
  --step-size 1D \
  --strategy pattern \
  --pattern FAIR_VALUE_GAP \
  --entry-mode MARKET_ON_CONFIRMATION_CLOSE \
  --allowed-pattern-statuses VALID \
  --min-pattern-score 0.7
```

Supported `--strategy pattern` metadata:

- `pattern`: supported pattern key such as `FAIR_VALUE_GAP` or `ORDER_BLOCK`.
- `entry_mode`: deterministic historical entry mode; it is a backtest simulation assumption, not a live order instruction.
- `allowed_pattern_statuses`: comma-separated status filter.
- `minimum_pattern_score`: fixed threshold used across all folds.
- `cost_profile` or manual cost bps: offline transaction-cost assumptions.
- `sizing_mode` and `sizing_value`: simulated engine sizing only.

Pattern action construction uses train candles plus the current test prefix for signal detection. Exit actions are simulated only inside the current fold's remaining test window. The runner does not optimize parameters on train data and does not select a best fold result.

Monte Carlo output uses `trade_return_bootstrap_v1`, records `seed`, `iterations`, `sample_size`, sample totals, and a distribution summary. Results are deterministic for a fixed seed/config.
