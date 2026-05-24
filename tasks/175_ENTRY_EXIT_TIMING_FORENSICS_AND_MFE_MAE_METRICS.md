# Goal

Measure whether entries and exits are algorithmically late, early, or structurally mismatched by adding MFE/MAE, time-to-stop/target, fill-reference divergence, and post-entry reaction metrics.

# Source Requirement

Owner concern: performance may be poor because buy/sell timing is algorithmically wrong, not merely because the economic idea is weak.

Latest repo findings:
- FVG/pattern default entry mode in `build_pattern_trade_actions()` remains `MARKET_ON_CONFIRMATION_CLOSE`.
- Task 172 aligns risk plan to actual fill, but market-confirmation entry can still chase displacement after the favorable move already happened.
- Existing metrics do not directly show MFE/MAE, entry lag, fill-reference divergence, or whether price moves favorably before exit.

# Extracted Roles

- Owner role:
  - Entry/exit timing diagnostics owner.
- Supporting roles:
  - Risk/exit simulator role: provides post-entry candle path.
  - Backtest engine role: persists fills and exits.
  - Frontend role: explains entry/exit timing evidence.
- Forbidden roles:
  - No strategy retuning in this task.
  - No live trading.
  - No exchange endpoint behavior.

# Context

A bad FVG or breakout result can be caused by late entry:
- FVG market entry after displacement may buy near local exhaustion.
- Stop may sit near the old structure while target is far after fill alignment.
- Soft invalidation or time stop may close after adverse retracement.
- A trade may show positive MFE before exit, suggesting exit timing failed.
- A trade may show immediate MAE, suggesting entry timing failed.

Current attribution tells what happened, but not enough about the path between entry and exit.

# Scope

- Add path-based trade timing analytics:
  - maximum favorable excursion per trade,
  - maximum adverse excursion per trade,
  - MFE/MAE in price, quote PnL, and R multiple,
  - bars to MFE,
  - bars to MAE,
  - bars to first favorable close,
  - bars to stop/target/soft invalidation/time stop,
  - entry fill vs pattern reference distance,
  - entry fill vs confirmation close,
  - entry fill vs zone midpoint/boundary when available.
- Use graph points and persisted executions where possible.
- Add metadata to `trade_attribution` or a new `timing_diagnostics` section.
- Frontend must show:
  - “Entry was late/chasing” if fill-reference divergence exceeds threshold,
  - “Exit left money on table” if MFE materially exceeded realized R,
  - “Immediate adverse excursion” if MAE occurs within first N bars.
- Keep calculations deterministic and offline.

# Out of Scope

- No strategy behavior changes.
- No new order fill model.
- No parameter optimization.
- No live execution behavior.

# Requirements

- MFE/MAE must use only candles between actual entry and exit.
- Long and short calculations must be direction-aware.
- Partial exits must be handled with a documented approximation if exact lifecycle reconstruction is unavailable.
- Missing data must produce warnings rather than crashes.
- Metrics must be exposed to frontend or diagnostics.

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
- Timing diagnostics are read-only analytics; they must not change strategy entries, exits, fills, sizing, or persistence semantics.
- Full OHLC candles are available only inside the strategy engine. Legacy persisted rows may have close-only graph points, so backend fallback diagnostics may be approximate and must carry warnings.
- Partial exits are approximated as one entry-to-final-exit lifecycle for MFE/MAE path analytics.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added deterministic `trade_timing_diagnostics_v1` with direction-aware MFE/MAE, R multiples, bars-to-MFE/MAE/first favorable close/exit reason, fill-reference/confirmation/zone distances, and timing flags.
- Strategy-engine runs store OHLC-based timing diagnostics; backend detail responses compute close-only fallback diagnostics for legacy saved rows with warnings.
- Frontend displays a dedicated read-only Entry/Exit Timing panel.
- Partial exits remain an entry-to-final-exit lifecycle approximation, documented in diagnostics metadata.
- Next task: Task 176 `FVG_ENTRY_MODE_RETEST_VERSUS_MOMENTUM_EXPERIMENTS`.

# Acceptance Criteria

- Trade timing diagnostics appear for completed trades.
- A synthetic long trade with high after entry reports positive MFE.
- A synthetic short trade with low after entry reports positive MFE.
- A trade whose fill is far above FVG midpoint is flagged as fill-reference divergence.
- Frontend displays timing diagnosis under a dedicated panel.

# Required Tests

## Unit Tests

- Long/short MFE and MAE calculations.
- Fill-reference divergence threshold classification.
- Missing candle/trade matching fallback.

## Integration Tests

- Saved run with trades exposes timing diagnostics through backend service.

## Contract Tests

- Document timing diagnostics schema.

## Safety Tests

- No exchange/API/live execution imports in diagnostics.

# Verification

Default:

```bash
pytest tests/backtesting/test_performance_metrics.py tests/backtesting/test_strategy_persistence_adapter.py backend/tests/test_backtest_results_service_runtime.py
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
