# Goal

Change the Order Block risk/exit model so stop and take-profit are derived from the immediately previous candle and the current entry/confirmation candle.

# Source Requirement

Owner reported that Order Block exits look wrong and clarified the intended stop/take-profit logic:

- For SHORT entries:
  - stop-loss should be the immediately previous candle high;
  - take-profit distance should equal the distance from previous candle high to current candle close;
  - take-profit price should be current candle close minus that same distance.
- For LONG entries:
  - stop-loss should be the immediately previous candle low;
  - take-profit distance should equal the distance from current candle close to previous candle low;
  - take-profit price should be current candle close plus that same distance.

In formula form:

```text
LONG:
  entry = current_close
  stop = previous_low
  risk = entry - previous_low
  target = entry + risk

SHORT:
  entry = current_close
  stop = previous_high
  risk = previous_high - entry
  target = entry - risk
```

# Extracted Roles

- Owner role: Defines the intended Order Block stop/take-profit contract.
- Supporting roles:
  - Risk/exit planner: Build stop and target prices from previous/current candle structure.
  - Pattern action builder: Align filled entry risk plan to the actual entry/confirmation close when needed.
  - Strategy runner: Pass enough previous/current candle context to compute deterministic no-lookahead risk.
  - Tests: Verify LONG/SHORT stop/target formulas, realized PnL reflection, metadata, and invalid cases.
- Forbidden roles:
  - Live trading or real order execution.
  - Exchange order/account endpoint calls.
  - Frontend/dashboard work unless separately assigned.
  - Changing unrelated FVG channel stop/target behavior.
  - Changing position sizing, cost, or cash denomination semantics unless needed to preserve the risk contract.

# Context

Current `ORDER_BLOCK` behavior after Task 270:

- Default entry mode remains `MARKET_ON_CONFIRMATION_CLOSE`.
- Optional retest entry modes remain supported, including `LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT`.
- Current risk model is Order Block zone structural stop plus default R-multiple target:
  - LONG stop: OB zone low minus ATR buffer.
  - SHORT stop: OB zone high plus ATR buffer.
  - Default target: `2R`.
- Owner now wants an entry-candle-relative model:
  - previous candle low/high defines stop;
  - current entry/confirmation close defines entry;
  - target is symmetric 1R from entry using that previous-candle stop distance.

This task should clarify whether the new model applies to:

- all `ORDER_BLOCK` entries, including retest entries;
- only `MARKET_ON_CONFIRMATION_CLOSE` entries;
- or an opt-in Order Block stop/target mode.

Default assumption for implementation unless owner clarifies otherwise:

- Add an explicit Order Block risk mode and make it the owner/default `ORDER_BLOCK` mode while preserving a compatibility option for the existing zone/2R model.

# Scope

- Add or update Order Block stop/target calculation so previous/current candle structure can drive exits.
- Apply the formula:
  - LONG stop = previous candle low.
  - LONG target = current close + (current close - previous low).
  - SHORT stop = previous candle high.
  - SHORT target = current close - (previous high - current close).
- Use only completed candles at or before the entry/confirmation decision.
- Fail closed with explicit skip metadata if:
  - previous candle is missing;
  - current candle is missing;
  - computed risk is zero or negative;
  - stop/target cannot be computed.
- Preserve exit/PnL accounting in the existing strategy engine; do not bypass normal `EXIT_LONG` / `EXIT_SHORT` actions.
- Add metadata describing:
  - previous candle timestamp/high/low/close;
  - current candle timestamp/close;
  - stop source;
  - target source;
  - risk distance;
  - target distance;
  - selected Order Block risk mode.

# Out of Scope

- Live trading.
- Real Binance order placement.
- Dashboard visualization.
- Database schema changes unless a later task explicitly requires persisted fields beyond existing metadata.
- Changing FVG v2 channel pre-retest stop behavior.
- Changing Task 270 volume/MTF filter behavior.
- Changing transaction cost defaults.
- Adding new entry signals.

# Requirements

- LONG formula:
  - `entry_price = current close` for confirmation-close entries.
  - `stop_price = previous low`.
  - `risk_per_unit = entry_price - stop_price`.
  - `target_price = entry_price + risk_per_unit`.
- SHORT formula:
  - `entry_price = current close` for confirmation-close entries.
  - `stop_price = previous high`.
  - `risk_per_unit = stop_price - entry_price`.
  - `target_price = entry_price - risk_per_unit`.
- For non-confirmation entry modes, implementation must either:
  - adapt the formula to the actual filled entry price while still using previous candle stop; or
  - explicitly restrict this mode to confirmation-close entries and skip/fallback otherwise with metadata.
- Realized exit PnL must be reflected through existing execution fields:
  - `executions[].gross_pnl`;
  - `executions[].net_pnl`;
  - `summary.metadata.gross_pnl`;
  - `summary.metadata.net_pnl`.
- The strategy engine should not be modified unless a reproducible PnL aggregation bug is found.
- No live exchange APIs or credentials.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read current Order Block risk plan and pattern action builder code.
- [x] Decide whether the mode is default-on for `ORDER_BLOCK` or explicit opt-in, and document the decision in metadata/tests.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

## Completion Notes

- Implemented `ORDER_BLOCK` risk/exit mode `PREVIOUS_CANDLE_1R` as the default CLI mode.
- Preserved the previous zone/structural mode through `--ob-risk-exit-mode zone_structural_2r`.
- Applied the new previous/current candle formula only to `MARKET_ON_CONFIRMATION_CLOSE`; unsupported entry modes fall back to the existing risk plan with explicit metadata.
- Added fail-closed skip metadata for missing candle context and non-positive LONG/SHORT risk.
- Added top-level strategy-engine summary metadata fields `gross_pnl` and `net_pnl` so profitable exits are directly visible in `summary.metadata`.

## Verification Results

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/patterns/test_order_block.py -q
# 167 passed

pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_pattern_strategy_backtest.py -q
# 62 passed

git diff --check
# passed
```

# Acceptance Criteria

- LONG Order Block confirmation-close entry uses previous candle low as stop.
- LONG target is exactly one risk distance above current close.
- SHORT Order Block confirmation-close entry uses previous candle high as stop.
- SHORT target is exactly one risk distance below current close.
- Invalid or missing previous/current candle cases skip or fail closed with explicit metadata.
- Exit actions still flow through the existing strategy engine and realized profit/loss fields.
- Existing Order Block volume/MTF filters remain unchanged.
- Existing FVG behavior is not regressed.
- No live trading or exchange order endpoint behavior is added.

# Required Tests

## Unit Tests

- LONG previous/current candle risk plan computes:
  - stop = previous low;
  - target = current close + risk.
- SHORT previous/current candle risk plan computes:
  - stop = previous high;
  - target = current close - risk.
- LONG invalid when previous low is greater than or equal to entry close.
- SHORT invalid when previous high is less than or equal to entry close.
- Missing previous candle fails closed with metadata.
- Non-confirmation entry mode behavior is explicitly tested according to the chosen contract.

## Integration Tests

- `ORDER_BLOCK` LONG entry emits an exit at the new target when target is reached.
- `ORDER_BLOCK` SHORT entry emits an exit at the new target when target is reached.
- `executions[].gross_pnl` is positive for profitable LONG and SHORT exits.
- `summary.metadata.gross_pnl` includes profitable exits.
- Existing `--pattern-entry-mode limit_at_order_block_618_retracement` behavior is either preserved or explicitly documented/tested under the new mode contract.

## Contract Tests

- CLI/config metadata records the selected Order Block risk/exit mode.
- Action metadata records previous/current candle risk source fields.
- Existing Task 270 cost/volume/MTF metadata still appears when enabled.

## Safety Tests

- No real exchange order/account endpoint calls.
- No API keys or `.env` files added.
- Backtests remain offline deterministic.

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

Default targeted verification:

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/patterns/test_order_block.py -q
git diff --check
```

If strategy engine PnL aggregation is touched, also run:

```bash
pytest tests/backtesting/test_strategy_engine.py tests/backtesting/test_pattern_strategy_backtest.py -q
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
