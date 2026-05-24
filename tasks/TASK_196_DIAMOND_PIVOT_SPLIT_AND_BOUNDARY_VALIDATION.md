# Task 196: DIAMOND_PIVOT_SPLIT_AND_BOUNDARY_VALIDATION

# Goal

Fix Diamond pivot-count semantics and wire boundary touch/deviation validation into the actual detector.

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

- DiamondConfig.minimum_pivot_count defaults to 6, but the split loop effectively requires at least 8 pivots for expansion/contraction segmentation.
- maximum_boundary_touch_deviation_atr exists in config but is not visibly enforced as boundary touch validation.
- Diamond is highly susceptible to pivot-window overfitting.

# Scope

- quant_bitcoin/patterns/diamond.py
- quant_bitcoin/patterns/diamond_risk_exit.py
- tests/patterns/test_diamond.py

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Make minimum_pivot_count consistent with feasible split requirements or adjust split logic to support the documented minimum.
- Add explicit boundary touch validation for upper/lower contraction boundaries.
- Require or score alternating high/low pivot structure when configured.
- Expose split_position, expansion_pivot_count, contraction_pivot_count, boundary_touch_count, and boundary_deviation_atr metadata.
- Ensure DiamondStrategy passes candles to risk planner when internal pivot stops are intended.

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
- Diamond detection remains OHLCV/pivot heuristic only.
- If documented 6-pivot splits are infeasible, the detector should reject them deterministically and expose metadata for accepted candidates.
- Boundary validation uses confirmed pivots visible at the breakout candle only.
- No live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior is introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- 6-pivot, 7-pivot, and 8-pivot fixtures have explicit documented outcomes.
- maximum_boundary_touch_deviation_atr affects candidate acceptance or score.
- Strategy wrapper can use last internal pivot stop when candles are supplied.
- No-lookahead with confirmed pivots remains intact.

# Required Tests

## Unit Tests

- Unit: 6-pivot window rejected with clear reason if infeasible.
- Unit: 8-pivot diamond accepted when expansion/contraction and boundary touch conditions pass.
- Unit: boundary deviation too large rejects candidate.
- Unit: risk planner receives candles through DiamondStrategy path.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Diamond signal count may change significantly.
- Tighter geometry validation can remove previously profitable but overfit trades.

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

- Files changed: `quant_bitcoin/patterns/diamond.py`, `quant_bitcoin/strategies/patterns.py`, `tests/patterns/test_diamond.py`, `tests/patterns/test_diamond_risk_exit.py`, `tests/strategies/test_pattern_strategies.py`, `tests/strategies/test_single_pattern_strategies.py`, `STATUS.md`, `BACKLOG.md`, `PROJECT_HISTORY.md`, and this task file.
- Implementation summary: made Diamond minimum pivot semantics match the feasible 4-pivot expansion plus 4-pivot contraction split, enforced contraction boundary touch/deviation validation, exposed split/count/boundary/alternating metadata, added optional alternating-pivot filtering, and passed candles through `DiamondStrategy` so internal pivot stops can use visible candle data.
- Tests added or updated: Diamond detector 6/7/8/10-pivot behavior, boundary deviation acceptance/score behavior, event metadata contract, Diamond risk fixture compatibility, and strategy risk-planner candle propagation.
- Tests run: `pytest tests/patterns/test_diamond.py tests/patterns/test_diamond_risk_exit.py tests/strategies/test_pattern_strategies.py`; `pytest tests/strategies`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; no live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior was introduced.
- Known limitations: Diamond detection remains a deterministic OHLCV/pivot heuristic and stricter boundary validation can reduce historical signal counts.
- Recommended next task: Task 197 `ADAM_AND_EVE_STOP_MODE_AND_LOCAL_DOWNTREND`.
