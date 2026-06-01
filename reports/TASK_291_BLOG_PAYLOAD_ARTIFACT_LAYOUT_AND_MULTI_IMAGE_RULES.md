# TASK 291 Blog Payload Artifact Layout and Multi-Image Rules

## Source

- Source persisted run: `1159` used internally for read-only graph/trade/cost/attribution extraction.
- Strategy: `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Period: `2026-04-20 00:00:00 UTC ~ 2026-05-19 23:59:00 UTC`.
- New artifact folder: `reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519`.

## Layout Change

Old Task 290 layout used a top-level payload plus shared image folder:

```text
reports/blog_payloads/task287-t281-pre-owner-high-slippage-report-payload.json
reports/blog_payloads/images/*.png
```

Task 291 replaces that with a strategy/period folder:

```text
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/payload.json
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/equity_curve.png
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/drawdown.png
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/price_with_trades.png
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/trade_pnl_distribution.png
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/cost_breakdown.png
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/side_attribution.png
reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/exit_reason_attribution.png
```

## Generated Images

- `equity_curve.png`: cost-adjusted equity curve from saved graph points.
- `drawdown.png`: drawdown from the same saved equity series.
- `price_with_trades.png`: BTCUSDT close price with saved entry/exit markers.
- `trade_pnl_distribution.png`: saved exit execution net PnL proxy distribution; official metrics still use lifecycle attribution.
- `cost_breakdown.png`: fee/spread/slippage totals from persisted cost metadata.
- `side_attribution.png`: Long/Short attribution from persisted lifecycle attribution.
- `exit_reason_attribution.png`: exit-reason attribution from persisted lifecycle attribution.

## Unavailable Images

- `rolling_return_or_expectancy.png`: not generated because official lifecycle-by-time rows are not available in the compact payload/read model.
- `regime_attribution.png`: not generated because current attribution is not sufficiently segmented beyond UNKNOWN groups for a useful daily-report figure.

## Legacy Cleanup

Removed legacy Task 290 shared-layout files:

- `reports/blog_payloads/task287-t281-pre-owner-high-slippage-report-payload.json`
- `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-equity-curve.png`
- `reports/blog_payloads/images/task287-t281-pre-owner-high-slippage-drawdown.png`
- `reports/blog_payloads/images`

## Verification Targets

- Payload JSON: `reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/payload.json`
- Image references are filenames only.
- All referenced images are colocated and non-empty.
- No new backtest was executed.
- No database mutation was performed.
