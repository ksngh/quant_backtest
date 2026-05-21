# Task 082: Strategy Backtest Architecture Boundary

## Area
Backtest/Core + Quant Research

## Goal
Convert the project direction from **pattern-level testing** to **strategy-level testing**.

Pattern modules must detect market structures only. Strategy modules must decide how detected patterns become trade actions. Risk/exit modules must define reusable stop-loss, take-profit, partial-exit, time-stop, and invalidation policies.

## Source Requirement

Owner requirements:

1. Pattern test should become strategy test.
2. Strategies must be implemented under `quant_bitcoin/strategies/`.
3. Single-pattern strategies must exist for each implemented pattern.
4. Strategy-level tests must use actual simulated capital.
5. Stop-loss and take-profit logic must be separated from pattern detection.
6. Risk/exit logic must be reusable and mixable with different patterns.
7. Strategy backtest must show actual buy/sell cash movement and final remaining equity.

## Current Problems To Address

Current pattern backtest behavior is not sufficient as strategy research:

- `quant-bitcoin-pattern-backtest` delegates to pattern simulation rather than a strategy object.
- Current pattern output stores semantic `ENTRY` rows instead of execution-level `BUY`/`SELL` rows.
- Pattern result summary can show `buy_count = 0` and `sell_count = 0` even when pattern trades exist.
- Pattern-specific risk/exit logic is coupled to pattern modules.
- Pattern persistence can confuse final remaining quantity with entry quantity.
- Cash/equity accounting is not yet a first-class strategy backtest contract.

## Required Reading

Before implementation, read:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- this task document
- `quant_bitcoin/backtesting/pattern_strategy.py`
- `quant_bitcoin/backtesting/pattern_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/basic.py`
- `quant_bitcoin/strategies/`
- `quant_bitcoin/patterns/`
- `quant_bitcoin/patterns/risk_exit.py`
- `quant_bitcoin/patterns/exit_simulation.py`

## Scope

Create or update architecture documentation and minimal code scaffolding defining the new separation:

```text
patterns/
  Pattern detection only.
  No cash accounting.
  No portfolio state.
  No strategy-level buy/sell decisions.
  No reusable risk/exit policy ownership.

risk/
  Stop-loss, take-profit, partial-exit, time-stop, trailing-stop, break-even, and invalidation policies.
  Reusable across patterns and strategies.

strategies/
  Strategy implementations.
  May consume pattern detectors and risk policies.
  Produces strategy actions.

backtesting/
  Strategy execution simulation.
  Converts strategy actions into BUY/SELL cashflows.
  Computes cash, position, equity, drawdown, and final summary.
```

## Required Design Decision

Adopt this execution model:

```text
Strategy semantic layer:
- ENTER_LONG
- EXIT_LONG
- PARTIAL_EXIT_LONG
- SKIP

Execution/accounting layer:
- BUY
- SELL
```

### Rationale

Use `ENTRY + EXIT reason` internally because pattern strategies need rich research semantics:

- stop-loss
- take-profit
- partial exit
- time stop
- soft invalidation
- no-fill
- skipped by risk policy

Use `BUY + SELL` at the execution/accounting layer because portfolio accounting needs explicit cashflow direction.

Do not choose only one. Preserve both.

## Out of Scope

- No live trading.
- No real Binance order execution.
- No signed requests.
- No API keys.
- No frontend/backend dashboard work.
- No new pattern family implementation.
- No futures or leverage.
- No production deployment work.

## Target Files / Directories

Likely files:

- `docs/22_STRATEGY_BACKTEST_ARCHITECTURE.md`
- `quant_bitcoin/strategies/`
- `quant_bitcoin/backtesting/`
- `quant_bitcoin/risk/`
- `STATUS.md`
- `PROJECT_HISTORY.md`
- `BACKLOG.md` if follow-up candidates are created

Do not move large modules in this task unless the implementation remains small and necessary. Heavy extraction belongs to Task 081.

## Execution Steps

1. Document the new architecture boundary.
2. Define the distinction between:
   - pattern event
   - risk/exit policy
   - strategy action
   - execution fill
   - portfolio trade
3. Define canonical strategy action names.
4. Define that long-only spot mode maps:
   - `ENTER_LONG` -> `BUY`
   - `EXIT_LONG` / `PARTIAL_EXIT_LONG` -> `SELL`
5. Define that short entries are disabled by default unless a future research-only paper-short task explicitly enables them.
6. Define how each single-pattern strategy should be named.
7. Update status/history documents after completion.

## Acceptance Criteria

- A document exists explaining pattern/risk/strategy/backtest boundaries.
- The project has an explicit decision that strategy actions and execution sides are separate concepts.
- The document explains why pure `BUY/SELL` is too weak for pattern research and why pure `ENTRY/EXIT` is too weak for cash accounting.
- No existing detector behavior is changed unless explicitly required.
- No live trading behavior is introduced.

## Verification

Run:

```bash
git diff --check
pytest -q
```

If full pytest cannot run in the environment, run targeted tests available for changed files and record the limitation.

## Required State Updates

After completion:

- Update `STATUS.md`.
- Append completion to `PROJECT_HISTORY.md`.
- Update `BACKLOG.md` only if new follow-up candidates are introduced or stale candidates are corrected.

## Completion Summary Required

Final response must include:

- files changed
- architecture decisions made
- tests run
- known limitations
- recommended next task
