# Task 087: Strategy Backtest Regression And Research Tests

## Area

Backtest/Core + Quant Research

## Goal

Add regression tests and research-facing tests proving that the new strategy-level backtest flow produces correct cash, position, equity, and `BUY`/`SELL` outputs.

This task ensures the issues discovered in the current pattern backtest flow do not return.

## Source Requirement

The owner requires that all previously discovered issues be solved so that strategy-level tests show actual capital movement and final remaining money.

## Required Reading

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- this task document
- Task 080 architecture doc
- Task 081 risk package
- Task 082 strategies
- Task 083 engine
- Task 084 CLI
- `docs/15_RESEARCH_PROTOCOL.md`
- `docs/21_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md`

## Scope

Add tests for the new strategy-level flow.

Recommended test files:

```text
tests/strategies/test_single_pattern_strategies.py
tests/backtesting/test_strategy_engine_accounting.py
tests/backtesting/test_strategy_cli_persistence.py
tests/backtesting/test_pattern_strategy_regressions.py
```

## Required Regression Tests

### 1. No `ENTRY`-only persistence regression

Assert strategy backtest persistence records execution-side rows:

```text
BUY
SELL
```

not only:

```text
ENTRY
```

### 2. No hardcoded zero buy/sell count

Assert:

```text
buy_count == number of BUY executions
sell_count == number of SELL executions
```

### 3. No final remaining quantity used as entry quantity

Create a synthetic trade that fully exits:

```text
remaining_quantity_ratio = 0.0
```

Expected:

```text
entry quantity > 0
BUY row quantity > 0
SELL row quantity > 0
```

### 4. Cash and equity move

Given:

```text
starting_cash = 10000
BUY 1 unit at 100
SELL 1 unit at 110
```

Expected:

```text
ending_cash = 10010
ending_position = 0
final_equity = 10010
total_return = 0.001
```

Before costs.

### 5. Partial exits are correct

Given:

```text
entry_quantity = 1.0
exit 0.33 at TP1
exit 0.33 at TP2
exit 0.34 at TP3
```

Expected:

```text
sum exit quantities = 1.0
ending_position = 0
cash reflects all exits
```

### 6. DIAMOND strategy diagnostic behavior

For DIAMOND:

```text
no event -> no trade with reason
WEAK event -> no trade or diagnostic skip depending strategy policy
VALID bullish event -> ENTER_LONG then BUY
VALID bearish event with short disabled -> SKIP SHORT_DISABLED
```

### 7. Exit reason preservation

When exit is caused by:

```text
HARD_STOP
TAKE_PROFIT
SOFT_INVALIDATION
TIME_STOP
```

The persisted execution metadata must preserve the reason.

### 8. Cost accounting sanity

If cost model is enabled:

```text
net_pnl <= gross_pnl
```

For zero cost:

```text
net_pnl == gross_pnl
```

### 9. No exchange behavior

Tests must assert or inspect that strategy backtests do not call:

```text
Binance order endpoints
exchange account endpoints
signed requests
API key loading
```

## Research Test Requirements

At least one test should validate quant-research semantics:

```text
strategy action reason is preserved
pattern event id is preserved
risk plan id or metadata is preserved
R-multiple is calculated
cash/equity accounting is deterministic
```

## Out of Scope

- No live trading.
- No real Binance calls.
- No frontend/backend dashboard tests.
- No walk-forward validation implementation.
- No multiple-testing experiment registry implementation.
- No new pattern detectors.

## Execution Steps

1. Add deterministic synthetic candles.
2. Add fake strategy or synthetic single-pattern strategy fixtures.
3. Add engine accounting tests.
4. Add CLI/persistence tests.
5. Add DIAMOND-specific regression tests.
6. Add cost-zero and cost-positive tests if cost support exists.
7. Run full test suite.

## Acceptance Criteria

- Tests fail against the old pattern-level accounting behavior.
- Tests pass after Tasks 080-084 are implemented.
- `BUY`/`SELL` execution rows are verified.
- Real cash/equity accounting is verified.
- DIAMOND behavior is covered.
- Exit reasons are covered.
- No live/exchange behavior is introduced.

## Verification

Run:

```bash
pytest -q tests/backtesting/test_strategy_engine_accounting.py
pytest -q tests/strategies/test_single_pattern_strategies.py
pytest -q tests/backtesting/test_strategy_cli_persistence.py
pytest -q tests/backtesting
pytest -q tests/strategies
pytest -q
git diff --check
```

## Required State Updates

- Update `STATUS.md`.
- Append completion to `PROJECT_HISTORY.md`.
- Update `BACKLOG.md` if new follow-up research metrics or experiment-registry tasks are discovered.

## Completion Summary Required

Include:

- tests added
- regressions covered
- tests run
- known limitations
- recommended next task
