# Goal

Add trade-level and grouped performance attribution so results can be analyzed by pattern, direction, long/short side, exit reason, timeframe, and market regime.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed gap:

- `performance_metrics.py` provides equity-curve metrics such as annualized return, volatility, Sharpe, Sortino, Calmar, MDD, and total return.
- Current summaries do not fully expose hit ratio, payoff ratio, expectancy, profit factor, exposure, turnover, drawdown duration, or attribution by pattern/regime/side.

Read and inspect:

- `tasks/132_BACKTEST_PERFORMANCE_METRICS_FROM_EQUITY_CURVE.md`
- `tasks/150_BACKTEST_DASHBOARD_VISUAL_ANALYTICS_UPGRADE.md`
- `quant_bitcoin/backtesting/performance_metrics.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- persistence/API/dashboard read models

# Extracted Roles

- Owner role:
  - Backtest research analytics owner.
- Supporting roles:
  - Engine role: supplies executions/equity points.
  - Persistence role: saves additive analytics metadata.
  - Dashboard/API role: may display read-only attribution later.
- Forbidden roles:
  - No strategy logic changes.
  - No live trading behavior.
  - No frontend redesign unless assigned in a separate UI task.

# Context

Code-level hints:

- Build pure helper functions in `performance_metrics.py` or a new `trade_metrics.py`.
- Use `StrategyExecution` metadata fields such as `pattern_event_id`, `pattern_type`, `pattern_direction`, `position_side`, `exit_reason`, `realized_r_multiple`, `net_pnl`.
- Add group keys carefully; missing metadata should group under `UNKNOWN`, not crash.
- Persist attribution metadata in summary or a dedicated schema only if additive and safe.

Functional intent:

- A backtest should answer where PnL came from, not just the aggregate return.

# Scope

- Add trade-level metrics: hit ratio, average win, average loss, payoff ratio, expectancy, profit factor, average R, median R, max consecutive losses, trade duration where available.
- Add grouped attribution by pattern, direction, position side, exit reason, and optional timeframe/session/regime tags.
- Add exposure and turnover metrics if enough data is available.
- Add drawdown duration/recovery duration from equity curve.
- Surface analytics in JSON metadata and persistence payload.

# Out of Scope

- Frontend visualization of attribution unless limited to existing metadata display.
- Strategy parameter optimization.
- Live monitoring metrics.

# Requirements

- Metrics must distinguish filled executions from skipped/blocked actions.
- Trade-level metrics must not double-count partial exits unless intentionally aggregating lifecycle trades.
- Grouped metrics must handle missing metadata deterministically.
- Profit factor must handle zero gross loss safely.
- Expectancy must be computed from completed trade outcomes or documented when unavailable.
- Persisted metadata must be JSON-safe.

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

- Summary metadata includes hit ratio, payoff ratio, expectancy, profit factor, drawdown duration, and exposure/turnover where available.
- Attribution table exists for at least pattern type, long/short side, and exit reason.
- Partial exits do not inflate trade count incorrectly.
- Tests cover edge cases with no losses, no wins, no completed trades, and partial exits.

# Required Tests

## Unit Tests

- Test pure metric helpers with synthetic executions.
- Test zero-loss/zero-win edge cases.
- Test partial-exit lifecycle aggregation.

## Integration Tests

- Test canonical strategy engine output contains attribution metadata.
- Test persistence adapter saves and reloads additive analytics metadata.

## Contract Tests

- Ensure existing summary fields remain backward-compatible.
- Update API contract docs if frontend/backend read models expose new fields.

## Safety Tests

- Confirm analytics code does not call exchange APIs or require secrets.

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
pytest tests/backtesting/test_performance_metrics.py tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_persistence_adapter.py
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
