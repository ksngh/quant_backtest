# Goal

Add explicit risk-per-trade sizing and backtest-only portfolio guardrails so position size can be derived from stop distance rather than only quantity, cash fraction, or target notional.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed gap:

- Current sizing supports fixed quantity, cash fraction, and target notional.
- Pattern risk plans calculate `risk_per_unit`, but there is no clearly implemented sizing mode like `equity_risk_fraction` that sizes quantity as `equity * risk_fraction / risk_per_unit`.
- There is no canonical daily loss limit, consecutive loss limit, or account drawdown stop in backtest engine.

Read and inspect:

- `tasks/140_POSITION_SIZING_POLICY_CONTRACT.md`
- `quant_bitcoin/backtesting/sizing.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/risk/exit_plan.py`
- `quant_bitcoin/backtesting/strategy_postgres_runner_core.py`
- `quant_bitcoin/strategies/patterns.py`

# Extracted Roles

- Owner role:
  - Backtest risk-sizing and guardrail owner.
- Supporting roles:
  - Risk-plan role: supplies stop distance / risk per unit.
  - Engine role: applies account-level guardrails during simulation.
  - CLI role: exposes explicit backtest-only controls.
- Forbidden roles:
  - No live risk engine.
  - No real exchange margin/order behavior.
  - No portfolio optimization.

# Context

Code-level hints:

- Extend `PositionSizingMode` with a mode such as `EQUITY_RISK_FRACTION` or `RISK_FRACTION`.
- To size from risk, the engine needs access to `risk_per_unit` from action metadata. Pattern action metadata already includes risk plan fields in some paths.
- Guardrails can be implemented as backtest-only state checks before entries:
  - max account drawdown;
  - max consecutive losses;
  - max daily loss;
  - max open notional;
  - max trades per day.
- Keep guardrail-triggered actions as blocked/skipped executions with reasons for audit.

Functional intent:

- Position size should be economically tied to loss-at-stop.
- Risk guardrails should be visible and deterministic in historical simulation.

# Scope

- Add risk-fraction sizing mode using `risk_per_unit` when available.
- Add backtest-only guardrail config models.
- Apply guardrails to entry actions without changing detector logic.
- Add metadata and blocked-action reasons for guardrail decisions.
- Add CLI wiring if task scope remains manageable.

# Out of Scope

- Real-time risk daemon.
- Broker/exchange kill switch.
- Multi-symbol portfolio optimization.
- Live liquidation prevention.

# Requirements

- Risk-fraction sizing must require a valid positive `risk_per_unit`.
- Missing risk information must block or fall back only by explicit policy.
- Guardrails must be deterministic and auditable.
- Existing sizing modes must remain backward-compatible.
- Guardrail decisions must not be counted as filled trades.
- Metadata must distinguish strategy skip, affordability block, and risk-guard block.

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

- With equity `10000`, risk fraction `0.01`, and risk per unit `100`, entry quantity resolves to `1.0`.
- If risk per unit is missing, the engine blocks the entry or applies an explicitly configured fallback.
- Max drawdown guard blocks new entries after threshold breach.
- Consecutive loss guard blocks new entries after threshold breach.
- Guardrail events appear in execution metadata and summary counts.

# Required Tests

## Unit Tests

- Test risk-fraction sizing calculation.
- Test missing/zero/negative risk per unit behavior.
- Test max drawdown, max daily loss, and consecutive-loss guardrails.

## Integration Tests

- Add canonical pattern backtest fixture using risk-fraction sizing.
- Verify blocked guardrail actions do not affect position/account state.

## Contract Tests

- Ensure new config models serialize to metadata safely.
- Ensure CLI argument validation is strict if CLI wiring is added.

## Safety Tests

- Confirm guardrails are simulation-only unless a future task explicitly wires live behavior.
- Confirm no exchange account/order endpoints are called.

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
pytest tests/backtesting/test_sizing.py tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_cli_persistence.py
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
