# Goal

Create a strict execution-readiness audit that documents what is still missing before any real trading, while preserving the current no-live-trading safety boundary.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed gap:

- The repository has paper/testnet-oriented execution components and explicit live-trading blockers.
- The review concluded the current project is not ready for live trading.
- Before any future execution work, the repo needs a concrete readiness checklist and safety boundary audit.

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `tasks/133_ORDER_INTENT_AND_PAPER_EXECUTION_CONTRACT.md`
- `tasks/134_REALTIME_CANDLE_CLOSE_STRATEGY_TRIGGER_AND_PAPER_EXECUTION.md`
- `tasks/136_BINANCE_SPOT_TESTNET_EXECUTION_CLIENT_SAFETY_AND_POLICY.md`
- `tasks/137_EXECUTION_FILL_RECONCILIATION_AND_ACTUAL_COST_METRICS.md`
- `tasks/138_GUARDED_BINANCE_SPOT_LIVE_EXECUTION_WITH_OWNER_APPROVAL.md`
- `quant_bitcoin/execution/`
- README safety sections

# Extracted Roles

- Owner role:
  - Execution safety and readiness audit owner.
- Supporting roles:
  - Paper execution role: documents simulated behavior.
  - Testnet client role: documents guarded signed request boundaries.
  - Documentation/status role: keeps blockers visible.
- Forbidden roles:
  - Do not implement live trading.
  - Do not enable Task 138.
  - Do not add credentials or live endpoint defaults.
  - Do not create order/account endpoints in backend.

# Context

Code-level hints:

- This is primarily a documentation/audit task unless small safety-test additions are needed.
- Confirm execution modules fail closed where expected.
- Confirm README and STATUS still say live trading is blocked.
- Produce a checklist covering:
  - order book/fill model;
  - partial fill;
  - cancel/replace;
  - rate limit;
  - stale data;
  - reconnect/reconciliation;
  - kill switch;
  - secrets;
  - min notional/lot size/tick size;
  - funding/margin/liquidation;
  - monitoring/alerting.

Functional intent:

- The project owner should know exactly why the system is not production-ready and what future tasks are required before live execution.

# Scope

- Audit execution-related modules and docs for safety boundary consistency.
- Add a production/execution readiness document or update existing docs.
- Add follow-up backlog candidates for missing readiness items.
- Add safety tests only if a gap is found and can be addressed without enabling live trading.

# Out of Scope

- Implementing live trading.
- Implementing Task 138.
- Adding exchange credentials.
- Adding backend order endpoints.
- Adding UI order controls.

# Requirements

- State clearly that live trading remains blocked.
- List missing capabilities before real execution.
- Confirm testnet-only boundaries remain explicit.
- Confirm no default enables live trading.
- Record blockers in `STATUS.md` and `BACKLOG.md` if needed.

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

- A readiness audit document exists or relevant docs are updated.
- STATUS/BACKLOG continue to record live trading as blocked unless explicitly approved by owner.
- Safety tests pass or identified safety gaps are recorded as blocked follow-ups.
- No live trading capability is enabled.

# Required Tests

## Unit Tests

- Add or update safety tests for fail-closed execution config if gaps are found.

## Integration Tests

- Run existing execution tests for paper/testnet safety boundaries.

## Contract Tests

- Verify README/STATUS/backlog docs align with execution boundary.
- Verify no backend/frontend API contract adds live order controls.

## Safety Tests

- Confirm no API keys are required.
- Confirm no `.env` files are committed.
- Confirm no live order/account endpoint is called.
- Confirm `ENABLE_LIVE_TRADING=true` or equivalent default is not introduced.

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
pytest tests/execution tests/risk
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
