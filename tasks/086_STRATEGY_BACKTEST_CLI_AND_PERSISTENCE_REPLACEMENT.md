# Task 086: Strategy Backtest CLI And Persistence Replacement

## Area

Backtest/Core + Quant Research

## Goal

Replace the pattern-level CLI behavior with a strategy-level backtest CLI that persists true simulated cash/equity and `BUY`/`SELL` execution rows.

The command must satisfy the owner expectation:

```bash
quant-bitcoin-pattern-backtest \
  --pattern DIAMOND \
  --start-time 2026-05-21T00:00:00Z \
  --starting-cash 10000
```

should either route to the new strategy backtest behavior or clearly deprecate the old command and provide the equivalent new command.

## Source Requirement

The owner wants pattern testing changed into strategy testing. Existing discovered issues must be solved so that strategy-level backtests show actual remaining money after buys and sells.

## Required Reading

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- this task document
- Task 080 architecture doc
- Task 081 risk package
- Task 082 strategy classes
- Task 083 strategy engine
- `quant_bitcoin/backtesting/pattern_postgres_runner_cli.py`
- `quant_bitcoin/persistence/`
- `pyproject.toml`
- existing CLI tests

## Scope

Create a strategy backtest CLI.

Recommended command:

```bash
quant-bitcoin-strategy-backtest \
  --strategy DIAMOND \
  --start-time 2026-05-21T00:00:00Z \
  --starting-cash 10000
```

Backward compatibility:

```bash
quant-bitcoin-pattern-backtest --pattern DIAMOND ...
```

may either:

1. route to the strategy backtest engine, or
2. emit a clear deprecation message and fail with the equivalent replacement command.

Preferred: route to the strategy engine for compatibility, while documenting that it is now strategy-level.

## Required CLI Options

Minimum:

```text
--database-url
--source
--symbol
--interval
--strategy
--pattern            # compatibility alias for single-pattern strategy
--start-time
--end-time
--starting-cash
--trade-quantity
--no-persist
```

Optional if implemented in Task 083:

```text
--sizing-mode
--risk-fraction
--cost-profile
--maker-fee-bps
--taker-fee-bps
--spread-bps
--slippage-bps
```

## Required JSON Output

The CLI output must include:

```json
{
  "strategy": {
    "name": "DIAMOND_PATTERN_STRATEGY",
    "strategy_type": "single_pattern",
    "pattern": "DIAMOND"
  },
  "portfolio": {
    "starting_cash": 10000.0,
    "ending_cash": 0.0,
    "ending_position": 0.0,
    "final_equity": 0.0,
    "total_return": 0.0
  },
  "summary": {
    "trade_count": 0,
    "buy_count": 0,
    "sell_count": 0,
    "max_drawdown": 0.0
  },
  "executions": [],
  "events": [],
  "warnings": []
}
```

Actual values depend on data and strategy outcomes.

## Persistence Requirements

Persist true strategy backtest outputs:

```text
backtest_runs.starting_cash
backtest_results.ending_cash
backtest_results.ending_position
backtest_results.final_equity
backtest_results.total_return
backtest_results.buy_count
backtest_results.sell_count
backtest_trades.signal = BUY or SELL
backtest_graph_points.cash
backtest_graph_points.position
backtest_graph_points.equity
```

Do not persist all strategy executions as `ENTRY` only.

## Diagnostics Requirement

If no `BUY`/`SELL` occurs, output must make the reason inspectable:

```text
candle_count = 0
no strategy events
only weak events
risk plan invalid
short disabled
insufficient cash
no fill
no exit
```

Do not silently output empty trades without diagnostics.

## Out of Scope

- No frontend/backend dashboard work.
- No live trading.
- No real orders.
- No exchange account/order endpoints.
- No futures/leverage.
- No walk-forward runner.
- No new pattern implementation.

## Execution Steps

1. Add new CLI or refactor existing CLI.
2. Select strategy by `--strategy` or compatibility `--pattern`.
3. Load PostgreSQL candles as before.
4. Run strategy engine from Task 083.
5. Persist true executions and equity curve.
6. Ensure `BUY`/`SELL` rows are stored.
7. Preserve exit reasons in trade metadata.
8. Update README or CLI docs.
9. Add CLI tests.

## Acceptance Criteria

- `--starting-cash 10000` affects actual simulated portfolio state.
- A synthetic DIAMOND strategy test can produce `BUY` and `SELL`.
- `buy_count` and `sell_count` are no longer hardcoded to zero.
- Fully exited trades are not saved with zero quantity.
- Graph points contain time-varying equity when trades occur.
- If no trade occurs, the CLI reports why.
- The command does not call exchange order/account endpoints.
- Backward compatibility behavior is documented.

## Verification

Run:

```bash
pytest -q tests/backtesting
pytest -q tests/strategies
pytest -q tests/market_data
pytest -q
quant-bitcoin-strategy-backtest --help
quant-bitcoin-pattern-backtest --help
git diff --check
```

If packaged CLI invocation is unavailable in the environment, use `python -m` equivalent and record the limitation.

## Required State Updates

- Update `STATUS.md`.
- Append completion to `PROJECT_HISTORY.md`.
- Update `BACKLOG.md` to remove or revise stale pattern-backtest placeholder-equity follow-ups.
- Update README or local docs if command behavior changes.

## Completion Summary Required

Include:

- CLI behavior changed
- persistence behavior changed
- compatibility behavior
- tests added
- tests run
- known limitations
- recommended next task
