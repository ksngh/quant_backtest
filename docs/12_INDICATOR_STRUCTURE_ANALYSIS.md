# Indicator Structure Analysis

# Purpose

This document reviews the implemented indicator modules in `quant_bitcoin.indicators` as of Task 046. It is a documentation-only analysis based on the current codebase and the owner-provided indicator task documents. It does not define new behavior, new public APIs, live trading behavior, or exchange execution behavior.

# Assumptions And Boundaries

- Input candle data is already available to the caller; indicator modules do not fetch market data.
- Indicator modules are pure calculation/detection helpers. They do not read secrets, call exchange APIs, place orders, persist data, schedule jobs, or make final trading decisions.
- The implemented indicator package currently covers ATR, Volume Ratio, Pivot High / Pivot Low, Swing Structure, Support / Resistance Zones, Displacement Candles, and OHLCV-derived Market Regime tagging.
- Liquidity and spread context are currently available as OHLCV proxy fields inside `market_regime.py`; real order-book liquidity and true bid/ask spread remain future external-data scope.

# Package Structure

The package entry point is `quant_bitcoin/indicators/__init__.py`. It re-exports the public calculation functions, configuration dataclasses, status/direction enums, output-column constants, and selected helper functions from the implemented modules.

Implemented modules:

- `atr.py` — Average True Range, normalized ATR, and volatility classification.
- `volume_ratio.py` — rolling baseline volume ratio and volume status classification.
- `pivots.py` — deterministic pivot high / pivot low detection.
- `swing_structure.py` — higher-high, lower-high, higher-low, lower-low labels and market structure status from pivot data.
- `support_resistance_zone.py` — mechanical support/resistance zone construction from pivot events.
- `displacement_candle.py` — directional displacement candle detection from candle body/range, ATR, and volume-ratio data.
- `market_regime.py` — realized-volatility, trading-value liquidity, high-low spread proxy, trend-strength, mean-reversion z-score, and combined market-regime labels from supplied OHLCV candles.

The package design keeps indicator logic inside the indicator modules and exposes only explicit public objects through `__all__`. This supports direct imports from either a concrete module, such as `quant_bitcoin.indicators.atr`, or the package namespace, such as `quant_bitcoin.indicators.calculate_atr`.

# Common Design Patterns

## Pandas DataFrame Inputs

Most indicator entry points expect a `pandas.DataFrame` with a documented set of required columns. Examples:

- ATR requires `symbol`, `timestamp`, `high`, `low`, and `close`.
- Volume Ratio requires `symbol`, `timestamp`, and `volume`.
- Pivots require `symbol`, `timestamp`, `open`, `high`, `low`, and `close`.
- Support / Resistance Zones consume pivot rows rather than raw candles.
- Swing Structure consumes pivot rows rather than raw candles.
- Displacement Candles require `symbol`, `timestamp`, `open`, `high`, `low`, `close`, and may use `atr` and `volume_ratio` columns depending on configuration.

Numeric columns are converted with pandas numeric conversion in the modules that consume them. Missing required columns raise `ValueError`. Empty input generally returns an empty output frame with the module's declared output columns, or a null-filled snapshot for snapshot helpers.

## Deterministic Validation

Configuration dataclasses validate their thresholds and windows in `__post_init__`. The validation style is explicit and deterministic:

- window/period values must be positive where applicable;
- thresholds that represent ratios or multipliers must be non-negative;
- ordered thresholds must remain in the expected order;
- enum-like options supplied as strings are coerced and invalid strings raise `ValueError`.

Input validation focuses on shape and numeric correctness. The modules avoid network calls, mutable global state, and hidden external dependencies.

## Configuration Objects

Each implemented indicator has a frozen configuration dataclass:

- `AtrConfig`
- `VolumeRatioConfig`
- `PivotConfig`
- `SwingStructureConfig`
- `SupportResistanceZoneConfig`
- `DisplacementCandleConfig`
- `MarketRegimeConfig`

These objects hold mechanical parameters and defaults. They are optional at the public entry point; when omitted, the module creates its default config.

## Enums And Status Values

Enums are used for explicit status and classification values:

- ATR: `AtrSmoothingMethod`, `VolatilityStatus`.
- Volume Ratio: `VolumeAverageMethod`, `VolumeStatus`.
- Pivots: `PivotType`.
- Swing Structure: `SwingLabel`, `MarketStructureStatus`.
- Support / Resistance Zones: `ZoneType`, `ZoneStatus`.
- Displacement Candles: `DisplacementDirection`, `DisplacementStatus`.
- Market Regime: `RegimeVolatility`, `LiquidityRegime`, `SpreadRegime`, `TrendRegime`, `MeanReversionRegime`.

Outputs generally store enum values as strings rather than enum instances, which makes the result frames easier to serialize and compare in tests.

## Snapshot Helpers

ATR, Volume Ratio, and Displacement Candle modules include latest-row snapshot helpers:

- `calculate_atr_snapshot(candles, config=None)`
- `calculate_volume_ratio_snapshot(candles, config=None)`
- `calculate_displacement_candle_snapshot(candles, config=None)`
- `calculate_market_regime_snapshot(candles, config=None)`

These helpers run the batch calculation/detection path and return the latest output row as a dictionary. If there are no rows, the helper returns a dictionary with the expected output fields set to `None`.

## Empty-Result Behavior

The DataFrame-returning modules define output-column constants and use empty-frame helpers. This means callers can rely on a stable schema even when no indicator row or no zone is available.

A common distinction is:

- invalid rows: the module returns one row for an input candle, but marks the row invalid and includes a reason/status;
- empty results: the input is empty or no eligible structure exists, so the module returns an empty frame with known columns.

# Indicator Modules

## Average True Range (`atr.py`)

Primary public entry points:

- `calculate_atr(candles, config=None) -> pd.DataFrame`
- `calculate_true_range(high, low, previous_close) -> float | None`
- `classify_volatility(normalized_atr_percent, config=None) -> str`
- `calculate_atr_snapshot(candles, config=None) -> dict`

`calculate_atr` returns one row per input candle with true range, ATR, normalized ATR, normalized ATR percentage, smoothing method, volatility status, and `is_valid`.

Supported smoothing methods are `SMA`, `EMA`, and `RMA`. The default is `RMA`, with the first RMA value initialized from the first full-period SMA. With `require_full_window=True`, early warm-up rows are returned as invalid rows and receive `UNKNOWN` volatility status.

Normalized ATR is calculated as `atr / close`; normalized ATR percent is the normalized value multiplied by 100. If `close <= 0`, normalized values are unavailable even when the ATR itself can be calculated.

Visible limitations:

- ATR consumes provided candles only; it does not source market data.
- The module does not decide stop placement or position sizing. It only provides mechanical volatility values for other consumers.

## Volume Ratio (`volume_ratio.py`)

Primary public entry points:

- `calculate_volume_ratio(candles, config=None) -> pd.DataFrame`
- `classify_volume_status(volume_ratio, config=None) -> str`
- `calculate_volume_ratio_snapshot(candles, config=None) -> dict`

`calculate_volume_ratio` returns one row per candle with current volume, rolling average volume, volume ratio, confirmation flag, volume status, and validity. The default rolling average uses a full configured window and includes the current candle in the rolling baseline.

Supported average methods are `MEAN` and `MEDIAN`. Volume status can be `HIGH`, `INCREASED`, `NORMAL`, `LOW`, or `INVALID`.

Visible limitations:

- The module measures relative volume only. It does not implement liquidity based on quote volume or trading value.
- It does not fetch candles or exchange volume data.

## Pivot High / Pivot Low (`pivots.py`)

Primary public entry points:

- `detect_pivots(candles, config=None) -> pd.DataFrame`
- `remove_close_duplicate_pivots(pivots, config) -> list[dict]`

`detect_pivots` scans local windows around each candle to find pivot highs and pivot lows. It uses configurable left and right windows. With `require_full_window=True`, boundary candles that do not have enough surrounding candles are emitted as unconfirmed rows rather than being silently interpreted as confirmed pivots.

Pivot rows include the pivot type, pivot index, pivot price, source OHLC values, confirmation index/timestamp, `is_confirmed`, and strength fields. Duplicate same-type pivots that occur too close together can be removed deterministically, retaining the stronger pivot based on price direction.

Visible limitations:

- The detector is based on local candle windows. It does not infer broader trend semantics by itself.
- ATR filtering exists as an optional mechanical threshold, but the module still only emits pivot events; downstream modules decide how to use those events.

## Swing Structure (`swing_structure.py`)

Primary public entry points:

- `classify_swing_structure(pivots, config=None) -> pd.DataFrame`
- `classify_high(current_high, previous_high, config=None) -> str`
- `classify_low(current_low, previous_low, config=None) -> str`
- `classify_market_status(recent_labels, config=None) -> str`

Swing Structure consumes pivot rows and labels relationships between consecutive highs and lows. High pivots can be classified as `HH`, `LH`, `EQUAL_HIGH`, `EQUAL_OR_NOISE`, or `UNKNOWN`; low pivots can be classified as `HL`, `LL`, `EQUAL_LOW`, `EQUAL_OR_NOISE`, or `UNKNOWN`. Recent labels are then summarized into market structure statuses such as `UPTREND`, `DOWNTREND`, `RANGE`, `TRANSITION`, or `UNKNOWN`.

The module is explicitly pivot-derived. It depends on the pivot schema rather than raw candle OHLCV input.

Visible limitations:

- Swing Structure does not detect pivots itself; callers must provide pivot rows.
- The classification is mechanical and does not execute trades or determine final strategy signals.

## Support / Resistance Zone (`support_resistance_zone.py`)

Primary public entry points:

- `detect_support_resistance_zones(pivots, current_close=None, atr=None, timestamp=None, config=None) -> pd.DataFrame`
- `merge_overlapping_zones(zones, config=None) -> list[dict]`
- `merge_support_resistance_overlaps(zones, config=None) -> list[dict]`
- `update_zone_status(zone, current_close, atr, config=None) -> dict`

Support / Resistance Zones are built from pivot events. Pivot lows produce support candidates and pivot highs produce resistance candidates. The module groups touches into price zones using either ATR-based zone width or a fallback price-rate width, applies minimum touch-count rules, optionally merges overlapping zones, and updates zone status relative to the latest close.

Zone types are `SUPPORT`, `RESISTANCE`, and `MIXED`. Zone statuses are `VALID`, `WEAK`, `STRONG`, `BROKEN`, `FLIPPED`, and `INVALID`.

Visible limitations:

- The module does not call the pivot detector itself; it expects pivot rows.
- It does not use order-book liquidity or bid-ask spread data.
- Zone output is a mechanical context object, not a trade order or strategy decision.

## Displacement Candle (`displacement_candle.py`)

Primary public entry points:

- `detect_displacement_candles(candles, config=None) -> pd.DataFrame`
- `detect_displacement_candle(candle, config=None) -> dict`
- `calculate_displacement_candle_snapshot(candles, config=None) -> dict`
- `invalid_displacement_result(reason, base=None) -> dict`

The Displacement Candle module identifies strong directional candles. It calculates body size, candle range, body ratio, close location, ATR-normalized range when ATR is supplied and enabled, and volume-ratio confirmation when volume filtering is enabled.

Directional values are `BULLISH`, `BEARISH`, `NONE`, and `INVALID`. Status values are `VALID`, `WEAK`, `NONE`, and `INVALID`. A valid displacement candle requires sufficient body ratio, directional close location, and configured ATR/volume filters. Weak rows may exist when the candle has some directional structure but does not satisfy every confirmation threshold.

Visible limitations:

- This module does not calculate ATR or Volume Ratio internally. Pattern detectors that need displacement confirmation enrich candles with ATR and Volume Ratio first.
- It does not infer a higher-level pattern by itself; it only labels candles.

## Market Regime (`market_regime.py`)

Primary public entry points:

- `calculate_market_regime(candles, config=None) -> pd.DataFrame`
- `calculate_market_regime_snapshot(candles, config=None) -> dict`
- classifier helpers for volatility, liquidity, spread, trend, mean-reversion, and combined market-regime labels.

`calculate_market_regime` returns one row per candle with realized volatility, trading value, average trading value, liquidity regime, high-low spread proxy, spread regime, trend strength, trend regime, mean-reversion z-score, mean-reversion regime, combined market regime, validity, and reason fields.

Output schema columns are defined by `MARKET_REGIME_OUTPUT_COLUMNS`. Required input columns are `symbol`, `timestamp`, `open`, `high`, `low`, `close`, and `volume`; optional `quote_volume` is used as trading value when present and enabled. Warm-up rows are emitted with `is_valid=false`, `market_regime=UNKNOWN`, and `reason=warmup`.

Visible limitations:

- Liquidity is a trading-value proxy from OHLCV, not an exchange order-book depth model.
- Spread is a high-low candle range proxy, not true bid/ask spread.
- The module supplies context labels only. It does not tune strategies, alter pattern entry behavior, place orders, or call exchange APIs.

# Relationship To Normalized Candle Data

Indicator modules assume candle data is normalized before or at the calculation boundary:

- timestamps must be present where required;
- OHLCV values must be numeric for modules that consume them;
- raw candles are expected to represent completed candles, especially when used by pattern detectors downstream;
- symbol is included in most indicator outputs for traceability.

The indicators do not know how candles were obtained. CSV providers, PostgreSQL providers, WebSocket ingestion, and future Binance downloaders remain separate concerns.

# Relationship To Pivot-Derived Data

Several indicators form a dependency chain:

1. Raw candle OHLCV data can be passed to ATR, Volume Ratio, Displacement Candle, and Pivot detection.
2. Pivot detection creates pivot events with pivot type, index, price, and confirmation metadata.
3. Swing Structure consumes pivot events to classify HH/LH/HL/LL style market structure.
4. Support / Resistance Zone detection consumes pivot events to create touch-based support, resistance, or mixed zones.
5. Pattern detectors reuse ATR, Volume Ratio, Pivots, and Displacement Candles directly. Pattern detectors may use support/resistance and swing-structure concepts from the source documents, but not every current detector calls every indicator module.

# Deferred Or Unsupported Indicator Behavior

The following behavior is visible in requirements or pattern configuration but not implemented as reusable indicator modules in the current package:

- Liquidity / trading-value filter.
- Bid-ask spread filter.
- Order-book or market-depth analysis.
- Live exchange execution or real order placement.
- Machine learning, portfolio optimization, leverage, futures, dashboards, schedulers, or web frameworks.

Pattern modules that mention liquidity or spread filters accept explicit pass/fail configuration values and validate them when required; they do not silently approximate unavailable modules.
