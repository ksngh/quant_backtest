# Candle Data Contract

# Standard Candle Schema

The standard candle schema has exactly these required fields:

| Field | Meaning |
| --- | --- |
| `timestamp` | Candle open time. |
| `open` | First traded price in the candle interval. |
| `high` | Highest traded price in the candle interval. |
| `low` | Lowest traded price in the candle interval. |
| `close` | Last traded price in the candle interval. |
| `volume` | Traded volume in the candle interval. |

# Rules

- `timestamp` must represent the candle open time.
- `open`, `high`, `low`, `close`, and `volume` must be numeric.
- Rows must be sorted ascending by `timestamp`.
- Data providers must normalize exchange-specific raw data before strategy code sees it.
- Strategy code must not depend on Binance-specific raw response fields.
- The first implementation may use a pandas `DataFrame`.
- Do not define a complex custom data model yet unless a future task asks for it.

# Multi-Timeframe Derived Candle Alignment

Multi-timeframe candles are derived research/backtest context, not a live feed.
When lower-timeframe candles are aggregated into a higher timeframe, the
higher-timeframe candle becomes visible only after it is fully closed.

For example, when deriving 5m candles from 1m candles:

- The 5m candle with open time `00:00` uses completed 1m candles from `00:00`
  through `00:04`.
- Its derived `close_time` is `00:05`.
- It is not visible to the base candle opened at `00:04`.
- It is first visible to the base candle opened at `00:05`.

The alignment helper returns explicit availability metadata rather than
silently forward-filling unavailable context:

- `contract_version`: multi-timeframe alignment contract identifier.
- `source_interval`: lower-timeframe source interval such as `1m`.
- `target_intervals`: derived intervals such as `5m` and `15m`.
- `availability_semantics`: higher-timeframe candles are visible only when
  `close_time <= base timestamp`.
- `no_lookahead_guarantee`: `true` when completed-candle alignment rules are
  applied.
- `mtf_<interval>_available`: per-row boolean availability flag.
- `mtf_<interval>_<field>`: aligned higher-timeframe OHLCV/open-close time
  fields, left missing when unavailable.

Partial or incomplete higher-timeframe windows are excluded from aligned OHLCV
fields and remain unavailable until a complete window exists.

# Review Checks

- Any provider returning candle data must return the standard schema.
- Strategy tests should use standard candle fields only.
- Binance downloader tests must prove raw Binance fields are normalized before strategy code receives data.
- Multi-timeframe backtest context must be derived from completed lower-timeframe candles only and must not expose in-progress higher-timeframe candles.
