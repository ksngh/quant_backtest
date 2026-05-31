# Task 286 BTCUSDT 1m Data Backfill And Gap Repair

- Status: `COMPLETED`
- Symbol: `BTCUSDT`
- Interval: `1m`
- Source: `binance_spot`
- Target range: `2026-04-20T00:00:00Z` to `2026-05-28T08:26:00Z`
- Dry run: `false`

## Before Audit

- Expected candles: `55227`
- Actual unique candles: `23027`
- Min open time: `2026-05-10T00:00:00Z`
- Max open time: `2026-05-28T08:26:00Z`
- Duplicate row count: `0`
- Missing range count: `2`
- Missing candle count: `32200`
- Missing ranges:
  - `2026-04-20T00:00:00Z` to `2026-05-09T23:59:00Z` (`28800` candles)
  - `2026-05-17T15:20:00Z` to `2026-05-19T23:59:00Z` (`3400` candles)

## Repair Results

| Range | Planned pages | Expected missing | Fetched closed | Estimated new | Duplicates | Conflicts | Repository upserts | Pages fetched |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2026-04-20T00:00:00Z` to `2026-05-09T23:59:00Z` | 29 | 28800 | 28800 | 28800 | 0 | 0 | 28800 | 29 |
| `2026-05-17T15:20:00Z` to `2026-05-19T23:59:00Z` | 4 | 3400 | 3400 | 3400 | 0 | 0 | 3400 | 4 |

## After Audit

- Expected candles: `55227`
- Actual unique candles: `55227`
- Min open time: `2026-04-20T00:00:00Z`
- Max open time: `2026-05-28T08:26:00Z`
- Duplicate row count: `0`
- Missing range count: `0`
- Missing candle count: `0`

## Safety Boundary

- Used Binance public market-data kline backfill path only.
- No API keys, signed requests, account endpoints, order endpoints, strategy tuning, live trading, futures, or leverage were used.

## Next Task

- Create or execute a locked OOS/WFO validation task on the repaired complete BTCUSDT 1m range before any strategy promotion claim.
