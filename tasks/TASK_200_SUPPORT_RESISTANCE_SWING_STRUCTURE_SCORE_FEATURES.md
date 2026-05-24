# Task 200: SUPPORT_RESISTANCE_SWING_STRUCTURE_SCORE_FEATURES

# Goal

Replace structure/support-resistance placeholder score priors with actual support/resistance and swing-structure features where safe.

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

- Support/resistance and swing structure indicators are exported from indicators/__init__.py.
- FVG, Order Block, and Trendline currently include structure/SR placeholder score components.
- Actual context features can improve economic interpretability if no-lookahead is preserved.

# Scope

- quant_bitcoin/indicators/support_resistance_zone.py
- quant_bitcoin/indicators/swing_structure.py
- quant_bitcoin/indicators/__init__.py
- quant_bitcoin/patterns/fair_value_gap.py
- quant_bitcoin/patterns/order_block.py
- quant_bitcoin/patterns/trendline_break.py
- tests/indicators/
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

- Define a no-lookahead support/resistance proximity feature based only on confirmed pivots/zones available by signal time.
- Define swing-structure alignment feature: bullish continuation/reversal alignment and bearish symmetry.
- Replace placeholder constants with observed features where inputs are computed.
- When features cannot be computed due to warm-up/no context, record missing_context rather than placeholder score.
- Expose feature windows and confirmation delays in score metadata.

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

Assumptions / notes:
- Support/resistance and swing-structure features must use only pivots whose `confirmed_index` is at or before the evaluated signal index.
- Missing warm-up/context should emit explicit `missing_context` metadata with zero favorable score, not a placeholder prior.
- Implementation remains limited to offline indicator/pattern score metadata and tests in the task scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- FVG/OB/Trendline score metadata includes observed S/R or swing feature when available.
- No future pivot/zone is used before confirmed_index.
- Missing context does not silently add favorable score.
- Feature values are JSON-safe and explainable.

# Required Tests

## Unit Tests

- Unit: support proximity uses only zones confirmed before event index.
- Unit: bullish FVG near support gets alignment component when configured.
- Unit: bearish OB near resistance symmetry.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- No-lookahead: adding future candles cannot change at-index score component.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Detector runtime may increase due to additional indicator calculations.
- Scores and VALID/WEAK classification may change.

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

# Completion Summary

- Files changed: `quant_bitcoin/indicators/support_resistance_zone.py`, `quant_bitcoin/indicators/swing_structure.py`, `quant_bitcoin/indicators/__init__.py`, `quant_bitcoin/patterns/fair_value_gap.py`, `quant_bitcoin/patterns/order_block.py`, `quant_bitcoin/patterns/trendline_break.py`, `quant_bitcoin/patterns/score_metadata.py`, `tests/indicators/test_support_resistance_zone.py`, `tests/indicators/test_swing_structure.py`, `tests/patterns/test_fair_value_gap.py`, `tests/patterns/test_order_block.py`, `tests/patterns/test_trendline_break.py`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: added no-lookahead support/resistance proximity and swing-structure alignment helpers, exposed feature metadata in score components, and replaced FVG/OB/Trendline structure/SR placeholder priors with observed features or explicit `missing_context` zero-score components.
- Tests added or updated: indicator no-lookahead tests, bullish FVG near confirmed support, bearish OB near confirmed resistance, FVG at-index future-candle invariance, and existing score-component expectations.
- Tests run: `pytest tests/indicators/test_support_resistance_zone.py tests/indicators/test_swing_structure.py tests/patterns/test_fair_value_gap.py tests/patterns/test_order_block.py tests/patterns/test_trendline_break.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; scope stayed within offline indicator/pattern score metadata, no live trading/order endpoints/secrets were introduced, and verification passed.
- Known limitations: detector runtime can increase because FVG/OB compute context pivots per emitted event; feature scoring remains deterministic heuristic research metadata, not calibrated alpha probability.
- Recommended next task: Task 201 `MARKET_REGIME_CONDITIONED_PATTERN_THRESHOLDS`.
