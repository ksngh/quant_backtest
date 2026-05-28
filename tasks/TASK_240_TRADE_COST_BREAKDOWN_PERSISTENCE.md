# Task 240: Trade Cost Breakdown Persistence

# Goal

Persist a structured per-execution `cost_breakdown` for every backtest trade row so fee, spread, slippage, and total transaction cost are auditable separately from raw price and effective price.

# Source Requirement

Owner concern: slippage and fee costs must be saved separately for every trade. The current behavior appears to mix spread/slippage into `price`, while fee and cost components are not consistently exposed as first-class, stable trade data.

Forensic finding from the 2026-05-20 02:17 FVG short case:

- Each execution already has calculated values such as `fee_cost`, `spread_cost`, `slippage_cost`, `total_cost`, `effective_slippage_bps`, and `volatility_bps`.
- The persistence/API/frontend contract does not expose raw/effective price and cost components as a clean stable trade object.
- The frontend currently renders a generic `Price` field and does not make the per-execution fee/spread/slippage breakdown obvious.

# Extracted Roles

- Owner role:
  - Backtest trade persistence and auditability owner.
- Supporting roles:
  - Strategy execution role: supplies per-execution cost values.
  - Persistence adapter role: writes cost breakdown into backtest trade rows.
  - API/read-model role: serializes cost breakdown consistently.
  - Frontend role: displays fee, spread, slippage, and total cost per execution.
  - Test role: verifies round-trip persistence and serialization.
- Forbidden roles:
  - No live trading.
  - No order placement.
  - No exchange account endpoints.
  - No API key or `.env` changes.
  - No profitability retuning.

# Context

The backtest engine calculates transaction-cost fields, but the durable contract should not rely on scattered metadata keys or adjusted prices. A single structured object should be attached to every execution/trade row so analysis can answer:

```text
What was the raw fill price?
What was the effective diagnostic price?
How much fee was charged?
How much spread cost was modeled?
How much slippage cost was modeled?
What was the total per-execution transaction cost?
Which cost profile and volatility estimate produced those values?
```

The recommended object shape is:

```json
{
  "cost_breakdown": {
    "fee_cost": 9.958456816965747,
    "spread_cost": 2.9875370450897236,
    "slippage_cost": 5.362947140131993,
    "total_cost": 18.308941002187463,
    "fee_bps": 10.0,
    "spread_bps": 3.0,
    "slippage_bps": 5.385319471381747,
    "effective_slippage_bps": 5.385319471381747,
    "volatility_bps": 3.853194713817474,
    "cost_profile_name": "conservative_crypto_1m",
    "cost_currency": "quote"
  }
}
```

# Scope

- Add a stable `cost_breakdown` object to each execution/trade payload.
- Persist `cost_breakdown` for every entry and exit row.
- Include at least:
  - `fee_cost`,
  - `spread_cost`,
  - `slippage_cost`,
  - `total_cost`,
  - `fee_bps`,
  - `spread_bps`,
  - `slippage_bps`,
  - `effective_slippage_bps`,
  - `volatility_bps`,
  - `cost_profile_name`,
  - `cost_currency`.
- Include `order_type` and `liquidity_role` only when they already exist or can be derived without adding maker/taker modeling.
- Ensure `cost_breakdown` is present in:
  - CLI JSON output,
  - persistence adapter payloads,
  - Postgres readback/API DTOs,
  - frontend `BacktestTrade` type,
  - frontend trade-table or detail view.
- Keep raw price, effective price, and cost breakdown separate.
- Add a deterministic fixture proving the 2026-05-20 02:17 FVG short entry and exit retain their fee/spread/slippage values after serialization and readback.

# Out of Scope

- Do not change the cost model rates or formulas in this task.
- Do not change net R/R entry filtering in this task.
- Do not add maker/taker differentiation unless the required fields already exist.
- Do not rewrite historical rows unless an explicit migration task is created.
- Do not introduce new database columns if the project convention prefers `metadata` JSON for extensible trade diagnostics; use the repo's current persistence style unless a schema owner explicitly approves a migration.
- Do not introduce live trading, exchange orders, account endpoints, API keys, or `.env` changes.

# Requirements

- Every newly persisted backtest trade row must contain a structured `cost_breakdown` object.
- `cost_breakdown.total_cost` must equal `fee_cost + spread_cost + slippage_cost` within normal floating-point tolerance.
- Entry and exit executions must both store their own cost breakdown; do not store only closed-position aggregate costs.
- API output must preserve numeric precision enough to reconcile trade-level PnL.
- Frontend types must treat `cost_breakdown` as optional for legacy rows and required for newly produced rows.
- UI must not imply that fee/spread/slippage are part of raw `price`.
- Documentation must state that costs are quote-currency amounts unless another currency is explicitly specified.

# Status Tracking

## Before Implementation

- [ ] Read `AGENTS.md`.
- [ ] Read `STATUS.md`.
- [ ] Read `BACKLOG.md`.
- [ ] Read `PROJECT_HISTORY.md` only as needed for recent context.
- [ ] Read this assigned task file before coding.
- [ ] Confirm the task matches the current phase and step.
- [ ] Confirm the current active task is recorded or should be updated.
- [ ] Confirm parallel work is allowed before starting any parallel tasks.
- [ ] Confirm no live trading, order endpoint, account endpoint, API key, or `.env` behavior is introduced.
- [ ] Record assumptions, blockers, or unclear status items before coding.

Assumptions before implementation:

- Existing execution objects already compute most cost fields; this task standardizes persistence and API shape rather than inventing a new cost model.
- Legacy rows may lack `cost_breakdown`; frontend/API code should handle that gracefully.
- If Task 238 has already landed, `price` should be raw and `effective_price` should remain separate.

## After Implementation

- [ ] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [ ] Append a concise progress/completion note to `PROJECT_HISTORY.md` when the task is completed.
- [ ] Update `BACKLOG.md` if the task was created, completed, blocked, reprioritized, or split.
- [ ] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [ ] Leave uncertain items open and document the uncertainty.
- [ ] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- New entry and exit trade rows contain `cost_breakdown`.
- `cost_breakdown` survives persistence adapter write and read-model/API serialization.
- Frontend types and UI can display fee, spread, slippage, and total cost separately for each execution.
- `total_cost` reconciles to `fee_cost + spread_cost + slippage_cost`.
- The 2026-05-20 02:17 FVG short fixture exposes the documented entry and exit cost values separately from price.
- Legacy rows without `cost_breakdown` do not crash API or frontend rendering.
- No live trading behavior is added.

# Required Tests

## Unit Tests

- Test cost-breakdown object construction from `StrategyExecution`.
- Test `total_cost` reconciliation from fee/spread/slippage components.
- Test missing optional fields are handled without crashing legacy serialization.
- Test numeric values remain floats/decimals suitable for PnL reconciliation.

## Integration Tests

- Persist a deterministic backtest with nonzero fee/spread/slippage and verify entry/exit rows store `cost_breakdown`.
- Read persisted rows through the API/read-model path and verify `cost_breakdown` is returned unchanged.
- Verify CLI JSON includes `cost_breakdown` for every execution row.
- Verify frontend build/type checks after adding `cost_breakdown` to `BacktestTrade`.

## Contract Tests

- API contract documents the `cost_breakdown` shape and legacy optionality.
- Frontend type contract includes `cost_breakdown` and does not conflate it with `price`.
- Documentation states that cost amounts are per execution, not only per closed position.

## Safety Tests

- Confirm no exchange endpoint imports or signed order/account behavior is added.
- Confirm no API key, `.env`, or live-trading flag changes are made.
- Confirm all tests use deterministic offline fixtures.

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

# Verification

Default:

```bash
pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_costs.py tests/persistence tests/api || true
pytest tests/backtesting/test_pattern_postgres_runner_cli.py
npm --prefix frontend run build
pytest
git diff --check
```

If the repo does not have one of the targeted test paths, run the nearest existing strategy-engine, persistence, API, CLI, and frontend build tests and record the substitution in the completion summary.

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
