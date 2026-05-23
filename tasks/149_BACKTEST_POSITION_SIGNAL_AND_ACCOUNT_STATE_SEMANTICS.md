# Goal

Fix strategy-backtest position signal semantics and account-state semantics so saved backtest results clearly distinguish long entry/exit and short entry/exit, and so cash/equity fields do not mislead users when short positions are open.

This task exists because current persisted/dashboard-facing `signal` values still collapse to `BUY`/`SELL`, and current `cash_after` can include short-sale proceeds, making a `10_000` cash account appear to have `20_000` cash after opening a `1 BTC` short at `10_000`.

# Source Requirement

Owner request (2026-05-24):

- Backtests must be reliable before further work.
- `signal` must not only show `BUY` and `SELL`.
- Long position buy/sell and short position buy/sell must be explicitly distinguishable.
- `cash_after` must not quickly exceed starting cash just because a short entry was represented as `SELL` proceeds.
- Short-position buy/cover behavior must not look like a fresh long buy.
- Equity graph spikes/drops caused by ambiguous cash/position/equity semantics must be investigated and corrected or explicitly separated.

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_TEMPLATE.md`
- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `tasks/142_SHORT_BUYING_POWER_POLICY.md`
- `tasks/144_ACCOUNT_STATE_VISIBILITY_FIELDS.md`
- `tasks/146_BACKTEST_CASH_EQUITY_DISPLAY_AND_API_SEMANTICS.md`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/persistence/postgres.py`
- `docs/api/API_CONTRACT.md`
- `frontend/src/types/api.ts`
- `frontend/src/app/page.tsx`
- relevant strategy/backtesting/persistence/frontend tests

# Extracted Roles

- Owner role:
  - Backtest semantic accounting owner.
  - Owns user-facing meaning of position signal, cash balance, free cash, locked proceeds/collateral, short liability, and equity series.
- Supporting roles:
  - Strategy action role: provides semantic `ENTER_LONG`, `EXIT_LONG`, `ENTER_SHORT`, `EXIT_SHORT`, partial exits, and execution-side mapping.
  - Strategy engine role: computes deterministic fills and account-state snapshots.
  - Persistence/API role: stores and serializes additive or migrated fields without losing backward compatibility.
  - Frontend role: displays unambiguous labels and graph series.
- Forbidden roles:
  - No live trading.
  - No real Binance order execution.
  - No exchange account/order endpoint calls.
  - No API keys or `.env` changes.
  - No real margin/futures implementation.
  - No borrow-fee, funding-fee, maintenance-margin, or liquidation model unless explicitly scoped as unsupported metadata.

# Context

The current code already has semantic strategy actions and position sides:

- `ENTER_LONG`
- `EXIT_LONG`
- `ENTER_SHORT`
- `EXIT_SHORT`
- partial exit variants

However, persisted trade `signal` and graph marker `signal` are currently derived from execution side (`BUY`/`SELL`). This collapses:

- long entry and short cover into `BUY`
- long exit and short entry into `SELL`

The current short-entry accounting also records short-sale proceeds in `cash_after`. For example:

- starting cash `10_000`
- short entry `1 BTC @ 10_000`
- current `cash_after = 20_000`
- current `position_after = -1`
- current `equity_after = 10_000`

That can be internally coherent as cash-balance accounting, but it is not acceptable as the primary user-facing cash/funds view. Users read `cash_after` as spendable cash or account cash, and dashboard graphs/tables become misleading.

Equity graph behavior is also ambiguous because equity points are candle-close mark-to-market snapshots after all actions on the candle are applied. When fill price differs from candle close, equity can jump immediately on the same candle. The graph needs explicit semantics or separated series.

# Scope

- Define and implement an unambiguous position signal contract.
- Replace or supplement persisted/displayed `signal` with a semantic signal that distinguishes at least:
  - `LONG_ENTRY`
  - `LONG_EXIT`
  - `SHORT_ENTRY`
  - `SHORT_EXIT`
  - partial long/short exits if present
- Preserve raw execution side (`BUY`/`SELL`) as a separate field for cashflow/audit purposes.
- Rework account-state fields so user-facing cash does not include unrestricted short-sale proceeds.
- Decide and document the exact meaning of:
  - `cash_after`
  - `free_cash_after`
  - `cash_balance_after` if introduced
  - `short_proceeds_locked_after`
  - `short_liability_after` if introduced
  - `margin_used_after`
  - `equity_after`
- Ensure short entry on a cash-bounded non-margin simulation does not show doubled spendable cash.
- Ensure short cover/exit is clearly displayed as short exit/cover, not long entry.
- Investigate same-candle fill/mark behavior and either:
  - separate execution-time equity from candle-close mark-to-market equity, or
  - document and display the current graph as mark-to-market only with no misleading fill-time implication.
- Update persistence/API/frontend display semantics where needed.
- Add regression tests for the exact confusing examples.

# Out of Scope

- Live trading.
- Real exchange margin/futures behavior.
- Borrow fees.
- Futures funding fees.
- Maintenance margin.
- Liquidation engine.
- Portfolio optimization.
- Broad dashboard redesign unrelated to backtest result semantics.
- Changing pattern detection, strategy rules, or risk/exit algorithms unless needed only to preserve signal metadata.

# Requirements

- A persisted/displayed trade must expose both:
  - semantic position signal, and
  - execution side (`BUY`/`SELL`).
- `signal` must no longer be ambiguous in user-facing backtest results. If the existing `signal` field remains for backward compatibility, add a new primary field such as `position_signal`, `action_type`, or `trade_intent` and update frontend labels to prefer it.
- Long entry, long exit, short entry, and short exit must be distinguishable in:
  - CLI JSON output,
  - persistence trade metadata/read model,
  - graph marker metadata,
  - API contract,
  - frontend table/chart display.
- Short entry must not present short-sale proceeds as unrestricted `cash_after`/free cash.
- If `cash_after` is retained as cash-balance accounting, UI/API docs must label it explicitly as `cash_balance_after`; otherwise redefine it to match spendable/free cash and move proceeds to locked fields.
- Equity calculation must remain economically coherent after any cash-field refactor.
- Equity graph semantics must be deterministic and documented:
  - execution-time equity and candle-close mark-to-market equity must not be conflated.
- Existing public fields must remain backward-compatible where practical, or migration/compatibility behavior must be documented and tested.
- No exchange/network dependencies are allowed in tests.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm this Task 149 is recorded as the current active implementation task before coding.
- [x] Confirm Task 138 remains blocked unless explicit live-order approval exists.
- [x] Confirm this task is limited to backtest semantics, persistence/API/frontend display, and tests.
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

- Backtest result rows no longer show only ambiguous `BUY`/`SELL` as the primary signal.
- Long entry, long exit, short entry, and short exit are visible and unambiguous in CLI JSON, persistence metadata/read models, API contract, graph markers, and frontend table/chart display.
- A short entry example with `starting_cash=10_000`, `price=10_000`, `quantity=1` does not show `20_000` as spendable/user-facing cash.
- Short cover/exit is displayed as short exit/cover and not confused with long buy.
- Equity graph behavior is either corrected or split into clearly named series so execution-time and mark-to-market effects are not conflated.
- Existing strategy accounting tests still pass after updates.
- New tests cover the owner-reported confusion cases.
- No live trading or exchange endpoint behavior is added.

# Required Tests

## Unit Tests

- Test semantic signal mapping for:
  - `ENTER_LONG`
  - `EXIT_LONG`
  - `PARTIAL_EXIT_LONG`
  - `ENTER_SHORT`
  - `EXIT_SHORT`
  - `PARTIAL_EXIT_SHORT`
- Test persisted/displayed signal contract keeps execution side separate from semantic position signal.
- Test `starting_cash=10_000`, `price=10_000`, `ENTER_SHORT quantity=1` does not expose `20_000` as user-facing free/spendable cash.
- Test short cover/exit records `SHORT_EXIT` or equivalent primary semantic signal with execution side `BUY`.
- Test long exit records long-exit semantics with execution side `SELL`.
- Test partial exits preserve long/short semantics.
- Test equity/account-state fields remain coherent for flat, long, short, partial exit, and full exit states.

## Integration Tests

- Test `run_strategy_backtest_engine` output for a deterministic long lifecycle and short lifecycle.
- Test canonical strategy runner no-persist JSON includes unambiguous signal/account-state fields.
- Test persistence payload stores semantic signal plus execution side and graph markers preserve both.
- Test API serialization returns backward-compatible fields plus the new preferred semantic fields.
- Test frontend display helpers/types prefer semantic signal and label cash/free-cash correctly.

## Contract Tests

- Existing `StrategyExecution.side` or `execution_side` remains available for raw BUY/SELL cashflow audit.
- Existing persisted `signal` compatibility is preserved or migration behavior is documented and tested.
- API contract documents all changed or additive fields.
- Frontend TypeScript types match API output.
- Existing backtest summary fields remain readable unless explicitly migrated with tests.

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
- User-facing signal and cash/equity fields are not ambiguous.
- Short simulation is not represented as real exchange margin/futures behavior.

# Verification

Default:

```bash
pytest
```

Additional verification:

```bash
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_strategy_persistence_adapter.py
pytest tests/backtesting/test_pattern_postgres_runner_cli.py
pytest tests/execution
npm --prefix frontend run build
git diff --check
```

If backend route tests are run, use an environment with `fastapi` installed or document the blocker.

# Codex Self-Review Requirement

Before completion, run through `reviews/CODEX_SELF_REVIEW.md` and include the result in the final summary.

# PR Review Requirement

Use `reviews/REVIEW_CHECKLIST.md` and `docs/06_PR_REVIEW_PROCESS.md` before merge.

# Completion Summary

- Files changed: strategy action/model/engine/persistence/CLI serialization, backend API service serialization, frontend dashboard types/display, API contract, regression tests, and root state ledgers.
- Implementation summary: Added semantic `position_signal` values (`LONG_ENTRY`, `LONG_EXIT`, `LONG_PARTIAL_EXIT`, `SHORT_ENTRY`, `SHORT_EXIT`, `SHORT_PARTIAL_EXIT`) while preserving raw `side`/`execution_side`; made cash-bounded short entries lock both short proceeds and cash collateral for user-facing `free_cash_after`; introduced `cash_balance_after`, `execution_equity_after`, and `mark_to_market_equity_after`; updated persisted trade/graph marker semantics and dashboard display.
- Tests added or updated: strategy action mapping, strategy engine/accounting, strategy persistence adapter, canonical strategy CLI JSON, pattern CLI short accounting, backend service serialization, and frontend type/build verification.
- Tests run: `pytest`; targeted strategy/persistence/backend service tests; `npm --prefix frontend run build`; `git diff --check`.
- Codex self-review result: Scope respected, no live trading/order/account endpoint/API key behavior added, docs and state ledgers updated, and verification passed.
- Known limitations: Existing legacy persisted runs may still contain `BUY`/`SELL` in `signal`; clients now fall back safely and prefer `position_signal` when present.
- Recommended next task: Review the Task 149 diff and assign the next explicit task before further implementation.

# Completion Summary Required

- files changed
- implementation summary
- tests added or updated
- tests run
- Codex self-review result
- known limitations
- recommended next task
