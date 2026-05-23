# Pivot-Heavy Pattern Candidate Pruning

# Goal

Optimize the slowest pivot-heavy pattern detectors so canonical backtests do not explode in runtime as candle count or pivot count grows.

This task focuses on:

- Trendline Break;
- Cup and Handle;
- Diamond;
- Adam and Eve.

The objective is to reduce candidate search complexity while preserving deterministic event output for representative fixtures.

# Source Requirement

Read and inspect:

- `STATUS.md`
- `AGENTS.md`
- `quant_bitcoin/backtesting/strategy_postgres_runner_cli.py`
- `quant_bitcoin/backtesting/pattern_detection_cache.py`
- `quant_bitcoin/strategies/patterns.py`
- `quant_bitcoin/patterns/trendline_break.py`
- `quant_bitcoin/patterns/cup_and_handle.py`
- `quant_bitcoin/patterns/diamond.py`
- `quant_bitcoin/patterns/adam_and_eve.py`
- `quant_bitcoin/indicators/pivots.py`
- related tests under `tests/patterns/` and `tests/backtesting/`

# Extracted Roles

- Owner role:
  - Pattern algorithm optimization owner.
  - Responsible for reducing candidate count and runtime for pivot-heavy detectors.

- Supporting roles:
  - Indicator role:
    - Provides confirmed pivot rows and cached indicators.
  - Backtesting role:
    - Ensures canonical strategy path uses optimized at-index detection.
  - Test role:
    - Verifies output equivalence and runtime guardrails.

- Forbidden roles:
  - No new pattern semantics unless required by documented pruning.
  - No live trading.
  - No order execution.
  - No API key handling.
  - No frontend changes.
  - No DB schema changes.
  - No hidden nondeterminism.

# Context

Pivot-heavy detectors can become slow because they evaluate many historical pivot combinations.

Likely complexity sources:

- Trendline Break:
  - combinations of visible pivots for candidate trendlines.
- Cup and Handle:
  - nested combinations of left rim, cup bottom, right rim, and handle low.
- Diamond:
  - contiguous pivot windows and split candidates with repeated line fitting.
- Adam and Eve:
  - combinations of Adam low, neckline high, Eve low, and breakout.

When these detectors are executed for every candle prefix, runtime can grow rapidly.

# Scope

- Add bounded candidate pruning for pivot-heavy patterns.
- Add at-index detection or current-breakout-only evaluation where practical.
- Add config limits, such as:
  - `max_recent_pivots`
  - `max_candidates_per_bar`
  - `max_pattern_lookback`
  - `max_trendline_pairs_per_bar`
- Apply cheap filters before expensive calculations.
- Cache reusable pivot-derived calculations where practical.
- Preserve deterministic output and stable event ids.
- Add performance regression tests that are not slow.

# Out of Scope

- Rewriting all pattern algorithms as full state machines unless necessary.
- Changing public batch detector behavior without compatibility tests.
- Persistence changes.
- Runtime UI changes.
- S/L and T/P lifecycle work.
- Transaction cost work.

# Requirements

- Trendline Break:
  - Restrict visible pivots to a bounded recent window.
  - Avoid re-evaluating identical pivot pairs where possible.
  - Apply slope, length, and touch-count filters before expensive event construction.
- Cup and Handle:
  - Restrict candidate pivots to a bounded recent window.
  - Apply index-order and duration filters before nested candidate generation.
  - Apply rim-difference and cup-depth filters before handle evaluation.
  - Add a maximum candidates-per-bar guard.
- Diamond:
  - Restrict contiguous pivot windows by duration and pivot count early.
  - Cache line-fit results when reused.
  - Add a maximum candidate windows-per-bar guard.
- Adam and Eve:
  - Restrict candidate pivots to a bounded recent window.
  - Apply prior downtrend, bottom-difference, duration, and neckline relation early.
  - Add a maximum candidates-per-bar guard.
- All pruning defaults must be conservative and deterministic.
- If pruning can change output, document the rule in strategy parameters or metadata.

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

- Each pivot-heavy pattern has bounded candidate evaluation in the canonical backtest path.
- Candidate counts per bar can be measured or reported in profiling metadata.
- 400-candle canonical backtests for each pivot-heavy pattern complete in a reasonable runtime.
- Representative fixture outputs remain stable.
- If pruning changes an existing edge-case output, the change is documented and covered by tests.
- No nondeterministic ordering is introduced.

# Required Tests

## Unit Tests

- Trendline Break:
  - candidate pair limit is respected;
  - valid breakout still emits event.
- Cup and Handle:
  - early pruning does not remove a valid fixture;
  - candidate cap is respected.
- Diamond:
  - window cap is respected;
  - valid bullish and bearish fixtures still emit expected events.
- Adam and Eve:
  - candidate cap is respected;
  - valid bullish fixture still emits expected event.
- All patterns:
  - deterministic ordering with identical input;
  - no duplicate event ids.

## Integration Tests

- Canonical pattern backtest fixture for:
  - `TRENDLINE_BREAK`
  - `CUP_AND_HANDLE`
  - `DIAMOND`
  - `ADAM_AND_EVE`
- Validate emitted actions or events remain expected.
- Validate performance metadata or benchmark helper reports candidate counts.

## Contract Tests

- Batch detectors remain available.
- At-index/canonical path does not fetch market data.
- Pattern detectors remain pure.
- No portfolio mutation in detectors.

## Safety Tests

- No exchange order endpoint calls.
- No account endpoint calls.
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
- Candidate pruning is deterministic.
- Candidate pruning is documented in config/metadata.
- Performance improvement is measured, not assumed.

# Verification

Default:

```bash
pytest
```

Recommended targeted tests:

```bash
pytest tests/patterns/test_trendline_break.py
pytest tests/patterns/test_cup_and_handle.py
pytest tests/patterns/test_diamond.py
pytest tests/patterns/test_adam_and_eve.py
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
- before/after runtime per pivot-heavy pattern
- candidate count before/after where measurable
- any changed pattern semantics
- Codex self-review result
- known limitations
- recommended next task
