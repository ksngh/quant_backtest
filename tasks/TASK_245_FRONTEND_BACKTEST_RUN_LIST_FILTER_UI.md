# Task 245: Frontend Backtest Run List Filter UI

# Goal

Add practical filter controls to the left-side saved-run list and wire them to the read-only backend run-list filters from Task 244.

# Source Requirement

Owner feedback:

4. The left-side run list is useful, but it should support filtering. This should be done together with backend support.

# Extracted Roles

- Owner role:
  - Frontend dashboard run-navigation owner.
- Supporting roles:
  - Backend API consumer role: uses the read-only filter contract from Task 244.
  - Frontend state role: owns filter form state, request parameters, loading/empty states, and reset behavior.
- Forbidden roles:
  - Do not add backend filter implementation here unless Task 244 is completed or explicitly included.
  - Do not run backtests from the frontend.
  - Do not add live trading controls, auth, credentials, account endpoints, or order endpoints.

# Context

The saved-run list is useful as navigation, but without filters it becomes hard to find specific runs by market, interval, strategy, date range, or cost profile. The UI should expose backend filters without making the left sidebar too heavy.

# Scope

- Add compact filter controls above or within the left-side run list.
- Support the filter fields implemented by Task 244.
- Include clear apply/reset behavior.
- Preserve current default list loading when filters are empty.
- Handle loading, empty results, and invalid/failed request states.
- Keep the sidebar scannable and responsive.

# Out of Scope

- Do not add backend filtering here unless explicitly assigned with Task 244.
- Do not add full advanced search/query language.
- Do not add saved filter presets.
- Do not add dashboard auth/login.

# Requirements

- Filters map directly to backend query parameters.
- Empty filters do not change existing list behavior.
- Reset clears filters and reloads the default list.
- Selected run detail remains stable or is cleared predictably when filters change.
- UI remains readable in the left panel on desktop and mobile.

# Status Tracking

## Before Implementation

- [x] Read `AGENTS.md`.
- [x] Read `STATUS.md`.
- [x] Read `BACKLOG.md`.
- [x] Read `frontend/AGENTS.md` if present.
- [x] Read `docs/api/API_CONTRACT.md`.
- [x] Confirm Task 244 is completed or explicitly included in the assigned work.
- [x] Read this assigned task file before coding.

## After Implementation

- [x] Update `STATUS.md` if project state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md` when completed.
- [x] Update `BACKLOG.md` if completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.

# Acceptance Criteria

- Left-side run list has usable filter controls.
- Filters call the backend with documented query parameters.
- Empty, loading, error, and reset states are handled.
- Existing run selection and detail loading still work.
- Frontend build/type checks pass.

# Required Tests

## Unit Tests

- Test query-param builder/filter-state helper if introduced.

## Integration Tests

- Run frontend typecheck/build.
- If available, test that filter state maps to API calls.

## Contract Tests

- Confirm frontend filter names and query parameters match `docs/api/API_CONTRACT.md`.

## Safety Tests

- Confirm no backtest execution, live trading controls, or credential behavior are added.

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
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:helpers
git diff --check
```

Completed verification:

- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:helpers`
- `git diff --check`

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
