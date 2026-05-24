# Goal

Audit pattern scoring components, remove or label placeholder features, and add calibration diagnostics so pattern scores are not mistaken for validated alpha probabilities.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- Several pattern score functions combine real features with placeholder or constant components such as structure alignment, support/resistance context, or liquidity score.
- Scores can appear quantitative even when some components are not economically validated.

Read and inspect:

- `quant_bitcoin/patterns/fair_value_gap.py`
- `quant_bitcoin/patterns/order_block.py`
- `quant_bitcoin/patterns/trendline_break.py`
- `quant_bitcoin/patterns/cup_and_handle.py`
- `quant_bitcoin/patterns/diamond.py`
- `quant_bitcoin/patterns/adam_and_eve.py`
- `quant_bitcoin/strategies/pattern_explanations.py`
- relevant task docs for each pattern

# Extracted Roles

- Owner role:
  - Pattern research quality owner.
- Supporting roles:
  - Detector role: computes mechanical scores.
  - Documentation role: explains score limitations.
  - Metrics role: evaluates score buckets against forward outcomes.
- Forbidden roles:
  - No profitability-optimized retuning without validation task.
  - No live trading claims.
  - No detector rewrite beyond score transparency unless explicitly accepted.

# Context

Code-level hints:

- Search for `_calculate_pattern_score` across pattern modules.
- Identify which score inputs are observed features and which are placeholders/constant priors.
- Add metadata such as `score_components`, `score_component_sources`, or `score_limitations` to pattern events where appropriate.
- Consider lowering confidence terminology: `pattern_score` is a heuristic quality score, not a calibrated probability.
- Add optional score-bucket diagnostics in event-study/backtest metrics.

Functional intent:

- Users should know why a pattern scored high and whether each component was actually measured.

# Scope

- Audit scoring components for all supported patterns.
- Add component-level score metadata where feasible.
- Label placeholder components explicitly.
- Update strategy explanations to state economic assumptions and limitations.
- Add score-bucket evaluation helpers or tests where feasible.

# Out of Scope

- Full statistical calibration to probability of profit.
- Parameter optimization.
- New detectors.
- UI redesign.

# Requirements

- Every pattern score should be decomposable into component contributions or documented rules.
- Placeholder components must be removed, replaced with real features, or labeled explicitly.
- Strategy explanations must not imply validated alpha unless validation exists.
- Score thresholds should be described as heuristic filters.
- Tests must verify score component metadata for representative events.

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

- Each supported pattern event exposes or documents score components.
- Placeholder score components are clearly labeled in metadata/docs or replaced with implemented indicators.
- Pattern explanations distinguish mechanical pattern detection from economic alpha validation.
- Backtest output can be grouped by score bucket for later validation.

# Required Tests

## Unit Tests

- Test score component metadata for FVG, Order Block, Trendline Break, Cup and Handle, Diamond, and Adam and Eve fixtures.
- Test placeholder labeling when liquidity/spread context is unavailable.

## Integration Tests

- Test canonical strategy output includes score component metadata where available.

## Contract Tests

- Ensure pattern event dataclass changes are backward-compatible or documented.
- Ensure JSON serialization handles component metadata.

## Safety Tests

- Confirm no live trading or external API behavior is introduced.

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
pytest tests/patterns tests/strategies tests/backtesting/test_strategy_cli_persistence.py
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
