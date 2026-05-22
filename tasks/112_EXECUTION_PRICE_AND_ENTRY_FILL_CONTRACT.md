# Goal

Add a clear execution-price and entry-fill contract so canonical backtests can execute at simulated fill prices instead of always using candle close.

This task focuses on the technical execution interface: pattern entry simulation, explicit execution price propagation, and engine support for using the requested fill or exit price.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/patterns/entry_simulation.py`
- `quant_bitcoin/backtesting/intrabar_policy.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- existing tests under `tests/backtesting/` and `tests/patterns/`

# Extracted Roles

- Owner role:
  - Backtesting execution-contract owner.
  - Owns how semantic actions become simulated executions at explicit prices.
- Supporting roles:
  - Pattern entry role: determines whether and where historical entries are filled.
  - Strategy action role: carries semantic intent and optional execution instructions.
  - Engine role: applies execution instructions to cash, position, and equity.
- Forbidden roles:
  - No real order execution.
  - No live exchange fill simulation based on real-time order books.
  - No market-depth modeling unless separately tasked.
  - No transaction-cost CLI implementation in this task.
  - No detector logic changes except where required for entry-fill metadata.

# Context

The current engine applies actions at the candle close for the matching timestamp. Existing pattern entry code can simulate market-on-confirmation, next-open, and limit-style fills, but the canonical engine does not consume an explicit simulated fill price. Pattern metadata may include `fill_price` or `exit_price`, yet engine accounting still uses close.

This causes large economic mismatch for FVG and Order Block strategies, where the intended entry may be a zone midpoint or boundary rather than breakout/confirmation close.

# Scope

- Extend `StrategyAction` or an adjacent execution instruction model to carry explicit execution price safely.
- Update `run_strategy_backtest_engine` to use explicit execution price when supplied.
- Preserve candle-close fallback when no explicit price is supplied.
- Ensure entry-fill simulation results can be converted into engine-consumable actions.
- Support at least:
  - `MARKET_ON_CONFIRMATION_CLOSE`
  - `MARKET_ON_NEXT_OPEN`
  - `LIMIT_AT_ENTRY_REFERENCE`
- Ensure explicit exit prices can also be used for stop and target actions.
- Include execution-price fields in `StrategyExecution`.

# Out of Scope

- Full lifecycle orchestration for every pattern.
- Fee, spread, and slippage implementation beyond preserving compatibility with cost hooks.
- Order book, volume-based partial fill, liquidity depth, latency, or queue modeling.
- Margin or funding behavior.
- Persistence schema redesign.

# Requirements

- The action/execution interface must clearly distinguish:
  - semantic action type;
  - action timestamp;
  - requested or simulated execution price;
  - raw candle close fallback price;
  - final effective price after future cost handling.
- If explicit execution price is provided, the engine must use it as the raw execution price.
- If explicit execution price is missing, the engine must use the existing candle close fallback.
- The fallback must be documented in execution metadata or code comments.
- Invalid explicit prices must be rejected or skipped deterministically.
- Entry-fill simulation must report:
  - status;
  - fill price;
  - fill timestamp;
  - fill candle index;
  - bars waited;
  - reason for no fill or invalid plan.
- Limit entries that are not touched must not create entry executions.
- Next-open entries must require a next candle.
- Market-on-confirmation entries must fill on the confirmation candle close.
- Stop-loss and take-profit action conversion must carry their simulated exit prices into the engine.

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

- A test action with explicit execution price executes at that price, not candle close.
- A test action without explicit execution price still executes at candle close.
- A limit-entry fixture fills only when high/low touches the limit price.
- A limit-entry fixture that does not touch the limit price creates no filled entry execution.
- A next-open entry fixture fills at the next candle open.
- Stop and target actions execute at the simulated stop or target price.
- Existing no-price action tests remain backward-compatible.

# Required Tests

## Unit Tests

- Test explicit price is used for `ENTER_LONG`.
- Test explicit price is used for `ENTER_SHORT`.
- Test explicit price is used for `EXIT_LONG`.
- Test explicit price is used for `EXIT_SHORT`.
- Test fallback close price remains unchanged when explicit price is absent.
- Test invalid negative, zero, NaN, or non-finite execution prices.
- Test `MARKET_ON_CONFIRMATION_CLOSE` fill.
- Test `MARKET_ON_NEXT_OPEN` fill.
- Test `LIMIT_AT_ENTRY_REFERENCE` fill and no-fill.

## Integration Tests

- Test canonical pattern CLI output includes raw price and effective price fields.
- Test FVG or Order Block fixture enters at entry reference when configured for limit entry.
- Test breakout fixture enters at confirmation close when configured for market-on-confirmation.

## Contract Tests

- `StrategyAction` remains a semantic action contract, not an order execution object.
- The backtest engine remains the only component that mutates cash and position.
- Explicit execution price must be optional for backward compatibility.

## Safety Tests

- No external order placement is used to simulate fills.
- No exchange account or order endpoint is called.
- No API key is loaded.

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

# Additional Verification

```bash
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_pattern_action_builder.py
pytest tests/patterns/test_entry_simulation.py
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
