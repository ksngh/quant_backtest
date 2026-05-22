# Goal

Add a clear execution-price and entry-fill contract so canonical backtests can execute at simulated fill prices instead of always using candle close.

# Scope

- Extend strategy action contract with optional explicit execution price.
- Propagate entry/exit simulated prices from pattern action builder.
- Update strategy engine to use explicit execution price when valid, fallback to candle close when absent.
- Keep behavior backward compatible for existing actions without explicit price.

# Requirements

- Explicit execution price must be optional and validated (>0 and finite).
- Invalid explicit prices must be skipped deterministically.
- Entry simulation modes supported: MARKET_ON_CONFIRMATION_CLOSE, MARKET_ON_NEXT_OPEN, LIMIT_AT_ENTRY_REFERENCE.
- Stop/target exits must carry simulated exit prices into engine-consumable actions.

# Verification

```bash
pytest
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_pattern_action_builder.py
pytest tests/patterns/test_entry_simulation.py
```
