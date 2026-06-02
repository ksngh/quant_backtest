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
- `strategy_key?: string`
- `actual_start_time?: string` (UTC ISO-8601)
- `actual_end_time?: string` (UTC ISO-8601)
- `created_start_time?: string` (UTC ISO-8601)
- `created_end_time?: string` (UTC ISO-8601)
- `min_total_return?: number`
- `max_total_return?: number`
- `cost_profile?: string`
- `limit?: integer` (default: `20`, max: `100`)

Validation:

- `limit < 1` => `400`
- `limit > 100` => `400`
- invalid datetime formats => `400`
- start/end range inversions => `400`
- `min_total_return > max_total_return` => `400`

Semantics:

- Filters must map directly to `list_completed_runs(...)` inputs.
- `strategy_key` filters persisted strategy config keys exactly.
- `cost_profile` matches saved run/result cost-profile metadata or persisted strategy cost-profile parameters when available.
- Returned rows are newest-first by persisted run creation time.

## 4.3 `GET /api/backtest-runs/{backtest_run_id}`

Path parameter:

- `backtest_run_id: integer` (positive)

Query parameters:

- `graph_max_points?: integer` (optional, 100 to 20000)
- `graph_sampling_mode?: string` (optional, default: `preserve_markers`)

Validation:

- non-integer or `<= 0` => `400`
- `graph_max_points < 100` or `> 20000` => `422`
- missing completed run => `404`

Semantics:

- Must map to `load_run_for_graphs(backtest_run_id)`.
- Must not synthesize run data by re-running strategies/backtests.
- When `graph_max_points` is provided, `graph_points` may be reduced for dashboard chart performance.
- Reduced graph payloads must preserve the first and last graph point, signal or execution marker points, and trade timestamps when those timestamps exist in the saved graph series.
- Reduced graph payloads must keep chronological order and must not invent prices, equity, cash, timestamps, or signals.
- Diagnostics and research-report summaries should remain based on the saved run data, not on an invented rerun.
- `chart_metadata.graph_points` must describe any bounded graph response.

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
        "starting_cash": 1000000.0,
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
    "starting_cash": 1000000.0,
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
    "starting_cash": 1000000.0,
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
      "raw_price": 50000.0,
      "effective_price": 50020.0,
      "price_semantics": "raw_fill_price",
      "effective_price_semantics": "spread_slippage_adjusted_diagnostic_price",
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
        "cash_after_semantics": "cash_after is cash balance; equity_after includes long position market value",
        "cost_breakdown": {
          "schema_version": "execution_cost_breakdown_v1",
          "fee_cost": 0.5,
          "spread_cost": 0.15,
          "slippage_cost": 0.1,
          "total_cost": 0.75,
          "fee_bps": 10.0,
          "spread_bps": 3.0,
          "slippage_bps": 2.0,
          "effective_slippage_bps": 2.0,
          "volatility_bps": 10.0,
          "cost_profile_name": "conservative_crypto_1m",
          "cost_currency": "quote"
        }
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
  "chart_metadata": {
    "schema_version": "chart_payload_metadata_v1",
    "graph_points": {
      "schema_version": "graph_sampling_v1",
      "sampled": true,
      "original_point_count": 50000,
      "returned_point_count": 3000,
      "max_points": 3000,
      "sampling_mode": "preserve_markers",
      "marker_point_count": 24,
      "preserved_marker_point_count": 24,
      "marker_points_preserved": true
    }
  },
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

Chart payload behavior:

- `chart_metadata` is additive and may be omitted by legacy-compatible responses.
- The dashboard should request bounded detail responses with `graph_max_points` for large chart views instead of fetching and rendering unbounded `graph_points`.
- If `chart_metadata.graph_points.sampled=true`, clients should display that the chart is sampled and show `returned_point_count` versus `original_point_count`.
- `marker_points_preserved=false` means the saved run contained more marker/trade points than the requested chart budget could include; clients should treat the chart as a high-level overview rather than exact marker inspection.

Cash/equity semantics:

- `signal` is the preferred semantic position signal for new strategy-engine runs. Expected values include `LONG_ENTRY`, `LONG_EXIT`, `LONG_PARTIAL_EXIT`, `SHORT_ENTRY`, `SHORT_EXIT`, and `SHORT_PARTIAL_EXIT`.
- Raw execution side remains available separately as `execution_side` (`BUY`/`SELL`) and may also appear in trade metadata as `side` for audit/cashflow compatibility.
- For new strategy-engine runs, trade `price` and `raw_price` are the market-reachable raw fill price. `effective_price` is a spread/slippage-adjusted diagnostic reference and may sit outside the candle high/low range; clients must not label it as the raw execution price. Older persisted runs may have ambiguous `price` semantics if they were produced before this contract split.
- New strategy-engine trade metadata may include `price_semantics=raw_fill_price`, `effective_price_semantics=spread_slippage_adjusted_diagnostic_price`, and `cost_breakdown` using schema `execution_cost_breakdown_v1`. Cost breakdown fields include `fee_cost`, `spread_cost`, `slippage_cost`, `total_cost`, `fee_bps`, `spread_bps`, `slippage_bps`, `effective_slippage_bps`, `volatility_bps`, `cost_profile_name`, and `cost_currency`; legacy rows may omit the object.
- New cost-aware pattern runs may include `strategy_config.parameters.cost_aware_entry_filter`, `summary.metadata.cost_aware_entry_filter`, and per-entry `metadata.cost_aware_entry_filter`. When enabled, entries that fail the deterministic net reward/RR gate are emitted as `SKIP` with reason `COST_INFEASIBLE_NET_RR`.
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
- `research_report` is optional and read-only. When present, schema `backtest_research_report_v1` summarizes the already-loaded saved run into portable JSON plus a markdown preview. It includes run identity, market, strategy parameters, redacted reproducibility metadata, risk settings, performance metrics, diagnostics, `pattern_research_note`, data-summary counts, limitations, safety boundary, and recommended next experiments. Report generation must not rerun a strategy, mutate parameters, call exchange/account endpoints, or expose API keys, database URLs, passwords, tokens, or credentials.
- `research_report.pattern_research_note` uses schema `pattern_research_note_v1` and records pattern hypothesis, detector conditions, windows/candles observed, selected entry mode, fill assumptions, risk plan, cost profile, score reliability, no-lookahead status, regime dependence, top failure reasons, limitations, and recommended next analyses. It is generated from saved metadata and diagnostics only; clients must render unavailable legacy fields explicitly and must not present the note as live-trading readiness.
- Trade and graph `metadata` preserve JSON-safe unknown diagnostic fields from the simulated execution path, including sizing source, fill model, intrabar policy, pattern geometry, score components, regime tags, and cost assumptions when available.
- For legacy runs with no diagnostic metadata, `diagnostics` may be `null`; clients must not infer missing diagnostics as zero or false values.
- New canonical strategy runs may include `run.metadata.reproducibility`. It is additive and may contain dataset identity, requested/actual candle ranges, candle-content hash, candle quality summary, strategy/config hashes, engine version, random seed slots, and redacted environment inputs. Clients must treat it as audit metadata, not executable instructions.
- New FVG strategy-engine runs may include `strategy_config.parameters.fvg_entry` and `summary.metadata.fvg_entry_mode`. These fields are read-only research metadata for selected FVG entry mode, expiry controls, fill rate, average bars waited, missed-trade count, and optional CLI comparison diagnostics. FVG comparison modes include `MARKET_ON_CONFIRMATION_CLOSE`, `MARKET_ON_NEXT_OPEN`, `LIMIT_AT_PATTERN_MIDPOINT`, `LIMIT_AT_PATTERN_NEAR_BOUNDARY`, `LIMIT_AT_PATTERN_FAR_BOUNDARY`, `LIMIT_AT_PATTERN_BOUNDARY`, `LIMIT_AT_ENTRY_REFERENCE`, and `LIMIT_AT_CUSTOM_PRICE`; clients must not treat them as live order instructions.
- FVG inverse-direction research runs may include `strategy_config.parameters.fvg_direction` and per-action metadata fields `fvg_direction_mode`, `fvg_inverse_direction_enabled`, `original_position_side`, `effective_position_side`, and `direction_inversion_reason`. Schema `fvg_direction_mode_config_v1` records whether FVG direction is normal or explicit `INVERSE_CONTRARIAN`. In inverse mode, bullish FVG actions are tested as short candidates and bearish FVG actions are tested as long candidates. This is offline research metadata only and must not be interpreted as live execution logic or an automatically selected profitable variant.
- New pattern strategy runs may include `strategy_config.parameters.pattern_execution_policy` and `summary.metadata.pattern_execution_policy`. Schema `pattern_execution_policy_v1` records `pattern_key`, `policy_key`, `selected_entry_mode`, `default_entry_mode`, `allowed_entry_modes`, `exit_assumptions`, `economic_rationale`, `research_hypothesis`, `selected_entry_hypothesis`, and `entry_mode_hypotheses`. FVG and Order Block market modes are explicitly labeled as chase/momentum variants; retest modes are separate research hypotheses, not claims of profitability or live execution policies.
- FVG retest v2 research runs may include `strategy_parameters.fvg_v2`, `diagnostics.fvg_retest_v2`, and `summary.metadata.fvg_retest_v2`. Schema `fvg_retest_v2_settings_v1` records opt-in trend-score settings, Fibonacci confluence setting, liquidity-target requirement, stop mode, entry trigger, optional `parallel_channel` settings, and optional `close_volume_entry_filter` settings. Schema `fvg_retest_v2_diagnostics_v1` records read-only aggregate counts and settings. Multi-timeframe trend-score fields must be derived from completed higher-timeframe candles only. Pattern execution metadata may also include `mtf_trend_score`, `mtf_trend_direction`, `mtf_trend_aligned`, `mtf_trend_metadata`, `fib_confluence_pass`, `fib_retracement_level`, `fib_metadata`, `entry_trigger`, `touch_*`, `reaction_*`, `target_semantics.risk_targets`, and `risk_plan_atr_metadata.fvg_stop_mode`. These fields are offline research metadata only and do not imply live order behavior, order-book liquidity, frontend execution controls, or automatic parameter selection.
- FVG v2 parallel-channel rows may include top-level trade fields copied from metadata: `channel_mode`, `channel_id`, `channel_candidate_source`, `channel_scan_source`, `channel_trend_direction`, `channel_direction_rule`, `channel_boundary_direction_mode`, `channel_identity`, `channel_geometry`, `fvg_channel`, `entry_boundary`, `original_channel_entry_side`, `effective_channel_entry_side`, `stop_boundary`, `target_boundary`, `stop_source`, `pre_retest_candle_index`, `pre_retest_candle_timestamp`, `pre_retest_candle_low`, `pre_retest_candle_high`, `pre_retest_stop_valid`, `pre_retest_stop_invalid_reason`, `retest_structure_low`, `channel_lower_line_price_at_entry`, `channel_upper_line_price_at_entry`, `channel_width_at_entry`, `target_price_source`, `target_source`, `channel_target_policy`, `projected_channel_width_target`, `opposite_boundary_target_price`, `line_stop_price`, `line_stop_price_diagnostic`, `line_target_price`, `same_candle_entry_exit_ambiguity`, `close_volume_entry_filter`, and `cost_aware_entry_filter`. Schema `fvg_parallel_channel_v1` records the completed-candle window, same-slope lower/upper lines, width, tolerance, fit status, `channel_trend_direction`, and the available anchor/touch fields for either uptrend low-anchor channels or downtrend high-anchor channels. For Task 256+ channel entries, `channel_boundary_direction_mode=UPPER_RETEST_LONG_LOWER_RETEST_SHORT_V1` means an upper-boundary retest maps to LONG and a lower-boundary retest maps to SHORT; `original_channel_entry_side` records the prior Task 248 mapping and `effective_channel_entry_side` records the executable side. For Task 257+ channel entries, `channel_target_policy=PROJECTED_ENTRY_PRICE_PLUS_OR_MINUS_CHANNEL_WIDTH_V1` means LONG target is `entry_price + channel_width_at_entry`, SHORT target is `entry_price - channel_width_at_entry`, and `opposite_boundary_target_price` is diagnostic only. For Task 259+ channel entries, metadata field `retest_confirmation_basis=CLOSE_BASED_CHANNEL_BOUNDARY_RETEST_V1` means upper-boundary retests require `close >= upper_channel_line` and lower-boundary retests require `close <= lower_channel_line`; wick-only boundary touches must not be treated as channel retests. For Task 264+ channel entries, LONG stops use the immediately previous retest candle low with `stop_source=PRE_RETEST_CANDLE_LOW`, SHORT stops use the immediately previous retest candle high with `stop_source=PRE_RETEST_CANDLE_HIGH`, and invalid/missing pre-retest stop data must emit a non-executable skip. For Task 262+ channel entries, `close_volume_entry_filter` uses schema `close_volume_entry_filter_v1` and may block LONG or SHORT entries with reason `LOW_CLOSE_VOLUME_ENTRY_FILTER` when the completed signal candle volume ratio is below the configured prior-only baseline threshold; metadata records `applies_to_side=ALL`, `applies_to_sides=["LONG","SHORT"]`, current volume, baseline volume, volume ratio, threshold, window, baseline mode, input mode, pass/fail, and invalid-volume diagnostics. Cost-aware channel guards may emit `SKIP` rows with reason `COST_INFEASIBLE_TAKE_PROFIT`; `cost_aware_entry_filter` records gross reward bps, estimated round-trip cost bps, net reward bps, net R/R, target price, stop price, cost profile, and liquidity role. `channel_candidate_source=fvg_event_expansion` means the channel action came from a detected FVG event expansion; `channel_candidate_source=standalone_visible_prefix_scan` means the action came from the opt-in rolling visible-prefix channel scan. `atr_used_for_stop_or_target=false` must be preserved when present. Frontends may draw channel lines from saved metadata only and must not recompute channel geometry from raw candles; channel overlay line segments should be clipped to the saved trade/retest point when present.
- Pattern entry execution rows may include `metadata.pattern_entry_policy`. Schema `pattern_entry_policy_v1` records `entry_mode`, `fill_assumption`, `fill_price_source`, `entry_reference`, `requested_price`, `confirmation_close`, `bars_waited`, `entry_status`, `limit_price`, `max_wait_bars`, `expire_status`, `invalid_reason`, `supported_modes`, `entry_mode_hypothesis`, `entry_style`, `entry_reference_distance`, `zone_distance`, and `zone_boundary_variant`. For pattern entries, `requested_price` is the simulated fill price consumed by the strategy engine for sizing and transaction costs; `entry_reference` is research/reference metadata only and must not be displayed as the execution price. Market modes use the simulated market fill (`CONFIRMATION_CLOSE` or `NEXT_OPEN`), while limit/reference modes only set `requested_price` after a deterministic candle touch. Invalid entry-mode/event-shape combinations must produce non-executable `SKIP` actions.
- Pattern execution rows may include `metadata.target_semantics`. Schema `target_semantics_v1` separates `detector_target_reference`, generated `r_multiple_targets`, candidate `structural_targets`, candidate `measured_targets`, and final executable `risk_targets`. Take-profit rows may also include top-level `metadata.target_source` (`R_MULTIPLE`, `STRUCTURE`, or `MEASURED`). Clients must not assume detector `target_reference` is a measured move; use `target_source` and `target_semantics.risk_targets` when explaining realized exits.
- New strategy-engine runs may include `summary.metadata.risk_exit_audit`. Saved producers may still write `schema_version=risk_exit_audit_v1`; the API-facing `risk_exit_audit_v2` contract is backward compatible and covers exit-reason distribution, average PnL/R by exit reason, stop/time/soft-invalidation dominance ratios, take-profit and hard-stop average R, first/final target hit rates, target distance averages, partial-exit PnL contribution, validation warnings for invalid stop/target direction, target-source quality, MFE/MAE path attribution, intrabar ambiguity contribution, break-even/trailing movement metadata, cost-dominance flags, and dominance flags for negative-expectancy runs. This is explanatory diagnostics only and must not change risk defaults or create live order controls.
- New strategy-engine runs may include `summary.metadata.score_calibration`. Schema `pattern_score_calibration_v1` records score-bucket outcomes, hit ratio, expectancy, average/median R, profit factor, component placeholder rates, component present/absent average-R deltas where possible, score lift, candidate diagnostics, and threshold sensitivity for candidate `minimum_pattern_score` values. Supported warning codes include `MISSING_SCORE_METADATA`, `SCORE_BUCKET_SAMPLE_TOO_SMALL`, `NO_MONOTONIC_SCORE_IMPROVEMENT`, `PLACEHOLDER_COMPONENT_DOMINATES_SCORE`, `HIGH_SCORE_NEGATIVE_EXPECTANCY`, and `CHART_PATTERN_CANDIDATE_OVERFIT_RISK`. This is research evidence only; clients must not mutate thresholds or claim calibrated probability from it.
- Pattern execution rows may include `metadata.score_components` using the API-facing `score_components_v1` contract. Each component key should map to a record with `raw_score`, `weight`, optional `weighted_score`, optional `executable_weighted_score`, `source`, optional `description`, `is_placeholder`, and `included_in_executable_score`. Placeholder components are diagnostics/policy priors and must not be presented as observed market evidence.
- Pattern execution rows may include intrabar metadata using the API-facing `intrabar_policy_v1` contract. The policy may appear at `metadata.intrabar_policy` or nested under `metadata.exit_metadata.intrabar_policy`, with related fields such as `ambiguous_stop_target` and ambiguity decision metadata. This records historical candle-path simulation assumptions only and must not be interpreted as live order sequencing.
- Backend detail responses include `diagnostics.summary.metadata_schema_index` when diagnostics are present. Schema `backtest_metadata_schema_index_v1` reports observed/expected schema contracts for `pattern_execution_policy_v1`, `target_semantics_v1`, `score_components_v1`, API-facing `risk_exit_audit_v2` with compatible saved `risk_exit_audit_v1`, optional `fvg_retest_v2_diagnostics_v1`, and `intrabar_policy_v1`. This index is read-only schema discovery; missing contracts mean unavailable metadata, not false/zero values.
- Pattern geometry panels may consume optional trade metadata fields when present: `pattern_type`, `pattern_direction`, `pattern_status`, `zone_low`, `zone_mid`, `zone_high`, FVG gap fields, Order Block source/mitigation fields, Trendline pivot/touch/slope/breakout fields, Cup/Handle rim/bottom/handle/neckline fields, Diamond pivot split/boundary fields, and Adam/Eve low/neckline/height fields. They may also consume `score_components` fields such as `raw_score`, `weight`, `weighted_score`, `source`, `is_placeholder`, `included_in_executable_score`, and `description`, plus `candidate_diagnostics` schema `chart_pattern_candidate_diagnostics_v1`. Missing geometry or score-component values must be displayed as unavailable, not defaulted to zero. Placeholder score components must be visually separated from observed components, and clients must not describe `pattern_score` as a calibrated win probability unless a separate calibration artifact explicitly supports that claim.
- Frontend strategy explanation, execution-assumption, and FVG v2 diagnostics panels consume these optional read-only fields when present: `strategy_config.metadata.explanation`, `strategy_config.parameters.pattern_execution_policy`, `strategy_config.parameters.fvg_v2`, `summary.metadata.pattern_execution_policy`, `summary.metadata.fvg_entry_mode`, `summary.metadata.fvg_retest_v2`, `summary.metadata.position_sizing`, `summary.metadata.cost_profile`, `summary.metadata.cost_summary`, `summary.metadata.risk_exit_audit`, `summary.metadata.trade_attribution`, `summary.metadata.performance_diagnostics`, and trade metadata fields such as `entry_mode`, `entry_trigger`, `fill_price_source`, `fill_assumption`, `bars_waited`, `touch_timestamp`, `reaction_timestamp`, `reaction_candle_index`, `requested_price`, `risk_per_unit`, `original_risk_per_unit`, `entry_reference`, `original_entry_reference`, `fill_adjusted_risk_per_unit`, `risk_plan_aligned_to_fill`, `effective_slippage_bps`, `confirmation_close`, `target_semantics`, `target_source`, `exit_reason`, `target_name`, `stop_price`, `exit_price`, `realized_r_multiple`, `mtf_trend_*`, `fib_*`, and `risk_plan_atr_metadata.fvg_stop_mode`. Missing values are legacy-compatible and must be rendered as unavailable/fallback text, not as zero or as live-trading readiness.
- Frontend execution-assumption panels also consume `summary.metadata.short_economics`, `summary.metadata.risk_exit_audit.intrabar_ambiguity`, and nested exit metadata such as `exit_metadata.intrabar_policy` and `exit_metadata.ambiguous_stop_target`. These fields are explanatory only; clients must not render backtest execution controls, live order controls, or live margin/futures capability from them.
- Frontend run-conclusion panels consume `summary.metadata.performance_diagnostics`, `summary.metadata.timing_diagnostics`, `summary.metadata.risk_exit_audit`, `summary.metadata.score_calibration`, `summary.metadata.cost_summary`, and `summary.metadata.trade_attribution` to map deterministic flags into likely failure reasons, confidence labels, evidence rows, and recommended next analyses. These recommendations are explanatory text only; clients must not expose backtest execution, strategy mutation, or live order controls from them.
- Market-regime-enabled runs may include OHLCV-derived tradability proxy metadata on executions and attribution groups: `trading_value_percentile`, `liquidity_zscore`, `range_spread_proxy_percentile`, `wick_dominance_proxy`, `session_tag`, `weekday_tag`, `liquidity_regime`, and `spread_regime`. These fields are deterministic research proxies from supplied candles only; they are not true bid-ask spread, order-book liquidity, or exchange-session data. Frontends may group losses by `summary.metadata.trade_attribution.attribution.by_session`, `by_liquidity_regime`, `by_spread_regime`, and `by_weekday_tag`.
- New canonical CLI runs may include `strategy_config.parameters.workflow_settings` and `summary.metadata.workflow_settings`. Schema `canonical_cli_workflow_settings_v1` records whether candle continuity enforcement and market-regime tagging were enabled, selected market-regime window/minimum trading value, backtest-only guardrail limits, and optional `owner_default_profile` metadata. The owner profile metadata uses schema `owner_fvg_v2_channel_default_profile_v1`, records profile key `owner_fvg_v2_channel_default_v1`, selected/defaulted/explicit fields, applied values, and `start_time_defaulted=false`. These fields describe offline workflow settings only.
- New canonical CLI runs may include `cash_denomination`, `strategy_config.parameters.cash_denomination`, and `summary.metadata.cash_denomination`. Schema `backtest_cash_denomination_v1` records `source_starting_cash`, `source_currency`, `quote_currency`, `effective_quote_starting_cash`, `engine_starting_cash`, optional manual `conversion_rate`/`conversion_pair`/`conversion_source`, whether the currency flags were explicit, and `live_fx_lookup_used=false`. For `BTCUSDT`, engine cash, costs, PnL, and equity are USDT quote-currency values; CLI capital input defaults to KRW with a manual `krw_per_usdt=1500` conversion unless the run explicitly uses `--starting-cash-currency USDT` or another supported quote-cash setting.
- New canonical CLI runs may include `strategy_config.parameters.cost_profile` and `summary.metadata.cost_profile`. Schema `transaction_cost_profile_v1` records selected static profile, manual override status, fee/spread/slippage bps, and zero-cost status. `summary.metadata.cost_summary.zero_cost_warning` carries explicit zero-cost warnings, with `diagnostic_severity=HIGH` for zero-cost 1m pattern runs. When requested, `summary.metadata.cost_sensitivity_report` uses `transaction_cost_sensitivity_report_v1` to compare zero, baseline, conservative, and stress profiles deterministically. Profiles are offline assumptions, not exchange fee lookups.
- New strategy-engine runs may include `summary.metadata.short_economics` schema `short_economics_research_v1`. When `enabled=false`, legacy semantics are preserved and borrow fees, futures funding, maintenance margin, and liquidation remain explicitly unmodeled. When `enabled=true`, the engine may deduct deterministic borrow/funding carrying costs from short exposure and include diagnostic-only `liquidation_diagnostics` schema `short_liquidation_diagnostics_v1` with `would_liquidate`, estimated liquidation price, maintenance settings, and buffer ratios. These fields are research metadata only; clients must not render them as live margin/futures support, forced liquidation execution, or exchange account state.

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
