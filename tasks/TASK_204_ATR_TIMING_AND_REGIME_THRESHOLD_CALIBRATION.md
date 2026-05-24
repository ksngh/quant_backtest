# Task 204: ATR_TIMING_AND_REGIME_THRESHOLD_CALIBRATION

# Goal

Calibrate ATR-based thresholds by regime and make ATR timing assumptions explicit in pattern/risk metadata.

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

- ATR normalizes gap size, displacement range, breakout distance, pattern height, stop buffers, and trailing stops.
- A single static ATR multiplier may not behave consistently across low/high volatility regimes.
- Current ATR uses the current closed candle; this is safe for after-close signals but must be recorded.

# Scope

- quant_bitcoin/indicators/atr.py
- quant_bitcoin/patterns/*.py
- quant_bitcoin/risk/exit_plan.py
- quant_bitcoin/backtesting/score_calibration.py
- tests/indicators/test_atr.py
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

- Attach ATR period, smoothing method, and current_candle_included metadata to pattern events and risk plans.
- Add calibration report for ATR multiplier sensitivity by pattern and regime.
- Support optional regime-conditioned ATR multipliers without changing defaults.
- Document how ATR warm-up invalid rows affect earliest possible pattern events.

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
- Preserve existing ATR defaults and pattern threshold defaults; regime-conditioned multipliers must be opt-in diagnostics/config only.
- `quant_bitcoin/risk/exit_plan.py` may not exist in the current tree; if absent, risk-plan metadata work will be limited to existing risk/action-builder modules already in the repository.
- Calibration diagnostics stay offline and operate on existing pattern/trade metadata without database schema or API route changes.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Pattern event metadata can explain which ATR period/smoothing was used.
- Calibration diagnostics can compare at least two ATR multiplier settings.
- Warm-up behavior is explicit in tests.

# Required Tests

## Unit Tests

- Unit: ATR metadata values reflect AtrConfig.
- Unit: first valid ATR appears at period-1 index under default.

## Integration Tests

- Integration: FVG earliest event constrained by ATR/volume warm-up.

## Contract Tests

- Diagnostics: ATR threshold sensitivity fixture returns stable schema.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Additional metadata may require persistence/API schema updates.

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

- Files changed: `quant_bitcoin/indicators/atr.py`, `quant_bitcoin/risk/exit_plan.py`, `quant_bitcoin/backtesting/pattern_action_builder.py`, `quant_bitcoin/backtesting/score_calibration.py`, pattern detector/risk-exit modules under `quant_bitcoin/patterns/`, `docs/26_INDICATOR_TIMING_CONTRACT.md`, `tests/indicators/test_atr.py`, `tests/patterns/test_fair_value_gap.py`, `tests/patterns/test_fair_value_gap_risk_exit.py`, `tests/backtesting/test_score_calibration.py`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: expanded ATR timing metadata with period, smoothing method, and first-valid index; attached ATR metadata to pattern events and risk plans; propagated ATR metadata and ATR buffer multipliers through canonical pattern action metadata; added ATR multiplier sensitivity diagnostics grouped by pattern and regime; documented ATR warm-up constraints for earliest ATR-normalized pattern events.
- Tests added or updated: ATR timing metadata contract, FVG ATR metadata/warm-up constraint, FVG risk-plan ATR metadata propagation, and ATR multiplier sensitivity diagnostics.
- Tests run: `pytest tests/indicators/test_atr.py tests/patterns/test_fair_value_gap.py tests/patterns/test_fair_value_gap_risk_exit.py tests/backtesting/test_score_calibration.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; scope stayed in offline indicator/pattern/risk/backtest diagnostics, defaults remain unchanged, no live trading/order endpoints/secrets were added, and verification passed.
- Known limitations: regime-conditioned ATR multiplier support is diagnostic/comparative metadata over runs; this task does not auto-retune live detector thresholds or change default multipliers.
- Recommended next task: Task 205 `PIVOT_STRENGTH_ATR_AND_MULTITIMEFRAME_RESEARCH`.
