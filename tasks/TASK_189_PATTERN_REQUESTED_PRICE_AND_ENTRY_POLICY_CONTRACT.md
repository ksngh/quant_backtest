# Task 189: PATTERN_REQUESTED_PRICE_AND_ENTRY_POLICY_CONTRACT

# Goal

Make pattern entry price policy explicit and prevent metadata-only entry_reference from being mistaken for execution price.

# Source Requirement

Owner requested a comprehensive follow-up task batch after the pattern/indicator/risk review of `quant_backtest` master. This task is part of the remediation plan for pattern execution correctness, indicator timing clarity, risk-management realism, score calibration, reporting, and final documentation/ledger reconciliation.

Priority: **P0**

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

- Pattern detector events contain entry_reference, but StrategyAction execution uses requested_price or candle close.
- FVG and Order Block detector/risk plans commonly use zone midpoint references, while market-on-confirmation-close fills can happen elsewhere.
- Task 172 improved risk-plan alignment after actual fill, but entry policy still needs an explicit contract across pattern paths.

# Scope

- quant_bitcoin/strategies/patterns.py
- quant_bitcoin/backtesting/pattern_action_builder.py
- quant_bitcoin/patterns/entry_simulation.py
- quant_bitcoin/backtesting/strategy_engine.py
- docs/api/API_CONTRACT.md
- tests/backtesting/
- tests/patterns/

# Out of Scope

- Real Binance order execution.
- Live trading enablement.
- API keys, credentials, or `.env` changes.
- Portfolio optimization or machine learning model training unless explicitly listed in Requirements.
- Broad UI redesign beyond the listed frontend/read-only display requirements.
- Database schema changes unless explicitly required by this task.
- Silent behavior changes outside the named files and contracts.

# Requirements

- Define an explicit pattern_entry_policy_v1 metadata schema.
- For each action, record entry_mode, fill_assumption, fill_price_source, entry_reference, requested_price, confirmation_close, and bars_waited where applicable.
- For market modes, requested_price must be actual simulated fill price.
- For limit/reference modes, requested_price must be limit/reference fill price only after a candle touch has been simulated.
- Disallow executable pattern entry actions when entry mode is invalid for the event shape.
- Document which modes are supported per pattern and why.

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

Assumptions before implementation:
- This task is limited to offline pattern entry metadata, requested-price contracts, docs, and deterministic tests.
- Existing default market-on-confirmation behavior is preserved.
- Cost/sizing paths already consume `StrategyAction.requested_price`; this task hardens metadata and tests that contract.
- No live trading, exchange order/account endpoint, signed request, API key, or `.env` behavior is introduced.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Append concise completion note to `PROJECT_HISTORY.md` if this task is completed.
- [x] Update `BACKLOG.md` if this task creates, completes, blocks, splits, or reprioritizes follow-up work.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added `pattern_entry_policy_v1` metadata to pattern entry actions, including entry mode, fill assumption/source, entry reference, requested price, confirmation close, bars waited, status, wait config, invalid reason, and supported modes.
- Confirmed market modes use simulated market fill price and limit/reference modes set requested price only after candle-touch simulation.
- Invalid entry-mode/event-shape combinations now return non-executable `SKIP` actions with reason `ENTRY_MODE_INVALID`.
- Documented the schema in `docs/api/API_CONTRACT.md`.
- Tests added/updated: builder policy tests, next-open/no-fill tests, invalid boundary-mode test, and strategy-engine requested-price replay assertion.
- Tests run: `pytest tests/backtesting/test_pattern_action_builder.py tests/patterns/test_entry_simulation.py tests/backtesting/test_strategy_engine.py tests/backtesting/test_pattern_postgres_runner_cli.py`; `pytest tests/patterns tests/risk tests/backtesting tests/strategies`; `git diff --check`.
- Codex self-review: scope respected, no live trading/order/account/API key behavior added, requested price remains offline simulated fill metadata only.
- Known limitation: supported modes are recorded as metadata for consumers; UI-specific rendering is not changed in this task.
- Recommended next task: Task 190.

# Acceptance Criteria

- Every executable pattern entry action has requested_price or equivalent explicit fill metadata.
- Engine sizing and cost calculations use the same price assumption as the entry simulation.
- FVG/OB midpoint or boundary entries cannot be represented as market close fills without explicit entry_mode metadata.
- The schema is stable and JSON-safe for persistence/API consumers.

# Required Tests

## Unit Tests

- Unit: MARKET_ON_CONFIRMATION_CLOSE records confirmation close as fill source.
- Unit: MARKET_ON_NEXT_OPEN requires a next candle and records bars_waited=1.
- Unit: LIMIT_AT_PATTERN_MIDPOINT fills only when low <= midpoint <= high.
- Unit: LIMIT_AT_PATTERN_BOUNDARY fails cleanly for patterns without zone/boundary fields unless supported.

## Integration Tests

- Integration: strategy engine execution price equals action requested_price after costs.

## Contract Tests

- Add contract tests for metadata schemas, no-lookahead behavior, CLI/API output, or compatibility where applicable.

## Safety Tests

- Confirm no live trading path, real exchange order endpoint, signed exchange request, API key handling, or `.env` mutation is introduced.
- Confirm strategy/backtest modules remain offline simulation/research modules.


# Side Effects / Risks

- Some existing fixtures may need to include future candles for non-market entry modes.
- Metadata payload size increases.

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
