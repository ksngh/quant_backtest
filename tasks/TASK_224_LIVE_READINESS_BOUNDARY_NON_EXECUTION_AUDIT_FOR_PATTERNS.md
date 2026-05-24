# Task 224: LIVE_READINESS_BOUNDARY_NON_EXECUTION_AUDIT_FOR_PATTERNS

# Goal

Re-audit pattern strategy live-readiness boundaries and explicitly keep live trading blocked while identifying remaining paper/live prerequisites.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P3**

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

- STATUS.md indicates live trading remains blocked.
- Pattern strategy improvements can increase temptation to use results for live trading.
- This project has strict safety boundaries: no live order execution without explicit future task and owner approval.

# Scope

- docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md
- STATUS.md
- BACKLOG.md
- quant_bitcoin/strategies/
- quant_bitcoin/backtesting/
- tests/safety/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Audit pattern strategy code paths for accidental exchange/order/client calls.
- Confirm strategy/backtest modules remain pure and offline.
- List remaining live prerequisites: kill switch, max notional, symbol filters, stale data, duplicate order idempotency, restart reconciliation, cancel/replace, partial fills, monitoring/alerting, secret policy.
- Update execution readiness audit doc if behavior or prerequisites changed.
- Add safety tests if new execution-adjacent code was introduced.

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

Assumptions:
- This task is an audit and safety-test hardening task; it must not enable live trading, add a live client, add credentials, or mutate pattern strategy behavior.
- Pattern research outputs remain offline backtest/paper-readiness artifacts only.
- Touched files are expected to be limited to `docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md`, `tests/safety/test_pattern_live_boundary.py`, this task file, and root status/backlog/history ledgers.
- The audit uses static source inspection plus targeted safety tests for strategy/backtesting boundaries.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- No live trading behavior is introduced.
- Audit doc explicitly states pattern research remains backtest/paper-only.
- STATUS/BACKLOG blockers remain accurate or are updated in the final reconciliation task.

# Required Tests

## Unit Tests

- Add unit tests appropriate to every changed pure function or data contract.

## Integration Tests

- Add integration tests for any changed strategy/backtest/risk flow.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.
- Safety grep/test: strategy and backtesting modules do not import exchange order clients.
- Safety test: no signed order endpoint path is called by pattern code.

# Side Effects / Risks

- May reveal new blocked work but should not implement live execution.

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

# Completion Notes

Files changed:
- `docs/25_EXECUTION_READINESS_SAFETY_AUDIT.md`
- `tests/safety/test_pattern_live_boundary.py`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `tasks/TASK_224_LIVE_READINESS_BOUNDARY_NON_EXECUTION_AUDIT_FOR_PATTERNS.md`

Implementation summary:
- Re-audited `quant_bitcoin/strategies/` and `quant_bitcoin/backtesting/` for execution-client imports, signed-order endpoint strings, credential keys, and signed-request helper usage.
- Updated the execution readiness audit to state that pattern research remains backtest/paper-only and must not submit orders, sign requests, read API secrets, or call exchange order/account endpoints.
- Added static safety tests that enforce the strategy/backtesting boundary against future execution-client coupling.

Tests added or updated:
- Added `tests/safety/test_pattern_live_boundary.py`.

Tests run:
- `pytest tests/safety/test_pattern_live_boundary.py`
- `pytest tests/execution/test_binance_spot_testnet.py tests/execution/test_order_intent.py tests/execution/test_product_policy.py`
- `pytest tests/patterns tests/risk tests/backtesting tests/strategies`
- `git diff --check`

Codex self-review result:
- Scope stayed limited to audit documentation, safety tests, task tracking, and ledgers.
- No live trading, real order execution, signed live request, exchange order/account endpoint, API key handling, `.env` change, or strategy/backtest behavior change was introduced.
- The added tests are static boundary tests and do not perform network calls.

Known limitations:
- This is a static non-execution audit; it does not implement live prerequisites.
- Task 138 remains blocked pending owner approval and the documented live-readiness controls.
- Backend FastAPI route tests remain environment-blocked by missing `fastapi`.

Recommended next task:
- Task 225 `REFACTOR_DOCUMENTATION_LEDGER_RECONCILIATION_AFTER_PATTERN_RESEARCH_BATCH`.
