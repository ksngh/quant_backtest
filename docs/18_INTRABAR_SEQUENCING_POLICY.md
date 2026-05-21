# Intrabar Sequencing Policy and Stress Modes

## Why intrabar ambiguity matters

Backtests that use OHLC candles cannot observe the true price path within each candle.
A candle confirms only range and close, not whether high or low occurred first.
That uncertainty becomes material whenever two or more execution levels are reachable
inside a single candle (for example: entry, stop, target).

Without an explicit deterministic policy, simulation outcomes can drift based on
implementation details, creating hidden bias and unstable research decisions.

## Same-candle entry/stop/target ambiguity impact

When entry, stop, and target are all reachable in one candle:

- a favorable-first assumption can inflate win-rate and expectancy,
- an adverse-first assumption can deflate apparent strategy quality,
- inconsistent assumptions across modules can make experiments incomparable.

To control this, intrabar outcomes must be resolved with a shared reusable policy.

## Supported policy modes

Implemented in `quant_bitcoin.backtesting.intrabar_policy`:

- `CONSERVATIVE`
  - Stress mode preferring adverse outcomes in ambiguous stop-vs-target cases.
- `OPTIMISTIC`
  - Favorable stress mode preferring target when stop and target are both reachable.
- `STOP_FIRST`
  - Always resolve stop-vs-target ambiguity to stop.
- `TARGET_FIRST`
  - Always resolve stop-vs-target ambiguity to target.
- `ENTRY_FIRST_THEN_STOP`
  - For all-three-touch ambiguity, assume entry is established then stop resolves first.
- `ENTRY_FIRST_THEN_TARGET`
  - For all-three-touch ambiguity, assume entry is established then target resolves first.
- `SKIP_AMBIGUOUS`
  - Returns an explicit skipped ambiguous decision for stress filtering workflows.

## Contract expectations

- Logic is pure and deterministic.
- No market data fetching, persistence, or exchange calls.
- Inputs validate numeric finite prices and `high >= low`.
- Direction validation supports both `LONG` and `SHORT`.

## Promotion guidance

For promotion or go/no-go research decisions, conservative stress results should be
preferred over optimistic outcomes. Optimistic outcomes are still useful as sensitivity
bounds, but should not be the primary evidence for production promotion decisions.
