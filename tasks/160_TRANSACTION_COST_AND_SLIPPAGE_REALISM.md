# Goal

Make transaction-cost assumptions explicit and more realistic for high-frequency 1m pattern backtests, including volatility-linked slippage usage and zero-cost warnings.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- `TransactionCostConfig` supports maker/taker fees, spread, slippage, minimum slippage, and volatility slippage multiplier.
- The canonical CLI defaults all cost values to zero.
- The cost helper accepts `volatility_bps`, but engine calls do not visibly pass candle volatility into cost calculation.

Read and inspect:

- `tasks/118_TRANSACTION_COST_CLI_AND_ACCOUNTING_INTEGRATION.md`
- `quant_bitcoin/backtesting/costs.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/performance_metrics.py`
- cost/accounting tests and CLI tests

# Extracted Roles

- Owner role:
  - Backtest cost-model owner.
- Supporting roles:
  - Engine role: applies cost to executions.
  - CLI role: accepts and reports cost assumptions.
  - Metrics role: reports net-vs-gross performance.
- Forbidden roles:
  - No real exchange fee-tier fetching.
  - No order-book market-impact implementation unless simulated offline.
  - No live order execution.

# Context

Code-level hints:

- In `strategy_engine._cost()`, consider passing a per-candle or per-action volatility proxy into `calculate_transaction_cost()`.
- Because `_apply_action()` receives only `close`, you may need to pass the current candle or action metadata containing `volatility_bps`.
- Add zero-cost warnings in CLI output when all maker/taker/spread/slippage values are zero.
- Consider a named cost profile, but keep it optional and explicit.
- Add summary fields such as `gross_pnl`, `net_pnl`, `total_cost`, `cost_to_gross_pnl_ratio`, and per-execution cost breakdown where missing.

Functional intent:

- The backtest should not look realistic when it used zero costs.
- Cost sensitivity should be easy to run and audit.

# Scope

- Add explicit zero-cost diagnostics.
- Wire volatility-linked slippage where possible using existing config fields.
- Add cost sensitivity helper or documented CLI examples if full automation is too large.
- Ensure cost metadata is persisted and JSON-safe.
- Add tests for cost-adjusted long and short executions.

# Out of Scope

- Real-time exchange fee lookup.
- Full market-impact model from order book depth.
- Portfolio capacity analysis beyond metadata placeholders.
- Live trading.

# Requirements

- Zero-cost runs must emit a clear warning in JSON output and/or metadata.
- Volatility slippage multiplier must either be wired to a real volatility proxy or documented as currently unused.
- Cost breakdown must be available at execution and summary levels.
- Long and short cost application must remain side-aware.
- Existing `TransactionCostConfig` validation must remain strict.
- CLI defaults may remain zero only if warnings make the assumption explicit.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent task context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A zero-cost CLI run includes a `zero_transaction_cost_assumption` warning or equivalent metadata.
- Non-zero spread/slippage changes effective execution prices in expected direction.
- Volatility-linked slippage changes when volatility proxy changes, or a clear limitation is recorded if deferred.
- Cost-adjusted net PnL differs from gross PnL correctly.

# Required Tests

## Unit Tests

- Test effective prices for BUY and SELL with fee/spread/slippage.
- Test summary total cost aggregation.
- Test zero-cost warning generation.

## Integration Tests

- Add canonical CLI test with non-zero cost flags.
- Add cost sensitivity fixture if implemented.

## Contract Tests

- Ensure JSON/persistence fields are additive and retain existing names.
- Document cost assumptions in README or relevant docs if behavior changes.

## Safety Tests

- Confirm no real exchange fee lookup or order endpoint call is added.
- Confirm no secrets or `.env` behavior.

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
pytest tests/backtesting/test_costs.py tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_cli_persistence.py
pytest
git diff --check
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
