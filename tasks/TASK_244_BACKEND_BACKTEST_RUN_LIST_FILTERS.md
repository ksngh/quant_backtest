# Task 244: Backend Backtest Run List Filters

# Goal

Extend the read-only backtest run listing API and persistence query path so the left-side run list can be filtered by useful saved-run attributes.

# Source Requirement

Owner feedback:

4. The left-side run list is useful, but it needs filters. This likely requires backend work together with frontend work.

# Extracted Roles

- Owner role:
  - Backend read-only dashboard API owner.
- Supporting roles:
  - Persistence repository role: owns query parameters and SQL filtering for saved backtest runs.
  - API contract role: owns documented request/response behavior.
  - Frontend integration role: consumes filters in Task 245.
- Forbidden roles:
  - Do not add backtest execution endpoints.
  - Do not mutate strategy/backtest logic.
  - Do not add live trading, account endpoints, order endpoints, credentials, or `.env` behavior.

# Context

The dashboard already has a saved-run list. Some filters may already exist in the API contract, but the UI needs practical run discovery. Backend should support a stable set of filters before the frontend builds controls on top.

# Scope

- Review existing `GET /api/backtest-runs` query parameters and repository support.
- Add or harden read-only filters for saved runs, such as:
  - source,
  - symbol,
  - interval,
  - strategy key/pattern,
  - actual start/end time,
  - created date range,
  - minimum/maximum total return if already available in persisted summary,
  - cost profile if available in persisted metadata.
- Preserve default newest-first listing.
- Validate query parameters and return `400` for invalid values.
- Update `docs/api/API_CONTRACT.md`.
- Add backend/service/repository tests.

# Out of Scope

- Do not implement frontend controls in this task; Task 245 owns UI.
- Do not add database migrations unless an existing indexed/persisted field cannot support the accepted minimum filter set.
- Do not rerun strategies or derive filters by executing backtests.
- Do not add auth/login.

# Requirements

- Filters are read-only and map to saved database/read-model fields.
- Unsupported/invalid filter values are handled deterministically.
- API response shape remains backward compatible.
- Existing unfiltered list behavior remains unchanged.
- Contract clearly documents which filters are exact match, partial match, numeric, or datetime.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `backend/AGENTS.md` if present.
- [ ] Read `docs/api/API_CONTRACT.md`.
- [ ] Read this assigned task file before coding.
- [ ] Confirm frontend changes are deferred to Task 245.

## After Implementation

- [ ] Update `STATUS.md` if project state changed.
- [ ] Append a concise progress/completion note to `PROJECT_HISTORY.md` when completed.
- [ ] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- `GET /api/backtest-runs` supports the agreed filter set.
- Repository/service tests cover filters and invalid input.
- API docs match implementation.
- No backtest execution or live trading behavior is added.

# Required Tests

## Unit Tests

- Test query/filter parsing and validation.

## Integration Tests

- Test repository/service list calls with one or more filters.
- Test unfiltered behavior remains newest-first.

## Contract Tests

- Verify API contract documents all supported filters and response compatibility.

## Safety Tests

- Confirm no order/account endpoint usage and no credential handling.

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
pytest backend/tests tests/persistence
pytest tests/backtesting/test_strategy_persistence_adapter.py
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
