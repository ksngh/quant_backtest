# Goal

Add optional Order Block volume and multi-timeframe filters, and make realistic transaction costs the default for Order Block backtests while preserving explicit overrides.

# Source Requirement

Owner wants to extend the `ORDER_BLOCK` strategy with several configurable filters:

1. Add volume options.
2. Make fees/costs default for Order Block backtests.
3. Add multi-timeframe Order Block confirmation.
4. Keep volume and multi-timeframe options opt-in so they only apply when explicitly enabled.

Owner also asked to clarify the current Order Block entry/exit model before implementation.

# Extracted Roles

- Owner role: Defines the desired Order Block research behavior and chooses which optional filters to enable during backtests.
- Supporting roles:
  - Strategy CLI/profile: Apply an Order Block default cost profile and expose explicit override controls.
  - Order Block detector/config: Expose configurable volume thresholds without changing unrelated pattern defaults.
  - Action builder/backtest runner: Apply optional entry-time volume and multi-timeframe gates before Order Block entries.
  - Market data/context role: Provide completed higher-timeframe candles or recorded MTF context when available.
  - Tests: Verify default cost behavior, opt-in filter behavior, metadata, and no-lookahead constraints.
- Forbidden roles:
  - Live trading or real order execution.
  - Exchange order/account endpoint calls.
  - Frontend/dashboard work unless a later task explicitly assigns it.
  - Broad redesign of the pattern strategy framework.

# Context

Current `ORDER_BLOCK` behavior:

- Default entry mode is `MARKET_ON_CONFIRMATION_CLOSE`.
- Retest entry modes already exist and can be selected explicitly, including:
  - `--pattern-entry-mode limit_at_order_block_618_retracement`
  - `--pattern-entry-mode limit_at_pattern_midpoint`
  - `--pattern-entry-mode limit_at_pattern_boundary`
- Current exit/risk model is structural stop plus R-multiple target:
  - LONG stop: Order Block zone low minus ATR buffer.
  - SHORT stop: Order Block zone high plus ATR buffer.
  - Default target: `2R`.
- Order Block detector already has internal volume thresholds:
  - `minimum_volume_ratio=1.5`
  - `weak_volume_ratio=1.3`
- Unlike `FAIR_VALUE_GAP`, `ORDER_BLOCK` does not currently receive an owner default cost profile; absent explicit cost settings, it is effectively a zero-cost run.

Task 265 exists for higher-timeframe `1h`/`4h` backfill and strategy context. This task may depend on Task 265 or should add only the minimum safe MTF context handling required for Order Block filters.

# Scope

- Add an Order Block-specific default transaction cost profile:
  - default: `conservative_crypto_1m`
  - explicit override preserved:
    - `--cost-profile zero`
    - any other supported cost profile
    - manual cost flags under existing conflict rules
- Add optional Order Block volume controls, default-off for new entry-time filters.
- Preserve existing Order Block detector defaults unless CLI options explicitly override them.
- Add optional multi-timeframe Order Block confirmation, default-off.
- Apply optional filters only to `ORDER_BLOCK` strategy runs.
- Record applied settings and pass/fail decisions in strategy/action metadata.
- Preserve the existing default Order Block entry and exit behavior unless the owner explicitly selects another entry mode.

# Out of Scope

- Live trading.
- Real Binance order placement.
- Frontend/dashboard changes.
- Database schema changes unless a later task explicitly requires persisted MTF context.
- Changing Fair Value Gap volume/cost behavior.
- Changing Order Block default entry from confirmation close to retest mode.
- Changing Order Block default target/stop semantics.
- Implementing Task 265 unless explicitly assigned.

# Requirements

- Cost default:
  - `quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK ...` should default to `--cost-profile conservative_crypto_1m` when no cost profile or manual cost flags are supplied.
  - Explicit `--cost-profile zero` must keep a true zero-cost run.
  - Metadata must show whether the cost profile was defaulted or explicitly supplied.
- Volume options:
  - Add CLI options for Order Block detector volume thresholds, for example:
    - `--ob-min-volume-ratio`
    - `--ob-weak-volume-ratio`
  - Add an opt-in entry/reaction volume filter, for example:
    - `--enable-ob-entry-volume-filter`
    - `--ob-entry-volume-window`
    - `--ob-min-entry-volume-ratio`
  - Default behavior must remain unchanged unless the opt-in entry-volume filter is enabled or detector thresholds are explicitly overridden.
- Multi-timeframe Order Block filter:
  - Add opt-in flag, for example:
    - `--enable-ob-mtf-filter`
  - Support configurable higher timeframes, for example:
    - `--ob-mtf-timeframes 15m,1h`
  - Require same-direction higher-timeframe OB confirmation when enabled.
  - Use only completed higher-timeframe candles available at or before the lower-timeframe decision timestamp.
  - Fail closed or skip with explicit metadata if MTF data is missing, depending on a documented config choice.
- Entry/exit behavior:
  - Keep current default entry:
    - `MARKET_ON_CONFIRMATION_CLOSE`.
  - Keep current supported retest entry modes.
  - Keep current structural stop plus default `2R` target.
- Safety:
  - No live order APIs.
  - No API keys.
  - Strategy/backtest code remains offline deterministic.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Confirm whether Task 265 higher-timeframe context is complete or whether this task must remain blocked/partial for MTF behavior.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `ORDER_BLOCK` runs default to realistic costs when no explicit cost configuration is supplied.
- `--cost-profile zero` works for `ORDER_BLOCK` and metadata reports zero cost.
- Existing `FAIR_VALUE_GAP` owner cost defaults are not regressed.
- Order Block detector volume thresholds can be overridden by CLI without changing unrelated patterns.
- Optional Order Block entry/reaction volume filter is default-off and blocks entries only when enabled.
- Optional MTF Order Block filter is default-off and blocks entries only when enabled.
- MTF filter uses only completed higher-timeframe candles at or before the decision timestamp.
- Metadata records cost defaulting, volume settings/decisions, and MTF settings/decisions.
- Existing Order Block default entry and exit semantics remain unchanged.
- No live trading or exchange order endpoint behavior is added.

# Required Tests

## Unit Tests

- Cost default builder applies `conservative_crypto_1m` for `ORDER_BLOCK` when no cost flags are supplied.
- Explicit `--cost-profile zero` overrides the Order Block default.
- Manual cost flags preserve existing conflict/override behavior.
- Order Block volume config builder preserves detector defaults when no OB volume args are supplied.
- Explicit OB volume threshold args update only the Order Block config.
- Entry-volume filter passes and blocks deterministic candles when enabled.
- Entry-volume filter returns no-op metadata when disabled.
- MTF filter passes for same-direction completed higher-timeframe OB.
- MTF filter blocks for missing/opposite-direction higher-timeframe OB when enabled.

## Integration Tests

- `ORDER_BLOCK` baseline run still emits actions with default `MARKET_ON_CONFIRMATION_CLOSE` entry semantics.
- `ORDER_BLOCK` with `--pattern-entry-mode limit_at_order_block_618_retracement` still uses 61.8 retest semantics.
- `ORDER_BLOCK` default run reports `conservative_crypto_1m` in summary metadata.
- `ORDER_BLOCK --cost-profile zero` reports zero cost metadata.
- Volume filter enabled changes trade eligibility and metadata.
- MTF filter enabled changes trade eligibility and metadata without lookahead.

## Contract Tests

- CLI help/metadata includes the new Order Block cost/volume/MTF settings.
- Saved or emitted execution metadata includes volume and MTF decision fields when filters are enabled.
- Existing `FAIR_VALUE_GAP` cost/profile metadata tests continue to pass.

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
pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/patterns/test_order_block.py -q
git diff --check
```

If MTF context code is touched, also run the relevant higher-timeframe/backfill tests added by Task 265 or this task.

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

# Completion Notes

- Completed (2026-05-28): `ORDER_BLOCK` now defaults to `conservative_crypto_1m` costs unless an explicit cost profile or manual cost flag is supplied.
- Added detector volume threshold CLI overrides:
  - `--ob-min-volume-ratio`
  - `--ob-weak-volume-ratio`
- Added opt-in entry volume filter:
  - `--enable-ob-entry-volume-filter`
  - `--ob-entry-volume-window`
  - `--ob-min-entry-volume-ratio`
- Added opt-in MTF OB filter:
  - `--enable-ob-mtf-filter`
  - `--ob-mtf-timeframes`
- MTF filter uses completed higher-timeframe candles resampled from the available base candles. Task 265 remains the follow-up if the owner wants separately backfilled higher-timeframe DB context.
- Targeted verification passed:
  - `pytest tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_action_builder.py tests/patterns/test_order_block.py -q`
  - `git diff --check`
