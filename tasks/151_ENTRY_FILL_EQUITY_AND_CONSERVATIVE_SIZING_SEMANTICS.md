# Goal

Correct entry-fill equity and sizing semantics so a backtest does not show an immediate favorable equity jump just because an entry filled at a better price than the candle close.

The equity curve must not make an entry look profitable at the same timestamp by mixing the simulated fill price for cash/quantity with the candle close for mark-to-market valuation.

# Source Requirement

Owner request (2026-05-24):

- After entry, equity should not immediately rise just because the fill price was lower than the candle close.
- If entry fill price and candle close differ, the engine currently appears to buy too much exposure.
- Entry sizing should be conservative enough that the position does not exceed the intended cash/notional exposure.
- Confirm and fix the suspected overbuy behavior in the existing repository.

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_TEMPLATE.md`
- `tasks/112_EXECUTION_PRICE_AND_ENTRY_FILL_CONTRACT.md`
- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `tasks/141_LONG_CASH_BOUNDED_ENTRY_EXECUTION.md`
- `tasks/149_BACKTEST_POSITION_SIGNAL_AND_ACCOUNT_STATE_SEMANTICS.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/sizing.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `docs/api/API_CONTRACT.md`
- frontend/API display files if persisted or API-facing equity fields change
- relevant tests under `tests/backtesting/`

# Extracted Roles

- Owner role:
  - Backtest entry-fill and equity-curve semantics owner.
  - Owns whether entry timestamp equity is execution-time equity or candle-close mark-to-market equity.
- Supporting roles:
  - Position sizing role: computes desired quantity from cash fraction, target notional, or fixed quantity.
  - Strategy engine role: applies fills, cash, position, and equity points deterministically.
  - Persistence/API/frontend roles: preserve and display the corrected semantics if output fields change.
- Forbidden roles:
  - No live trading.
  - No real Binance order execution.
  - No exchange order/account endpoint calls.
  - No API keys or `.env` changes.
  - No margin/futures/liquidation model unless limited to existing backtest-only metadata.
  - No unrelated dashboard redesign.

# Context

Task 112 introduced explicit `StrategyAction.requested_price`, so canonical backtests can fill at a simulated execution price instead of always using candle close.

Task 149 separated execution-time equity and candle-close mark-to-market equity:

- `execution_equity_after`: value immediately after fill at effective execution price.
- `mark_to_market_equity_after`: value after fill marked to candle close.
- `equity_points.equity`: currently candle-close mark-to-market after all actions on the candle.

Current behavior can create an immediate favorable entry jump:

- `starting_cash = 10_000`
- long entry `requested_price = 99`
- candle `close = 100`
- `CASH_FRACTION = 1.0`
- current quantity is `10_000 / 99 = 101.0101`
- `cash_after = 0`
- `execution_equity_after = 10_000`
- `equity_points.equity = 10_101.01`

This is internally explainable as same-candle mark-to-market, but it is not acceptable as the primary equity-curve behavior. It makes the graph look profitable at entry before any subsequent market movement.

Also, sizing from the more favorable fill price can create larger close-marked exposure than the intended cash/notional budget. Reducing quantity alone cannot fully remove same-candle favorable PnL when `fill_price < close`; the equity curve must also stop re-marking entry fills to a different candle close at the same timestamp.

# Scope

- Define the canonical entry timestamp equity policy.
- Prevent same-timestamp favorable equity jumps caused only by `requested_price` versus candle `close` differences.
- Make long and short entry sizing conservative for cash-fraction and target-notional modes when fill price and candle close differ.
- Preserve explicit execution price support from Task 112.
- Preserve Task 149's separate execution-time and mark-to-market audit fields, or migrate them with documented compatibility.
- Update performance metrics if they consume `equity_points.equity`.
- Update persistence/API/frontend docs or fields only if the output contract changes.
- Add regression tests for long and short entry cases where fill price differs from candle close.

# Out of Scope

- Live trading.
- Real exchange order execution.
- Real exchange margin/futures behavior.
- Borrow fees, funding fees, maintenance margin, or liquidation.
- Order book, depth, queue, latency, or volume-based fill simulation.
- Broad dashboard redesign unrelated to corrected equity semantics.
- Strategy signal or pattern detector changes unless required only to pass through entry-fill metadata.

# Requirements

- Entry timestamp equity must not rise above starting equity solely because the fill price is more favorable than the candle close.
- For a long entry with `requested_price < close`, the primary equity curve must use execution-time valuation at the entry timestamp or an equivalent deterministic policy that avoids same-candle favorable re-marking.
- For a short entry with `requested_price > close`, the primary equity curve must likewise avoid same-candle favorable re-marking.
- Subsequent candles may mark open positions to candle close normally.
- `execution_equity_after` and `mark_to_market_equity_after` must remain clearly distinguishable if both are kept.
- `equity_points.equity` semantics must be documented after the change.
- Cash-fraction and target-notional sizing must use a conservative valuation price so favorable fill prices do not increase intended exposure beyond the configured cash/notional budget.
- Fixed-quantity entries must remain supported, but affordability and metadata must still make the resulting exposure clear.
- Any resize/block metadata caused by conservative sizing must be deterministic and tested.
- Performance metrics must use the corrected primary equity series, not the misleading same-candle favorable MTM series.
- No exchange/network dependencies are allowed in tests.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 151 is recorded as the current active implementation task before coding.
- [x] Confirm Tasks 112, 140, 141, and 149 are completed dependencies.
- [x] Confirm this task is limited to backtest engine semantics, output contract updates if needed, docs, and tests.
- [x] Confirm no live trading, order endpoint, account endpoint, or API key behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to the next task if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A long entry with `starting_cash=10_000`, `requested_price=99`, candle `close=100`, and `CASH_FRACTION=1.0` does not produce a primary equity point above `10_000` at the entry timestamp.
- The same long entry still records the actual execution price and execution-time equity.
- A short entry with a favorable fill versus candle close does not produce a primary equity point above starting equity at the entry timestamp solely from same-candle re-marking.
- The next candle after an entry marks open positions to that candle close normally.
- Cash-fraction sizing no longer increases configured exposure simply because the fill price was favorable versus the candle close.
- Target-notional sizing no longer increases configured exposure simply because the fill price was favorable versus the candle close.
- Existing long/short cash accounting and Task 149 signal semantics remain intact.
- Performance metrics are based on the corrected primary equity series.
- API/docs/frontend semantics are updated if any serialized or displayed equity field changes.
- Existing strategy accounting tests still pass after updates.

# Required Tests

## Unit Tests

- Test long entry with favorable fill price does not create same-timestamp primary equity gain.
- Test short entry with favorable fill price does not create same-timestamp primary equity gain.
- Test long cash-fraction sizing uses conservative valuation when `requested_price < close`.
- Test short cash-fraction sizing uses conservative valuation when same-candle valuation would otherwise overstate exposure.
- Test target-notional sizing uses conservative valuation when requested fill and candle close differ.
- Test fixed-quantity behavior remains explicit and affordability metadata remains coherent.
- Test `execution_equity_after` and `mark_to_market_equity_after` remain distinguishable or are migrated with equivalent fields.

## Integration Tests

- Test `run_strategy_backtest_engine` equity points for entry candle and next candle.
- Test performance metrics consume the corrected equity curve.
- Test canonical strategy runner JSON output includes coherent equity semantics after the change.
- Test persistence payload preserves corrected graph/equity behavior if persistence is affected.

## Contract Tests

- Existing `StrategyExecution.raw_price`, `effective_price`, `cash_after`, `position_after`, and `equity_after` fields remain available or migration is documented and tested.
- `equity_points.equity` semantics are documented in `docs/api/API_CONTRACT.md` if API-facing.
- Backward-compatible audit fields remain available where practical.
- Frontend TypeScript types match any changed API output.

## Safety Tests

- No Binance order endpoint is called.
- No Binance account endpoint is called.
- No Binance margin/futures endpoint is called.
- No API keys are required.
- No `.env` files are created or modified.
- No live trading default or flag is introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Equity curve no longer shows same-candle favorable entry PnL caused only by fill/close mismatch.
- Conservative sizing does not silently change strategy intent beyond the documented policy.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_cli_persistence.py
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
