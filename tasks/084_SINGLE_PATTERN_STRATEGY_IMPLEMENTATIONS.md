# Task 084: Single-Pattern Strategy Implementations

## Area

Backtest/Core + Quant Research

## Goal

Implement strategy objects under `quant_bitcoin/strategies/` for each currently implemented single pattern.

Pattern detectors should remain pure detection modules. Strategies consume detectors plus risk/exit policies and produce strategy actions.

## Source Requirement

The owner wants strategies implemented under `strategies/`, with at least one strategy per pattern. Future tests should be strategy-level, not pattern-level.

## Required Reading

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- this task document
- `docs/22_STRATEGY_BACKTEST_ARCHITECTURE.md`
- Task 081 risk package changes
- `quant_bitcoin/backtesting/pattern_strategy.py`
- `quant_bitcoin/strategies/`
- `quant_bitcoin/patterns/`
- `quant_bitcoin/risk/`

## Scope

Create single-pattern strategy implementations for:

```text
FairValueGapStrategy
TrendlineBreakStrategy
OrderBlockStrategy
CupAndHandleStrategy
DiamondStrategy
AdamAndEveStrategy
```

Recommended layout:

```text
quant_bitcoin/strategies/patterns/
  __init__.py
  base.py
  fair_value_gap.py
  trendline_break.py
  order_block.py
  cup_and_handle.py
  diamond.py
  adam_and_eve.py
```

## Strategy Contract

Each strategy should expose a deterministic interface that can be consumed by a strategy backtester.

Recommended interface:

```python
class PatternStrategy:
    strategy_key: str
    strategy_name: str
    strategy_version: str

    def evaluate(self, candles_so_far, portfolio_state) -> list[StrategyAction]:
        ...
```

Or an equivalent dataclass/protocol.

## Strategy Action Contract

Strategies should emit semantic actions, not raw portfolio mutations.

Minimum fields:

```text
action_type:
  ENTER_LONG
  EXIT_LONG
  PARTIAL_EXIT_LONG
  SKIP

side:
  BUY or SELL when action maps to cashflow
  None when skipped/no action

reason:
  PATTERN_CONFIRMED
  TAKE_PROFIT
  HARD_STOP
  SOFT_INVALIDATION
  TIME_STOP
  NO_FILL
  RISK_PLAN_INVALID
  SHORT_DISABLED
  etc.

pattern_event_id
pattern_type
direction
entry_reference
stop_reference
target_reference
risk_plan
quantity_ratio
metadata
```

## Long/Short Policy

Default mode must be spot long-only.

- Bullish pattern entries may map to `ENTER_LONG`.
- Exits and partial exits may map to `EXIT_LONG` / `PARTIAL_EXIT_LONG`.
- Bearish pattern entries must not create short positions unless a future task explicitly enables paper-short research mode.
- If bearish events are detected while shorting is disabled, record `SKIP` with reason `SHORT_DISABLED` when diagnostics are enabled.

## Pattern-Specific Strategy Behavior

Each single-pattern strategy must:

1. Run only its own detector.
2. Use a configurable risk/exit policy from `quant_bitcoin.risk`.
3. Produce strategy actions.
4. Preserve no-look-ahead behavior by using completed candle prefixes only.
5. Avoid direct cash/equity mutation.
6. Avoid database access.
7. Avoid exchange/API access.

## Out of Scope

- No live trading.
- No real order execution.
- No exchange account/order endpoints.
- No frontend/backend dashboard changes.
- No new pattern detectors.
- No multi-pattern confluence strategy in this task.
- No walk-forward orchestration.

## Execution Steps

1. Define strategy base contract.
2. Implement single-pattern strategy classes.
3. Wire each strategy to its detector and default risk/exit policy.
4. Make strategies configurable but deterministic.
5. Add factory/helper for selecting a strategy by name or pattern.
6. Preserve old pattern backtest module until replacement task.
7. Add focused unit tests with synthetic candles/events.

## Acceptance Criteria

- Each currently supported pattern has a strategy class under `quant_bitcoin/strategies/`.
- Strategy classes do not mutate cash directly.
- Strategy classes do not persist records.
- Strategy classes emit semantic actions with reasons.
- Strategy classes can use different risk/exit policies through configuration.
- DIAMOND has a strategy implementation separate from `detect_diamond_patterns`.
- Bearish DIAMOND does not create a spot short by default.
- Tests prove that at least one synthetic bullish pattern can emit an `ENTER_LONG` action.

## Verification

Run:

```bash
pytest -q tests/strategies
pytest -q tests/patterns
pytest -q
git diff --check
```

## Required State Updates

- Update `STATUS.md`.
- Append completion to `PROJECT_HISTORY.md`.
- Update `BACKLOG.md` if new strategy follow-up candidates are created.

## Completion Summary Required

Include:

- strategies added
- default risk policies connected
- action contract summary
- tests added
- tests run
- known limitations
- recommended next task
