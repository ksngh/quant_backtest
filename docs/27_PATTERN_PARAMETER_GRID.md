# Pattern Parameter Grid Runner

Task 214 adds an offline parameter-grid runner for pattern research. It is a
local backtest utility only: it does not fetch exchange data, place orders, sign
requests, read API keys, or mutate `.env` files.

## Scope

The runner varies selected parameters across deterministic combinations:

- `detector.<field>` for the selected pattern detector config.
- `risk.<field>` for the selected pattern risk config.
- `entry.mode`, `entry.max_wait_bars`, `entry.expire_status`, and `entry.trigger`.
- `cost.profile`.
- `sizing.mode` and `sizing.value`.
- `filter.minimum_pattern_score` and `filter.minimum_risk_reward`.

Each row emits a stable `parameter_hash` from the JSON-safe parameter set.

## CLI

```bash
python -m quant_bitcoin.backtesting.pattern_parameter_grid_cli \
  --csv data/sample.csv \
  --pattern FAIR_VALUE_GAP \
  --param entry.mode=market_on_confirmation_close,limit_at_entry_reference \
  --param cost.profile=zero,conservative_crypto_1m \
  --max-combinations 20
```

Use `--dry-run` to validate and hash the grid without running the strategy
engine. `--max-combinations` blocks accidental large grids; outputs include a
warning once `--warning-combinations` is reached.

## Metrics

Executed rows include trade count, candidate count, fill rate, expectancy,
average R, hit rate, profit factor, max drawdown, cost ratio, and no-fill count.
Rows with no completed fills are marked `NO_FILLS`; invalid rows are marked
`FAILED` with the error message.

## FVG Retest V2 Protocol

Task 236 adds `docs/29_FVG_RETEST_V2_RESEARCH_PROTOCOL.md` and code helpers for FVG v2 research governance. FVG v2 grids must predeclare entry trigger, stop mode, and cost profile, must retain losing/no-fill variants, and must not promote a strategy from the grid winner. Zero-cost-only evidence is rejected by the FVG v2 protocol validator.
