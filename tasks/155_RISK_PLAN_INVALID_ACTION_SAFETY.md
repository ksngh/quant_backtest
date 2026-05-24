# Goal

Harden risk-plan validation so invalid pattern risk plans cannot create executable entry actions in any caller path.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed issue:

- The canonical runner checks invalid risk plans before expanding actions.
- `build_pattern_trade_actions()` still has an internal branch that can leave an entry action in place when `risk_plan.status != VALID`.
- The builder is a reusable function and should be safe even when called outside the canonical runner.

Read and inspect:

- `quant_bitcoin/backtesting/pattern_action_builder.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/risk/exit_plan.py`
- `quant_bitcoin/strategies/patterns.py`
- tests covering `RISK_PLAN_INVALID`

# Extracted Roles

- Owner role:
  - Backtest safety contract owner.
- Supporting roles:
  - Risk-plan role: defines validity statuses.
  - Pattern action-builder role: converts only valid plans into executable entries.
- Forbidden roles:
  - No detector tuning.
  - No live trading behavior.
  - No dashboard behavior.

# Context

Code-level hints:

- In `pattern_action_builder.py`, inspect the section after entry action creation where invalid risk plans replace `actions[0]` with an entry action and reason `RISK_PLAN_INVALID`.
- That branch should likely return a `StrategyActionType.SKIP`, not an executable `ENTER_LONG` or `ENTER_SHORT`.
- Keep `_risk_plan_invalid_skip()` in `strategy_postgres_runner_core.py`, but do not rely on it as the only protection.

Functional intent:

- Invalid risk plan means no executable entry.
- The reason and risk-plan status should remain visible in metadata for diagnostics.
- The action-builder should be safe as a public reusable primitive.

# Scope

- Change builder behavior for invalid, skipped, or malformed risk plans.
- Preserve diagnostic metadata.
- Add direct builder tests independent of the CLI path.
- Ensure canonical CLI warnings still report invalid risk plans.

# Out of Scope

- Changing risk-plan creation logic.
- Making weak pattern statuses executable by default.
- Changing stop/target formulas.

# Requirements

- `RiskExitPlanStatus.VALID` is the only status that can produce executable entry/exit lifecycle actions.
- `INVALID` or `SKIPPED` risk plans must produce a `SKIP` action with reason `RISK_PLAN_INVALID` or a more specific reason.
- Metadata must include risk plan status and reasons when available.
- The canonical CLI should still warn on invalid risk plan events.
- No existing valid risk plan flow should regress.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md` only as needed for recent task context.
- [x] Read this assigned task file before coding.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Direct calls to `build_pattern_trade_actions()` with invalid risk plans return only `SKIP` actions.
- No `ENTER_LONG` or `ENTER_SHORT` action is emitted for invalid risk plans.
- Canonical runner invalid-risk warnings remain accurate.
- Existing valid plan tests still pass.

# Required Tests

## Unit Tests

- Test invalid risk plan returns `SKIP`.
- Test skipped risk plan returns `SKIP`.
- Test metadata includes risk-plan reasons.
- Test valid risk plan remains executable.

## Integration Tests

- Test canonical CLI/action path with a synthetic invalid risk plan and confirm zero fills.

## Contract Tests

- Confirm `StrategyActionType.SKIP` remains the standard non-executable diagnostic action.

## Safety Tests

- Confirm no real order behavior can be triggered by invalid plans.
- Confirm no exchange endpoints are introduced.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.

# Verification

Default:

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_strategy_cli_persistence.py
pytest
git diff --check
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
