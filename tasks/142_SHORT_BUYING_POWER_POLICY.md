# Goal

Make short-entry buying-power behavior explicit so a `10_000` cash account cannot silently open `1 BTC` of short exposure at an `80_000` price under default backtest settings.

This task should preserve Task 117 short PnL accounting while preventing misleading oversized short exposure unless a later or explicit simulation policy allows it.

# Source Requirement

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/117_SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS.md`
- `tasks/135_PRODUCT_SPECIFIC_SHORT_POLICY_AND_EXECUTION_BOUNDARIES.md`
- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `tasks/141_LONG_CASH_BOUNDED_ENTRY_EXECUTION.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/strategies/actions.py`
- `tests/backtesting/test_strategy_engine_accounting.py`
- `tests/backtesting/test_strategy_engine.py`
- `tests/execution/`

# Extracted Roles

- Owner role:
  - Simulated short buying-power policy owner.
  - Owns whether short entries are allowed, resized, blocked, or delegated to explicit margin simulation.
- Supporting roles:
  - Product policy role: preserves Task 135 separation between simulated shorts and spot execution.
  - Strategy engine role: blocks/resizes short entries deterministically.
  - Metrics role: reports blocked/resized short intents clearly.
- Forbidden roles:
  - No real margin trading.
  - No real futures trading.
  - No borrow-fee or funding model.
  - No liquidation model.
  - No live order execution.
  - No exchange account/order endpoint calls.

# Context

Short accounting currently treats an `ENTER_SHORT` as a `SELL` that creates a negative position and adds the short-sale notional to `cash_after`. Equity remains correct because the negative position offsets cash, but `cash_after` can look like spendable money.

The default behavior must not allow oversized short exposure that exceeds the starting account's buying power unless a user explicitly selects a simulation policy that supports it.

Task 143 will introduce a minimal explicit margin/leverage guard. This task should establish the default non-margin short behavior.

# Scope

- Add a default short buying-power policy for backtest simulation.
- Determine and implement whether default non-margin shorts are blocked or resized when requested notional exceeds available cash/equity.
- Add stable reason strings for blocked/resized short entries.
- Preserve profitable and losing short PnL correctness from Task 117.
- Preserve `ENTER_SHORT -> SELL` and `EXIT_SHORT -> BUY` mappings for allowed simulation shorts.
- Ensure spot paper/testnet/live policy from Task 135 remains stricter than backtest simulation.
- Add tests for the observed high-price short scenario.

# Out of Scope

- Initial margin and leverage checks. Those are Task 143.
- New account-state fields such as free cash or locked proceeds. Those are Task 144.
- CLI flag wiring. That is Task 145.
- Documentation cleanup. That is Task 148.
- Real margin/futures/live trading behavior.

# Requirements

- With `starting_cash=10_000`, `price=80_000`, and requested `quantity=1`, default backtest settings must not silently open a full `1 BTC` short.
- The task must choose one deterministic default for oversized non-margin shorts:
  - block the entry, or
  - resize to cash-equivalent exposure.
- The chosen behavior must be documented in tests and metadata.
- Blocked short entries must not increment filled trade count.
- Resized short entries must record requested and filled quantity metadata.
- Existing short close PnL tests must still pass for allowed short fixtures.
- `allow_short=False` behavior must remain deterministic.
- Unsupported short-economics limitations must remain in summary metadata.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Tasks 140 and 141 are completed or explicitly approved as dependencies.
- [x] Confirm this Task 142 is recorded as the current active implementation task before coding.
- [x] Confirm Task 143 is not started before this task is complete.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to Task 143 as next if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Default simulated short policy prevents silent oversized `1 BTC` short exposure on a `10_000` cash account at an `80_000` price.
- Allowed short fixtures still compute profitable and losing short PnL correctly.
- Blocked/resized short entries have stable metadata and reason strings.
- Product-specific spot short blocking from Task 135 is not weakened.
- No live trading behavior is added.

# Required Tests

## Unit Tests

- Test `starting_cash=10_000`, `price=80_000`, `quantity=1` short is blocked or resized under default policy.
- Test blocked short does not count as filled trade.
- Test resized short records requested quantity and filled quantity if resizing is chosen.
- Test allowed short below buying-power limit still works.
- Test profitable short PnL remains positive.
- Test losing short PnL remains negative.
- Test `allow_short=False` remains deterministic.

## Integration Tests

- Test canonical strategy runner cannot silently produce oversized short exposure with default settings.
- Test spot paper/testnet/live product policy still rejects short intents.
- Test existing execution tests for simulated short behavior still pass where simulation is explicitly allowed.

## Contract Tests

- `ENTER_SHORT` remains `SELL` for allowed simulation shorts.
- `EXIT_SHORT` remains `BUY` for allowed simulation shorts.
- Existing result fields remain available.
- Summary limitation metadata remains present.

## Safety Tests

- No Binance order endpoint is called.
- No Binance account endpoint is called.
- No Binance margin endpoint is called.
- No Binance futures endpoint is called.
- No API keys are required.
- No live trading default is introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Short-buying-power changes do not pretend to be full margin/futures modeling.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_engine.py
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
