# Goal

Make intrabar stop/target ambiguity handling explicit and consistently applied in pattern exit simulation.

When OHLC data shows both stop-loss and take-profit levels were touched in the same candle, the backtest must resolve the ambiguity deterministically and conservatively by default.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/risk/exit_simulation.py`
- `quant_bitcoin/backtesting/intrabar_policy.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/patterns/entry_simulation.py`
- existing exit simulation and backtesting tests

# Extracted Roles

- Owner role:
  - Backtesting exit-simulation owner.
  - Owns same-candle sequencing behavior for historical OHLC simulation.
- Supporting roles:
  - Intrabar policy role: provides deterministic ambiguity resolution helpers.
  - Risk / exit role: applies stop, target, soft invalidation, and time-stop rules.
  - Test role: proves precedence behavior.
- Forbidden roles:
  - No tick reconstruction.
  - No probabilistic intrabar sequencing.
  - No exchange data fetching.
  - No new live execution logic.

# Context

`risk/exit_simulation.py` currently documents conservative precedence: break-even/trailing update, hard stop, take-profit checks, soft invalidation, then time stop. When stop and target are both reachable in the same candle, stop wins. `intrabar_policy.py` also contains reusable intrabar sequencing helpers, but they are not clearly integrated everywhere.

This task makes the policy explicit, test-covered, and visible in metadata.

# Scope

- Confirm or wire conservative same-candle precedence in exit simulation.
- Ensure stop-first behavior is applied consistently for long and short trades.
- Ensure metadata records the applied intrabar/precedence policy.
- Add tests for ambiguous stop/target candles.
- Optionally expose policy config internally, but default must remain conservative.

# Out of Scope

- Tick-level simulation.
- Real order-book sequencing.
- Optimistic policy as default.
- Market impact modeling.
- Full lifecycle integration beyond exit precedence.

# Requirements

- Default policy must resolve stop/target ambiguity to stop.
- Long trade ambiguity must be tested.
- Short trade ambiguity must be tested.
- If entry, stop, and target are all touched in the same candle, conservative behavior must be documented and tested.
- Exit event metadata must include precedence or intrabar policy information.
- Any configurable policy must be explicit and deterministic.

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

- Same-candle long stop/target touch exits by stop under default config.
- Same-candle short stop/target touch exits by stop under default config.
- Exit metadata explains stop-before-target precedence.
- Existing non-ambiguous target behavior still exits at target.
- Existing non-ambiguous stop behavior still exits at stop.

# Required Tests

## Unit Tests

- Test long stop-only candle.
- Test long target-only candle.
- Test long stop-and-target same candle.
- Test short stop-only candle.
- Test short target-only candle.
- Test short stop-and-target same candle.
- Test metadata includes precedence policy.

## Integration Tests

- Test pattern lifecycle fixture where stop and target are both touched.
- Test canonical output includes exit reason and precedence metadata.

## Contract Tests

- Exit simulation remains pure.
- No mutation of input candle data.
- Standard candle high/low/close contract remains unchanged.

## Safety Tests

- No external data or exchange calls are introduced.

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
pytest tests/risk/test_exit_simulation.py
pytest tests/backtesting/test_intrabar_policy.py
pytest tests/backtesting/test_pattern_action_builder.py
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
