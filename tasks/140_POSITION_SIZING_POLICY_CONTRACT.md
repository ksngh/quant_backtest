# Goal

Define an explicit position-sizing contract for strategy backtests so `trade_quantity`, cash-based sizing, target-notional sizing, and future margin-aware sizing cannot be confused.

This task is a contract task. It should introduce the smallest model/API surface needed for later execution tasks without changing live-order behavior and without implementing real exchange margin/futures behavior.

# Source Requirement

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_TEMPLATE.md`
- `tasks/117_SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS.md`
- `tasks/135_PRODUCT_SPECIFIC_SHORT_POLICY_AND_EXECUTION_BOUNDARIES.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/postgres_runner_cli.py`
- `quant_bitcoin/strategies/actions.py`
- `tests/backtesting/test_strategy_engine_accounting.py`
- existing strategy runner CLI tests under `tests/backtesting/`

# Extracted Roles

- Owner role:
  - Backtest sizing contract owner.
  - Owns how requested strategy quantities are interpreted before the execution engine fills an action.
- Supporting roles:
  - Strategy engine role: consumes the sizing contract at fill time.
  - CLI role: eventually exposes the sizing mode safely.
  - Persistence/API role: receives additive metadata only when a later task wires it.
- Forbidden roles:
  - No live trading.
  - No real Binance order execution.
  - No Binance margin/futures integration.
  - No account endpoint calls.
  - No liquidation, borrow-fee, or funding implementation.
  - No frontend redesign.

# Context

The engine currently accepts `StrategyEngineConfig(starting_cash=10000.0, trade_quantity=1.0, allow_short=True)`. A `quantity=1` action against BTCUSDT can mean `1 BTC`, which is much larger than a `10_000` cash account when BTC is near `80_000`.

Long entry already has a cash cap path, but the contract is implicit. Short entry accounting from Task 117 is internally coherent, but sizing/buying-power semantics are still implicit and can confuse users when `cash_after` jumps after a short entry.

The next tasks depend on a stable sizing contract before modifying fill behavior.

# Scope

- Add an explicit backtest position-sizing contract.
- Support at least these conceptual modes, unless an equivalent simpler naming scheme is chosen:
  - `FIXED_QUANTITY`: preserve current explicit quantity semantics.
  - `CASH_FRACTION`: size by a fraction of available cash/equity.
  - `TARGET_NOTIONAL`: size by desired quote-currency notional.
- Define how action-level `quantity` interacts with config-level sizing.
- Define deterministic behavior when both action quantity and sizing config are present.
- Add validation for invalid sizing inputs.
- Add metadata/reason strings sufficient for later tasks to explain resizing or blocking.
- Keep public result objects backward-compatible.

# Out of Scope

- Enforcing long cash cap behavior beyond existing behavior.
- Enforcing short buying-power rules.
- Implementing leverage or initial-margin checks.
- Adding `free_cash`, `margin_used`, or locked-proceeds fields.
- Wiring full CLI flags.
- Updating frontend or backend display.
- Real order/account endpoint behavior.

# Requirements

- Position sizing must be represented by a focused config/model rather than ad hoc booleans.
- Defaults must preserve current behavior unless the task explicitly documents a safe default change and updates tests.
- Invalid values must fail deterministically:
  - negative sizing values,
  - non-finite values,
  - cash fractions outside the allowed range,
  - zero or negative target notional.
- The contract must specify precedence between action-level quantity and engine-level sizing mode.
- The contract must be side-aware enough for later long and short tasks to reuse it.
- The contract must not imply that margin or futures execution is implemented.
- The contract must be testable without database, network, Binance, or frontend dependencies.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 139 is the latest completed task and no active implementation task is recorded.
- [x] Confirm Task 138 remains blocked unless explicit live-order approval exists.
- [x] Confirm this Task 140 is recorded as the current active implementation task before coding.
- [x] Confirm Task 141 is not started before this task is complete.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to Task 141 as next if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A position-sizing config/model exists and is imported from a sensible backtesting module.
- The sizing model can express fixed quantity, cash fraction, and target notional semantics or their documented equivalents.
- Sizing validation has deterministic errors for invalid values.
- Existing backtest behavior remains unchanged unless explicitly covered by tests.
- Existing Task 117 short accounting tests still pass.
- No live trading behavior is added.

# Required Tests

## Unit Tests

- Test valid fixed-quantity sizing config.
- Test valid cash-fraction sizing config.
- Test valid target-notional sizing config.
- Test invalid negative, zero, non-finite, and out-of-range sizing values.
- Test action-level quantity precedence is deterministic.
- Test default config preserves existing strategy-engine behavior.

## Integration Tests

- Test `run_strategy_backtest_engine` accepts the new sizing config without changing existing fixed-quantity fixtures.
- Test canonical strategy runner can construct the default sizing config internally if needed.

## Contract Tests

- Existing `StrategyEngineConfig.trade_quantity` remains readable or has a backward-compatible migration path.
- Existing `StrategyExecution` fields remain unchanged.
- `ENTER_SHORT` and `EXIT_SHORT` execution-side mappings remain unchanged.

## Safety Tests

- No Binance order endpoint is called.
- No Binance account endpoint is called.
- No Binance margin endpoint is called.
- No Binance futures endpoint is called.
- No API keys are required.
- No `.env` files are created or modified.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- No behavior change hidden inside a contract-only task.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
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
