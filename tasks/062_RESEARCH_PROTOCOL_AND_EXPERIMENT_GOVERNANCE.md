# Task 062: Research Protocol And Experiment Governance

## Purpose
Define a formal, repository-level research governance protocol that prevents data snooping, uncontrolled parameter search, overfitting, and premature promotion toward live trading.

## Scope
Documentation-only changes for governance and process:
- Add `docs/15_RESEARCH_PROTOCOL.md`.
- Define the strategy lifecycle and promotion gates for pattern research.
- Define train/validation/test/holdout protection and parameter search governance.
- Define multiple-testing controls and baseline comparison expectations.
- Reassert live-trading blocker conditions.
- Update status/history state tracking documents.

## Out Of Scope
- Strategy implementation changes.
- Backtest engine changes.
- Execution/live-trading changes.
- Exchange order endpoint integrations.
- Credential handling implementation.

## Required Deliverables
1. `docs/15_RESEARCH_PROTOCOL.md` created with required sections and lifecycle states.
2. `STATUS.md` updated to record completion and next step.
3. `PROJECT_HISTORY.md` appended with concise completion note.
4. Repository safety posture unchanged (no live trading behavior).

## Acceptance Criteria
- Protocol document clearly defines:
  - hypothesis -> event study -> net backtest -> walk-forward progression;
  - promotion vs research-only vs rejection outcomes;
  - train/validation/test/holdout protection rules;
  - pre-declared parameter search requirements;
  - repeated testing and multi-pattern governance;
  - baseline comparison policy;
  - mandatory cost/slippage/spread/fill assumptions prior to candidacy.
- Document includes lifecycle states exactly:
  - `IDEA`
  - `MECHANICAL_DEFINITION`
  - `EVENT_STUDY`
  - `GROSS_BACKTEST`
  - `NET_BACKTEST`
  - `WALK_FORWARD_VALIDATED`
  - `PAPER_ONLY_CANDIDATE`
  - `RESEARCH_ONLY`
  - `REJECTED`
- Document explicitly states strategy research is not sufficient for live trading and repeats live-trading blocker prerequisites.
- Document explicitly calls out FVG, Order Block, and Trendline Break as requiring cost, fill, and out-of-sample controls before promotion.

## Verification
- Review docs for internal consistency.
- Run `git diff --check`.
- Run `python -m compileall quant_bitcoin` as lightweight sanity check.

## Notes
This task is process governance only and must not alter trading/runtime behavior.
