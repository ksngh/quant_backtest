# Goal

Define and enforce a product-specific short policy so backtest short simulation, spot execution, margin execution, and futures execution cannot be confused.

This task does not implement margin or futures execution. It makes spot live/testnet behavior long-only and blocks short entry deterministically while preserving backtest short simulation metadata.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/execution/`
- `quant_bitcoin/risk/`
- `tests/backtesting/test_strategy_engine_accounting.py`
- `tests/execution/`
- `tasks/117_SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS.md`

# Extracted Roles

- Owner role:
  - Product execution policy owner.
  - Owns the difference between simulated shorts and executable product-specific short behavior.
- Supporting roles:
  - Backtest role: keeps simulated short accounting explicit.
  - Execution role: blocks unsupported short order intents.
  - Documentation role: makes limitations visible.
- Forbidden roles:
  - No margin borrow implementation.
  - No futures funding implementation.
  - No leverage implementation.
  - No liquidation model.
  - No real order execution in this task.

# Context

The strategy engine can simulate short positions using negative position quantity. That is useful for research, but it is not equivalent to real spot execution. Spot `SELL` reduces existing holdings; it does not open a short position. Margin and futures shorts require separate models and safety rules. This policy must be explicit before adding Binance testnet/live execution.

# Scope

- Add a product-mode policy contract such as `BACKTEST_SIMULATION`, `SPOT_PAPER`, `SPOT_TESTNET`, `SPOT_LIVE`, `MARGIN_DEFERRED`, and `FUTURES_DEFERRED`.
- Enforce that `ENTER_SHORT` is blocked for spot paper/testnet/live modes.
- Preserve `ENTER_SHORT` and `EXIT_SHORT` in backtest simulation mode.
- Add metadata/warnings when simulated shorts are used.
- Add deterministic reason strings for blocked short intents.
- Document that margin/futures shorts remain deferred.

# Out of Scope

- Implementing margin short execution.
- Implementing futures short execution.
- Borrow fee model.
- Funding fee model.
- Maintenance margin/liquidation model.
- Account endpoint integration.
- Live order execution.

# Requirements

- Spot-like execution modes must block `ENTER_SHORT`.
- Spot-like execution modes must not reinterpret `ENTER_SHORT` as a normal `SELL` of holdings.
- Spot-like `EXIT_SHORT` must be blocked unless there is a documented simulation context.
- Backtest simulation mode must continue to allow shorts if `allow_short=True`.
- Output metadata must clearly state unsupported short economics: no borrow fees, no futures funding, no maintenance margin or liquidation model.
- Reason strings must be stable for tests, for example `SHORT_NOT_SUPPORTED_FOR_SPOT`.
- The product policy must be reusable by paper, testnet, live, and real-time runner paths.

# Status Tracking

## Before Implementation

- [ ] Read `STATUS.md`.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `ENTER_SHORT` is blocked in spot paper/testnet/live product modes.
- `ENTER_SHORT` remains allowed in backtest simulation when configured.
- Blocked short intents include deterministic reason metadata.
- Documentation and CLI/runtime output do not imply that simulated shorts are real margin/futures shorts.
- Tests prove a spot short entry cannot become a plain `SELL` order.

# Required Tests

## Unit Tests

- Test spot product policy blocks `ENTER_SHORT`.
- Test spot product policy blocks `EXIT_SHORT` when no simulation context exists.
- Test backtest simulation policy allows `ENTER_SHORT`.
- Test reason string for blocked spot short.
- Test metadata includes short-model limitations.

## Integration Tests

- Test paper execution in spot mode blocks short intent.
- Test real-time runner in paper spot mode blocks short intent.
- Test canonical backtest still produces short executions when allowed.

## Contract Tests

- `ENTER_SHORT` remains mapped to `SELL` execution side for simulation.
- `EXIT_SHORT` remains mapped to `BUY` execution side for simulation.
- Execution product policy, not strategy logic, decides whether a short is executable.

## Safety Tests

- No margin endpoints.
- No futures endpoints.
- No order/account endpoint calls.
- No API keys.
- No live trading.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/execution
```

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
