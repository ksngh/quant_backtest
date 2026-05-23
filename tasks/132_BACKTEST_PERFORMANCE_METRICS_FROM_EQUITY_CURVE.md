# Goal

Add deterministic backtest performance analytics including Sharpe ratio, Sortino ratio, annualized return, annualized volatility, downside deviation, Calmar ratio, and max drawdown metadata using the existing strategy-engine equity curve.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/persistence/`
- `db/init/001_schema.sql`
- `tests/backtesting/`
- `tests/persistence/`

# Extracted Roles

- Owner role:
  - Backtest analytics owner.
  - Owns return-series calculation, annualization, risk metric definitions, and metadata representation.
- Supporting roles:
  - Engine role: supplies ordered equity points.
  - CLI role: exposes metrics in JSON output.
  - Persistence role: saves metrics in summary metadata.
- Forbidden roles:
  - No strategy logic changes.
  - No detector changes.
  - No order execution.
  - No exchange calls.
  - No schema redesign unless metadata cannot hold required outputs.

# Context

The canonical strategy engine already emits dense `StrategyEquityPoint` values with equity, drawdown, realized PnL, and unrealized PnL. Current summaries include total return and max drawdown, but not Sharpe, Sortino, Calmar, annualized return, annualized volatility, or downside deviation. The owner wants these metrics available from backtests.

# Scope

- Add a pure analytics module, for example `quant_bitcoin/backtesting/performance_metrics.py`.
- Calculate metrics from ordered equity points.
- Support interval-aware annualization for minute intervals.
- Add risk-free-rate input with default `0.0` annual rate.
- Store metrics in `StrategyBacktestSummary.metadata["performance_metrics"]`.
- Expose metrics in canonical CLI JSON output.
- Persist metrics through `backtest_results.metadata`.
- Add deterministic tests for normal, flat, empty, and degenerate equity curves.

# Out of Scope

- Portfolio optimization.
- Statistical significance testing.
- Rolling-window analytics.
- Frontend graph changes.
- New database columns for metrics.
- Exchange-specific benchmark/risk-free-rate fetching.

# Requirements

- Metric calculation must be pure and side-effect free.
- Empty equity curves must not crash the CLI.
- Flat equity curves must produce deterministic `None` or `0.0` values according to documented policy.
- Sharpe ratio must use excess returns over the configured risk-free rate.
- Sortino ratio must use downside deviation only.
- Calmar ratio must use annualized return divided by absolute max drawdown when max drawdown is non-zero.
- Annualization must be interval-aware for at least `1m`, `3m`, `5m`, `15m`, and `30m`.
- Unsupported intervals must fail clearly or return metrics with an explicit warning.
- Existing summary fields must remain backward-compatible.

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

- CLI output includes `summary.metadata.performance_metrics`.
- Persisted backtest summary metadata includes the same metrics.
- Sharpe and Sortino are computed from equity returns, not trade returns.
- Flat/zero-variance equity does not raise divide-by-zero errors.
- Metrics are deterministic for identical inputs.
- Tests verify annualization for `1m`, `5m`, and `15m`.

# Required Tests

## Unit Tests

- Test period return calculation from equity points.
- Test annualization factor for `1m`.
- Test annualization factor for `5m`.
- Test annualization factor for `15m`.
- Test Sharpe ratio on a deterministic return series.
- Test Sortino ratio on a deterministic return series with downside returns.
- Test Sortino ratio when no downside returns exist.
- Test Calmar ratio with non-zero max drawdown.
- Test flat equity curve behavior.
- Test empty equity curve behavior.

## Integration Tests

- Test canonical strategy CLI output contains performance metrics.
- Test persistence adapter stores performance metrics in summary metadata.
- Test read model loads metrics from persisted metadata without recomputing strategy output.

## Contract Tests

- Metrics module must not call market-data providers.
- Metrics module must not call exchanges.
- Strategy engine remains responsible for generating equity points.
- Persistence adapter must not recompute strategy actions.

## Safety Tests

- No API keys.
- No signed requests.
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
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
pytest tests/backtesting/test_strategy_persistence_adapter.py
pytest tests/persistence
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
