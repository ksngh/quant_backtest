# Goal

Wire transaction-cost modeling into the canonical backtest CLI and ensure cost-adjusted accounting is internally consistent.

The existing cost helper supports fees, spread, and slippage. This task makes those parameters configurable through the canonical CLI and verifies that cash, equity, realized PnL, and execution records reflect costs without double-counting.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/costs.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/postgres_runner_cli.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- existing accounting tests under `tests/backtesting/`

# Extracted Roles

- Owner role:
  - Backtesting cost-accounting owner.
  - Owns how fees, spread, and slippage alter simulated executions and portfolio state.
- Supporting roles:
  - CLI role: exposes cost configuration.
  - Persistence role: stores cost metadata.
  - Test role: verifies deterministic cost-adjusted accounting.
- Forbidden roles:
  - No real exchange fee lookup.
  - No live order execution.
  - No funding, borrow fee, liquidation, or margin implementation in this task.
  - No order book depth simulation.

# Context

`costs.py` already defines `TransactionCostConfig`, `LiquidityRole`, and deterministic cost calculation. `strategy_engine.py` can use a transaction cost config, but `strategy_postgres_runner_cli.py` does not currently expose or pass cost options. As a result, canonical CLI backtests default to zero fees, zero spread, and zero slippage.

There is also a risk of cost double-counting if effective price already reflects spread/slippage and net PnL subtracts those costs again. Accounting must be made explicit and consistent.

# Scope

- Add CLI options for cost configuration.
- Pass `TransactionCostConfig` into `StrategyEngineConfig`.
- Include liquidity role in CLI and engine config.
- Ensure zero-cost defaults preserve current behavior.
- Ensure non-zero costs affect cash and equity.
- Ensure execution records include fee, spread, slippage, total cost, raw price, and effective price.
- Ensure net PnL is consistent with cash/equity accounting.
- Include transaction-cost config in output JSON and persisted metadata.

# Out of Scope

- Borrow fees.
- Futures funding.
- Maintenance margin.
- Liquidation.
- Dynamic exchange fee-tier lookup.
- Order book spread modeling.
- Market impact modeling beyond deterministic bps slippage.

# Requirements

- Add canonical CLI args:
  - `--maker-fee-bps`
  - `--taker-fee-bps`
  - `--spread-bps`
  - `--slippage-bps`
  - `--minimum-slippage-bps`
  - `--volatility-slippage-multiplier`
  - `--liquidity-role`
- All cost args must validate non-negative finite values.
- `--liquidity-role` must accept `MAKER` or `TAKER` case-insensitively.
- Defaults must be zero-cost and taker liquidity unless existing behavior requires otherwise.
- BUY effective price must move upward with spread/slippage.
- SELL effective price must move downward with spread/slippage.
- Fee cost must be deducted from cash for both buys and sells.
- Cost metadata must appear in each filled execution.
- Summary metadata must include the transaction cost config used for the run.
- Avoid double-counting spread/slippage in net PnL.
- Document unsupported short economics in summary limitations.

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

- Running the CLI with zero-cost defaults produces the same final equity as before for a deterministic fixture.
- Running the CLI with non-zero taker fee reduces final equity versus zero-cost behavior.
- Running the CLI with spread and slippage changes effective execution prices according to side.
- Execution records include fee, spread, slippage, and total cost fields.
- Cost config appears in output JSON metadata.
- Cost-adjusted realized PnL matches the change implied by cash and position accounting.

# Required Tests

## Unit Tests

- Test `TransactionCostConfig` rejects invalid negative values.
- Test `basis_points_to_decimal` conversion.
- Test BUY effective price increases with spread/slippage.
- Test SELL effective price decreases with spread/slippage.
- Test long entry and exit with taker fee.
- Test short entry and exit with taker fee.
- Test partial exit cost accounting.
- Test zero-cost behavior remains unchanged.
- Test net PnL does not double-count spread/slippage.

## Integration Tests

- Test CLI parses all transaction-cost args.
- Test CLI passes cost config into `StrategyEngineConfig`.
- Test pattern backtest output includes cost fields.
- Test persisted trade metadata includes cost fields.

## Contract Tests

- Cost helpers remain pure and side-effect free.
- Engine remains responsible for applying costs to portfolio state.
- CLI does not perform accounting itself.

## Safety Tests

- No exchange fee endpoint is called.
- No account endpoint is called.
- No API key is required.

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
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
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
