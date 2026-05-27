# Task 229: FVG Fibonacci Retracement Confluence Filter

# Goal

Add a deterministic Fibonacci retracement confluence feature so FVG retest candidates can be scored or filtered when the FVG zone overlaps a predeclared retracement band such as 0.382 to 0.618.

# Source Requirement

Owner requested a task bundle on 2026-05-27 to apply the FVG retest strategy design, add multi-timeframe trend scoring across 1m/5m/15m-style candles, and finish with documentation/status/history/backlog reconciliation.


# Extracted Roles

- Owner role:
  - FVG research feature owner for Fibonacci confluence calculation and metadata.
- Supporting roles:
  - Pivot/swing structure role.
  - FVG detector role.
  - Backtest diagnostics role.
  - Test fixture role.
- Forbidden roles:
  - No live trading, no real Binance order execution, no signed order/account endpoints, no API keys, no `.env` changes, no optimizer that silently selects the most profitable configuration, and no behavior outside offline research/backtest scope.

# Context

The FVG retest thesis prefers gaps that sit inside meaningful pullback areas rather than arbitrary imbalance zones. This task adds Fibonacci confluence as an opt-in research feature and must avoid look-ahead when choosing impulse anchors.

# Scope

- Add `quant_bitcoin/indicators/fibonacci_retracement.py` or a focused helper near FVG research features.
- Define configurable anchor methods, initially limited to no-lookahead choices such as displacement candle range and confirmed pivot swing range.
- Add `FairValueGapConfig` fields for `use_fibonacci_confluence`, `fib_min_level`, `fib_max_level`, `fib_tolerance_atr_multiplier`, and `fib_anchor_method`.
- Compute whether `zone_low`/`zone_high`/`zone_mid` overlaps the configured retracement band.
- Attach metadata: anchor prices/indexes, retracement level at zone midpoint, band bounds, overlap mode, pass/fail reason, and limitations.
- Support diagnostic-only scoring and hard-filter mode without changing defaults.

# Out of Scope

- No automatic anchor optimization or hindsight selection of the most favorable swing.
- No entry-order placement or execution changes.
- No multi-timeframe Fibonacci anchoring unless explicitly implemented as a deterministic extension after base tests pass.
- No profitability claim based only on in-sample confluence results.

# Requirements

- Anchor selection must use only candles available at FVG confirmation time.
- Fibonacci level calculations must be direction-aware for bullish and bearish FVG events.
- FVG zone overlap should be configurable: midpoint-only, any-zone-overlap, or full-zone-contained if implemented.
- Invalid or unavailable anchors must produce explicit metadata and must fail required-confluence mode.
- Default FVG behavior remains unchanged when Fibonacci confluence is disabled.
- Score contribution must be explainable and separable from EMA/trend-score contribution.

# Status Tracking

## Execution Notes

- Assumption: initial no-lookahead anchor support is limited to `DISPLACEMENT_CANDLE_RANGE`.
- Assumption: Fibonacci confluence is default-off and uses score metadata weight `0.0` to avoid changing baseline FVG scoring.
- Blockers: none for Task 229.
- Safety: no live trading, network, exchange, order/account, key, `.env`, or execution behavior was added.

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

- Added deterministic Fibonacci retracement confluence helper with direction-aware band math, overlap modes, tolerance, and invalid-anchor metadata.
- Added default-off FVG Fibonacci confluence diagnostics/hard-filter config and event metadata.
- Propagated Fibonacci metadata through canonical pattern action metadata.
- Updated FVG strategy documentation for default-off Fibonacci confluence semantics and limitations.
- Verification:
  - `pytest tests/indicators/test_fibonacci_retracement.py tests/patterns/test_fair_value_gap.py tests/backtesting/test_pattern_action_builder.py`

# Acceptance Criteria

- Synthetic bullish and bearish examples produce expected 0.382-0.618 confluence pass/fail results.
- Confluence metadata is included in FVG events when enabled.
- Hard-filter mode suppresses non-confluent events with a clear reason.
- Diagnostic mode records confluence but preserves event emission.
- No-lookahead anchor behavior is verified with fixture candles.

# Required Tests

## Unit Tests

- `tests/indicators/test_fibonacci_retracement.py` covers bullish/bearish retracement math, band overlap, tolerance, invalid anchors, and direction handling.
- `tests/patterns/test_fair_value_gap.py` covers FVG confluence pass/fail and default-disabled behavior.
- Metadata serialization test for Fibonacci fields.

## Integration Tests

- Pattern action metadata propagation test for Fibonacci event fields.
- Optional FVG detection-cache test if Fibonacci features are cached.

## Contract Tests

- Document Fibonacci anchor method, band defaults, and no-lookahead limitation in FVG strategy docs.
- Document that Fibonacci confluence is a filter/diagnostic feature, not an optimizer.

## Safety Tests

- No external API, order endpoint, account endpoint, or secret handling.
- No live trading behavior.

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
pytest tests/indicators/test_fibonacci_retracement.py tests/patterns/test_fair_value_gap.py
pytest tests/backtesting/test_pattern_action_builder.py
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
