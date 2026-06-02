# Backend Status

## Current Purpose
Backend read-only FastAPI API aligned to dashboard API contract and integration verification completed in Task 078.

## Active Task
No active backend task. Task 323 completed bounded graph payload support for large `1m` dashboard runs.

## Current Boundary
- Read-only API scope for completed backtest result dashboard.
- No backtest execution endpoints.
- No live trading, order execution, or exchange account endpoints.
- No auth/login in current dashboard task batch.
- FVG retest v2 diagnostics are exposed only as saved-run metadata/research-report fields; no backend execution endpoint was added.
- `GET /api/backtest-runs` supports read-only filters for market identity, strategy key, actual/created time ranges, total-return range, and saved cost profile metadata.
- `GET /api/backtest-runs/{id}` supports optional read-only graph payload controls: `graph_max_points` and `graph_sampling_mode=preserve_markers`. When bounded, the response includes `chart_metadata.graph_points` with original/returned counts, requested max, sampling mode, and marker preservation status.
- Saved-run detail responses flatten optional FVG v2 parallel-channel metadata fields from trade metadata when present: channel geometry, channel candidate/scan source, entry/stop/target boundaries, stop source, retest structure low, line prices, and same-candle ambiguity flags.
