# Backend Status

## Current Purpose
Backend read-only FastAPI API aligned to dashboard API contract and integration verification completed in Task 078.

## Active Task
No active backend task. Task 254 completed additional read-only FVG v2 channel source metadata exposure.

## Current Boundary
- Read-only API scope for completed backtest result dashboard.
- No backtest execution endpoints.
- No live trading, order execution, or exchange account endpoints.
- No auth/login in current dashboard task batch.
- FVG retest v2 diagnostics are exposed only as saved-run metadata/research-report fields; no backend execution endpoint was added.
- `GET /api/backtest-runs` supports read-only filters for market identity, strategy key, actual/created time ranges, total-return range, and saved cost profile metadata.
- Saved-run detail responses flatten optional FVG v2 parallel-channel metadata fields from trade metadata when present: channel geometry, channel candidate/scan source, entry/stop/target boundaries, stop source, retest structure low, line prices, and same-candle ambiguity flags.
