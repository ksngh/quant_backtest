# Task 232: FVG Stop Mode and Reaction-Failure Exit Policy

# Goal

Extend FVG risk/exit planning with explicit stop modes and stronger reaction-failure handling so retest entries can choose between FVG boundary, swing pivot, and wider structural stop policies.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - FVG risk/exit policy owner.
- Supporting roles:
  - Pivot/swing structure role.
  - Exit simulation role.
  - Pattern action builder role.
  - Backtest diagnostics role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

The current FVG risk planner uses the FVG boundary plus ATR buffer and records midpoint reaction-failure metadata. The retest strategy needs explicit stop-mode research variants and a clearer post-entry failure rule for trades that do not react from the FVG zone.

# Scope

- Add stop-mode configuration to `FairValueGapRiskExitConfig`, for example `FVG_BOUNDARY_ATR_BUFFER`, `SWING_PIVOT`, and `WIDER_OF_FVG_AND_SWING`.
- Allow `create_fair_value_gap_risk_exit_plan()` to consume visible candles or precomputed pivots when swing stops are selected.
- Ensure stop selection is direction-aware and no-lookahead.
- Wire selected stop-mode metadata into risk plans, action metadata, target semantics, and diagnostics.
- Strengthen midpoint/reaction-failure behavior by ensuring soft invalidation or time-stop metadata is applied consistently after retest entry.
- Preserve existing FVG boundary stop as the default for backward compatibility.

# Out of Scope

- No entry trigger changes; that is Task 230.
- No liquidity target resolver implementation; that is Task 231.
- No leverage/futures/liquidation model changes.
- No live trading behavior.

# Requirements

- FVG boundary stop must match existing behavior when default mode is used.
- Swing-pivot stop must use only confirmed swing/pivot information visible at entry planning time.
- Wider stop mode must choose the more conservative stop between FVG boundary and swing stop for the selected direction.
- Invalid stop configurations must produce invalid risk-plan status with clear reasons, not silent fallback.
- Reaction-failure metadata must include reference price, favorable condition, max bars after entry, and configured action semantics.
- Risk-plan alignment to actual fill must continue to rebuild targets and risk per unit correctly.

# Status Tracking

## Execution Notes

- Assumption: swing stop mode consumes explicit no-lookahead swing stop input; automatic pivot stop discovery can be expanded later if assigned.
- Assumption: missing swing stop is invalid for swing/wider modes and does not silently fall back.
- Blockers: none for Task 232.
- Safety: no live trading, network, exchange, order/account, key, or `.env` behavior was added.

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [x] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

## Completion Notes

- Added FVG stop modes `FVG_BOUNDARY_ATR_BUFFER`, `SWING_PIVOT`, and `WIDER_OF_FVG_AND_SWING`.
- Added stop metadata schema `fvg_stop_mode_v1` and invalid risk-plan behavior for missing swing stops.
- Extended reaction-failure metadata with explicit `SOFT_INVALIDATION_EXIT` action semantics.
- Updated FVG docs for stop modes and reaction-failure semantics.
- Verification:
  - `pytest tests/patterns/test_fair_value_gap_risk_exit.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_risk_exit_audit.py`

# Acceptance Criteria

- Default stop mode preserves existing FVG boundary + ATR buffer behavior.
- Swing stop mode selects a prior confirmed pivot low for long and pivot high for short when available.
- Wider stop mode is directionally correct and produces larger or equal risk distance versus boundary-only mode.
- Reaction-failure rule is wired into exit simulation/soft invalidation metadata for FVG retest trades.
- Diagnostics can group outcomes by stop mode and reaction-failure outcome when later aggregation consumes metadata.

# Required Tests

## Unit Tests

- `tests/patterns/test_fair_value_gap_risk_exit.py` covers all stop modes, missing swing stop, invalid configs, and reaction-failure metadata.
- `tests/backtesting/test_pattern_action_builder.py` covers fill-adjusted risk with each stop mode.
- Exit simulation tests cover soft invalidation/time-stop trigger for no favorable midpoint reaction.

## Integration Tests

- FVG strategy backtest test confirms stop-mode metadata reaches execution metadata.
- Risk-exit audit test confirms grouping by stop mode if audit grouping is extended.

## Contract Tests

- Update FVG strategy docs and API metadata notes for stop-mode fields and reaction-failure semantics.
- Document backward-compatible default stop mode.

## Safety Tests

- No exchange/order/account endpoint imports.
- No API key or `.env` changes.
- No live/paper order execution behavior.

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
pytest tests/patterns/test_fair_value_gap_risk_exit.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_risk_exit_audit.py
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
