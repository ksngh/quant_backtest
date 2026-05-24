# Goal

Review and improve the RSI/mean-reversion signal contract so RSI behavior is explicit, economically interpretable, and safe from repeated level-trigger artifacts.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue/gap:

- `RsiStrategy` uses simple rolling RSI and latest-level thresholds, not crossing rules.
- RSI can emit repeated BUY signals while oversold if a caller does not de-duplicate by position state.
- RSI is not clearly integrated as a regime filter for pattern strategies.

Read and inspect:

- `quant_bitcoin/strategies/rsi.py`
- `quant_bitcoin/backtesting/basic.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/strategies/actions.py`
- existing RSI tests

# Extracted Roles

- Owner role:
  - Mean-reversion signal contract owner.
- Supporting roles:
  - Backtest engine role: controls position state.
  - Indicator role: computes RSI variants.
  - Documentation role: explains RSI economic assumptions.
- Forbidden roles:
  - No pattern detector rewrite.
  - No live trading.
  - No ML signal generation.

# Context

Code-level hints:

- `rsi.py` currently calculates simple rolling RSI. Consider adding a Wilder/RMA RSI option while preserving the simple method as legacy/default if needed.
- Consider adding crossing-based signals:
  - BUY only when RSI crosses up/down through a threshold depending on strategy definition;
  - SELL on exit threshold or overbought crossing.
- Position-state-aware de-duplication may belong in the engine/strategy action layer, not the indicator itself.
- If RSI is intended only as a demo strategy, document limitations clearly.

Functional intent:

- RSI should not be mistaken for a validated alpha model without regime context.
- Mean-reversion logic should be explicit and testable.

# Scope

- Review RSI calculation method and signal trigger contract.
- Add optional Wilder/RMA RSI if accepted.
- Add optional crossing-based signal mode if accepted.
- Update docs/tests to describe level vs crossing behavior.
- Do not force RSI into pattern strategies unless separately assigned.

# Out of Scope

- Full indicator library rewrite.
- ML-based signal generation.
- Live trading.
- Pattern strategy retuning.

# Requirements

- Existing RSI behavior must remain backward-compatible unless explicitly migrated.
- New RSI modes must be opt-in and documented.
- Warm-up behavior must remain deterministic.
- RSI signal emission must not require future candles.
- Repeated signal behavior must be documented or mitigated.

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

- RSI tests cover simple rolling and any new Wilder/RMA mode.
- RSI tests cover level-trigger and crossing-trigger behavior if crossing is added.
- README/docs explain RSI limitations and intended use.
- Existing basic backtester behavior remains valid or documented.

# Required Tests

## Unit Tests

- Test RSI numeric calculation for known sequences.
- Test warm-up `HOLD` behavior.
- Test repeated level-trigger behavior or crossing suppression.

## Integration Tests

- Test `BasicBacktester` with RSI strategy after any contract changes.

## Contract Tests

- Ensure `Signal` enum remains compatible.
- Document new RSI config options if added.

## Safety Tests

- Confirm RSI strategy does not call exchange APIs or place orders.

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
pytest tests/strategies/test_rsi.py tests/backtesting/test_basic.py
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
