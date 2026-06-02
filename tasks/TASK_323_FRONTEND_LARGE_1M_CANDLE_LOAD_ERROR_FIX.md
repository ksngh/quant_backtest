# Task 323: FRONTEND_LARGE_1M_CANDLE_LOAD_ERROR_FIX

# Goal

Fix the dashboard load failure that occurs when a selected run contains too many `1m` candle graph points for the frontend to fetch, parse, and render reliably.

The preferred outcome is a read-only backend/frontend change that lets the dashboard load large `1m` runs through bounded or downsampled chart data while preserving enough detail for interpretation, markers, warnings, and diagnostics.

# Source Requirement

Owner request:

> 야 1분봉이 너무 많으니까 프론트엔드에서 안불러와져. 에러가 떠버려. 이거 에러해결하는거 task로 만들어줘

Follow-up owner request:

> task 생성 다 되고나면 바로 실행해주고 끝나면 테스트하고 PR올려줘

Interpreted as: create a bounded implementation task for the dashboard load error. The owner wants the implementation, tests, and PR after the task exists. The task was created first under the mandatory project workflow, then executed after the owner assigned it.

# Extracted Roles

- Owner role:
  - Reports that long `1m` candle runs are too large for the frontend and cause a dashboard error.
  - Wants the issue fixed, verified, and raised as a PR after the task is assigned.
- Supporting roles:
  - Frontend maintainer: update dashboard data fetching and chart rendering so large runs do not fail client-side.
  - Backend API maintainer: add or extend read-only API behavior for bounded/downsampled chart payloads.
  - API contract maintainer: update `docs/api/API_CONTRACT.md` before changing any backend/frontend API shape.
  - Test/verification role: reproduce or simulate large `1m` graph payload behavior and verify the dashboard handles it.
- Forbidden roles:
  - Strategy/backtest implementer.
  - Backtest runner or parameter tuner.
  - Database mutator or candle backfill executor.
  - Live trading or exchange-order executor.
  - Auth/login implementer.
  - Direct frontend-to-database access implementer.

# Context

Current dashboard behavior:

- `frontend/src/lib/api.ts` calls `GET /api/backtest-runs/{run_id}` through `getBacktestRun(runId)`.
- `frontend/src/app/page.tsx` stores the full detail response in React state and renders both Close Price and Equity charts from `detail.graph_points`.
- `backend/quant_backtest_api/routers/backtest_runs.py` exposes `GET /api/backtest-runs/{backtest_run_id}` with no chart-size query controls.
- `backend/quant_backtest_api/services/backtest_results.py` serializes all `row.graph_points` into the detail response.
- `docs/api/API_CONTRACT.md` already notes that `/api/backtest-runs/{id}/chart` is optional and that richer chart payload compression/downsampling is a future extension.

Likely failure mode:

- Long `1m` runs can contain tens of thousands or more graph points.
- The full detail payload can become too large for reliable browser fetch/JSON parse/React state update/SVG path rendering.
- Rendering all points into an SVG path and computing overlays/markers on every selected detail can make the dashboard unresponsive or show an API/loading error.

# Scope

- Read required state files and this task before implementation.
- Read area rules and contracts before editing:
  - `frontend/AGENTS.md`
  - `frontend/STATUS.md`
  - `backend/AGENTS.md`
  - `backend/STATUS.md`
  - `docs/api/API_CONTRACT.md`
- Inspect the current dashboard detail fetch/render flow:
  - `frontend/src/lib/api.ts`
  - `frontend/src/types/api.ts`
  - `frontend/src/app/page.tsx`
  - chart-related helpers as needed.
- Inspect current backend detail API flow:
  - `backend/quant_backtest_api/routers/backtest_runs.py`
  - `backend/quant_backtest_api/services/backtest_results.py`
  - `backend/quant_backtest_api/schemas/backtest.py`
  - backend tests for run detail responses.
- Update `docs/api/API_CONTRACT.md` before implementation if adding query params, chart metadata, or a chart-focused endpoint.
- Implement a bounded large-chart data path. Acceptable approaches include:
  - Add optional read-only detail query params such as `graph_max_points` and `graph_sampling_mode`, and make the frontend request bounded graph data for dashboard charts.
  - Or implement the existing optional `GET /api/backtest-runs/{backtest_run_id}/chart` endpoint and make the frontend use it for charts while avoiding a full unbounded `graph_points` payload.
  - Or a narrower equivalent design that prevents unbounded `graph_points` from being sent to the frontend by default for dashboard use.
- Sampling/downsampling must preserve:
  - first and last graph points;
  - graph points with `signal`, `position_signal`, or `execution_side`;
  - trade/marker timestamps or enough nearby context to keep trade markers meaningful;
  - chronological order and existing graph point schema.
- The frontend must:
  - avoid fetching or rendering unbounded `1m` graph arrays for dashboard chart views;
  - display clear sampling/limited-data metadata or warning text when chart points are reduced;
  - keep existing run summary, diagnostics, trade table, and read-only safety boundaries intact;
  - handle API errors with a useful message rather than leaving the page unusable.
- Update focused backend/frontend status docs if behavior changes materially.
- Update root state files after execution.

# Out of Scope

- Running a new strategy backtest.
- Tuning a strategy or changing strategy/risk/cost logic.
- Mutating saved run data or database records.
- Backfilling candle data.
- Adding live trading behavior, order endpoints, account endpoints, or signed exchange requests.
- Adding frontend controls that execute strategies or place orders.
- Direct PostgreSQL access from the frontend.
- Adding auth/login.
- Replacing the charting stack with a new framework unless the existing SVG path approach cannot be made reliable with bounded data.
- Changing report/blog workflows or report artifacts.

# Requirements

- The dashboard must not request/render an unbounded full `graph_points` array for large `1m` chart views.
- The backend must expose chart-size metadata when it reduces graph points, such as:
  - original point count;
  - returned point count;
  - sampling mode;
  - max requested points;
  - whether marker/trade points were preserved.
- The frontend must surface that metadata near the chart or warnings area.
- Sampling must be deterministic and stable for the same saved run and query params.
- Sampling must not invent new prices, equity values, cash values, signals, or timestamps.
- API changes must remain read-only and backward compatible where possible.
- If the backend still offers an unbounded detail response for compatibility, the dashboard must not use it for large chart rendering by default.
- If exact unsampled chart inspection is impossible for very large runs, document that limitation and expose the sampled view honestly.
- If reproduction cannot use a real large `1m` saved run in the current environment, create deterministic test fixtures with enough synthetic graph points to exercise the large-payload path.

# Status Tracking

## Before Implementation

- [x] Read `BACKLOG.md`.
- [x] Read `PROJECT_HISTORY.md`.
- [x] Read `STATUS.md`.
- [x] Read this task.
- [x] Read `frontend/AGENTS.md` and `frontend/STATUS.md`.
- [x] Read `backend/AGENTS.md` and `backend/STATUS.md`.
- [x] Read `docs/api/API_CONTRACT.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm this is a read-only dashboard load-error fix, not a strategy/backtest task.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `docs/api/API_CONTRACT.md` if API behavior changed.
- [x] Update `frontend/STATUS.md` if frontend behavior changed.
- [x] Update `backend/STATUS.md` if backend behavior changed.
- [x] Update root `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append completion progress to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` if this task was completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A large `1m` run can be selected in the dashboard without the frontend failing due to excessive graph payload/render size.
- The dashboard no longer fetches/renders unbounded chart graph points for large `1m` runs by default.
- Backend response metadata tells the frontend when chart data was reduced or sampled.
- Frontend displays a concise sampled/limited chart notice when applicable.
- Trade markers/signals remain meaningful in the sampled chart view.
- Existing list filters and run detail summary panels continue to work.
- API contract is updated for any new query params, endpoint, or response metadata.
- Backend and frontend tests cover the large graph path.
- No strategy/backtest execution, DB mutation, candle backfill, live trading behavior, exchange endpoint behavior, secret, or `.env` change is introduced.

# Required Tests

## Unit Tests

- Backend tests for deterministic graph downsampling or bounded chart serialization:
  - preserves first and last points;
  - preserves signal/trade marker points;
  - respects max point limits;
  - keeps chronological order;
  - reports sampling metadata.
- Frontend helper/component tests if a helper is added for chart metadata, sampled notices, or bounded detail/chart fetch parameters.

## Integration Tests

- Backend API test for the large chart/detail path using a fake repository/read model with a large synthetic `1m` graph series.
- Frontend type/build check after API type changes.
- If practical, local dashboard smoke test with a large synthetic or persisted run.

## Contract Tests

- Verify API contract references the new bounded chart behavior:

```bash
rg -n "chart|graph_max_points|sampling|downsample|original.*point|returned.*point|1m|large" docs/api/API_CONTRACT.md
```

- Verify backend/frontend code contains the bounded chart path:

```bash
rg -n "graph_max_points|sampling|downsample|chart" backend frontend/src
```

## Safety Tests

```bash
rg -n "ENABLE_LIVE_TRADING|create_order|new_order|SIGNED|apiKey|api_key|secret|\\.env" backend frontend/src docs/api STATUS.md PROJECT_HISTORY.md BACKLOG.md tasks/TASK_323_FRONTEND_LARGE_1M_CANDLE_LOAD_ERROR_FIX.md
```

Expected: no unsafe live-trading/order/secret behavior is introduced; declarative safety text in task/state files is acceptable.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- API contract updated before shared contract implementation.
- Frontend remains read-only and uses backend API only.
- Backend remains read-only and does not run backtests.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution.
- No unnecessary abstractions.
- Large `1m` graph behavior is tested.

# Verification

Default focused verification:

```bash
pytest backend/tests
npm --prefix frontend run typecheck
npm --prefix frontend run test:helpers
git diff --check
```

If dependencies or local services are unavailable, document the blocker and run the subset that is available.

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

# Completion Summary

Completed on 2026-06-02.

Files changed:

- `docs/api/API_CONTRACT.md`
- `backend/quant_backtest_api/routers/backtest_runs.py`
- `backend/quant_backtest_api/schemas/backtest.py`
- `backend/quant_backtest_api/services/backtest_results.py`
- `backend/tests/test_backtest_results_service.py`
- `backend/tests/test_backtest_results_service_runtime.py`
- `backend/tests/test_backtest_runs_api.py`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/chartSampling.ts`
- `frontend/src/app/page.tsx`
- `frontend/src/types/api.ts`
- `frontend/tests/chartSampling.test.ts`
- `frontend/package.json`
- `frontend/tsconfig.test.json`
- State files: `STATUS.md`, `BACKLOG.md`, `PROJECT_HISTORY.md`, `backend/STATUS.md`, `frontend/STATUS.md`

Implementation summary:

- Added optional `graph_max_points` and `graph_sampling_mode=preserve_markers` support to `GET /api/backtest-runs/{id}`.
- Added deterministic graph sampling metadata under `chart_metadata.graph_points`.
- Sampling preserves first/last points, marker/signal/execution points, trade timestamps when present, nearby marker context as budget allows, and chronological order.
- Backend diagnostics and research-report summaries remain based on the saved full graph series rather than the sampled response series.
- Updated the dashboard detail fetch to request bounded chart data by default with `graph_max_points=3000`.
- Added a frontend chart-sampling notice near the chart area when the API returns a sampled graph payload.

Tests added or updated:

- Backend service tests for deterministic graph sampling, marker preservation, boundary preservation, max point limit, chronological order, and metadata.
- Backend API tests for bounded graph query parameter forwarding, metadata response, and unsupported sampling-mode rejection.
- Frontend helper tests for chart sampling notice text and marker-warning behavior.
- Updated a runtime service fixture to include the current list-item `starting_cash` contract required by the full backend test suite.

Tests run:

- `pytest backend/tests` -> `22 passed`, with one existing Starlette deprecation warning from FastAPI TestClient.
- `npm --prefix frontend run typecheck` -> passed.
- `npm --prefix frontend run test:helpers` -> passed.
- `git diff --check` -> passed.
- Contract search and safety search were run. Safety search returned only existing declarative safety text, redaction tests, and `NEXT_PUBLIC_BACKTEST_API_BASE_URL`; no new live trading, signed exchange, order endpoint, secret, or `.env` behavior was introduced.

Codex self-review result:

- Scope respected. This task changed only the read-only dashboard API/frontend path, API contract, focused tests, and required state files.
- No strategy, backtest execution, DB mutation, candle backfill, live trading, exchange account/order endpoint, secret, or `.env` change was added.

Known limitations:

- The backend still loads the saved run graph series from persistence before reducing the response payload. This fixes browser fetch/JSON/render pressure but does not optimize database read memory for very large saved runs.
- Exact unsampled chart inspection remains available only through compatibility use of the detail endpoint without `graph_max_points`; the dashboard defaults to sampled chart data for reliability.

Recommended next task:

- Create the owner-requested `Lookback Return Momentum V2` no-cost 1 ATR stop/take-profit validation task after the Task 323 PR is opened.
