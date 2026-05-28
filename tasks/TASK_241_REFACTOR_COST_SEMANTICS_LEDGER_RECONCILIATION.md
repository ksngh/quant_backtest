# Task 241: Refactor Cost Semantics and Reconcile Status, History, and Backlog

# Goal

Finalize the cost/price semantics task batch by refactoring duplicated accounting helpers, verifying documentation and UI/API wording, and reconciling `STATUS.md`, `PROJECT_HISTORY.md`, `BACKLOG.md`, and ledger archives after Tasks 238-240.

# Source Requirement

Owner requirement: the final task in the batch must always focus on refactoring and rechecking `status.md`, history, and backlog after the functional tasks are written or implemented.

This task follows the price/cost task batch:

- Task 238: split raw price from effective price semantics.
- Task 239: add cost-aware net R/R entry filtering.
- Task 240: persist per-execution fee, spread, slippage, and total cost breakdown.

# Extracted Roles

- Owner role:
  - Refactor and project-ledger reconciliation owner.
- Supporting roles:
  - Backtest accounting role: removes duplicated or stale price/cost semantics.
  - API/frontend documentation role: verifies exposed contract wording.
  - Test role: runs regression suites after refactor.
  - Backlog/status maintenance role: updates ledger state and next task.
  - Archive maintenance role: checks fixed task-range archive rules.
- Forbidden roles:
  - No new trading feature work.
  - No profitability retuning.
  - No live trading.
  - No exchange order execution.
  - No signed account/order endpoints.
  - No API key or `.env` changes.

# Context

After price semantics, cost-aware admission, and per-execution cost persistence changes, the repo can easily accumulate duplicate helpers, stale docs, old frontend labels, and inconsistent ledger entries. This task exists to make the final state coherent rather than adding another feature.

The desired final state is:

```text
price/raw_price/effective_price semantics are consistent everywhere
fee/spread/slippage are explicit cost components
net R/R filtering is documented as cost-aware and no-look-ahead
STATUS.md, PROJECT_HISTORY.md, and BACKLOG.md agree on completed work, remaining blockers, and next step
```

# Scope

- Review implementation from Tasks 238-240 and remove duplicated or stale helper functions where safe.
- Consolidate price/cost naming so the same terms are used consistently in:
  - strategy engine,
  - cost model,
  - action builder metadata,
  - persistence adapter,
  - API DTOs,
  - frontend types,
  - frontend labels,
  - docs.
- Verify docs explain:
  - `price` / `raw_price`,
  - `effective_price`,
  - `cost_breakdown`,
  - `raw_gross_pnl`,
  - `net_pnl`,
  - cost-aware net R/R skip diagnostics.
- Update `STATUS.md` with the current phase, active task, completed task state, blockers, safety boundary, and recommended next step.
- Append concise completion notes to `PROJECT_HISTORY.md` for Tasks 238-241 when completed.
- Update `BACKLOG.md` to mark Tasks 238-241 created/completed/blocked and to list any follow-up explicitly.
- Check ledger archive rules for the current task range and update `docs/ledger_archives/` only if the repo's fixed archive policy requires it.
- Run the relevant backend, persistence/API, frontend, and full regression checks after refactor.

# Out of Scope

- Do not add new cost models.
- Do not add maker/taker differentiation.
- Do not add additional entry filters.
- Do not modify strategy thresholds beyond documenting the values implemented by Task 239.
- Do not rewrite historical backtest rows.
- Do not introduce live trading, exchange order placement, signed endpoints, account endpoints, API keys, or `.env` changes.

# Requirements

- Refactoring must preserve the behavior introduced by Tasks 238-240.
- Public contracts must use one consistent vocabulary:
  - raw fill price,
  - effective diagnostic price,
  - explicit cost breakdown,
  - raw gross PnL,
  - net PnL,
  - cost-infeasible net R/R skip.
- Docs and frontend labels must not imply that `effective_price` is the raw market fill.
- `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` must agree with each other after the batch.
- Ledger archive pointers must remain valid and no historical task entries may be deleted without archive preservation.
- Live-trading safety boundaries must remain explicit and unchanged unless a separate owner-approved task changes them.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [ ] Read Tasks 238, 239, and 240 before refactoring.
- [ ] Read this assigned task file before coding.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [ ] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:

- This task should run after the functional tasks or after a partial batch where the completion state is explicitly recorded.
- If any functional task is not completed, this task should document that state rather than pretending the batch is complete.
- Archive updates should follow the repo's existing fixed-range ledger policy.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [ ] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Price/cost naming is consistent across backend, persistence, API, frontend, and docs.
- Duplicated or stale accounting helpers introduced during Tasks 238-240 are removed or explicitly justified.
- Docs/API/frontend labels distinguish raw fill price from effective diagnostic price.
- `cost_breakdown` is documented and displayed as explicit per-execution cost, not hidden inside price.
- Cost-aware net R/R skip diagnostics are documented and do not imply future-data optimization.
- `STATUS.md`, `PROJECT_HISTORY.md`, and `BACKLOG.md` are internally consistent after the batch.
- Archive files are updated only if required by the repo's ledger policy.
- Full regression or documented substitute verification is run.
- No live trading behavior is added.

# Required Tests

## Unit Tests

- Run unit tests added or updated by Tasks 238-240.
- Add or update helper-level tests only if refactoring moves accounting logic.
- Verify raw/effective price and cost-breakdown reconciliation tests still pass after refactor.

## Integration Tests

- Run deterministic backtest integration tests covering:
  - raw/effective price serialization,
  - cost-aware skip diagnostics,
  - persisted cost breakdown readback.
- Run frontend build/type checks if labels or types changed.
- Run API/persistence tests if DTOs or read models changed.

## Contract Tests

- Verify API contract docs match actual serialized trade rows and skip diagnostics.
- Verify frontend `BacktestTrade` type matches API DTOs.
- Verify ledger entries and archive pointers are consistent.

## Safety Tests

- Confirm docs do not claim live-trading readiness.
- Confirm no `.env`, secret, API key, signed request, order endpoint, or account endpoint behavior is added.
- Confirm live execution blockers remain in `STATUS.md` unless separately resolved by an explicit approved task.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- Backtest behavior changes are deterministic and covered by tests.
- No look-ahead behavior is introduced.
- Documentation/API notes are updated when behavior or metadata changes.
- Ledger state is consistent across status, history, backlog, and archives.

# Verification

Default:

```bash
pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_costs.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py
pytest tests/persistence tests/api || true
npm --prefix frontend run build
pytest
git diff --check
```

If any path is unavailable, run the nearest existing backtesting, persistence, API, and frontend checks and record the substitution in the completion summary.

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
