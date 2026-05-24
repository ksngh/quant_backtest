# Strategy Backtest Architecture Boundary (Task 082)

## Decision Summary

This project now separates **research semantics** from **execution accounting**:

- Semantic strategy actions are for research meaning and explainability.
- Execution sides are for cashflow and portfolio accounting.
- Both layers are required; neither is sufficient alone.

## Layer Boundaries

### `quant_bitcoin/patterns/`

Owns pattern detection only.

- Detects and emits pattern events.
- Must not own portfolio cash/equity state.
- Must not own reusable risk/exit policy packages.
- Must not emit final accounting trades.

### `quant_bitcoin/risk/`

Owns reusable risk/exit policies.

- Stop-loss, take-profit, partial-exit, time-stop, break-even, trailing-stop, invalidation policy contracts.
- Reusable across multiple pattern families and strategy classes.
- No market-data fetching, no exchange calls.

### `quant_bitcoin/strategies/`

Owns strategy decisions.

- Consumes pattern events and risk policy outputs.
- Emits canonical **semantic** strategy actions.
- Does not directly persist or account cash/equity.

### `quant_bitcoin/backtesting/`

Owns strategy execution simulation and accounting.

- Maps semantic actions into execution sides.
- Produces BUY/SELL cashflow records.
- Computes cash, position quantity, equity, and drawdown.
- Produces final strategy-level performance summaries.

## Canonical Action Model

### Semantic strategy actions (research layer)

- `ENTER_LONG`
- `EXIT_LONG`
- `PARTIAL_EXIT_LONG`
- `SKIP`

These actions preserve reasoning context such as:

- stop-loss exit
- take-profit exit
- partial exit
- time-stop
- soft invalidation
- no-fill
- skipped by policy

### Execution/accounting sides (portfolio layer)

- `BUY`
- `SELL`

These sides provide explicit cashflow direction required for accounting.

## Why Two Layers Are Required

### Why `BUY/SELL` alone is too weak for pattern research

`BUY/SELL` cannot represent *why* a strategy acted (invalidation, time-stop, policy skip, partial logic). Research quality drops when rationale is lost.

### Why `ENTRY/EXIT` semantics alone are too weak for accounting

Semantic action labels do not guarantee deterministic cashflow direction or quantity movement. Portfolio accounting requires explicit BUY/SELL side mapping.

## Strategy-Engine Execution Mapping

The strategy engine maps semantic actions into simulated cashflow sides:

- `ENTER_LONG` -> `BUY`
- `EXIT_LONG` -> `SELL`
- `PARTIAL_EXIT_LONG` -> `SELL`
- `ENTER_SHORT` -> `SELL`
- `EXIT_SHORT` -> `BUY`
- `PARTIAL_EXIT_SHORT` -> `BUY`
- `SKIP` -> no execution

Short actions are backtest simulation semantics only. They do not imply spot
paper/testnet/live short support and do not call exchange order/account
endpoints. Default simulated shorts are cash-bounded; explicit simulated margin
is opt-in, backtest-only, and models initial margin only by default. Optional
`ShortEconomicsConfig` settings can add research-only borrow/funding carrying
costs and diagnostic maintenance/liquidation flags. Those diagnostics never
submit orders, fetch exchange account data, or force-close positions.

The engine records both cash-balance fields (`cash_after`, `ending_cash`) and
account-state metadata (`free_cash_after`, `margin_used_after`,
`short_proceeds_locked_after`). When shorts are open, cash balance can include
short-sale proceeds and must not be presented as unrestricted free cash.

## Single-Pattern Strategy Naming Convention

Single-pattern strategy classes should follow:

- `FairValueGapStrategy`
- `TrendlineBreakStrategy`
- `OrderBlockStrategy`
- `CupAndHandleStrategy`
- `DiamondStrategy`
- `AdamAndEveStrategy`

These classes belong under `quant_bitcoin/strategies/` and consume detectors + reusable risk policies.
