# Task 230: FVG Retest Entry Trigger and Policy Preset

# Goal

Add an explicit opt-in FVG retest strategy preset that favors midpoint/boundary retest entries and can distinguish simple limit-touch fills from touch-plus-reaction confirmation entries.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - Pattern entry simulation and FVG execution-policy owner.
- Supporting roles:
  - Strategy policy role.
  - CLI/backtest role.
  - Risk-plan alignment role.
  - Test fixture role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

The current FVG baseline preserves market-on-confirmation behavior for backward compatibility. The retest thesis requires waiting for price to rebalance into the FVG zone and optionally confirm reaction before entry. This task introduces that behavior as opt-in research behavior, not a silent default replacement.

# Scope

- Extend `quant_bitcoin/patterns/entry_simulation.py` with an entry trigger concept if needed, for example `TOUCH`, `TOUCH_AND_REACTION_CLOSE`, and `TOUCH_AND_RECLAIM_MIDPOINT`.
- Preserve existing `PatternEntryMode` values and backward-compatible fill semantics unless an explicit trigger is selected.
- Add `FAIR_VALUE_GAP_RETEST` policy or strategy preset with default `LIMIT_AT_PATTERN_MIDPOINT`, bounded wait bars, and retest/reaction economic rationale.
- Support near-boundary, midpoint, far-boundary, and custom-price retest modes with clear metadata.
- Propagate touch/reaction metadata through `build_pattern_trade_actions()` and serialized diagnostics.
- Keep risk-plan alignment to actual fill price active for all retest and reaction fills.

# Out of Scope

- No EMA/Fibonacci/liquidity target implementation in this task beyond consuming fields that already exist.
- No live order placement or exchange order behavior.
- No default behavior change for existing `FAIR_VALUE_GAP` strategy unless explicitly approved.
- No optimizer that picks the best entry trigger automatically.

# Requirements

- Simple retest mode must retain deterministic limit fill when price touches the selected level within max wait bars.
- Reaction mode must require a direction-aware post-touch confirmation before fill or else emit no-fill/cancel diagnostics.
- Metadata must include selected entry mode, trigger type, limit price, touch timestamp/index, reaction timestamp/index, fill timestamp/index, bars waited, and reason for no fill.
- Default retest max wait should be explicitly configured by the retest preset, proposed 5 bars, without altering existing baseline unless selected.
- Existing `MARKET_ON_CONFIRMATION_CLOSE` and `MARKET_ON_NEXT_OPEN` tests must continue to pass.
- All entry simulation remains based on completed historical candles.

# Status Tracking

## Execution Notes

- Assumption: `TOUCH` remains the default trigger and preserves existing limit-touch fill semantics.
- Assumption: reaction-trigger fills use completed candle close after touch, so fill-adjusted risk-plan alignment continues to apply.
- Blockers: none for Task 230.
- Safety: entry simulation remains offline/backtest-only with no live trading, network, exchange, order/account, key, or `.env` behavior.

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

- Added `PatternEntryTrigger` with `TOUCH`, `TOUCH_AND_REACTION_CLOSE`, and `TOUCH_AND_RECLAIM_MIDPOINT`.
- Added FVG retest preset config and `FAIR_VALUE_GAP_RETEST` policy with midpoint retest default.
- Propagated touch/reaction metadata through action metadata and CLI FVG entry config metadata.
- Updated FVG docs for opt-in retest trigger semantics.
- Verification:
  - `pytest tests/patterns/test_entry_simulation.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/strategies/test_pattern_execution_policy.py`

# Acceptance Criteria

- `FAIR_VALUE_GAP_RETEST` or equivalent opt-in preset exists and validates allowed FVG retest modes.
- Midpoint retest fills only after touch in touch mode.
- Reaction trigger fills only after touch plus valid bullish/bearish reaction confirmation.
- No-fill diagnostics distinguish never-touched, touched-without-reaction, expired, and invalid custom price cases.
- Risk plan is aligned to actual fill price for all successful retest/reaction entries.

# Required Tests

## Unit Tests

- `tests/patterns/test_entry_simulation.py` or existing action-builder tests cover touch, no touch, touch without reaction, and touch with reaction.
- `tests/backtesting/test_pattern_action_builder.py` covers metadata propagation and fill-adjusted risk for reaction entries.
- Policy validation tests cover allowed modes for baseline FVG and retest FVG.

## Integration Tests

- CLI test runs FVG retest preset with midpoint and reaction trigger over deterministic candles.
- Backtest engine test confirms no-fill retest entries do not create executions.

## Contract Tests

- Update API/README/FVG docs to define retest preset and trigger metadata if output schema changes.
- Document that baseline FVG market-confirmation behavior remains preserved.

## Safety Tests

- No exchange/order/account endpoint imports.
- No live trading flags or `.env` changes.
- Static or grep test confirms entry simulation remains offline/backtest-only.

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
pytest tests/patterns/test_entry_simulation.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py
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
