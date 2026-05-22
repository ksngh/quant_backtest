# Goal

Improve backtest metrics and persistence metadata so filled executions, skipped actions, blocked actions, partial exits, full exits, realized PnL, unrealized PnL, and costs are represented accurately.

This task focuses on result quality, not on adding new pattern logic.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_persistence_adapter.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/persistence/`
- existing persistence and result tests under `tests/backtesting/` and `tests/persistence/`

# Extracted Roles

- Owner role:
  - Backtesting result and persistence owner.
  - Owns summary metrics, execution record fields, graph points, and persisted metadata.
- Supporting roles:
  - Engine role: produces accurate execution and equity records.
  - Persistence role: stores completed simulated output without re-running strategies.
  - CLI role: prints deterministic JSON result output.
- Forbidden roles:
  - No new strategy logic.
  - No detector changes.
  - No large schema redesign unless current metadata cannot hold required data.
  - No live execution or exchange calls.

# Context

Current `StrategyBacktestSummary` includes basic fields, but some metrics can be misleading. Blocked zero-quantity records may inflate trade count. Short exits can be missed by win/loss logic if win/loss is inferred only from `SELL` executions. Persistence metadata currently stores only limited execution details, losing cost, exit reason, pattern event id, and lifecycle details.

Reliable backtest review requires separating real filled executions from skipped and blocked actions.

# Scope

- Extend summary metrics or metadata to distinguish action and execution categories.
- Prevent blocked or skipped actions from inflating filled trade count.
- Add explicit metrics for partial and full exits.
- Add open-position metrics at the end of the run.
- Track realized and unrealized PnL separately.
- Track long and short performance where practical.
- Persist enriched trade metadata without unnecessary schema redesign.
- Ensure graph points reflect partial exits and position changes.
- Keep backward-compatible legacy summary fields where needed.

# Out of Scope

- Full analytics suite such as Sharpe, Sortino, Calmar unless already easy and deterministic.
- Frontend graph changes.
- Database schema redesign unless required.
- New strategy or detector behavior.
- Cost-model implementation unless fields are already available from another task.

# Requirements

- Summary must distinguish:
  - filled execution count;
  - skipped action count;
  - blocked action count;
  - entry count;
  - exit count;
  - partial exit count;
  - full exit count;
  - open ending position;
  - realized PnL;
  - unrealized PnL;
  - gross PnL;
  - net PnL where costs are available;
  - max drawdown.
- Legacy fields must remain available:
  - `trade_count`
  - `buy_count`
  - `sell_count`
  - `final_equity`
  - `total_return`
- `trade_count` must mean filled executions or be clearly documented if legacy meaning is preserved elsewhere.
- Win/loss logic must use closing executions for both long and short positions.
- Persisted trade metadata should include:
  - `action_type`
  - `execution_side`
  - `position_side`
  - `pattern_event_id`
  - `pattern_type`
  - `entry_mode`
  - `exit_reason`
  - `target_name`
  - `quantity_ratio`
  - `remaining_quantity_ratio`
  - `gross_pnl`
  - `net_pnl`
  - `realized_r_multiple`
  - `fee_cost`
  - `spread_cost`
  - `slippage_cost`
  - `total_cost`
- CLI JSON output must expose enough fields to debug lifecycle behavior.
- Graph points must be ordered and deterministic.

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

- Blocked entries are not counted as filled trades.
- Skipped actions are not counted as filled trades.
- Partial exits increase partial-exit count and reduce position in graph points.
- Full exits increase full-exit count and close position.
- Open final position is reported explicitly.
- Short winning and losing trades are reflected in win/loss metrics.
- Persistence metadata includes lifecycle and cost fields when available.
- JSON output remains deterministic for identical inputs.

# Required Tests

## Unit Tests

- Test summary excludes blocked action from filled trade count.
- Test summary excludes skipped action from filled trade count.
- Test partial-exit metrics.
- Test full-exit metrics.
- Test open ending position metrics.
- Test realized vs unrealized PnL separation.
- Test long win/loss counting.
- Test short win/loss counting.
- Test graph points after partial exit.

## Integration Tests

- Test persisted metadata includes pattern lifecycle fields.
- Test output JSON includes new metrics.
- Test loading graph-ready persisted result still works.
- Test deterministic run replacement behavior remains unchanged if applicable.

## Contract Tests

- Persistence adapter must not re-run strategies.
- Persistence adapter must not call market-data providers.
- Graph points remain ordered by timestamp and sequence.
- Existing persistence payload contract remains backward-compatible where possible.

## Safety Tests

- No exchange calls.
- No real order execution.
- No secrets.

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
pytest tests/backtesting/test_strategy_persistence_adapter.py
pytest tests/backtesting/test_strategy_engine_accounting.py
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
