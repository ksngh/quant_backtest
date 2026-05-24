# Goal

Add explicit FVG entry-mode experiments comparing market-on-confirmation momentum entry versus retest/limit entries at midpoint, boundary, and custom reference levels.

# Source Requirement

Owner concern: FVG strategy performance is poor; buying/selling timing may be structurally wrong.

Latest repo findings:
- FVG risk planning starts from FVG midpoint/reference concepts.
- Current canonical action builder defaults to `MARKET_ON_CONFIRMATION_CLOSE`.
- Task 172 fixed stale risk-plan targets after actual fill, but that does not prove market-on-confirmation is the economically correct entry mode.
- FVG economics often imply retest/imbalance-fill behavior rather than chasing confirmation close.

# Extracted Roles

- Owner role:
  - FVG research owner.
- Supporting roles:
  - Pattern entry simulation role: implements entry mode mechanics.
  - CLI/backtest role: runs comparative experiments.
  - Frontend role: displays selected entry mode and trade timing.
- Forbidden roles:
  - No profitability retuning by default.
  - No live trading.
  - No exchange/order endpoint behavior.

# Context

A bullish FVG formed by displacement can close far above the midpoint. Entering immediately at confirmation close may be a momentum-continuation strategy, but the FVG narrative often expects price to rebalance into the gap. If the default enters at confirmation close while stop is based on the FVG boundary, R/R can deteriorate. After Task 172, targets are aligned to fill, preventing mislabeled take-profit losses, but market entry can still be economically late.

# Scope

- Add configurable FVG entry mode for canonical pattern strategy/CLI:
  - `market_on_confirmation_close`,
  - `market_on_next_open`,
  - `limit_at_entry_reference`,
  - `limit_at_pattern_midpoint`,
  - `limit_at_pattern_boundary`.
- Add max wait bars and expire behavior controls.
- Ensure risk plan alignment to actual fill remains active.
- Add experiment output comparing:
  - fill rate,
  - trade count,
  - hit rate,
  - average R,
  - expectancy,
  - MFE/MAE if Task 175 exists,
  - average bars waited,
  - missed-trade count.
- Add docs explaining economic interpretation:
  - market confirmation = momentum continuation,
  - midpoint/boundary retest = imbalance rebalancing.

# Out of Scope

- Do not change default behavior silently unless owner explicitly approves.
- Do not implement optimizer that picks best entry mode automatically.
- No live trading or exchange behavior.

# Requirements

- CLI can run FVG backtest with each entry mode.
- Output metadata records selected entry mode and bars waited.
- Limit entry modes can produce `ENTRY_NOT_FILLED` SKIP diagnostics.
- Comparative report makes it clear whether bad performance is due to late market entry, no-fill retest entry, or weak post-fill follow-through.

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
- Existing default `MARKET_ON_CONFIRMATION_CLOSE` behavior remains unchanged unless a CLI/config argument explicitly selects another mode.
- Retest/limit modes are research/backtest-only simulations and must emit SKIP diagnostics when not filled.
- Comparative output is explanatory metadata; it must not optimize or automatically select a profitable mode.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Append a concise progress/completion note to `PROJECT_HISTORY.md`.
- [x] Update `BACKLOG.md` to mark this task created, completed, blocked, reprioritized, or split.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

Completion notes:
- Added FVG-only CLI controls for market confirmation, next-open, entry-reference, midpoint, boundary, and custom-price entry simulations.
- Added max-wait and expiry controls, preserved the existing default, and kept all behavior offline/backtest-only.
- Added JSON diagnostics for selected entry mode and optional mode comparison with fill rate, missed-trade count, trade quality, and Task 175 MFE/MAE aggregates.
- Updated README, API contract notes, and the FVG strategy specification with economic interpretation.
- Next task: Task 177 `PATTERN_SPECIFIC_ENTRY_EXIT_POLICY_MATRIX`.

# Acceptance Criteria

- FVG entry-mode CLI argument works.
- Tests show market mode uses confirmation close, midpoint mode requires touch, boundary mode requires touch.
- Risk plan is aligned to actual fill for all modes.
- Output metadata records entry mode, fill source, and bars waited.
- No live trading behavior added.

# Required Tests

## Unit Tests

- Entry mode parsing and action builder behavior.
- FVG event proxy with midpoint/boundary fields.
- No-fill behavior.

## Integration Tests

- CLI test for each FVG entry mode over deterministic candles.
- Compare JSON output contains entry mode and fill diagnostics.

## Contract Tests

- Update README/API docs for entry-mode metadata.

## Safety Tests

- Confirm no exchange endpoint imports or API key handling changes.

# Verification

Default:

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/patterns/test_fair_value_gap.py
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
