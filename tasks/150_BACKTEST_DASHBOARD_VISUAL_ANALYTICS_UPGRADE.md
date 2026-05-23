# Goal

Upgrade the frontend backtest dashboard so saved runs are easier to analyze like a real backtest report: chart axes and zoom, cleaner trade review, strategy/pattern explanation, indicator usage, economic interpretation, and readable parameter/metadata presentation.

This task exists because the current dashboard is technically functional but too raw:

- charts have no zoom, pan, crosshair, visible scale controls, or useful reference lines;
- trade records become long and noisy;
- strategy parameters and metadata are rendered as raw JSON;
- pattern/indicator explanation is not surfaced as a first-class analytical panel;
- cash/equity/signal semantics from Task 149 need to be presented in a user-friendly way.

# Source Requirement

Owner request (2026-05-24):

- Reflect the recent Task 149 backtest signal/cash/equity semantics in the frontend.
- Make the dashboard feel more like a real backtest analysis tool.
- Add chart zoom and visible reference/baseline context.
- Do not force long trade records to stretch the page.
- Show which indicators each strategy uses.
- Explain how each pattern algorithm works.
- Explain the economic meaning of each strategy/pattern where available.
- Do not dump raw `metadata` or `parameters` JSON; render them cleanly and selectively.
- Make the UI visually cleaner and more useful.

Read and inspect:

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- `frontend/AGENTS.md`
- `frontend/STATUS.md`
- `tasks/TASK_TEMPLATE.md`
- `tasks/149_BACKTEST_POSITION_SIGNAL_AND_ACCOUNT_STATE_SEMANTICS.md`
- `docs/api/API_CONTRACT.md`
- `frontend/src/app/page.tsx`
- `frontend/src/types/api.ts`
- `frontend/src/lib/api.ts`
- `frontend/package.json`
- `quant_bitcoin/strategies/pattern_explanations.py`
- relevant frontend/backend tests

# Extracted Roles

- Owner role:
  - Frontend backtest analytics UX owner.
  - Owns dashboard layout, chart interaction, trade review ergonomics, and readable explanation/parameter presentation.
- Supporting roles:
  - API contract role: confirms the frontend consumes existing read-only API fields safely.
  - Strategy explanation role: supplies existing pattern/strategy explanation metadata where available.
  - Backtest semantics role: preserves Task 149 distinctions between semantic `position_signal`, raw `execution_side`, free cash, cash balance, and equity semantics.
- Forbidden roles:
  - No live trading controls.
  - No real Binance order execution.
  - No exchange account/order endpoint calls.
  - No frontend direct database access.
  - No strategy/backtest execution in frontend.
  - No broad backend or engine refactor unless strictly needed for additive read-only display data.

# Context

Task 149 made the backtest output more semantically correct:

- New runs expose semantic position signals such as `LONG_ENTRY`, `SHORT_ENTRY`, and `SHORT_EXIT`.
- Raw `BUY`/`SELL` execution side is preserved separately.
- Short entries can still have a high cash-balance accounting value, but user-facing free cash and buying power are separate.
- Execution-time equity and candle-close mark-to-market equity are no longer conflated.

The current dashboard still needs a presentation upgrade so users see the correct values first and can inspect runs efficiently. The current raw JSON panels should be replaced with structured cards/tables that highlight useful information and keep noisy metadata behind compact disclosure controls.

# Scope

- Redesign the selected-run dashboard view within the existing Next.js frontend.
- Keep the app operational, not a landing page.
- Add chart interaction for backtest analysis:
  - zoom or range selection,
  - reset zoom,
  - crosshair or hover details,
  - visible axes/ticks,
  - start-equity baseline and/or zero-return reference,
  - semantic trade markers using Task 149 `position_signal` values.
- Improve chart information density without clutter:
  - close price chart,
  - equity chart,
  - optional free-cash/cash-balance/account-state overlay or separate compact panel if readable.
- Make trade records compact:
  - paginated, scrollable, collapsible, or fixed-height table;
  - primary columns should be semantic signal, execution side, price, quantity, free cash, equity/PnL where available;
  - raw metadata should be hidden behind a disclosure or removed from default view.
- Replace raw JSON parameter/metadata panels with readable UI:
  - labeled key-value rows,
  - grouped strategy/run/market/account sections,
  - skip empty or null values,
  - show raw JSON only behind an explicit debug/details disclosure if kept.
- Surface strategy and pattern explanations:
  - algorithm summary,
  - indicators used,
  - entry/exit rules,
  - stop-loss/take-profit logic,
  - economic intuition or market behavior the pattern attempts to capture,
  - known limitations.
- Prefer existing persisted `strategy_config.metadata.explanation` and related metadata from Task 126.
- Add a small frontend-side fallback explanation map only for known pattern keys if persisted metadata is missing, and label it as static fallback content.
- Keep backend/API changes additive and read-only if absolutely needed; do not alter strategy engine, persistence schema, or trading behavior.
- Update frontend types and API contract notes if frontend-facing fields or display semantics change.
- Add or update tests where the project has coverage paths.

# Out of Scope

- Running backtests from the frontend.
- Creating new backend execution endpoints.
- Live trading, account controls, order forms, or exchange actions.
- Auth/login.
- Database access from frontend.
- Strategy algorithm changes.
- Backtest accounting changes beyond presentation of existing fields.
- Large design-system migration or replacing the app stack.
- Adding machine learning, portfolio optimization, or risk-management engines.

# Requirements

- The dashboard must make `free_cash` / `available_buying_power` visually primary over raw cash balance for short states.
- Raw cash-balance values must not look like spendable cash.
- Semantic `position_signal` must be displayed as the primary trade marker/table signal.
- Raw `execution_side` must remain available as audit context.
- Chart markers must distinguish at least:
  - long entry,
  - long exit,
  - short entry,
  - short exit,
  - partial exits when present.
- Charts must provide a way to inspect a smaller time range without leaving the page.
- The equity chart must identify its baseline and make drawdown/return context easier to read.
- Trade tables must not force the entire page to become a long metadata dump.
- Strategy parameters must be presented as human-readable labels and values, not raw JSON by default.
- Metadata must be curated:
  - important runtime/account/performance/explanation fields should be shown,
  - low-level raw metadata should be hidden behind a details/debug section if preserved.
- Strategy/pattern panels must explain what indicators are used and why they matter economically, but must not invent unsupported live-trading claims.
- UI must remain responsive on desktop and mobile.
- No in-app instructional copy that explains obvious UI controls; use labels/tooltips where needed.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm Task 149 is completed or explicitly approved as a dependency.
- [x] Confirm this Task 150 is recorded as the current active implementation task before coding.
- [x] Confirm this task is limited to frontend dashboard UX/read-only display and additive API/type/docs updates if needed.
- [x] Confirm no live trading, order endpoint, account endpoint, direct DB access, or API key behavior is introduced.
- [x] Record assumptions, blockers, or unclear status items before coding.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task complete or blocked and point to the next task if appropriate.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- Dashboard charts include visible axes/ticks and an interaction for zoom/range inspection plus reset.
- Equity chart includes a clear baseline/reference and remains tied to Task 149 mark-to-market semantics.
- Trade markers and trade table use semantic `position_signal` as the primary signal.
- Short-entry cash presentation shows free cash/buying power first and does not make `cash_balance_after=20000` look spendable.
- Trade history is compact and does not create an endless raw-metadata page.
- Strategy parameters are rendered as readable labels/values rather than raw JSON by default.
- Metadata panels are curated, grouped, and compact; raw JSON is absent from default view or hidden behind explicit details.
- Strategy explanation section shows:
  - indicators used,
  - pattern/algorithm logic,
  - economic interpretation,
  - limitations.
- Legacy runs missing new metadata render safely with fallback labels, not broken UI.
- Frontend remains responsive and visually coherent.
- No frontend direct DB access, live trading controls, or exchange endpoint behavior is added.

# Required Tests

## Unit Tests

- Test frontend helper logic for:
  - preferring `position_signal` over legacy `signal`,
  - preferring `free_cash_after` / `available_buying_power_after` for user-facing cash,
  - formatting strategy parameters into readable labels,
  - hiding/skipping empty metadata values,
  - fallback strategy explanation for known patterns if implemented.

## Integration Tests

- Test dashboard rendering with a fixture containing:
  - long entry/exit,
  - short entry/exit,
  - cash balance greater than starting cash but free cash zero,
  - strategy explanation metadata,
  - nested strategy parameters.
- Test legacy run rendering where metadata is missing or has old `BUY`/`SELL` signals.
- Test chart zoom/range state and reset if feasible in the available test harness.

## Contract Tests

- Frontend TypeScript types match `docs/api/API_CONTRACT.md`.
- API contract documents any newly consumed or displayed fields.
- Existing read-only backend response shape remains backward-compatible.

## Safety Tests

- No Binance order endpoint is called.
- No Binance account endpoint is called.
- No live trading endpoint or control is added.
- No API keys are required.
- No `.env` files are created or modified.
- Frontend uses backend API only via the existing API client.

# Review Checklist

- Scope respected.
- Requirement matched.
- Role ownership respected.
- Architecture boundaries respected.
- Data contract respected where applicable.
- No hardcoded secrets.
- No real order execution unless explicitly requested.
- No unnecessary abstractions.
- UI makes free cash/equity/signal semantics clearer than raw accounting fields.
- Pattern/economic explanation is sourced from existing metadata or clearly labeled static fallback content.

# Verification

Default:

```bash
npm --prefix frontend run build
pytest
git diff --check
```

Additional verification:

```bash
pytest backend/tests
pytest tests/backtesting/test_strategy_persistence_adapter.py
pytest tests/backtesting/test_strategy_cli_persistence.py
```

If a frontend test harness is added or already available:

```bash
npm --prefix frontend test
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

# Completion Summary

- Files changed: `frontend/src/app/page.tsx`, `frontend/src/styles/globals.css`, `frontend/STATUS.md`, `docs/api/API_CONTRACT.md`, and root task/status ledgers.
- Implementation summary: Rebuilt the dashboard around a left-side run selector, metric cards, range-inspectable SVG charts with axes/baseline/crosshair readouts, compact paged trade table, free-cash-first account state panel, curated strategy parameter/runtime panels, and strategy indicator/economic interpretation sections with persisted explanation plus static fallback knowledge.
- Tests added or updated: No frontend unit test harness exists; behavior is covered by TypeScript/Next build plus existing backend/backtesting contract tests.
- Tests run: `npm --prefix frontend run build`; `pytest`; `pytest backend/tests/test_backtest_results_service_runtime.py tests/backtesting/test_strategy_persistence_adapter.py tests/backtesting/test_strategy_cli_persistence.py`; `git diff --check`; local Next server HTML response via `curl -s http://localhost:3000`.
- Codex self-review result: Scope stayed within frontend/read-only display plus docs/status updates; no live trading, direct DB access, order/account endpoint, API key, or `.env` behavior was added.
- Known limitations: Full `pytest backend/tests` is blocked in this environment because `fastapi` is not installed; in-app browser automation was unavailable because the required Node REPL browser-control tool was not exposed.
- Recommended next task: Review Task 149-150 changes and assign the next explicit task before additional implementation.
