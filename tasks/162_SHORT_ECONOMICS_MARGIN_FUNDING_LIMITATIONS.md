# Goal

Make short-side backtest economics explicit by modeling or clearly accounting for borrow/funding/liquidation limitations, without enabling live futures or margin trading.

# Source Requirement

Owner-requested remediation pack after repository review.

Observed gap:

- The README and engine metadata state that borrow fees, futures funding, maintenance margin, and liquidation are not modeled.
- Short simulation supports cash-bounded and simulated-margin modes, but not real futures/margin economics.
- Short pattern results can therefore look better than live or futures-equivalent execution would allow.

Read and inspect:

- `tasks/117_SHORT_ACCOUNTING_CONSISTENCY_AND_LIMITATIONS.md`
- `tasks/135_PRODUCT_SPECIFIC_SHORT_POLICY_AND_EXECUTION_BOUNDARIES.md`
- `tasks/143_SIMULATED_MARGIN_INITIAL_MARGIN_GUARD.md`
- `quant_bitcoin/backtesting/sizing.py`
- `quant_bitcoin/backtesting/strategy_engine.py`
- `quant_bitcoin/strategies/actions.py`
- `README.md`

# Extracted Roles

- Owner role:
  - Backtest short-economics limitation owner.
- Supporting roles:
  - Engine/accounting role: records simulated short account state.
  - Documentation role: prevents live/futures overclaiming.
  - Metrics role: reports short-side performance separately.
- Forbidden roles:
  - No real futures trading.
  - No live margin account endpoints.
  - No signed exchange requests beyond already approved testnet-only clients.

# Context

Code-level hints:

- Extend metadata under `summary.metadata.limitations` and `short_exposure_policy` if behavior remains unsupported.
- If adding simulation fields, keep them offline-only:
  - funding rate per interval or per day;
  - borrow fee bps;
  - maintenance margin rate;
  - liquidation price estimate;
  - liquidation event simulation.
- Ensure `ProductMode` boundaries from previous tasks are respected.

Functional intent:

- Short results should be interpreted correctly.
- If economics are not modeled, the output must clearly say so.
- If a simple model is added, it must be explicitly simulation-only and configurable.

# Scope

- Decide whether to add a simple backtest-only short cost/liquidation model or strengthen limitation metadata.
- Add short-side attribution and warnings where needed.
- Update README/docs if short semantics change.
- Add tests for short accounting and limitation metadata.

# Out of Scope

- Real futures/margin trading.
- Live liquidation prevention.
- Exchange account balance integration.
- Portfolio-level margin offsets.

# Requirements

- Backtest output must not imply real spot short execution.
- Simulated-margin output must state unsupported economics unless modeled.
- If funding/borrow is modeled, it must reduce equity/PnL deterministically.
- If liquidation is modeled, it must be opt-in and clearly simulation-only.
- Short-side win/loss and PnL metrics must remain correct.

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

- Short strategy summaries clearly show whether funding/borrow/liquidation were modeled.
- If unsupported, warnings are present in JSON metadata and docs.
- If implemented, funding/borrow costs reduce net PnL and are tested.
- No live futures/margin behavior is introduced.

# Required Tests

## Unit Tests

- Test short limitation metadata in default cash-bounded and simulated-margin modes.
- If adding costs, test funding/borrow cost application.
- If adding liquidation simulation, test threshold trigger and metadata.

## Integration Tests

- Add canonical CLI short fixture showing warnings or modeled costs in output.

## Contract Tests

- Ensure README/API/docs align with output semantics.
- Ensure metadata remains additive and JSON-safe.

## Safety Tests

- Confirm no futures, margin, account, or live order endpoint is called.
- Confirm no API keys or `.env` files are required.

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
pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_strategy_cli_persistence.py tests/execution
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
