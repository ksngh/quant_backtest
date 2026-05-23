# Pattern Backtest Performance Regression Tests

# Goal

Add lightweight performance regression checks so future changes do not reintroduce multi-hour runtime for small candle sets.

This task should validate performance characteristics without making normal unit tests flaky or slow.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/pattern_detection_cache.py`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/patterns/*.py`
- `tests/backtesting/`
- `tests/patterns/`
- `tests/indicators/`

# Extracted Roles

- Owner role:
  - Test/performance regression owner.
  - Responsible for creating stable, lightweight runtime guardrails.

- Supporting roles:
  - Backtesting role:
    - Provides benchmarkable canonical functions.
  - Pattern detection role:
    - Provides fixture-friendly detectors.
  - CI/test role:
    - Ensures tests are not flaky or environment-dependent.

- Forbidden roles:
  - No production algorithm changes unless required to make code testable.
  - No live trading.
  - No exchange endpoints.
  - No API key handling.
  - No DB dependency in ordinary performance tests.

# Context

The current runtime issue is severe enough that regression coverage is required. However, wall-clock performance tests can be flaky if thresholds are too strict.

The preferred strategy:

- use candidate-count assertions;
- use phase-timing structure assertions;
- use small wall-clock smoke thresholds only for local/optional benchmark tests;
- mark heavier benchmarks as optional.

# Scope

- Add lightweight performance regression tests.
- Add optional benchmark tests or scripts for local verification.
- Ensure ordinary `pytest` remains fast.
- Use fixture candles, not live market data.
- Test canonical path with mocked provider and `--no-persist`.

# Out of Scope

- Frontend tests.
- DB integration performance tests unless explicitly marked optional.
- Full historical benchmark suite.
- New algorithm implementation.

# Requirements

- Add fixture-based tests for 400-candle equivalent input or a representative compressed fixture.
- Test each supported pattern path can build actions without pathological candidate growth.
- Add assertions for:
  - indicator cache constructed once;
  - detector called in at-index mode where expected;
  - candidate counts stay below configured caps;
  - no repeated full indicator calculation inside candle loop.
- Optional local benchmark command should report:
  - pattern key;
  - candle count;
  - elapsed ms;
  - events detected;
  - actions emitted.
- Avoid strict wall-clock thresholds in CI unless environment is controlled.

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

- Tests cover all supported pattern paths.
- Tests fail if canonical path falls back to repeated full-prefix indicator recalculation.
- Tests verify candidate caps for pivot-heavy patterns.
- Optional benchmark script or command is documented.
- Ordinary `pytest` remains reasonably fast.
- No live data or DB is required for ordinary performance regression tests.

# Required Tests

## Unit Tests

- Indicator cache single-build tests.
- Candidate cap tests.
- At-index detector invocation tests.
- No duplicate event emission tests.

## Integration Tests

- Mocked canonical backtest path for each pattern.
- `--no-persist` integration path.
- Optional benchmark smoke test marked appropriately.

## Contract Tests

- Tests use standard candle schema.
- No external network required.
- Deterministic fixture output.

## Safety Tests

- No exchange calls.
- No account endpoints.
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
- Performance tests are not flaky.
- Optional heavy benchmarks are clearly marked.

# Verification

Default:

```bash
pytest
```

Optional benchmark command to document after implementation:

```bash
pytest tests/backtesting/test_pattern_runtime_benchmark.py -m benchmark
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
- benchmark command
- benchmark result if run
- Codex self-review result
- known limitations
- recommended next task
