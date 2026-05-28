# Task 238: Backtest Execution Price Semantics Split

# Goal

Make backtest execution price semantics unambiguous by storing and displaying the market-reachable raw fill price as `price`, keeping `effective_price` as an explicit cost-adjusted diagnostic field, and calculating closed-trade PnL from raw price movement minus explicit fee, spread, and slippage costs.

# Source Requirement

Owner concern: backtest trade rows currently appear to fill outside the candle range because `StrategyExecution.price` is assigned to `effective_price`. The user wants slippage and fee handling clarified and does not want spread/slippage hidden inside the visible `price` field.

Forensic finding from the 2026-05-20 02:17 FVG short case:

- `SHORT_ENTRY` raw/requested price was `76,793.42`, inside the 02:17 candle range.
- `SHORT_ENTRY` displayed `price` was `76,729.026264` because the engine stored the cost-adjusted sell `effective_price` as `StrategyExecution.price`.
- `SHORT_EXIT` raw/stop price was `76,804.41459133071`, inside the same candle range.
- `SHORT_EXIT` displayed `price` was `76,868.8175466468` because the engine stored the cost-adjusted buy `effective_price` as `StrategyExecution.price`.
- Fees are not embedded in `effective_price`; spread and slippage are embedded in `effective_price` and also exposed as cost components.

# Extracted Roles

- Owner role:
  - Backtest accounting and execution-contract owner.
- Supporting roles:
  - Strategy engine role: owns `StrategyExecution` construction and PnL reconciliation.
  - Persistence/API role: owns trade row serialization and read-model compatibility.
  - Frontend role: owns trade-table labels and displayed price semantics.
  - Test role: owns regression tests proving raw price is market-range-valid and costs remain explicit.
- Forbidden roles:
  - No live trading.
  - No exchange order execution.
  - No signed account/order endpoint behavior.
  - No API key or `.env` changes.
  - No optimizer or profitability retuning in this task.

# Context

The current code path resolves a requested action price into `raw_price`, applies spread/slippage to derive `effective_price`, then writes `StrategyExecution.price = effective_price`. This makes the user-visible `Price` column look like a raw market fill even though it is an accounting-adjusted price. For candle-based backtests, this is misleading because valid raw fills can be rendered outside candle high/low after spread and slippage adjustment.

The recommended contract is:

```text
price = raw_price
raw_price = requested/candle/stop/target fill price before transaction costs
effective_price = diagnostic cost-adjusted price, not the canonical visible fill price
raw_gross_pnl = closed-position PnL from raw entry/exit prices
net_pnl = raw_gross_pnl - fee_cost - spread_cost - slippage_cost for the full closed position
```

This task intentionally separates price and cost accounting. It should make cost impact auditable without making the fill price appear impossible.

# Scope

- Change `StrategyExecution` creation so `price` is assigned to `raw_price`, not `effective_price`.
- Preserve `raw_price` and `effective_price` as separate fields on execution records.
- Ensure persisted `backtest_trades.price` represents the raw market-reachable fill price for newly produced backtest rows.
- Ensure API/CLI JSON responses expose both `raw_price` and `effective_price` distinctly.
- Rename frontend trade-table `Price` semantics so raw price and effective price are not conflated:
  - show `Raw Price` from `price`/`raw_price`,
  - show `Effective Price` from `effective_price` where available.
- Reconcile closed-trade accounting so net PnL is computed from raw gross PnL minus explicit transaction-cost components rather than implicitly relying on adjusted price movement.
- Add metadata or diagnostics that clearly mark:
  - `price_semantics = "raw_fill_price"`,
  - `effective_price_semantics = "spread_slippage_adjusted_reference"`.
- Add backward-compatibility notes for older persisted rows whose `price` may have been produced before this contract change.

# Out of Scope

- Do not change the configured fee, spread, or slippage rates.
- Do not add maker/taker fee modeling in this task.
- Do not add a cost-aware entry filter in this task.
- Do not tune strategy parameters for profitability.
- Do not migrate or rewrite historical backtest rows unless an explicit migration task is created.
- Do not introduce live trading, order placement, account access, signed exchange calls, API keys, or `.env` changes.

# Requirements

- Newly generated execution rows must satisfy `execution.price == execution.raw_price`.
- `execution.effective_price` must remain available for diagnostics and must equal the side-aware spread/slippage-adjusted value produced by the cost model.
- Closed-trade `raw_gross_pnl`, `total_transaction_cost`, and `net_pnl` must reconcile without hidden spread/slippage in the visible fill price.
- For the reproduced FVG short case, entry/exit raw prices must remain inside the candle range while effective prices may be outside the range and clearly labeled as adjusted diagnostics.
- CLI JSON, persisted payloads, API responses, and frontend types must not use the generic name `price` for adjusted execution price semantics.
- Documentation must state that fees, spread, and slippage are explicit costs and that `effective_price` is not the raw market touch price.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [ ] Read this assigned task file before coding.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [ ] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:

- The repo may contain historical backtest rows where `price` means `effective_price`; this task updates the contract for newly produced rows and documents the legacy ambiguity.
- The accounting reconciliation should prefer explicit cost subtraction over hidden cost-adjusted fill prices.
- Any schema change should preserve API compatibility by adding fields rather than removing existing fields without a migration path.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [ ] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `StrategyExecution.price` equals `raw_price` for new executions.
- `effective_price` remains serialized and is labeled as a spread/slippage-adjusted diagnostic value.
- Persisted trade rows and API responses expose raw and effective prices separately.
- The frontend no longer labels an adjusted price as generic `Price`.
- Closed-trade PnL has a deterministic reconciliation path:

```text
net_pnl = raw_gross_pnl - total_fee_cost - total_spread_cost - total_slippage_cost
```

- A regression fixture reproducing the 2026-05-20 02:17 FVG short confirms raw entry and raw exit prices are inside the candle high/low range.
- No cost component is double-counted after the price semantics change.
- Existing no-cost backtests remain unchanged except for added fields/labels.
- No live trading behavior is added.

# Required Tests

## Unit Tests

- Test `StrategyExecution` construction with nonzero spread/slippage:
  - `price == raw_price`,
  - `effective_price != raw_price`,
  - `effective_price` moves down for sell and up for buy.
- Test closed-trade PnL reconciliation from raw entry/exit prices minus explicit costs.
- Test zero-cost profile:
  - `raw_price == effective_price`,
  - `raw_gross_pnl == net_pnl` before unrelated account effects.
- Test no spread/slippage double counting after the contract change.

## Integration Tests

- Run a deterministic pattern backtest with `conservative_crypto_1m` and verify generated trade rows include raw and effective price fields.
- Reproduce the 2026-05-20 02:17 FVG short fixture and assert raw prices are inside candle range while effective prices may fall outside with explicit adjusted semantics.
- Verify persistence adapter writes raw price into the trade payload `price` field for new rows.
- Verify frontend/API integration renders raw price and effective price separately.

## Contract Tests

- API response contract includes:
  - `price`,
  - `raw_price`,
  - `effective_price`,
  - `price_semantics`,
  - `effective_price_semantics`.
- Frontend `BacktestTrade` type represents raw/effective price separation without overloading `price` as adjusted price.
- Documentation and API contract notes state the new semantics and legacy caveat for old persisted rows.

## Safety Tests

- Confirm no exchange endpoint imports or signed order/account endpoint behavior is added.
- Confirm no API keys, `.env`, live-order flags, or real trading logic are introduced.
- Confirm all tests run offline with deterministic fixtures.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are deterministic and covered by tests.
- No look-ahead behavior is introduced.
- Documentation/API notes are updated when behavior or metadata changes.

# Verification

Default:

```bash
pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_costs.py tests/backtesting/test_pattern_postgres_runner_cli.py
pytest tests/persistence tests/api || true
npm --prefix frontend run build
pytest
git diff --check
```

If the repo does not have one of the targeted test paths, run the nearest existing backtesting, persistence, API, and frontend type/build tests and record the substitution in the completion summary.

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
