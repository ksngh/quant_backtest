# Indicator Timing Contract

This document records whether indicator calculations include the current completed candle.
It is a research/backtest timing contract only. It does not add live trading, order execution,
exchange credentials, or intrabar exchange data.

## General Rule

Current-inclusive indicators are no-lookahead when the strategy signal is evaluated after the
current candle has closed. They are not appropriate for pre-close or intrabar assumptions unless
the caller explicitly uses a prior-only baseline where one is available.

## Timing Metadata

Indicator timing metadata uses `indicator_timing_metadata_v1`:

- `current_candle_included`: whether the indicator value uses the evaluated candle.
- `requires_closed_candle`: whether the value assumes the evaluated candle is complete.
- `warmup_period`: minimum candle count before the default output can become valid.
- `confirmation_delay`: number of future closed candles required before the event is confirmed.
- `baseline_mode`: plain-language baseline semantics.
- `safe_usage`: recommended timing context.

## Indicator Contracts

| Indicator | Default Current Candle | Closed Candle Required | Warm-up | Confirmation Delay | Notes |
| --- | --- | --- | --- | --- | --- |
| ATR | Included | Yes | `AtrConfig.period` | `0` | True range uses current high/low/close and previous close. Safe after candle close. First valid default row is at index `period - 1`. |
| Volume Ratio | Included by default | Yes by default | `VolumeRatioConfig.window` | `0` | Use `baseline_mode=PRIOR_ONLY` or the compatibility flag `baseline_includes_current=False` for a prior-only baseline; warm-up becomes `window + 1`. |
| Displacement Candle | Included | Yes | External ATR/volume warm-up | `0` | Uses current OHLC, ATR, and volume ratio supplied by caller. |
| Pivot | Excluded until confirmed | Yes | `left_window + right_window + 1` | `right_window` | Pivot at index `i` is only confirmed at `i + right_window`. |
| Market Regime | Included | Yes | max configured windows | `0` | Percentile/z-score baselines can exclude current via `percentile_zscore_include_current=False`. |
| RSI | Included | Yes | `window + 1` effective closes | `0` | RSI is based on latest close-to-close change and is safe after candle close. |
| EMA Trend | Included | Yes | `max(slow_period, slope_lookback + 1)` | `0` | EMA fast/slow and slope features include the current completed candle close. |
| Multi-Timeframe Trend Score | Included | Yes | EMA trend warm-up per available timeframe | `0` | Diagnostic-only composite score using completed base candles and latest completed higher-timeframe candles. Missing higher-timeframe context is explicit and not treated as neutral agreement. |

## Multi-Timeframe Trend Score Metadata

The multi-timeframe trend score uses `multitimeframe_trend_score_v1` row metadata:

- `source_timeframe`: base timeframe such as `1m`.
- `timeframes`: configured score components such as `1m`, `5m`, and `15m`.
- `configured_weight`: sum of configured component weights.
- `available_weight`: sum of weights whose component is valid at the row timestamp.
- `missing_timeframes`: timeframes unavailable because of warm-up or missing completed candles.
- `components`: per-timeframe score, weight, direction, feature timestamp, missing reason, and EMA subcomponents.
- `diagnostic_only`: `true`; the score is not an auto-trading signal by default.

Pattern detectors currently consume completed candle frames. Their ATR, volume-ratio,
displacement, pivot, and regime inputs should therefore be interpreted as after-close features
unless a future task explicitly adds pre-close or intrabar signal semantics.

ATR warm-up rows are emitted as invalid (`is_valid=False`) when `require_full_window=True`.
Pattern detectors that normalize gap size, breakout distance, pattern height, or stop buffers
by ATR must skip candidate events until the relevant ATR row is valid. For a pattern requiring
the current candle's ATR, this means the earliest possible ATR-normalized event cannot occur
before candle index `AtrConfig.period - 1` under the default configuration.
