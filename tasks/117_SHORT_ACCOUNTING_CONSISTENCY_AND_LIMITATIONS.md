# Goal

Make short-position accounting explicit, internally consistent, and correctly measured, while clearly documenting unsupported margin economics.

This task does not implement a full futures or margin model. It fixes current short trade metric issues and makes limitations impossible to miss.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/backtesting/strategy_models.py`
- `quant_bitcoin/strategies/actions.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- existing accounting tests under `tests/backtesting/`

# Extracted Roles

- Owner role:
  - Backtesting accounting owner.
  - Owns short cash, position, realized PnL, unrealized PnL, and summary interpretation.
- Supporting roles:
  - Strategy action role: maps short entry/exit actions to execution side.
  - Metrics role: reports short trades correctly.
  - CLI role: documents limitations in output metadata.
- Forbidden roles:
  - No borrow-fee implementation.
  - No futures funding implementation.
  - No margin requirement implementation.
  - No liquidation engine.
  - No real short selling or exchange integration.

# Context

The current engine supports negative position quantities for shorts. `ENTER_SHORT` maps to `SELL`, and `EXIT_SHORT` maps to `BUY`. However, the model does not implement borrow fees, funding, maintenance margin, or liquidation. Win/loss counting can be wrong if it only evaluates `SELL` executions, because short exits are `BUY` executions.

The goal is to make the current short model honest and coherent without pretending it is a full futures or margin simulator.

# Scope

- Verify and correct short cash accounting in the existing engine model.
- Verify and correct short realized PnL calculation.
- Ensure short exits are included in win/loss counts.
- Add summary fields or metadata for short-specific performance where practical.
- Add clear limitations metadata to summary and CLI output.
- Add tests for profitable and losing short trades.

# Out of Scope

- Borrow fees.
- Funding payments.
- Margin requirements.
- Liquidation price calculation.
- Cross/isolated margin models.
- Leverage configuration.
- Exchange-specific futures behavior.

# Requirements

- A profitable short must produce positive realized PnL when exit price is below entry price.
- A losing short must produce negative realized PnL when exit price is above entry price.
- Short exits must be counted in win/loss metrics.
- Summary metadata must include limitations:
  - `No borrow fees modeled`
  - `No futures funding modeled`
  - `No maintenance margin or liquidation model`
- CLI output must not imply that short backtests are full margin/futures simulations.
- If short positions are allowed by default in pattern backtests, that limitation must be visible in the output.
- If `allow_short=False`, bearish entries must be skipped or blocked deterministically.

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

- Profitable short fixture has positive realized PnL.
- Losing short fixture has negative realized PnL.
- Short profitable close increments win count.
- Short losing close increments loss count.
- `allow_short=False` prevents short entries.
- Output metadata includes unsupported short-economics limitations.
- Existing long accounting remains unchanged.

# Required Tests

## Unit Tests

- Test short entry increases cash and creates negative position.
- Test short exit decreases cash and returns position toward zero.
- Test profitable short realized PnL.
- Test losing short realized PnL.
- Test short win count.
- Test short loss count.
- Test `allow_short=False` behavior.
- Test summary limitations metadata.

## Integration Tests

- Test bearish pattern fixture with short allowed.
- Test bearish pattern fixture with short disallowed.
- Test CLI output includes short-model limitations.

## Contract Tests

- `ENTER_SHORT` remains `SELL` execution side.
- `EXIT_SHORT` remains `BUY` execution side.
- Position side remains `SHORT` for short lifecycle executions.

## Safety Tests

- No borrow endpoint or margin endpoint is called.
- No futures account endpoint is called.
- No real order execution.

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
pytest tests/backtesting/test_strategy_engine_accounting.py
pytest tests/backtesting/test_strategy_engine.py
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
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
