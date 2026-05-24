# Backtest Result Dashboard API Contract (Task 073)

## 1) Purpose and Safety Boundary

This contract defines the **first read-only backend/frontend API shape** for viewing completed simulated backtest results.

Safety boundary:

- Read-only dashboard API only.
- No backtest execution endpoints.
- No strategy mutation endpoints.
- No login/auth in this task batch.
- No live trading.
- No real Binance order execution.
- No exchange account access.
- No API key handling.

This contract must be implemented using existing read-only persistence methods first:

- `PostgresBacktestResultRepository.list_completed_runs(...)`
- `PostgresBacktestResultRepository.load_run_for_graphs(backtest_run_id)`

## 2) Backend Base Path

- Base path: `/api`
- Content type: `application/json`
- Time format: UTC ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ`)

## 3) Endpoint List

1. `GET /api/health`
2. `GET /api/backtest-runs`
3. `GET /api/backtest-runs/{backtest_run_id}`
4. Optional: `GET /api/backtest-runs/{backtest_run_id}/chart`

## 4) Request Query Parameters

## 4.1 `GET /api/health`

No query parameters.

## 4.2 `GET /api/backtest-runs`

- `source?: string`
- `symbol?: string`
- `interval?: string`
- `actual_start_time?: string` (UTC ISO-8601)
- `actual_end_time?: string` (UTC ISO-8601)
- `limit?: integer` (default: `20`, max: `100`)

Validation:

- `limit < 1` => `400`
- `limit > 100` => `400`
- invalid datetime formats => `400`

Semantics:

- Filters must map directly to `list_completed_runs(...)` inputs.
- Returned rows are newest-first by persisted run creation time.

## 4.3 `GET /api/backtest-runs/{backtest_run_id}`

Path parameter:

- `backtest_run_id: integer` (positive)

Validation:

- non-integer or `<= 0` => `400`
- missing completed run => `404`

Semantics:

- Must map to `load_run_for_graphs(backtest_run_id)`.
- Must not synthesize run data by re-running strategies/backtests.

## 4.4 Optional `GET /api/backtest-runs/{backtest_run_id}/chart`

Path parameter:

- `backtest_run_id: integer` (positive)

Validation:

- non-integer or `<= 0` => `400`
- missing completed run => `404`

Semantics:

- Uses same saved run source as detail endpoint.
- Returns chart-focused graph series and marker fields only.

## 5) Response Schemas

## 5.1 `GET /api/health` (200)

```json
{
  "status": "ok",
  "service": "quant-backtest-api",
  "database": {
    "configured": true,
    "reachable": true
  }
}
```

Notes:

- `database.configured=false` is allowed when DB URL is not configured.
- `database.reachable=false` means process is alive but DB cannot currently be reached.

## 5.2 `GET /api/backtest-runs` (200)

```json
{
  "items": [
    {
      "id": 123,
      "run_key": "string",
      "strategy": {
        "config_id": 1,
        "key": "pattern",
        "name": "FAIR_VALUE_GAP_PATTERN_STRATEGY",
        "version": "pattern_strategy_v1",
        "parameters": {"patterns": ["FAIR_VALUE_GAP"]},
        "parameters_hash": "string"
      },
      "market": {
        "source": "binance_spot",
        "symbol": "BTCUSDT",
        "interval": "1m",
        "actual_start_time": "2024-01-01T00:00:00Z",
        "actual_end_time": "2024-01-02T00:00:00Z",
        "candle_count": 1440
      },
      "summary": {
        "final_equity": 10050.25,
        "total_return": 0.005025,
        "trade_count": 12
      },
      "runtime": {
        "total_elapsed_ms": 1500.0,
        "engine_elapsed_ms": 500.0
      },
      "created_at": "2026-05-21T00:00:00Z",
      "completed_at": "2026-05-21T00:00:01Z"
    }
  ],
  "limit": 20
}
```

Field mapping notes:

- `strategy.*` maps from list item strategy config fields.
- `market.source` maps from persisted `candle_source`.
- `summary.*` maps from persisted `backtest_results` summary row.
- `runtime` is optional and maps from `backtest_runs.metadata.runtime` when numeric timing fields are present. Legacy runs may return `null`.

## 5.3 `GET /api/backtest-runs/{backtest_run_id}` (200)

```json
{
  "run": {
    "id": 123,
    "run_key": "string",
    "engine_name": "BasicBacktester",
    "engine_version": "basic_backtester_v1",
    "status": "completed",
    "market": {
      "source": "binance_spot",
      "symbol": "BTCUSDT",
      "interval": "1m",
      "requested_start_time": "2024-01-01T00:00:00Z",
      "requested_end_time": "2024-01-02T00:00:00Z",
      "actual_start_time": "2024-01-01T00:00:00Z",
      "actual_end_time": "2024-01-02T00:00:00Z",
      "candle_count": 1440
    },
    "starting_cash": 10000.0,
    "trade_quantity": 0.01,
    "created_at": "2026-05-21T00:00:00Z",
    "completed_at": "2026-05-21T00:00:01Z",
    "metadata": {}
  },
  "strategy_config": {
    "id": 1,
    "key": "pattern",
    "name": "FAIR_VALUE_GAP_PATTERN_STRATEGY",
    "version": "pattern_strategy_v1",
    "parameters": {"patterns": ["FAIR_VALUE_GAP"]},
    "parameters_hash": "string",
    "metadata": {}
  },
  "summary": {
    "starting_cash": 10000.0,
    "ending_cash": 9500.0,
    "ending_position": 0.01,
    "final_price": 50000.0,
    "final_equity": 10000.0,
    "total_return": 0.0,
    "trade_count": 2,
    "buy_count": 1,
    "sell_count": 1,
    "metadata": {
      "account_state": {
        "free_cash_after": 9500.0,
        "margin_used_after": 0.0,
        "short_proceeds_locked_after": 0.0,
        "short_collateral_locked_after": 0.0,
        "available_buying_power_after": 9500.0,
        "cash_after_semantics": "cash_after is cash balance; equity_after includes long position market value"
      },
      "trade_attribution": {
        "schema_version": "trade_attribution_metrics_v1",
        "trade_metrics": {
          "completed_trade_count": 1,
          "hit_ratio": 1.0,
          "payoff_ratio": null,
          "expectancy": 500.0,
          "profit_factor": null,
          "profit_factor_is_infinite": true
        },
        "attribution": {
          "by_pattern_type": {},
          "by_position_side": {},
          "by_exit_reason": {}
        }
      }
    },
    "created_at": "2026-05-21T00:00:01Z"
  },
  "trades": [
    {
      "id": 1,
      "sequence": 1,
      "candle_open_time": "2024-01-01T00:10:00Z",
      "signal": "LONG_ENTRY",
      "position_signal": "LONG_ENTRY",
      "execution_side": "BUY",
      "position_side": "LONG",
      "price": 50000.0,
      "quantity": 0.01,
      "cash_after": 9500.0,
      "cash_balance_after": 9500.0,
      "position_after": 0.01,
      "metadata": {
        "position_signal": "LONG_ENTRY",
        "execution_side": "BUY",
        "position_side": "LONG",
        "cash_balance_after": 9500.0,
        "execution_equity_after": 10000.0,
        "mark_to_market_equity_after": 10000.0,
        "free_cash_after": 9500.0,
        "margin_used_after": 0.0,
        "short_proceeds_locked_after": 0.0,
        "short_collateral_locked_after": 0.0,
        "available_buying_power_after": 9500.0,
        "cash_after_semantics": "cash_after is cash balance; equity_after includes long position market value"
      }
    }
  ],
  "graph_points": [
    {
      "id": 1,
      "sequence": 1,
      "candle_open_time": "2024-01-01T00:00:00Z",
      "close_price": 50000.0,
      "cash": 10000.0,
      "position": 0.0,
      "equity": 10000.0,
      "trade_id": null,
      "signal": null,
      "metadata": {
        "free_cash": 10000.0,
        "margin_used": 0.0,
        "short_proceeds_locked": 0.0,
        "short_collateral_locked": 0.0,
        "available_buying_power": 10000.0,
        "cash_semantics": "cash_after equals free_cash_after when flat",
        "equity_semantics": "candle-close mark-to-market equity after applying actions at this timestamp",
        "equity_valuation_price": 50000.0
      }
    }
  ],
  "diagnostics": {
    "schema_version": "research_diagnostics_api_v1",
    "available_sections": [
      "run.runtime",
      "summary.performance_metrics",
      "summary.trade_attribution",
      "trades.metadata",
      "graph_points.metadata"
    ],
    "run": {
      "runtime": {
        "total_elapsed_ms": 1500.0,
        "engine_elapsed_ms": 500.0
      }
    },
    "summary": {
      "performance_metrics": {},
      "trade_attribution": {}
    },
    "trade_metadata_keys": ["fill_price_source", "position_sizing_source"],
    "graph_metadata_keys": ["drawdown", "trades"]
  },
  "warnings": [
    {
      "code": "PATTERN_PLACEHOLDER_EQUITY",
      "message": "Older persisted pattern runs may contain placeholder-neutral cash/equity values from pre-canonical compatibility history; treat those runs as non-financial diagnostics."
    }
  ],
  "research_report": {
    "schema_version": "backtest_research_report_v1",
    "run_identity": {
      "id": 123,
      "run_key": "abc",
      "engine_name": "strategy_engine",
      "engine_version": "v1",
      "status": "completed"
    },
    "market": {
      "source": "csv",
      "symbol": "BTCUSDT",
      "interval": "1m"
    },
    "strategy": {
      "key": "pattern",
      "name": "Pattern Strategy",
      "version": "v1",
      "parameters": {},
      "parameters_hash": "..."
    },
    "reproducibility": {},
    "risk": {},
    "performance": {},
    "diagnostics": {},
    "data_summary": {
      "trade_rows": 1,
      "graph_points": 1,
      "warnings": []
    },
    "limitations": [],
    "safety_boundary": [
      "Read-only saved-run report."
    ],
    "recommended_next_experiments": [],
    "markdown": "# Backtest Research Report: Run 123\n..."
  }
}
```

Warning behavior:

- `warnings` is always present (may be empty array).
- Include `PATTERN_PLACEHOLDER_EQUITY` when run data indicates older placeholder-neutral pattern persistence (for example legacy pattern metadata without summary metadata, or zeroed cash/equity semantics).

Cash/equity semantics:

- `signal` is the preferred semantic position signal for new strategy-engine runs. Expected values include `LONG_ENTRY`, `LONG_EXIT`, `LONG_PARTIAL_EXIT`, `SHORT_ENTRY`, `SHORT_EXIT`, and `SHORT_PARTIAL_EXIT`.
- Raw execution side remains available separately as `execution_side` (`BUY`/`SELL`) and may also appear in trade metadata as `side` for audit/cashflow compatibility.
- Legacy persisted runs may still have `signal=BUY` or `signal=SELL`; clients should prefer `position_signal` when present and fall back to `signal` for older runs.
- `ending_cash`, `cash_after`, and graph `cash` are cash-balance fields, not always spendable free cash.
- `cash_balance_after` is the explicit alias for the same cash-balance accounting value retained for compatibility.
- `final_equity` and graph `equity` are the primary net account value fields when positions are open.
- Trade `equity_after` is retained for compatibility as the execution row's mark-to-market audit value; clients should prefer `execution_equity_after` for entry-row equity display and `mark_to_market_equity_after` when explicitly showing candle-close audit valuation.
- `execution_equity_after` is fill-price equity immediately after execution. `mark_to_market_equity_after` is the audit value after the fill marked to candle close.
- Graph `equity` is the primary equity series. When a new entry remains open on its entry candle, graph `equity` uses execution-price valuation for that entry candle to avoid same-candle fill/close PnL; later candles use candle-close mark-to-market.
- Graph `close_price` remains the candle close for market reference. Graph metadata may include `equity_valuation_price`, the price actually used for the primary equity value when it differs from `close_price`.
- `final_equity` is the last value of the primary equity series, so a backtest ending on an entry candle follows the same entry-candle execution-price policy.
- New account-state fields are additive and optional for legacy runs. When present, `free_cash_after`/`free_cash`, `margin_used_after`/`margin_used`, and `short_proceeds_locked_after`/`short_proceeds_locked` should be preferred for buying-power display.
- For cash-bounded short simulations, `cash_after` may include short-sale proceeds. Those proceeds and the matching cash-bounded short collateral must not be displayed as unrestricted free cash; use `free_cash_after`/`available_buying_power_after`.
- Simulated margin metadata is backtest-only and must not be represented as real exchange margin/futures account state.
- `summary.metadata.trade_attribution` is additive for newer strategy-engine runs. It is computed from saved executions/equity points and contains lifecycle-based trade metrics plus grouped attribution by pattern, side, exit reason, and optional regime/session/timeframe tags.
- Frontend performance diagnostics consume these optional saved metadata paths when present:
  - `summary.metadata.performance_metrics.total_return`
  - `summary.metadata.performance_metrics.annualized_return`
  - `summary.metadata.performance_metrics.annualized_volatility`
  - `summary.metadata.performance_metrics.sharpe_ratio`
  - `summary.metadata.performance_metrics.sortino_ratio`
  - `summary.metadata.performance_metrics.calmar_ratio`
  - `summary.metadata.performance_metrics.max_drawdown`
  - `summary.metadata.performance_metrics.max_drawdown_duration_periods`
  - `summary.metadata.trade_attribution.trade_metrics.hit_ratio`
  - `summary.metadata.trade_attribution.trade_metrics.payoff_ratio`
  - `summary.metadata.trade_attribution.trade_metrics.expectancy`
  - `summary.metadata.trade_attribution.trade_metrics.profit_factor`
  - `summary.metadata.trade_attribution.trade_metrics.profit_factor_is_infinite`
  - `summary.metadata.trade_attribution.trade_metrics.average_r`
  - `summary.metadata.trade_attribution.trade_metrics.median_r`
  - `summary.metadata.trade_attribution.trade_metrics.max_consecutive_losses`
  - `summary.metadata.trade_attribution.exposure.exposure_fraction`
  - `summary.metadata.trade_attribution.turnover.turnover_ratio`
  - `summary.metadata.cost_summary.cost_to_gross_pnl_ratio`
  - `summary.metadata.cost_summary.zero_transaction_cost_assumption`
  Missing fields are legacy-compatible and must render as unavailable rather than as zero.
- `summary.metadata.performance_diagnostics` is additive for newer runs and may also be computed by the read-only API from saved metadata/trade/graph rows for legacy runs. Schema:
  - `schema_version`: `backtest_performance_diagnostics_v1`
  - `flags`: array of `{code, severity, category, message, evidence, suggested_next_analysis}`
  - `severity`: one of `INFO`, `WARNING`, `CRITICAL`
  - supported flag codes include `NEGATIVE_EXPECTANCY`, `LOW_HIT_RATE`, `POOR_PAYOFF_RATIO`, `HIGH_COST_DRAG`, `LARGE_OR_PERSISTENT_DRAWDOWN`, `NO_COMPLETED_TRADES`, `LOW_EXPOSURE`, `HIGH_TURNOVER`, `SHORT_SIMULATION_ONLY`, `ZERO_COST_ASSUMPTION`, `ENTRY_FILL_REFERENCE_DIVERGENCE`, `TAKE_PROFIT_NEGATIVE_PNL_ANOMALY`, `SOFT_INVALIDATION_DOMINANT`, `TIME_STOP_DOMINANT`, and `STOP_LOSS_DOMINANT`
  - `warnings`: non-fatal caveats such as missing metadata or weak sample size
  - `inference_strength`: `PARTIAL`, `WEAK`, or `NORMAL`
  This diagnostic is explanatory only. It must not trigger execution, parameter mutation, or strategy reruns.
- `summary.metadata.timing_diagnostics` is additive for newer strategy-engine runs and may also be approximated by the read-only API from saved trade and graph rows for legacy runs. Schema:
  - `schema_version`: `trade_timing_diagnostics_v1`
  - `path_mode`: `HIGH_LOW`, `MIXED_HIGH_LOW_CLOSE_APPROXIMATION`, or `CLOSE_ONLY_APPROXIMATION`
  - `completed_trade_count`: number of matched entry-to-final-exit lifecycles
  - `aggregate`: average `mfe_r`, `mae_r`, `realized_r`, `bars_to_mfe`, and `bars_to_mae`
  - `trades`: array of per-lifecycle path metrics including `mfe_price`, `mae_price`, `mfe_quote_pnl`, `mae_quote_pnl`, `mfe_r`, `mae_r`, `bars_to_mfe`, `bars_to_mae`, `bars_to_first_favorable_close`, `bars_to_exit`, exit-reason timing fields, and entry fill/reference/confirmation/zone distances
  - `flags`: array of `{code, severity, message, evidence}` where supported codes include `ENTRY_WAS_LATE_CHASING`, `EXIT_LEFT_MONEY_ON_TABLE`, and `IMMEDIATE_ADVERSE_EXCURSION`
  - `warnings`: non-fatal caveats such as close-only approximation or unmatched trade/path rows
  - `partial_exit_policy`: documents the entry-to-final-exit lifecycle approximation for partial exits
  Engine-created diagnostics use the full OHLC candle path between actual entry and exit. API fallback diagnostics for legacy rows may be close-only approximations and must be presented as explanatory, not as execution or optimization instructions.
- Trade attribution uses an entry-to-final-exit lifecycle as the completed trade unit, so partial exits contribute realized PnL to the lifecycle without inflating `completed_trade_count`.
- Missing attribution group keys are represented as `UNKNOWN`. Profit factor is `null` with `profit_factor_is_infinite=true` when there is positive gross profit and zero gross loss, avoiding non-JSON finite values.
- `diagnostics` is optional. When present, it is an index over saved run/summary/trade/graph metadata sections; it must not be generated by rerunning a strategy.
- `research_report` is optional and read-only. When present, schema `backtest_research_report_v1` summarizes the already-loaded saved run into portable JSON plus a markdown preview. It includes run identity, market, strategy parameters, redacted reproducibility metadata, risk settings, performance metrics, diagnostics, data-summary counts, limitations, safety boundary, and recommended next experiments. Report generation must not rerun a strategy, mutate parameters, call exchange/account endpoints, or expose API keys, database URLs, passwords, tokens, or credentials.
- Trade and graph `metadata` preserve JSON-safe unknown diagnostic fields from the simulated execution path, including sizing source, fill model, intrabar policy, score components, regime tags, and cost assumptions when available.
- For legacy runs with no diagnostic metadata, `diagnostics` may be `null`; clients must not infer missing diagnostics as zero or false values.
- New canonical strategy runs may include `run.metadata.reproducibility`. It is additive and may contain dataset identity, requested/actual candle ranges, candle-content hash, candle quality summary, strategy/config hashes, engine version, random seed slots, and redacted environment inputs. Clients must treat it as audit metadata, not executable instructions.
- New FVG strategy-engine runs may include `strategy_config.parameters.fvg_entry` and `summary.metadata.fvg_entry_mode`. These fields are read-only research metadata for selected FVG entry mode, expiry controls, fill rate, average bars waited, missed-trade count, and optional CLI comparison diagnostics. Supported entry modes are `MARKET_ON_CONFIRMATION_CLOSE`, `MARKET_ON_NEXT_OPEN`, `LIMIT_AT_ENTRY_REFERENCE`, `LIMIT_AT_PATTERN_MIDPOINT`, `LIMIT_AT_PATTERN_BOUNDARY`, and `LIMIT_AT_CUSTOM_PRICE`; clients must not treat them as live order instructions.
- New pattern strategy runs may include `strategy_config.parameters.pattern_execution_policy` and `summary.metadata.pattern_execution_policy`. Schema `pattern_execution_policy_v1` records `pattern_key`, `policy_key`, `selected_entry_mode`, `default_entry_mode`, `allowed_entry_modes`, `exit_assumptions`, `economic_rationale`, and `research_hypothesis`. This is a documented research hypothesis matrix, not a claim of profitability or a live execution policy.
- New strategy-engine runs may include `summary.metadata.risk_exit_audit`. Schema `risk_exit_audit_v1` records exit-reason distribution, average PnL/R by exit reason, stop/time/soft-invalidation dominance ratios, take-profit and hard-stop average R, first/final target hit rates, target distance averages, partial-exit PnL contribution, validation warnings for invalid stop/target direction, and dominance flags for negative-expectancy runs. This is explanatory diagnostics only and must not change risk defaults or create live order controls.
- New strategy-engine runs may include `summary.metadata.score_calibration`. Schema `pattern_score_calibration_v1` records score-bucket outcomes, hit ratio, expectancy, average/median R, profit factor, component placeholder rates, component present/absent average-R deltas where possible, and threshold sensitivity for candidate `minimum_pattern_score` values. Supported warning codes include `MISSING_SCORE_METADATA`, `SCORE_BUCKET_SAMPLE_TOO_SMALL`, `NO_MONOTONIC_SCORE_IMPROVEMENT`, `PLACEHOLDER_COMPONENT_DOMINATES_SCORE`, and `HIGH_SCORE_NEGATIVE_EXPECTANCY`. This is research evidence only; clients must not mutate thresholds or claim calibrated probability from it.
- Frontend strategy explanation panels consume these optional read-only fields when present: `strategy_config.metadata.explanation`, `strategy_config.parameters.pattern_execution_policy`, `summary.metadata.pattern_execution_policy`, `summary.metadata.fvg_entry_mode`, `summary.metadata.position_sizing`, `summary.metadata.cost_profile`, `summary.metadata.cost_summary`, `summary.metadata.risk_exit_audit`, `summary.metadata.trade_attribution`, `summary.metadata.performance_diagnostics`, and trade metadata fields such as `entry_mode`, `fill_price_source`, `fill_assumption`, `risk_per_unit`, `entry_reference`, `original_entry_reference`, `fill_adjusted_risk_per_unit`, `confirmation_close`, `exit_reason`, `target_name`, `stop_price`, `exit_price`, and `realized_r_multiple`. Missing values are legacy-compatible and must be rendered as unavailable/fallback text, not as zero or as live-trading readiness.
- Frontend run-conclusion panels consume `summary.metadata.performance_diagnostics`, `summary.metadata.timing_diagnostics`, `summary.metadata.risk_exit_audit`, `summary.metadata.score_calibration`, `summary.metadata.cost_summary`, and `summary.metadata.trade_attribution` to map deterministic flags into likely failure reasons, confidence labels, evidence rows, and recommended next analyses. These recommendations are explanatory text only; clients must not expose backtest execution, strategy mutation, or live order controls from them.
- Market-regime-enabled runs may include OHLCV-derived tradability proxy metadata on executions and attribution groups: `trading_value_percentile`, `liquidity_zscore`, `range_spread_proxy_percentile`, `wick_dominance_proxy`, `session_tag`, `weekday_tag`, `liquidity_regime`, and `spread_regime`. These fields are deterministic research proxies from supplied candles only; they are not true bid-ask spread, order-book liquidity, or exchange-session data. Frontends may group losses by `summary.metadata.trade_attribution.attribution.by_session`, `by_liquidity_regime`, `by_spread_regime`, and `by_weekday_tag`.
- New canonical CLI runs may include `strategy_config.parameters.workflow_settings` and `summary.metadata.workflow_settings`. Schema `canonical_cli_workflow_settings_v1` records whether candle continuity enforcement and market-regime tagging were enabled, selected market-regime window/minimum trading value, and backtest-only guardrail limits. These fields describe offline workflow settings only.
- New canonical CLI runs may include `strategy_config.parameters.cost_profile` and `summary.metadata.cost_profile`. Schema `transaction_cost_profile_v1` records selected static profile, manual override status, fee/spread/slippage bps, zero-cost status, and approximate cost sensitivity such as cost-to-gross-PnL ratio and break-even cost bps. Profiles are offline assumptions, not exchange fee lookups.

## 5.4 Optional `GET /api/backtest-runs/{backtest_run_id}/chart` (200)

Example shape:

```json
{
  "run_id": 123,
  "graph_points": [
    {
      "sequence": 1,
      "candle_open_time": "2024-01-01T00:00:00Z",
      "close_price": 50000.0,
      "equity": 10000.0,
      "signal": null
    }
  ],
  "warnings": []
}
```

Notes:

- Keep this endpoint read-only and derived from existing persisted rows.
- Do not return execution or mutation controls.

## 6) Error Response Schemas

All non-2xx responses:

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "human-readable message",
    "details": {
      "field": "limit"
    }
  }
}
```

Recommended error codes:

- `BAD_REQUEST` (`400`) for invalid path/query values.
- `NOT_FOUND` (`404`) when completed run does not exist.
- `INTERNAL_ERROR` (`500`) for unexpected server exceptions.
- `SERVICE_UNAVAILABLE` (`503`) when DB is configured but currently unreachable for a data endpoint.

## 7) Frontend Usage Notes

- Frontend must consume dashboard data through this API only.
- Frontend must not query PostgreSQL directly.
- Use `GET /api/backtest-runs` for the run selector list.
- Use `GET /api/backtest-runs/{id}` for selected-run detail panels and tables.
- Optional performance path: use `/chart` for large chart views if full trade metadata is not needed.
- UI should render:
  - completed run list
  - run summary cards
  - close price line
  - equity line
  - semantic position-signal markers with raw execution-side context
  - compact trade table
  - curated strategy parameters and metadata rather than raw JSON by default
  - strategy/pattern explanation, indicator usage, economic interpretation, and limitations when metadata is available
  - warnings banner/panel

## 8) Known Limitations

- Some older persisted pattern strategy runs (written before canonical strategy-engine financial persistence) can still contain placeholder-neutral values (`cash`, `equity`, and summary fields may be `0.0` or non-financial placeholders).
- This API must expose that limitation via `warnings` and must not silently reinterpret those values as real PnL outcomes.
- This contract does not provide pagination metadata beyond `limit` in v1.

## 9) Future Extension Notes

Potential future non-breaking additions:

- cursor/offset pagination metadata for run listing.
- explicit warning metadata flags on list rows.
- richer chart endpoint payload compression and downsampling hints.
- endpoint-level schema version field.
- filter by strategy key/version/parameter hash.

Out-of-scope future work (separate tasks required):

- backtest execution APIs
- strategy update APIs
- auth/user/account models
- live trading/order/account endpoints
