# Task 205: PIVOT_STRENGTH_ATR_AND_MULTITIMEFRAME_RESEARCH

# Goal

Reduce noisy 1m pivot overfitting by adding ATR-strength pivot filters and optional higher-timeframe pivot context.

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

- PivotConfig has use_atr_filter and minimum_pivot_strength_atr, but default is disabled.
- Trendline, Cup, Diamond, and Adam/Eve depend heavily on confirmed pivots.
- 1m data can produce many noisy pivots and excessive candidate combinations.

# Scope

- quant_bitcoin/indicators/pivots.py
- quant_bitcoin/patterns/trendline_break.py
- quant_bitcoin/patterns/cup_and_handle.py
- quant_bitcoin/patterns/diamond.py
- quant_bitcoin/patterns/adam_and_eve.py
- tests/indicators/test_pivots.py
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

- Add documented pattern configs for ATR-strength pivot filtering.
- Expose pivot strength and confirmation delay in pattern event metadata.
- Add optional higher-timeframe pivot context as metadata-only if resampling support exists or can be added safely.
- Do not introduce future leakage when using higher timeframe context.
- Add pivot density diagnostics per pattern run.

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
- Keep pivot ATR filtering disabled by default; expose and test it as an opt-in research filter.
- Higher-timeframe context will remain metadata-only unless a safe existing resampling helper is found in scope.
- Pattern changes are limited to pivot-dependent detectors and metadata/diagnostics; no execution or live behavior changes.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- ATR pivot filter changes candidate counts in deterministic fixtures.
- Pattern events include pivot window/confirmation metadata.
- No pattern uses unconfirmed pivots by default.

# Required Tests

## Unit Tests

- Unit: weak pivot rejected when use_atr_filter=True.
- Unit: strong pivot accepted.

## Integration Tests

- Integration: Trendline candidate count decreases with ATR pivot filter.

## Contract Tests

- No-lookahead: confirmed_index remains <= current_index.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Signal counts can decrease.
- Resampling/higher-timeframe context may expand data contract scope.

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

- Files changed: `quant_bitcoin/indicators/pivots.py`, `quant_bitcoin/indicators/__init__.py`, `quant_bitcoin/patterns/trendline_break.py`, `quant_bitcoin/patterns/cup_and_handle.py`, `quant_bitcoin/patterns/diamond.py`, `quant_bitcoin/patterns/adam_and_eve.py`, `tests/indicators/test_pivots.py`, `tests/patterns/test_trendline_break.py`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: added `pivot_strength_diagnostics_v1`, included ATR-filter settings in pivot timing metadata, passed ATR into pivot detection for pivot-dependent pattern detectors, attached pivot strength/window/confirmation/density metadata to Trendline/Cup/Diamond/Adam-Eve events, and kept higher-timeframe context metadata-only/unconfigured without resampling or future leakage.
- Tests added or updated: strong ATR-filtered pivot acceptance and density diagnostics, trendline event pivot metadata/no-lookahead assertions, and trendline candidate reduction under opt-in ATR-strength pivot filtering.
- Tests run: `pytest tests/indicators/test_pivots.py tests/patterns/test_trendline_break.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; scope stayed within offline pivot/pattern metadata, no defaults were changed, no live trading/order endpoints/secrets were added, and verification passed.
- Known limitations: higher-timeframe pivot context remains explicitly metadata-only and disabled; no resampling/data-contract expansion was introduced in this task.
- Recommended next task: Task 206 `TRANSACTION_COST_DEFAULT_PRESETS_AND_FAILSAFE_WARNINGS`.
