# Walk-Forward Validation Schema

Task 166 adds an offline validation payload for fixed-parameter walk-forward checks.

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

Fold rows include UTC `train_start`, `train_end`, `test_start`, `test_end`, candle counts, action count, status, strategy parameters, and summary metrics. Status values are:

- `OK`: at least one filled execution.
- `NO_FILLS`: fold ran but no fills occurred.
- `FAILED`: fold could not run; `reason` is present.

Aggregate metrics include fold count, failure count, no-fill fold count, positive-fold ratio, and distribution summaries for total return, net PnL, trade count, and max drawdown.

Monte Carlo output uses `trade_return_bootstrap_v1`, records `seed`, `iterations`, `sample_size`, sample totals, and a distribution summary. Results are deterministic for a fixed seed/config.
