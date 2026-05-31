# Goal

Replace the slow FVG Order Block confluence check with a local entry-time Order Block filter that uses only the immediately previous candle and the current FVG entry/confirmation candle.

# Source Requirement

Owner clarified that the backtest should not repeatedly scan all visible candles to find historical Order Blocks. At the FVG buy/sell timing, the filter should compare the immediately previous candle with the current entry confirmation candle and decide whether that local two-candle structure is an Order Block.

Owner intent:

- Do not run full Order Block detection for every FVG entry candidate.
- At the exact FVG entry timing, check the previous candle and current candle only.
- LONG entries should require a local bullish Order Block structure.
- SHORT entries should require a local bearish Order Block structure.

# Extracted Roles

- Owner role: Define the local Order Block rule and inspect whether the faster entry filter matches the intended trading idea.
- Supporting roles:
  - FVG action builder: Apply the local two-candle OB gate before entry.
  - FVG v2/channel entry builder: Use the retest/confirmation candle and its immediately previous candle for the same local OB gate.
  - CLI/config: Expose the local rule clearly and avoid repeated full-history OB scans by default for this mode.
  - Tests: Prove the local rule is fast, same-direction, no-lookahead, and applied to LONG/SHORT entries.
- Forbidden roles:
  - Live trading or real order execution.
  - Exchange order/account endpoint usage.
  - Frontend/dashboard work.
  - Reworking the full Order Block detector beyond disabling it from this FVG entry-time path.

# Context

Task 266 added `--fvg-require-order-block-confluence`, but the implementation checks confluence by running Order Block detection over visible candles for each FVG candidate. That is functionally richer than the owner now wants and can make backtests slow.

The owner wants a simpler local rule:

```text
FVG entry candidate
-> previous completed candle + current entry confirmation candle
-> decide if that pair forms a same-direction Order Block
-> enter only if yes
```

# Scope

- Add or change the FVG Order Block filter so it can use a local two-candle rule.
- Make the local rule the preferred behavior for `--fvg-require-order-block-confluence` unless an explicit compatibility mode is kept for the older full-detector check.
- Apply the local rule to:
  - baseline FVG entries;
  - FVG v2/channel retest entries.
- Derive the current candle from the actual entry/confirmation candle:
  - baseline market/retest entry fill candle;
  - channel retest confirmation candle.
- Derive the previous candle as the immediately preceding completed candle by index/timestamp.
- Avoid full historical Order Block scanning in the local path.
- Emit clear metadata for pass/fail decisions.
- Keep Task 266 skip reason unless a more specific reason is added:
  - `FVG_ORDER_BLOCK_CONFLUENCE_MISSING`

# Out of Scope

- Live trading.
- Real Binance order placement.
- Dashboard rendering.
- Full Order Block detector redesign.
- Multi-timeframe Order Block confirmation.
- Machine learning or optimization.
- Any new database schema.

# Requirements

- The local rule must be deterministic and no-lookahead.
- The local rule must use only:
  - immediately previous candle;
  - current FVG entry/confirmation candle.
- LONG local bullish OB rule:
  - previous candle is bearish (`close < open`);
  - current candle is bullish (`close > open`);
  - current candle closes above a configured previous-candle reference, default expected rule: `current_close > previous_high`.
- SHORT local bearish OB rule:
  - previous candle is bullish (`close > open`);
  - current candle is bearish (`close < open`);
  - current candle closes below a configured previous-candle reference, default expected rule: `current_close < previous_low`.
- The local Order Block zone should be the previous candle range:
  - `local_ob_zone_low = previous_low`
  - `local_ob_zone_high = previous_high`
- If strict break of previous high/low is too restrictive during implementation, the task may add an explicit mode:
  - `break_previous_range`
  - `break_previous_body`
  - but the default must be documented and tested.
- Existing `--fvg-require-order-block-confluence` should no longer trigger repeated full-history Order Block detection in the default path.
- If backwards compatibility is kept, it must be explicit, for example:
  - `--fvg-order-block-confluence-source local_entry_candles`
  - `--fvg-order-block-confluence-source historical_detector`
  - default: `local_entry_candles`
- Metadata should include:
  - `schema_version`;
  - filter enabled;
  - source/mode, expected default `local_entry_candles`;
  - position side;
  - previous candle timestamp/index/open/high/low/close;
  - current candle timestamp/index/open/high/low/close;
  - required OB direction;
  - local OB pass/fail;
  - local OB zone low/high;
  - failure reason.
- Failure reasons should distinguish:
  - previous candle missing;
  - current candle missing;
  - previous candle not opposing side;
  - current candle not confirming side;
  - break condition not met.
- Tests must prove no call to `detect_order_blocks()` is made in the default local path.

# Status Tracking

## Before Implementation

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before coding.
- [x] Read Task 266 implementation before changing the FVG OB filter.

## After Implementation

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- `--fvg-require-order-block-confluence` can run using the local two-candle OB rule.
- Default local rule does not run full historical `detect_order_blocks()` for every FVG entry candidate.
- LONG entries pass only when the previous/current candle pair forms a bullish local OB.
- SHORT entries pass only when the previous/current candle pair forms a bearish local OB.
- Missing or non-confirming candle pairs skip with `FVG_ORDER_BLOCK_CONFLUENCE_MISSING` and useful metadata.
- Baseline FVG and FVG v2/channel paths both use the local rule.
- Existing default behavior remains unchanged when `--fvg-require-order-block-confluence` is not supplied.
- No live trading or exchange order endpoint behavior is added.

# Required Tests

## Unit Tests

- Local bullish OB passes for LONG:
  - previous bearish candle;
  - current bullish candle;
  - current close breaks the required previous-candle reference.
- Local bearish OB passes for SHORT:
  - previous bullish candle;
  - current bearish candle;
  - current close breaks the required previous-candle reference.
- LONG fails when previous candle is not bearish.
- LONG fails when current candle is not bullish.
- LONG fails when break condition is not met.
- SHORT fails when previous candle is not bullish.
- SHORT fails when current candle is not bearish.
- SHORT fails when break condition is not met.
- Missing previous/current candle fails closed.

## Integration Tests

- Baseline FVG entry is skipped when local OB fails.
- Baseline FVG entry is allowed when local OB passes.
- FVG v2/channel entry is skipped when local OB fails.
- FVG v2/channel entry is allowed when local OB passes.
- Monkeypatch `detect_order_blocks()` to raise and confirm default local mode still passes/fails without calling it.

## Contract Tests

- CLI metadata records the local source/mode and default behavior.
- Saved action metadata contains local previous/current candle details and pass/fail reason.

## Safety Tests

- No real exchange order/account endpoint calls.
- No API keys required.
- Strategy/backtest code remains offline deterministic.

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

- Completed (2026-05-28): Default `--fvg-require-order-block-confluence` now uses the local previous/current entry-candle OB rule instead of calling `detect_order_blocks()`.
- Compatibility path remains explicit via `--fvg-order-block-confluence-source historical_detector`.
- Targeted verification passed:
  - `pytest tests/backtesting/test_pattern_action_builder.py tests/backtesting/test_pattern_postgres_runner_cli.py -q`
