# Task 102: CANONICAL_PATTERN_ACTION_BUILDER_CLI_INTEGRATION

## Status

Planned

# Goal

Integrate canonical pattern risk/entry/exit action generation into the active strategy PostgreSQL CLI path.

# Source Requirement

Repository verification showed `pattern_action_builder.py` can generate entry, skip, partial-exit, and final-exit `StrategyAction` objects, while `strategy_postgres_runner_cli.py` currently builds actions by calling pattern strategy evaluation directly and returns `events: []`.

# Extracted Roles

- Owner role: Project owner approves canonical pattern-backtest semantics, especially entry timing, exit timing, and whether non-FVG patterns should initially use existing prefix detection.
- Supporting roles: Codex agent implements canonical action-builder integration, updates tests, and records limitations.
- Forbidden roles: New pattern algorithms, dashboard/backend changes, real order execution, live trading, new exchange endpoints, API-key handling, or broad persistence redesign beyond required metadata.

# Context

The active CLI path currently uses `strategy_for_pattern(...)`, special-cases `FairValueGapStrategy`, collects emitted entry/skip actions, and runs `run_strategy_backtest_engine(...)`. It does not appear to call `build_pattern_trade_actions(...)`, so risk/entry/exit simulation actions may not be represented in canonical CLI executions.

# Scope

- Refactor the action build path for pattern strategies so detected pattern events and valid risk plans are converted through `build_pattern_trade_actions(...)`.
- Preserve the optimized FVG cache/local-index path where possible.
- For non-FVG patterns, use existing detectors/planners and document any performance limitation.
- Ensure generated actions include entry and exit semantics where the risk plan and future candles support them.
- Update CLI JSON output minimally as needed to expose diagnostics without taking over Task 110 output-schema expansion.
- Update tests around pattern CLI action generation and persistence compatibility.

# Out of Scope

- Do not implement new pattern detectors.
- Do not change `StrategyEngine` accounting semantics except if a narrow bug is required and explicitly documented.
- Do not modify backend/frontend UI or API contracts.
- Do not remove deprecated modules in this task.

# Requirements

- Use canonical `StrategyAction` and `StrategyEngine` paths.
- Preserve no-look-ahead behavior: events may only be detected from candles available up to confirmation.
- Risk plans must remain paper/backtest-only and must never call exchange APIs.
- Diagnostic skips such as entry not filled or invalid risk plan must be explicit.

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

- FVG bullish fixture can produce ENTER_LONG plus exit/partial-exit actions when future candles trigger exits.
- FVG bearish fixture can produce ENTER_SHORT plus exit/partial-exit actions when future candles trigger exits.
- `quant-bitcoin-strategy-backtest --pattern FAIR_VALUE_GAP --no-persist` behavior remains deterministic.
- Existing RSI canonical CLI behavior is not regressed.
- Pattern action builder tests and CLI integration tests pass.

# Required Tests

## Unit Tests

- Update or add unit tests for action orchestration around builder invocation and no-fill/invalid-plan diagnostics.

## Integration Tests

- Update pattern CLI tests and persistence CLI tests to validate canonical pattern action sequences.

## Contract Tests

- Validate generated actions preserve `action_type`, `position_side`, `pattern_event_id`, and exit metadata needed by persistence/read-model contracts.

## Safety Tests

- No live trading, no signed requests, no exchange order/account endpoint calls, no secrets.

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

Task-specific:

```bash
pytest -q tests/backtesting/test_pattern_action_builder.py
pytest -q tests/backtesting/test_pattern_postgres_runner_cli.py
pytest -q tests/backtesting/test_strategy_cli_persistence.py
pytest -q tests/backtesting/test_strategy_engine.py
python -m compileall quant_bitcoin
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
