# Synthetic Pattern Fixtures

These fixtures provide small deterministic OHLCV candle sets for pattern tests.
They are offline research/test data only:

- no exchange clients
- no API keys
- no live order or account endpoints
- no random generation

The builders intentionally keep candle paths simple so detector, entry, exit,
risk, and no-lookahead tests can reuse the same economic setup without hidden
state or network dependencies.
