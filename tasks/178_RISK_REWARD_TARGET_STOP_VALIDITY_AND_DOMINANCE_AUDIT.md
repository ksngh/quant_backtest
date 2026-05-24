# Goal

Audit whether each strategy’s stop, target, partial exit, soft invalidation, and time stop rules are economically coherent and whether one exit type dominates poor performance.

# Source Requirement

Owner request: analyze risk management and buy/sell timing; performance is poor and may be caused by risk/exit policy rather than alpha alone.

Latest repo findings:
- `RiskExitPlan` supports structural stops, ATR buffer, R-multiple targets, partial exits, break-even, trailing stop, and time stop.
- `simulate_pattern_exit()` supports hard stop, take profit, soft invalidation, and time stop.
- The frontend currently shows generic risk rules but not actual realized exit-reason distribution or rule dominance.

# Extracted Roles

- Owner role:
  - Risk/exit policy audit owner.
- Supporting roles:
  - Backtesting metrics role: aggregates exit reasons.
  - Frontend role: explains risk policy and realized exits.
- Forbidden roles:
  - No live risk engine.
  - No exchange order controls.
  - No hidden retuning.

# Context

A strategy can have valid entries but bad exits:
- targets may be too far after fill alignment;
- stop distance may be too wide or too tight;
- partial exits may cap winners;
- soft invalidation may close trades at systematically bad prices;
- time stop may dominate before targets are reachable;
- break-even/trailing assumptions may distort results.

# Scope

- Add risk/exit audit metrics:
  - exit reason distribution,
  - average PnL/R by exit reason,
  - stop-loss dominance ratio,
  - time-stop dominance ratio,
  - soft-invalidation dominance ratio,
  - take-profit average R,
  - hard-stop average R,
  - partial-exit contribution to PnL,
  - first target hit rate,
  - final target hit rate,
  - average target distance in R and price.
- Add validation checks:
  - LONG target above fill,
  - SHORT target below fill,
  - stop direction valid,
  - risk_per_unit positive,
  - first target R above minimum.
- Show in frontend Risk Management panel:
  - configured risk logic,
  - realized risk behavior,
  - which exit rule hurt/helped the most.
- Add warning when `HARD_STOP` or `SOFT_INVALIDATION` dominates and expectancy is negative.

# Out of Scope

- Do not change risk defaults.
- Do not optimize targets.
- No live trading or order controls.

# Requirements

- Risk diagnostics must be calculated per completed run.
- Exit reason distribution must match trade/execution data.
- Invalid target/stop direction must be critical.
- Frontend must distinguish configured risk design from realized risk outcomes.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [x] Read `AGENTS.md`.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:
- Risk audit diagnostics are explanatory only and must not alter stops, targets, sizing, entries, exits, or fill behavior.
- Legacy persisted rows may lack target/stop metadata, so diagnostics must produce partial warnings rather than fail.
- Dominance warnings are based on completed closing executions available in saved metadata.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added `risk_exit_audit_v1` for exit distribution, dominance ratios, target quality, partial-exit contribution, and risk validation.
- Strategy-engine runs store the audit; backend details compute fallback audits for legacy rows.
- Frontend now shows a read-only Risk Management panel with configured design and realized outcomes.
- No risk defaults, live execution behavior, or order controls were changed.
- Next task: Task 179 `CANONICAL_REGIME_GUARDRAIL_AND_CONTINUITY_CLI_WIRING`.

# Acceptance Criteria

- Dashboard shows both “Risk design” and “Realized risk outcomes”.
- Synthetic fixtures detect stop dominance and soft-invalidation dominance.
- No existing runs without metadata crash.
- Tests cover long and short direction validity.

# Required Tests

## Unit Tests

- Exit reason aggregation.
- Target/stop direction validation.
- Partial-exit contribution calculation.

## Integration Tests

- Backend diagnostics include risk audit.
- Frontend build after Risk panel changes.

## Contract Tests

- Document risk audit schema.

## Safety Tests

- No live execution logic introduced.

# Verification

Default:

```bash
pytest tests/backtesting/test_performance_metrics.py tests/backtesting/test_pattern_action_builder.py backend/tests/test_backtest_results_service_runtime.py
npm --prefix frontend run build
pytest
git diff --check
```

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are covered by deterministic regression tests.
- Frontend/API changes remain read-only and do not run backtests or place orders.

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
