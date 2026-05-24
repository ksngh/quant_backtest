# Goal

Add named transaction-cost profiles and optional cost-sensitivity reporting so weak backtest performance can be separated from fee/slippage drag.

# Source Requirement

Latest repo findings:
- Transaction cost model supports maker/taker fee, spread, slippage, minimum slippage, and volatility-adjusted slippage.
- CLI defaults remain zero-cost, with warning metadata.
- Poor performance can be caused by excessive turnover or cost drag, while good zero-cost results can disappear after realistic costs.

# Extracted Roles

- Owner role:
  - Backtest cost realism owner.
- Supporting roles:
  - CLI role: maps profile names to config.
  - Metrics role: computes cost sensitivity.
  - Frontend role: displays cost assumptions.
- Forbidden roles:
  - No live fee lookup.
  - No exchange account endpoint.
  - No strategy retuning.

# Context

Users should not need to manually remember bps assumptions. A zero-cost backtest is useful for baseline debugging but misleading for 1m strategies. The frontend should clearly identify whether the run used zero cost, conservative costs, or a named exchange-style profile.

# Scope

- Add cost profile support:
  - `zero`,
  - `binance_spot_taker_baseline`,
  - `conservative_crypto_1m`,
  - `high_slippage_stress`.
- CLI must reject combining a profile with conflicting manual bps unless an explicit override flag is used.
- Add optional sensitivity report:
  - rerun or recompute approximate results under multiple cost scenarios if feasible,
  - at minimum, calculate cost-to-gross-PnL and break-even cost bps.
- Persist `cost_profile`.
- Frontend must show:
  - selected cost profile,
  - fee/spread/slippage assumptions,
  - total cost,
  - cost-to-gross-PnL ratio,
  - zero-cost warning.

# Out of Scope

- No real exchange fee API.
- No live order execution.
- No hidden default change without docs.

# Requirements

- User can run CLI with a named cost profile.
- Output metadata records profile and bps values.
- Zero-cost profile is clearly marked.
- Frontend cost panel explains whether costs likely explain poor performance.
- Tests verify profile mapping and conflict behavior.

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
- Cost profiles are fixed offline presets; no external fee lookup is allowed.
- Existing manual bps arguments remain valid when no profile is explicitly selected.
- Profile/manual conflicts fail unless `--allow-cost-profile-overrides` is explicitly set.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added static offline cost profiles and deterministic manual override validation.
- Existing manual bps arguments still work when no profile is selected.
- Strategy output records profile assumptions and approximate cost sensitivity.
- Frontend performance diagnostics show the selected cost profile and retain zero-cost warning behavior.
- Next task: Task 181 `PATTERN_SCORE_CALIBRATION_ABLATION_AND_THRESHOLDS`.

# Acceptance Criteria

- Cost profile CLI tests pass.
- Manual bps override behavior is deterministic.
- Dashboard displays profile and warning.
- Existing manual bps arguments still work.

# Required Tests

## Unit Tests

- Cost profile mapping.
- Conflict validation.
- Cost drag classification.

## Integration Tests

- CLI run with each profile.
- Frontend build.

## Contract Tests

- README/API docs for `cost_profile`.

## Safety Tests

- No external fee lookup or order endpoints.

# Verification

Default:

```bash
pytest tests/backtesting/test_costs.py tests/backtesting/test_pattern_postgres_runner_cli.py
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
