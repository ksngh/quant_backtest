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
    "metadata": {},
    "created_at": "2026-05-21T00:00:01Z"
  },
  "trades": [
    {
      "id": 1,
      "sequence": 1,
      "candle_open_time": "2024-01-01T00:10:00Z",
      "signal": "BUY",
      "price": 50000.0,
      "quantity": 0.01,
      "cash_after": 9500.0,
      "position_after": 0.01,
      "metadata": {}
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
      "metadata": {}
    }
  ],
  "warnings": [
    {
      "code": "PATTERN_PLACEHOLDER_EQUITY",
      "message": "Some persisted pattern runs may contain placeholder-neutral cash/equity values until richer financial persistence is implemented."
    }
  ]
}
```

Warning behavior:

- `warnings` is always present (may be empty array).
- Include `PATTERN_PLACEHOLDER_EQUITY` when run data indicates placeholder-neutral pattern persistence (for example pattern mode metadata or zeroed cash/equity semantics).

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
  - buy/sell/entry markers
  - trade table
  - strategy metadata
  - run metadata
  - warnings banner/panel

## 8) Known Limitations

- Some persisted pattern strategy runs currently use placeholder-neutral financial values (`cash`, `equity`, and summary fields can remain `0.0` or non-financial placeholders).
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
