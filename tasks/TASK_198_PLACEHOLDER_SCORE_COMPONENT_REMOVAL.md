# Task 198: PLACEHOLDER_SCORE_COMPONENT_REMOVAL

# Goal

Prevent placeholder score components from contributing to executable pattern_score while preserving their diagnostic metadata.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P2**

# Extracted Roles

- Owner role: Project owner / quant research lead.
- Supporting roles:
  - Quant researcher: validate economic assumptions, score calibration, and OOS diagnostics.
  - System trading architect: maintain action, risk, sizing, cost, and execution contracts.
  - Backtest verification engineer: preserve no-lookahead, fill correctness, intrabar policy, and deterministic tests.
  - Code reviewer: enforce scope, safety, and architecture boundaries.
- Forbidden roles:
- Live trading implementation unless the task explicitly says otherwise.
- Real exchange order execution.
- Secret/key management changes outside documented safety scope.
- Unrelated frontend/backend/database changes unless listed in Scope.

# Context

- Some pattern score components are placeholder constants or policy priors, including structure alignment, support/resistance context, and liquidity.
- score_metadata.py already warns that pattern_score is not a calibrated probability.
- If placeholder weights contribute to entry filtering, score can appear more evidential than it is.

# Scope

- quant_bitcoin/patterns/score_metadata.py
- quant_bitcoin/patterns/fair_value_gap.py
- quant_bitcoin/patterns/order_block.py
- quant_bitcoin/patterns/trendline_break.py
- quant_bitcoin/patterns/diamond.py
- tests/patterns/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Add an option or default behavior in build_score_metadata() to exclude is_placeholder components from executable_score.
- Preserve raw diagnostic_score including placeholders if useful for display.
- Expose score_components with included_in_executable_score boolean.
- Rename or add fields: pattern_score, executable_pattern_score, diagnostic_pattern_score as needed without breaking current consumers unexpectedly.
- Update entry filters to use executable score when configured.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for this task's historical context.
- [x] Confirm this task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Identify exact source files and tests touched by this task.
- [x] Confirm no live trading, real order execution, signed exchange request, or secret handling is introduced.

Assumptions before implementation:
- `pattern_score` should remain backward-compatible and map to executable score by default.
- Diagnostic score with placeholders should remain available as `diagnostic_pattern_score`.
- Placeholder components stay visible in `score_components` with an explicit `included_in_executable_score` flag.
- Entry filters should prefer `executable_pattern_score` when available and fall back to legacy `pattern_score`.
- No live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior is introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Placeholder components no longer raise executable score unless explicitly allowed by config.
- All placeholder components remain visible in metadata and limitations.
- Entry filtering behavior is deterministic and documented.
- No pattern loses score metadata keys required by existing persistence tests.

# Required Tests

## Unit Tests

- Unit: placeholder-only component list produces executable score 0 or configured exclusion behavior.
- Unit: FVG score decreases when placeholder components are excluded.
- Unit: observed components still contribute normally.

## Integration Tests

- Integration: entry filter uses executable score when available.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Pattern status may downgrade from VALID to WEAK if executable score falls below thresholds.
- Historical score calibration reports need schema compatibility handling.

# Review Checklist

- [x] Scope respected.
- [x] Requirement matched.
- [x] Role ownership respected.
- [x] Architecture boundaries respected.
- [x] Data contract respected where applicable.
- [x] No hardcoded secrets.
- [x] No real order execution unless explicitly requested by a future owner-approved live task.
- [x] No unnecessary abstractions.
- [x] No lookahead introduced.
- [x] Pattern/risk/indicator semantics are documented in metadata or docs.
- [x] Tests cover both success and failure/skip paths.

# Verification

Default:

```bash
pytest
```

Recommended targeted verification for this task:

```bash
pytest tests/patterns tests/risk tests/backtesting
pytest tests/strategies
git diff --check
```

If frontend files are changed:

```bash
cd frontend && npm run build
```

If backend/API files are changed and dependencies are available:

```bash
pytest backend/tests
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

## Completion Summary

- Files changed: `quant_bitcoin/patterns/score_metadata.py`, `quant_bitcoin/patterns/fair_value_gap.py`, `quant_bitcoin/patterns/order_block.py`, `quant_bitcoin/patterns/trendline_break.py`, `quant_bitcoin/patterns/diamond.py`, `quant_bitcoin/strategies/patterns.py`, `quant_bitcoin/backtesting/pattern_action_builder.py`, `tests/patterns/test_score_metadata.py`, pattern/strategy/walk-forward tests, `STATUS.md`, `BACKLOG.md`, `PROJECT_HISTORY.md`, and this task file.
- Implementation summary: `build_score_metadata()` now excludes placeholder components from executable score by default, preserves placeholder-inclusive `diagnostic_pattern_score`, marks every component with `included_in_executable_score`, keeps legacy `pattern_score` mapped to executable score, exposes executable/diagnostic scores on scoped pattern events and action metadata, and makes entry filters prefer executable score.
- Tests added or updated: direct score metadata tests, FVG/Order Block/Trendline placeholder-score contract assertions, executable-score entry filter coverage, action metadata coverage, and walk-forward fixtures that explicitly allow WEAK after placeholder exclusion.
- Tests run: `pytest tests/patterns/test_score_metadata.py tests/patterns/test_fair_value_gap.py tests/patterns/test_order_block.py tests/patterns/test_trendline_break.py tests/patterns/test_diamond.py tests/strategies/test_pattern_strategies.py tests/backtesting/test_pattern_action_builder.py`; `pytest tests/backtesting/test_walk_forward.py tests/patterns/test_score_metadata.py tests/patterns/test_fair_value_gap.py tests/patterns/test_order_block.py tests/patterns/test_trendline_break.py tests/strategies/test_pattern_strategies.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; no live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior was introduced.
- Known limitations: placeholder exclusion can downgrade previously VALID heuristic patterns to WEAK unless callers explicitly relax status filters; diagnostic score remains for display only.
- Recommended next task: Task 199 `PATTERN_SCORE_OOS_LIFT_AND_COMPONENT_ABLATION`.
