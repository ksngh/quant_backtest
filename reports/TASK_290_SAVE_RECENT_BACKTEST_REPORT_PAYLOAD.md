# TASK 290 Save Recent Backtest Report Payload

## Source Selection

- Selected source: latest completed persisted backtest run `1159` from PostgreSQL.
- Strategy label: `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Source window: `pre_owner_0420_0519`.
- Cost profile: `high_slippage_stress`.
- Period: `2026-04-20 00:00:00 UTC ~ 2026-05-19 23:59:00 UTC`.
- PR reference for blog template field: https://github.com/ksngh/quant_backtest/pull/167.

## Generated Artifacts

- Task 290 originally generated a top-level payload and shared `images/` folder.
- Task 291 migrated the artifact to the current colocated folder layout:
  - Payload JSON: `reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/payload.json`
  - Equity curve image: `reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/equity_curve.png`
  - Drawdown image: `reports/blog_payloads/t281-b1-priority-ensemble-h120-t150-s75-cf100-ff002/20260420-20260519/drawdown.png`

## Payload Summary

- Completed trades: `252` round trips (`504` executions)
- Total return: `-35.5861%`
- Final equity: `644,139.40`
- Max drawdown: `-35.6147%`
- Win rate: `+3.97%`
- Profit factor: `0.0584`
- Expectancy: `-1,412.15`
- Total cost: `318,287.68`

## Notes

- The payload intentionally excludes internal run IDs, git commit IDs, raw experiment config, and artifact path inventories.
- Payload image fields contain filenames only: `task287-t281-pre-owner-high-slippage-equity-curve.png` and `task287-t281-pre-owner-high-slippage-drawdown.png`.
- Official performance values come from persisted lifecycle attribution, not ad hoc execution-row aggregation.
- This task did not execute a new backtest and did not mutate database records.
- Current image references are colocated filenames under the Task 291 artifact folder.
