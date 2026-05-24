# Goal

Wire pattern-specific soft invalidation rules into the canonical strategy-engine backtest path instead of leaving them only in deprecated or compatibility code.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- Deprecated `quant_bitcoin/backtesting/pattern_strategy.py` defines `_soft_invalidation_for_event()` for FVG midpoint, trendline value, neckline, Diamond boundary, and Adam/Eve neckline rules.
- The active canonical path in `strategy_postgres_runner_core.py` calls `build_pattern_trade_actions()` without passing a soft invalidation rule.
- Therefore active pattern exits may rely only on hard stop, take profit, and time stop.

Read and inspect:

- `quant_bitcoin/backtesting/pattern_strategy.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/risk/exit_simulation.py`
- `quant_bitcoin/strategies/patterns.py`
- pattern-specific risk-exit files

# Extracted Roles

- Owner role:
  - Pattern lifecycle exit-contract owner.
- Supporting roles:
  - Pattern detector role: supplies event-specific references.
  - Risk simulator role: evaluates soft invalidation on completed candle closes.
  - Strategy runner role: transports rules through action building.
- Forbidden roles:
  - No live execution.
  - No detector redefinition unless needed only to expose existing event fields.
  - No frontend work except additive docs.

# Context

Code-level hints:

- Move or duplicate `_soft_invalidation_for_event()` from `pattern_strategy.py` into an active shared module, for example `quant_bitcoin/backtesting/pattern_invalidation.py` or `quant_bitcoin/strategies/patterns.py`.
- Ensure the active strategy path has access to the original event fields needed by the rule.
- In `_expand_raw_actions()`, build the soft invalidation rule from the event metadata/proxy and pass it to `build_pattern_trade_actions()`.
- `build_pattern_trade_actions()` already accepts `soft_invalidation`; use that argument.
- Verify `exit_reason=SOFT_INVALIDATION` appears in executions when the rule triggers.

Functional intent:

- Pattern failure conditions should be part of the active canonical backtest, not only legacy code.
- Soft invalidation should be close-based and deterministic.

# Scope

- Create an active soft-invalidation builder for supported patterns.
- Wire canonical runner/action-builder to pass soft invalidation to `simulate_pattern_exit()`.
- Preserve current behavior for patterns with no soft invalidation rule.
- Add tests for at least FVG, Trendline Break, and a neckline-based bullish pattern.

# Out of Scope

- Designing new economic invalidation rules.
- Intrabar invalidation based on tick/order-book data.
- Frontend display redesign.

# Requirements

- FVG invalidation must use midpoint logic equivalent to existing legacy rule.
- Trendline Break invalidation must use trendline value logic equivalent to existing legacy rule.
- Cup and Handle / Adam and Eve should use neckline invalidation when event fields exist.
- Diamond should use boundary invalidation when event fields exist.
- Rule metadata must appear in exit event metadata.
- Missing event fields must fail safe by omitting soft invalidation, not by crashing the whole backtest, unless the selected pattern requires the field.

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

- Active canonical pattern backtest can produce `SOFT_INVALIDATION` exits.
- Existing hard stop and take profit behavior remains unchanged when soft invalidation is absent.
- Tests show active canonical path, not deprecated path, uses soft invalidation.
- JSON execution metadata exposes the invalidation rule.

# Required Tests

## Unit Tests

- Test soft-invalidation builder for each supported pattern event shape.
- Test missing optional fields behavior.
- Test `simulate_pattern_exit()` receives and acts on the rule.

## Integration Tests

- Add canonical action-building tests where price closes beyond FVG midpoint and exits via soft invalidation.
- Add at least one trendline or neckline fixture through canonical runner path.

## Contract Tests

- Ensure exit reason values remain compatible with `PatternExitReason`.
- Ensure persisted metadata additions are JSON-safe.

## Safety Tests

- Confirm no exchange calls or live orders.
- Confirm soft invalidation is analysis-only and historical.

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
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_cli_persistence.py tests/risk/test_exit_simulation.py
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
