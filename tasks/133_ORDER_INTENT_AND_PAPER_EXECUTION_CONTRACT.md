# Goal

Introduce a canonical order-intent and execution-report contract, then migrate paper execution to use strategy semantic actions with explicit `action_type`, `position_side`, and `execution_side` instead of ambiguous `BUY`/`SELL` signals.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/execution/paper_trader.py`
- `quant_bitcoin/risk/`
- `tests/execution/`
- `tests/backtesting/test_strategy_engine_accounting.py`

# Extracted Roles

- Owner role:
  - Execution contract owner.
  - Owns order-intent semantics, paper execution reports, and position-side aware execution behavior.
- Supporting roles:
  - Strategy action role: emits `ENTER_LONG`, `EXIT_LONG`, `ENTER_SHORT`, `EXIT_SHORT`, and partial exits.
  - Risk role: approves or blocks order intents later.
  - Test role: verifies long/short semantics.
- Forbidden roles:
  - No Binance account integration.
  - No signed requests.
  - No live orders.
  - No testnet orders.
  - No margin/futures implementation.

# Context

The canonical backtest engine already supports semantic long/short actions. The older paper trader is still signal-based and treats `SELL` as long-position reduction only. Real-time execution needs an explicit bridge from `StrategyAction` to `OrderIntent`, and paper execution must no longer rely on ambiguous `BUY`/`SELL` labels alone.

# Scope

- Add an `OrderIntent` model with symbol, action type, position side, execution side, quantity, order type, reference price, client order id, and metadata.
- Add `ExecutionReport` and `ExecutionFill` models.
- Add pure conversion from `StrategyAction` to `OrderIntent`.
- Implement or refactor paper execution around `OrderIntent`.
- Keep existing `PaperTrader` backward-compatible where practical, but mark legacy signal behavior clearly.
- Ensure paper execution can represent long entry, long exit, short entry in simulation mode, and short exit in simulation mode.
- Add controls to disallow shorts for spot-like paper mode.

# Out of Scope

- Binance testnet client.
- Binance live client.
- Signed request implementation.
- Real account balances.
- Margin/futures borrow/funding/liquidation behavior.
- Real fee/slippage reconciliation.

# Requirements

- `OrderIntent` must distinguish `position_side` from `execution_side`.
- `ENTER_LONG` must map to `position_side=LONG`, `execution_side=BUY`.
- `EXIT_LONG` must map to `position_side=LONG`, `execution_side=SELL`.
- `ENTER_SHORT` must map to `position_side=SHORT`, `execution_side=SELL`.
- `EXIT_SHORT` must map to `position_side=SHORT`, `execution_side=BUY`.
- `PaperExecutionClient` must return deterministic execution reports.
- Paper execution must support dry-run mode that records intent without mutating state.
- Spot-like paper mode must block `ENTER_SHORT` unless explicit simulation-short mode is enabled.
- No code in this task may call an exchange.

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

- Order-intent contract exists and is tested.
- Paper execution uses `OrderIntent` for new canonical paths.
- Long and short lifecycle labels are explicit in reports.
- Legacy `BUY`/`SELL` ambiguity is not used in new execution paths.
- Spot-like paper mode blocks short entries deterministically.
- Existing tests remain passing or are intentionally migrated.

# Required Tests

## Unit Tests

- Test `ENTER_LONG` to order intent mapping.
- Test `EXIT_LONG` to order intent mapping.
- Test `ENTER_SHORT` to order intent mapping.
- Test `EXIT_SHORT` to order intent mapping.
- Test generated client order id is deterministic or idempotent for the selected policy.
- Test paper long entry and exit.
- Test paper short entry and exit in simulation-short mode.
- Test spot-like paper mode blocks `ENTER_SHORT`.
- Test dry-run mode returns report without mutating balances.

## Integration Tests

- Test canonical strategy actions can flow into paper execution.
- Test real-time runner dependency can consume the order-intent interface through a fake execution client.

## Contract Tests

- Strategy code does not execute orders.
- Execution code does not generate strategy signals.
- Paper execution does not call exchange APIs.

## Safety Tests

- No signed requests.
- No API keys.
- No order/account endpoints.
- No live trading behavior.

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
pytest tests/execution
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_engine.py
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
