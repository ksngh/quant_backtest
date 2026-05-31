# Goal

Add an explicit FVG Order Block confluence entry filter so Fair Value Gap LONG/SHORT entry candidates can enter only when the same-direction Order Block condition is present.

# Source Requirement

Owner clarified that this is not a standalone Order Block strategy. The desired behavior is:

- FVG still creates the LONG/SHORT signal candidate.
- A LONG FVG candidate may enter only if it has bullish Order Block confluence.
- A SHORT FVG candidate may enter only if it has bearish Order Block confluence.
- If the FVG signal is not also an Order Block confluence signal, the backtest must skip the entry candidate.

# Extracted Roles

- Owner role: Define the research rule and inspect whether FVG entries improve when same-direction Order Block confluence is required.
- Supporting roles:
  - FVG detector/action builder: Produce the original FVG candidate and apply the optional confluence gate before entry.
  - Order Block detector/helper: Identify completed-candle bullish/bearish Order Block zones available without lookahead.
  - Backtest runner/CLI: Expose explicit configuration, record metadata, and preserve reproducible behavior.
  - Tests: Cover pass/fail, direction matching, zone matching, and no-lookahead behavior.
- Forbidden roles:
  - Live trading or real order execution.
  - Frontend/dashboard changes unless a later task explicitly assigns visualization work.
  - Redesigning the base strategy/backtest result contracts beyond the metadata needed for this filter.

# Context

Existing work already includes Fair Value Gap strategy/backtest flows, FVG v2 channel entry logic, volume entry filters, stop/target behavior, and Order Block-related detection code. This task must add a confluence requirement to FVG entry candidates without replacing FVG with a separate Order Block strategy.

The confluence filter must be deterministic and must use only candles completed at or before the FVG entry decision point.

# Scope

- Add an explicit FVG Order Block confluence filter for strategy backtests.
- Apply the filter to FVG entry candidates before simulated entry:
  - baseline FVG candidates where the current action builder supports filtering;
  - FVG v2/channel candidates in the current owner workflow.
- Require same-direction matching:
  - effective FVG LONG requires bullish Order Block confluence;
  - effective FVG SHORT requires bearish Order Block confluence.
- Define and implement deterministic zone matching using existing FVG and Order Block metadata when available.
- Add CLI/configuration flags for the filter.
- Add skip/pass metadata so saved runs can explain why an FVG candidate entered or was skipped.
- Add focused tests for the new behavior.

# Out of Scope

- Live trading.
- Real Binance order placement.
- Order/account endpoint calls.
- Frontend overlay or dashboard marker rendering.
- Machine learning or optimization.
- Redesigning Order Block definitions beyond what is needed for this FVG confluence filter.
- Using future candles after the FVG entry decision point.
- Replacing the FVG strategy with a standalone Order Block strategy.

# Requirements

- Add an explicit enable flag, expected name:
  - `--fvg-require-order-block-confluence`
- Add confluence configuration where useful:
  - `--fvg-order-block-confluence-lookback-bars`
  - `--fvg-order-block-confluence-mode`
  - optional fresh/unmitigated requirement if existing Order Block state supports it.
- The default must remain clearly documented in CLI metadata. If the implementation changes owner-profile defaults, that must be explicit in metadata and tests.
- Same-direction matching is mandatory:
  - FVG LONG + bullish OB passes only when zone/timing criteria pass.
  - FVG SHORT + bearish OB passes only when zone/timing criteria pass.
  - Opposite-direction OB must not pass.
- Zone matching must be deterministic. Preferred modes:
  - `zone_overlap`: FVG zone and OB zone overlap by a positive price interval.
  - `entry_price_inside_ob`: FVG entry/reference price is inside the OB zone.
  - `fvg_midpoint_inside_ob`: FVG midpoint is inside the OB zone.
- The filter must not look ahead:
  - only completed candles and Order Block zones known at or before the FVG entry decision may be used;
  - future OB zones must not validate an earlier FVG entry.
- If enabled and no valid confluence exists, the action must be skipped with a clear reason, expected name:
  - `FVG_ORDER_BLOCK_CONFLUENCE_MISSING`
- Metadata should include:
  - filter enabled/pass state;
  - FVG effective side;
  - FVG zone/reference price used;
  - matched Order Block direction;
  - matched Order Block zone;
  - confluence mode;
  - lookback bars;
  - overlap/containment result;
  - no-lookahead decision timestamp or candle index where available.
- Preserve all current safety boundaries:
  - no exchange order calls;
  - no API keys;
  - no live execution behavior.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read relevant FVG and Order Block source/tests before changing code.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `quant-bitcoin-strategy-backtest` exposes an explicit way to require FVG Order Block confluence.
- When the filter is disabled, existing FVG behavior is preserved.
- When the filter is enabled:
  - same-direction valid OB confluence allows the FVG entry candidate;
  - missing OB confluence skips the FVG entry candidate;
  - opposite-direction OB confluence skips the FVG entry candidate;
  - non-overlapping or otherwise invalid zone match skips the FVG entry candidate;
  - future-only OB data cannot validate a prior FVG entry.
- Skip/pass metadata is visible in strategy/backtest outputs and saved-run metadata where those paths already store pattern metadata.
- Tests cover LONG and SHORT sides.
- No live trading behavior or exchange order endpoint usage is introduced.

# Required Tests

## Unit Tests

- Add/extend FVG Order Block confluence helper tests:
  - bullish OB validates LONG FVG when zones match;
  - bearish OB validates SHORT FVG when zones match;
  - bullish OB does not validate SHORT FVG;
  - bearish OB does not validate LONG FVG;
  - missing OB fails when the filter is enabled;
  - non-overlapping zones fail in `zone_overlap` mode;
  - future OB zones are ignored.

## Integration Tests

- Add/extend pattern action builder or strategy-backtest tests so:
  - enabled filter emits `FVG_ORDER_BLOCK_CONFLUENCE_MISSING` when no match exists;
  - enabled filter allows an entry when a same-direction match exists;
  - disabled filter preserves existing FVG entries.

## Contract Tests

- Confirm CLI/config values are reflected in run metadata.
- Confirm metadata keys are stable enough for saved-run inspection.

## Safety Tests

- Confirm no real exchange order/account endpoint calls are added.
- Confirm strategy code does not require API keys.

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
pytest tests/patterns/test_fair_value_gap.py tests/patterns/test_order_block.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_detection_optimization.py -q
git diff --check
```

If any listed test file does not exist in the current tree, replace it with the closest existing test module that covers the same role and document the substitution in the completion summary.

Completed verification:

```bash
pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q
pytest tests/patterns/test_fair_value_gap.py tests/patterns/test_order_block.py tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py tests/backtesting/test_pattern_detection_optimization.py -q
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
