# Goal

Create a no-lookahead contract across pattern detectors by separating event detection from later lifecycle-state updates and testing rolling-prefix parity.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- Some full-batch detectors classify lifecycle state using candles after the event confirmation candle.
- Canonical optimized FVG/Order Block paths use current-index slices, but direct full-batch detector calls can be misused in research and event studies.
- The repository already has no-lookahead work for FVG cache; broaden and formalize the contract.

Read and inspect:

- `tasks/113_FVG_NO_LOOKAHEAD_CACHE_CORRECTION.md`
- `tasks/121_SHARED_INDICATOR_CACHE_AND_AT_INDEX_PATTERN_DETECTION.md`
- `quant_bitcoin/backtesting/fvg_detection_cache.py`
- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/patterns/order_block.py`
- `quant_bitcoin/patterns/trendline_break.py`
- `quant_bitcoin/patterns/cup_and_handle.py`
- `quant_bitcoin/patterns/diamond.py`
- `quant_bitcoin/patterns/adam_and_eve.py`
- pattern detector tests

# Extracted Roles

- Owner role:
  - Research correctness and pattern detector contract owner.
- Supporting roles:
  - Indicator cache role: provides current-index data safely.
  - Detector role: emits events only from visible candles.
  - Event-study role: may evaluate forward lifecycle after event confirmation.
- Forbidden roles:
  - No live trading.
  - No strategy profitability tuning.
  - No dashboard changes.

# Context

Code-level hints:

- For FVG, `_classify_fvg_state()` uses later candles when full history is passed. Consider separating:
  - initial event detection at confirmation candle;
  - lifecycle update after event confirmation for analysis only.
- For Order Block, `_classify_state()` similarly uses later candles when full history is passed.
- Add public `detect_*_at_index()` functions or a common detector context for every supported pattern.
- Add parity tests:
  - `detect_at_index(full, t)` equals `detect(full.iloc[:t+1])` ending at `t`.
- Label any function that intentionally performs retrospective lifecycle analysis as such.

Functional intent:

- Backtest signals must never depend on candles after the event timestamp.
- Retrospective event-study state updates must be explicit.

# Scope

- Define no-lookahead detector contract for all supported patterns.
- Add current-index detection helpers where missing.
- Separate lifecycle-state updates from signal-time event detection where needed.
- Add rolling-prefix parity tests across patterns.
- Update docs/comments to warn against full-history misuse.

# Out of Scope

- Changing pattern economic definitions.
- Optimizing detector speed beyond what is necessary for correctness.
- Rewriting all pattern algorithms from scratch.

# Requirements

- Signal-time detector output must use only candles `<= current_index`.
- Lifecycle fields that require future candles must be absent, neutral, or explicitly marked retrospective.
- Every supported pattern must have a testable no-lookahead path.
- Full-history helper APIs must be documented as either safe rolling evaluation or retrospective analysis.
- Existing canonical runner behavior must remain deterministic.

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

- No-lookahead parity tests pass for FVG, Order Block, Trendline Break, Cup and Handle, Diamond, and Adam and Eve.
- Direct detector usage has documented safe and retrospective modes.
- FVG/Order Block lifecycle state no longer silently contaminates signal-time events.
- Backtest results do not change except where prior look-ahead behavior was being used accidentally.

# Required Tests

## Unit Tests

- Add detector-level current-index parity tests for each pattern.
- Add tests proving future candles that fill/break a zone do not change the event emitted at confirmation time.

## Integration Tests

- Add canonical strategy runner tests comparing cached optimized paths and rolling-prefix baseline paths.

## Contract Tests

- Document detector API modes and verify public exports remain stable or deprecated explicitly.

## Safety Tests

- Confirm no exchange calls, no live trading, and no API key behavior.

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
pytest tests/patterns tests/backtesting/test_fvg_detection_cache.py tests/backtesting/test_pattern_strategy.py
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
