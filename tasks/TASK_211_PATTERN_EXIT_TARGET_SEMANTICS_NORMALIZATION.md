# Task 211: PATTERN_EXIT_TARGET_SEMANTICS_NORMALIZATION

# Goal

Normalize detector-level target_reference and risk-plan target semantics so reports do not conflate R targets, structural targets, and measured-move targets.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P1**

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

- Some detectors compute target_reference from entry_reference plus 2R, while risk planners may compute measured targets from neckline plus height or breakout plus height.
- Cup and Adam/Eve detector targets can differ from risk measured targets.
- Reports need to distinguish signal target, measured target, R target, and nearest structural target.

# Scope

- quant_bitcoin/patterns/*.py
- quant_bitcoin/patterns/*_risk_exit.py
- quant_bitcoin/risk/exit_plan.py
- quant_bitcoin/backtesting/pattern_action_builder.py
- docs/
- tests/patterns/
- tests/risk/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Introduce target_semantics_v1 metadata with fields: detector_target_reference, risk_targets, measured_targets, structural_targets, r_multiple_targets.
- Normalize target names and sources across all pattern risk plans.
- Avoid reusing target_reference as if it always means measured move.
- Ensure fill alignment preserves source metadata and renames generated R targets deterministically.
- Document target precedence in create_risk_exit_plan/combine_targets.

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
- Keep existing target fill behavior intact; this task normalizes target names/sources/metadata and preserves source through fill alignment.
- Use the existing `RiskExitTargetSource` enum as the canonical source contract and add `target_semantics_v1` metadata around it.
- Exact files expected: `quant_bitcoin/risk/exit_plan.py`, `quant_bitcoin/backtesting/pattern_action_builder.py`, selected `quant_bitcoin/patterns/*_risk_exit.py`, target-semantics docs, and focused pattern/backtesting tests.
- No live trading, real exchange order execution, signed exchange requests, credentials, or `.env` behavior are in scope.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Every exit target has source R_MULTIPLE, STRUCTURE, or MEASURED.
- Pattern event target_reference is preserved separately from risk plan targets.
- Reports can identify whether a take-profit was R-based or measured-move based.

# Required Tests

## Unit Tests

- Unit: Cup detector target and risk measured target both appear with distinct names.
- Unit: Adam/Eve stop/target metadata reflects stop mode.
- Unit: fill-aligned targets preserve source metadata.

## Integration Tests

- Integration: exit action metadata includes target_source.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Existing metadata consumers may need schema migration.

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

- Files changed: `quant_bitcoin/risk/exit_plan.py`, `quant_bitcoin/risk/__init__.py`, `quant_bitcoin/patterns/__init__.py`, selected `quant_bitcoin/patterns/*_risk_exit.py`, `quant_bitcoin/backtesting/pattern_action_builder.py`, `docs/19_PATTERN_EVENT_STUDY_SCHEMA.md`, `docs/api/API_CONTRACT.md`, and focused pattern/backtesting tests.
- Implementation summary: added `target_semantics_v1`, preserved detector `target_reference` separately from measured/structural/R targets, passed detector target references from pattern risk planners, preserved target source metadata through fill alignment, and exposed realized take-profit `target_source` on exit action metadata.
- Tests added or updated: risk target semantics unit tests, Cup/Adam/Eve/Diamond/FVG/Trendline/Order Block risk-exit metadata assertions, fill-aligned target semantics coverage, and exit action target-source integration coverage.
- Tests run: targeted 101-test risk/action suite; `pytest tests/patterns tests/risk tests/backtesting`; `pytest tests/strategies`; `git diff --check`.
- Codex self-review result: scope respected, no live trading or exchange calls, no secrets, no lookahead behavior added, docs and ledgers updated, and verification passed.
- Known limitations: this is metadata/reporting normalization only; it does not change target selection economics or UI rendering beyond available metadata.
- Recommended next task: Task 212 `RISK_EXIT_AUDIT_MFE_MAE_AND_INTRABAR_ATTRIBUTION`.
