# Goal

Separate partial-exit quantity ratios from absolute execution quantities so partial exits remain correct under any entry sizing mode.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- `quant_bitcoin/risk/exit_simulation.py` emits `PatternExitEvent.quantity_ratio` as a position ratio.
- `quant_bitcoin/backtesting/pattern_action_builder.py` maps that ratio directly into `StrategyAction.quantity`.
- `quant_bitcoin/backtesting/strategy_engine.py` interprets `StrategyAction.quantity` as an absolute quantity.
- The current behavior only appears correct when entry quantity is exactly `1.0`.

Read and inspect:

- `tasks/152_PATTERN_SIZING_PROPAGATION_CONTRACT.md`
- `quant_bitcoin/risk/exit_simulation.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/strategies/actions.py`
- relevant tests for partial exits and multi-fill graph markers

# Extracted Roles

- Owner role:
  - Backtest position lifecycle contract owner.
  - Owns absolute-vs-ratio quantity semantics for exits.
- Supporting roles:
  - Risk simulation role: provides ratio-based planned exits.
  - Strategy action role: transports either absolute quantity or ratio intent clearly.
  - Engine role: converts intent into account-state changes.
- Forbidden roles:
  - No detector logic changes.
  - No live trading behavior.
  - No exchange endpoint integration.

# Context

Code-level hints:

- Inspect `_to_exit_action()` in `pattern_action_builder.py`; it currently passes `exit_event.quantity_ratio` as `StrategyAction.quantity`.
- Inspect `_resolve_exit_quantity()` and `_close_position()` in `strategy_engine.py`; they treat the quantity as absolute units and cap by `min(abs(position), qty)`.
- Consider one of two safe designs:
  - Add a `quantity_mode` field to `StrategyAction` with values like `ABSOLUTE` and `POSITION_RATIO`.
  - Or convert ratio to absolute quantity in the builder using the known entry quantity. This is less robust if engine-owned sizing remains unknown until execution.
- Prefer an explicit `quantity_mode` contract if possible because engine-owned sizing means the builder may not know the filled entry quantity.

Functional intent:

- A 33% partial exit should close 33% of the current open position, not `0.33 BTC` unconditionally.
- Full exit should close all remaining position.
- Existing full-exit behavior must remain backward-compatible.

# Scope

- Add explicit quantity semantics for partial exits.
- Update the engine to handle ratio-based exit actions deterministically.
- Preserve absolute quantity actions for existing callers.
- Update persistence/JSON metadata so executions can be audited.
- Add tests covering non-1.0 entry quantity and multiple partial exits.

# Out of Scope

- Changing the default partial exit plan ratios.
- Changing pattern target selection rules.
- Adding portfolio-level risk sizing.
- Live execution partial-fill handling.

# Requirements

- Partial-exit ratio actions must close a proportion of the current position.
- Absolute-quantity exit actions must keep existing behavior.
- Engine must reject invalid ratio values below 0 or above 1 when appropriate.
- Full exit actions may use an explicit full-exit marker or a ratio of 1.0.
- Metadata must include original ratio, resolved absolute quantity, and quantity mode.
- Existing graph marker and persistence behavior must remain deterministic.

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

- Entry size `0.25` with TP1 ratio `0.33` closes `0.0825`, not `0.33`.
- Entry size `2.0` with TP1 ratio `0.33` closes `0.66`, not `0.33`.
- Multiple partial exits reduce position in expected sequence and final exit closes only the remainder.
- Long and short partial exits both behave correctly.
- Output metadata exposes ratio and resolved absolute quantity.

# Required Tests

## Unit Tests

- Test engine ratio-based partial exits for long positions.
- Test engine ratio-based partial exits for short positions.
- Test invalid ratio rejection or block behavior.
- Test backward-compatible absolute exit quantity behavior.

## Integration Tests

- Run a pattern lifecycle test with engine-owned sizing and partial exits.
- Verify persisted executions and graph markers show correct quantities after multiple exits.

## Contract Tests

- If `StrategyAction` changes, add contract tests for default quantity mode compatibility.
- Confirm public JSON fields are additive or backward-compatible.

## Safety Tests

- Confirm no live trading or exchange endpoint behavior is added.
- Confirm no real order partial-fill behavior is implied by historical ratio simulation.

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
pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_persistence_adapter.py
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
