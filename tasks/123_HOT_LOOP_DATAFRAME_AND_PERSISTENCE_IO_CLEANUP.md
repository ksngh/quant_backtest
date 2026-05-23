# Hot-Loop DataFrame And Persistence I/O Cleanup

# Goal

Remove avoidable hot-loop overhead from the canonical pattern backtest path.

This task targets runtime waste from repeated DataFrame deep copies, repeated DataFrame construction, repeated prefix slicing, and accidental database or persistence operations inside candle loops.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/backtesting/pattern_detection_cache.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/patterns/*.py`
- `quant_bitcoin/persistence/postgres.py`
- related tests under `tests/backtesting/` and `tests/patterns/`

# Extracted Roles

- Owner role:
  - Backtest runtime efficiency owner.
  - Responsible for removing repeated in-memory and persistence overhead in canonical backtest loops.

- Supporting roles:
  - Pattern detection role:
    - Avoids defensive deep copies in hot loops when not needed.
  - Persistence role:
    - Ensures DB writes remain one transaction per completed run.
  - Test role:
    - Verifies output is unchanged after overhead cleanup.

- Forbidden roles:
  - No algorithmic pruning changes unless strictly required for copy cleanup.
  - No DB schema changes.
  - No frontend changes.
  - No live trading.
  - No exchange order/account endpoints.
  - No API key handling.

# Context

The current pattern backtest path may create repeated slices and deep copies, such as:

```text
candles.iloc[:i]
copy(deep=True)
pd.DataFrame(list(...))
```

inside loops. This can become expensive when combined with pattern detection and indicator recalculation.

Persistence must happen once per completed run, not inside each candle or event loop.

# Scope

- Audit canonical pattern backtest hot loops.
- Remove unnecessary `copy(deep=True)` calls inside repeated candle loops.
- Avoid creating new DataFrames repeatedly where views or pre-normalized frames are sufficient.
- Ensure candle normalization happens once per run where possible.
- Ensure database loading happens once before in-memory evaluation.
- Ensure database persistence happens once after in-memory evaluation.
- Preserve defensive copying at public API boundaries where needed.
- Add tests to confirm caller input data is not mutated.

# Out of Scope

- Implementing shared indicator cache.
- Implementing candidate pruning.
- Runtime metric persistence.
- Frontend/API changes.
- Strategy logic changes.

# Requirements

- Canonical pattern action building must not deep-copy full candle prefixes per candle unless proven necessary.
- Pattern detection hot paths should use:
  - cached normalized candles;
  - `.iloc` views where safe;
  - arrays or cached columns where practical.
- Any removed defensive copy must be justified by immutability or non-mutation tests.
- No DB query should occur inside per-candle pattern evaluation loops.
- No DB insert/update should occur inside per-candle pattern evaluation loops.
- Persistence must remain all-or-nothing per completed run.
- Output must remain deterministic.

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

- Hot-loop deep copies are removed or reduced in the canonical path.
- Candle data is still not mutated by backtests.
- DB load occurs once per run.
- DB persistence occurs once per completed run.
- Outputs remain stable for representative fixtures.
- Runtime improvement is measured and included in completion summary.

# Required Tests

## Unit Tests

- Verify canonical action building does not mutate input candles.
- Verify pattern detectors do not mutate input candles.
- Verify output remains identical before and after removing copies for fixture inputs.
- Add tests for empty candle frames and invalid schema after refactor.

## Integration Tests

- Run canonical pattern backtest with mocked provider and repository.
- Assert provider `load()` is called once.
- Assert repository `save_completed_backtest()` is called once when persistence is enabled.
- Assert repository is not called when `--no-persist` is used.

## Contract Tests

- Standard candle schema remains unchanged.
- Strategy output remains deterministic.
- Persistence payload remains graph-ready and ordered.

## Safety Tests

- No exchange order endpoint calls.
- No private/account endpoint calls.
- No API key loading.
- No signed requests.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- No accidental input mutation.
- DB I/O is not inside candle loops.
- Persistence remains transactional per completed run.

# Verification

Default:

```bash
pytest
```

Recommended targeted tests:

```bash
pytest tests/backtesting/test_strategy_postgres_runner_cli.py
pytest tests/backtesting/test_strategy_engine.py
pytest tests/patterns
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
- copies removed or reduced
- DB I/O verification result
- before/after runtime
- Codex self-review result
- known limitations
- recommended next task
