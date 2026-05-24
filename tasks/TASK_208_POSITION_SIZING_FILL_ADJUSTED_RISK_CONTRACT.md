# Task 208: POSITION_SIZING_FILL_ADJUSTED_RISK_CONTRACT

# Goal

Ensure equity-risk-fraction sizing uses fill-adjusted risk_per_unit and cannot size from stale reference-entry risk.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P0**

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

- EQUITY_RISK_FRACTION sizing reads risk_per_unit from action metadata.
- Before fill alignment, risk_per_unit can be based on entry_reference rather than actual fill.
- Task 172 added fill-adjusted risk metadata in action builder, but the contract should be enforced for all pattern entries.

# Scope

- quant_bitcoin/backtesting/pattern_action_builder.py
- quant_bitcoin/backtesting/strategy_engine.py
- quant_bitcoin/backtesting/sizing.py
- tests/backtesting/test_pattern_action_builder.py
- tests/backtesting/test_strategy_engine.py

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- For pattern entries, action metadata risk_per_unit must equal fill-adjusted risk_per_unit when actual fill is known.
- Preserve original_risk_per_unit separately for diagnostics.
- Block equity-risk-fraction sizing if only stale/original risk is present for a pattern entry.
- Record sizing_risk_source metadata: FILL_ADJUSTED, ORIGINAL_REFERENCE, MISSING, or ACTION_OVERRIDE.
- Add safety checks for risk_per_unit <= 0 after fill alignment.

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
- Canonical pattern entries should expose `risk_per_unit` equal to fill-adjusted risk and preserve stale/reference risk only as `original_risk_per_unit`.
- Strategy-engine equity-risk-fraction sizing should block canonical pattern entries when fill-adjusted risk metadata is missing or mismatched by default.
- Explicit action quantity overrides continue to bypass engine risk sizing and should record `sizing_risk_source=ACTION_OVERRIDE`.
- Exact files expected: `quant_bitcoin/backtesting/pattern_action_builder.py`, `quant_bitcoin/backtesting/strategy_engine.py`, `quant_bitcoin/backtesting/sizing.py`, `tests/backtesting/test_pattern_action_builder.py`, and `tests/backtesting/test_strategy_engine.py`.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Risk sizing quantity uses fill-adjusted risk_per_unit.
- Original reference risk is visible but not used for sizing unless explicitly allowed.
- Missing risk_per_unit blocks risk sizing with clear reason.

# Required Tests

## Unit Tests

- Unit: fill higher than FVG midpoint changes risk_per_unit and quantity.
- Unit: stale risk metadata blocks in strict mode.
- Unit: action override quantity retains explicit override semantics.

## Integration Tests

- Integration: strategy_engine metadata records sizing_risk_source.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Risk-based position sizes can change materially.
- Strict blocking may reduce executed trades where metadata is incomplete.

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

- Files changed: `quant_bitcoin/backtesting/sizing.py`, `quant_bitcoin/backtesting/pattern_action_builder.py`, `quant_bitcoin/backtesting/strategy_engine.py`, `quant_bitcoin/backtesting/__init__.py`, `tests/backtesting/test_pattern_action_builder.py`, `tests/backtesting/test_strategy_engine.py`, `STATUS.md`, `BACKLOG.md`, and `PROJECT_HISTORY.md`.
- Implementation summary: added `SizingRiskSource`, made canonical pattern entries record `FILL_ADJUSTED` risk sizing metadata, preserved `original_risk_per_unit`, made explicit quantity overrides record `ACTION_OVERRIDE`, and made equity-risk-fraction sizing block stale/missing/non-positive pattern risk metadata by default.
- Tests added or updated: fill-adjusted pattern risk quantity calculation, stale reference-risk blocking, explicit quantity override behavior, missing-risk source metadata, and builder metadata assertions.
- Tests run: `pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_engine.py`; `pytest tests/backtesting`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review result: passed; changes stayed in backtesting/action metadata only, no exchange clients/order endpoints/secrets/live behavior were introduced, and verification passed.
- Known limitations: non-pattern equity-risk-fraction actions still rely on caller-provided `risk_per_unit`; the strict fill-adjusted enforcement applies to canonical pattern entries.
- Recommended next task: Task 209 `GUARDRAIL_OPEN_POSITION_KILL_SWITCH_AND_EXPOSURE_CAPS`.
