# Goal

Make long-entry fill behavior explicitly cash-bounded under the new position-sizing contract.

A backtest starting with `10_000` cash must not silently buy more than `10_000` quote-currency notional plus costs can support. If a requested long quantity is too large, the engine must deterministically resize or block according to the selected sizing/fill policy.

# Source Requirement

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `tasks/117_SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/costs.py`
- `quant_bitcoin/strategies/actions.py`
- `tests/backtesting/test_strategy_engine_accounting.py`
- `tests/backtesting/test_strategy_engine.py`

# Extracted Roles

- Owner role:
  - Long-entry cash-bounded fill owner.
  - Owns long-side affordability, resize/block behavior, and reason metadata.
- Supporting roles:
  - Position-sizing role: provides desired quantity/notional.
  - Transaction-cost role: contributes fee/spread/slippage to affordability.
  - Metrics role: reports blocked/resized fills clearly.
- Forbidden roles:
  - No short buying-power changes.
  - No margin/leverage behavior.
  - No live trading.
  - No real order/account endpoint calls.
  - No frontend redesign.

# Context

The current `_open_position` path for longs already reduces quantity when `notional + fee` exceeds cash. That behavior is useful, but it is implicit and tied directly to fixed quantity. After Task 140 introduces an explicit sizing contract, long behavior should be made deliberate, tested, and explainable.

This task focuses only on long entries. Short buying-power behavior is Task 142.

# Scope

- Apply the Task 140 sizing contract to long entries.
- Preserve or formalize current long auto-resize behavior.
- Add deterministic block behavior if the selected policy says not to resize.
- Include reason metadata for resized or blocked long entries.
- Ensure transaction costs are included in affordability checks.
- Ensure cash never becomes invalid due to a long entry that exceeds available cash.
- Add regression coverage for high-price BTC-style examples.

# Out of Scope

- Short entry behavior.
- Margin/leverage behavior.
- Free-cash/margin-used fields beyond the existing long cash/equity values.
- CLI flag wiring.
- Persistence schema changes unless strictly necessary for additive metadata.
- Live/testnet/paper execution behavior.

# Requirements

- With `starting_cash=10_000`, `price=80_000`, and requested `quantity=1`, long fill must be no larger than affordable quantity after costs.
- Cash-fraction sizing must compute deterministic long quantity.
- Target-notional sizing must compute deterministic long quantity and respect available cash.
- Fixed-quantity sizing must remain backward-compatible unless the selected policy says to block rather than resize.
- If the fill is resized, execution metadata must explain that the requested quantity was reduced by affordability constraints.
- If the fill is blocked, execution metadata must include a stable reason string such as `INSUFFICIENT_CASH_FOR_LONG`.
- Existing long PnL tests must remain valid.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 140 is completed or explicitly approved as a dependency.
- [x] Confirm this Task 141 is recorded as the current active implementation task before coding.
- [x] Confirm Task 142 is not started before this task is complete.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to Task 142 as next if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Long fills are explicitly cash-bounded through the sizing contract.
- The `10_000` cash / `80_000` price / `1 BTC` long scenario fills at an affordable quantity or blocks deterministically.
- Transaction costs are included in long affordability.
- Resize/block reason metadata is stable and tested.
- Existing long and short accounting tests still pass.
- No short policy behavior is changed in this task.

# Required Tests

## Unit Tests

- Test fixed-quantity long request greater than cash is resized or blocked according to policy.
- Test `starting_cash=10_000`, `price=80_000`, `quantity=1` long cannot produce negative cash.
- Test cash-fraction long sizing at 25%, 50%, and 100% where practical.
- Test target-notional long sizing respects cash and costs.
- Test long resize metadata includes requested quantity and filled quantity.
- Test long block reason string is deterministic.

## Integration Tests

- Test `run_strategy_backtest_engine` high-price long fixture.
- Test transaction-cost config with high-price long fixture.
- Test canonical strategy runner default still produces expected long fills on existing fixtures.

## Contract Tests

- Existing `cash_after`, `position_after`, and `equity_after` fields remain available.
- Existing summary `trade_count`, `buy_count`, and `sell_count` semantics remain compatible.
- Existing long execution side remains `BUY` for entry and `SELL` for exit.

## Safety Tests

- No Binance order endpoint is called.
- No Binance account endpoint is called.
- No margin/futures endpoint is called.
- No API keys are required.
- No live trading flag or default is introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Long-only behavior changes do not leak into short/margin policy.

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
