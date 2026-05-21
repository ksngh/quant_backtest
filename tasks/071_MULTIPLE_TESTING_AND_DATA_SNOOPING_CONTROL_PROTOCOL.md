# Task 071: MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL

## Goal
Define and adopt a repository-level multiple-testing and data-snooping control protocol for pattern strategy research so promotion decisions are based on conservative, auditable evidence rather than repeated retuning.

## Scope
Documentation-first governance task:
- Create `docs/21_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md`.
- Define required concepts, reporting schema, rejection rules, and promotion rules for research families spanning multiple pattern detectors and filter/confluence variants.
- Apply explicitly to FVG, Order Block, Trendline Break, Cup and Handle, Diamond, Adam and Eve, RSI filters, and confluence studies.
- Update status tracking documents for completed task state.

Optional lightweight utility helpers are allowed but not required.

## Out Of Scope
- Bootstrap reality-check implementation.
- Deflated Sharpe implementation.
- New ML workflows.
- Live trading or real exchange order execution.
- Pattern detector logic changes.
- Backtest execution engine changes.

## Required Deliverables
1. `docs/21_MULTIPLE_TESTING_AND_DATA_SNOOPING_CONTROL_PROTOCOL.md` created.
2. `STATUS.md` updated with completion summary and next recommended task.
3. `PROJECT_HISTORY.md` appended with concise completion note.

## Acceptance Criteria
- Protocol document exists and explains why multiple testing and snooping controls are required.
- Requires pre-declared search spaces before sweeps.
- Requires locked holdout usage and anti-reinspection controls.
- Requires reporting family-wise tested variant counts.
- States strategy promotion cannot be based only on best in-sample run.
- Defines: experiment family, strategy variant, parameter search space, primary/secondary metrics, baselines, validation/holdout periods, tested variant count, minimum report fields, rejection rules, promotion rules.
- Explicitly applies to FVG, Order Block, Trendline Break, Cup and Handle, Diamond, Adam and Eve, RSI filters, and confluence studies.

## Verification
- Manual consistency review against `docs/15_RESEARCH_PROTOCOL.md` and `docs/20_FAIR_VALUE_GAP_STRATEGY_V1_SPECIFICATION.md`.
- `git diff --check`
- Run `pytest` only if code is added.

## Notes
This task introduces governance documentation only and preserves the current safety boundary (no live trading, no exchange order endpoints).
