# Goal

Define and execute a larger staged backtest matrix across `ORDER_BLOCK`, `FAIR_VALUE_GAP`, Order Block confluence, entry modes, volume filters, and available multi-timeframe settings.

# Source Requirement

Owner clarified after Task 274 creation:

```text
task 더 잡아줘 아니 경우의 수가 더 많잖아
```

Interpretation:

- Task 274 is too small and only covers a representative sweep.
- A broader matrix is needed to cover more meaningful combinations.
- The matrix should still be staged and bounded so runs are interpretable and not an unbounded brute-force search.

# Extracted Roles

- Owner role: Wants broader coverage of available strategy/filter/timeframe combinations.
- Supporting roles:
  - Matrix designer: Enumerate meaningful current-feature combinations.
  - Research runner: Execute batches with persistence enabled.
  - Backtest analyst: Compare results by family, filter, timeframe, entry mode, and cost behavior.
  - Status tracker: Record batch IDs, completed runs, blocked variants, and next batch.
- Forbidden roles:
  - Live trading or real exchange order execution.
  - Exchange order/account endpoint calls.
  - Strategy implementation changes.
  - Database schema changes.
  - New backfill implementation.
  - Dashboard/frontend changes.

# Context

Current available features relevant to this matrix:

- `ORDER_BLOCK`
  - default confirmation-close entry;
  - `limit_at_order_block_618_retracement`;
  - previous-candle 1R exit mode;
  - legacy `zone_structural_2r` mode;
  - optional entry volume filter;
  - optional MTF OB filter using completed resampled base candles;
  - available MTF strings include `15m`, `30m`, `1h`.
- `FAIR_VALUE_GAP`
  - owner default FVG v2 channel profile;
  - default close-volume filter;
  - standalone channel scan;
  - optional OB confluence;
  - local OB confluence source;
  - historical detector OB confluence source;
  - FVG entry modes/retest parameters where compatible.
- Costs
  - realistic default cost profile;
  - zero-cost diagnostic profile;
  - cost-aware entry filter currently optional and known to be too restrictive for current `ORDER_BLOCK` 1R in Task 273.

Known limitations:

- Current `ORDER_BLOCK` MTF filter uses resampled base candles, not DB-backed native 15m/30m/1h candles.
- Task 265 remains the separate DB-backed higher-timeframe backfill/context task.
- Task 272 remains the separate implementation task for default `ORDER_BLOCK` cost-aware RR guard.

# Scope

- Execute saved `quant-bitcoin-strategy-backtest` runs only.
- Use persistence enabled unless a diagnostic dry run is explicitly needed to avoid wasting saved run slots.
- Use the same base date/cash/sizing unless a batch explicitly documents a different comparison axis:

```bash
--start-time 2026-05-25T00:00:00Z
--starting-cash 1000000
--position-sizing-mode cash_fraction
--position-sizing-value 0.10
```

- Run in staged batches so results remain understandable.

# Proposed Matrix

## Batch A: ORDER_BLOCK Entry And Exit Families

- A1: default OB confirmation-close, previous-candle 1R.
- A2: default OB confirmation-close, `--ob-risk-exit-mode zone_structural_2r`.
- A3: OB 61.8% retest, wait 10.
- A4: OB 61.8% retest, wait 20.
- A5: OB 61.8% retest, wait 40.

## Batch B: ORDER_BLOCK MTF Variants

Apply to the best two Batch A variants:

- B1: `--enable-ob-mtf-filter --ob-mtf-timeframes 15m`
- B2: `--enable-ob-mtf-filter --ob-mtf-timeframes 30m`
- B3: `--enable-ob-mtf-filter --ob-mtf-timeframes 1h`
- B4: `--enable-ob-mtf-filter --ob-mtf-timeframes 15m,30m`
- B5: `--enable-ob-mtf-filter --ob-mtf-timeframes 15m,1h`
- B6: `--enable-ob-mtf-filter --ob-mtf-timeframes 30m,1h`
- B7: `--enable-ob-mtf-filter --ob-mtf-timeframes 15m,30m,1h`

## Batch C: ORDER_BLOCK Volume Variants

Apply to the best MTF/entry candidates:

- C1: volume ratio 1.25x.
- C2: volume ratio 1.5x.
- C3: volume ratio 2.0x.
- C4: volume ratio 2.5x.
- C5: volume ratio 3.0x.

## Batch D: ORDER_BLOCK Cost Diagnostics

Apply only to a small number of candidates:

- D1: realistic default cost profile.
- D2: `--cost-profile zero` diagnostic.
- D3: `--enable-cost-aware-entry-filter --min-net-reward-bps 0 --min-net-rr 0.4`
- D4: `--enable-cost-aware-entry-filter --min-net-reward-bps 0 --min-net-rr 0.6`

## Batch E: FAIR_VALUE_GAP Owner Profile Families

- E1: default owner FVG profile.
- E2: default owner FVG profile + `--fvg-require-order-block-confluence`.
- E3: default owner FVG profile + local OB confluence + `--fvg-order-block-confluence-mode entry_price_inside_ob`.
- E4: default owner FVG profile + local OB confluence + `--fvg-order-block-confluence-mode zone_overlap`.
- E5: default owner FVG profile + historical detector OB confluence.

## Batch F: FAIR_VALUE_GAP Channel/Volume Sensitivity

Apply to E1/E2 if runtime is acceptable:

- F1: default close volume ratio 2.0.
- F2: close volume ratio 1.5.
- F3: close volume ratio 2.5.
- F4: disable close-volume filter.
- F5: disable standalone channel scan.

## Batch G: Combined Best-Candidate Confirmation

After A-F, save a final small set:

- G1: best `ORDER_BLOCK` candidate by net PnL.
- G2: best `ORDER_BLOCK` candidate by drawdown/trade count balance.
- G3: best `FAIR_VALUE_GAP` candidate by net PnL.
- G4: best `FAIR_VALUE_GAP` candidate by trade count/filter balance.
- G5: zero-cost diagnostic version of the best realistic-cost candidate to isolate cost drag.

# Out of Scope

- Code changes.
- Test changes.
- New CLI options.
- New indicator implementations.
- New candle downloads/backfills.
- Native DB-backed 15m/30m/1h context implementation.
- Live trading.
- Real Binance order placement.

# Requirements

- Do not run all possible combinations blindly in one batch.
- Start with Batch A and Batch E unless the owner explicitly asks to skip straight to a full run.
- Record run IDs and summary metrics after each batch.
- Prefer saving successful runs.
- Stop a branch early when it produces zero fills or is clearly dominated by a less restrictive variant.
- Do not use live order/account endpoints.
- Do not add or modify code.

# Status Tracking

## Before Execution

- [x] Read `STATUS.md`.
- [x] Confirm the task matches the current phase and step.
- [x] Confirm the current active task is recorded or should be updated.
- [x] Confirm parallel work is allowed before starting any parallel tasks.
- [x] Record assumptions, blockers, or unclear status items before running commands.
- [x] Confirm selected commands use existing CLI options.
- [x] Decide which batch to run first.

## After Execution

- [x] Update `STATUS.md` if the phase, step, goal, active task, blocker, open question, or completion state changed.
- [x] Mark checklist items complete only when acceptance criteria and verification are satisfied.
- [x] Leave uncertain items open and document the uncertainty.
- [x] Confirm the next step is accurate or explicitly left undecided.

# Acceptance Criteria

- A staged matrix is defined.
- At least one batch is executed when assigned for execution.
- Saved run IDs and summary metrics are recorded.
- Zero-fill/dominated branches are identified and not expanded unnecessarily.
- No code changes are made.
- No live trading or exchange order endpoints are used.

# Required Tests

## Unit Tests

- Not applicable; this is a saved-run research matrix task.

## Integration Tests

- Execute selected `quant-bitcoin-strategy-backtest` commands with persistence enabled.

## Contract Tests

- Confirm successful outputs are parseable JSON and include `backtest_run_id`.

## Safety Tests

- Confirm commands use offline backtest CLI only.
- Confirm no live trading or exchange order/account endpoints are called.

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
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK ...
quant-bitcoin-strategy-backtest --pattern FAIR_VALUE_GAP ...
```

Exact batch commands and saved run IDs must be recorded after execution.

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

# Execution Results

Executed on 2026-05-28 with persistence enabled. Per this task's staged requirement, the initial execution covered Batch A and Batch E, while reusing already-saved Task 273 and Task 274 runs where they exactly matched matrix cells.

Common options:

```bash
--start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10
```

## Batch A: ORDER_BLOCK Entry And Exit Families

| Cell | Variant | Saved run | Trades | Gross PnL | Net PnL | Final equity | Total cost | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A1 | Default confirmation close, previous-candle 1R | 98 | 197 | 0.1814 | -24.3289 | 642.357 | n/a | Existing Task 273 reference |
| A2 | Default confirmation close, zone structural 2R | 110 | 214 | 0.2878 | -18.0363 | 648.7291 | 18.3241 | Saved in this task |
| A3 | 61.8 retest, wait 10 | 111 | 108 | 0.1089 | -12.9566 | 653.7101 | 13.0654 | Saved in this task |
| A4 | 61.8 retest, wait 20 | 102 | 126 | 0.0677 | -15.2115 | 651.455 | n/a | Existing Task 273 reference |
| A5 | 61.8 retest, wait 40 | 112 | 158 | 0.0569 | -19.1360 | 647.5306 | 19.1930 | Saved in this task |

Initial Batch A read:

- Wait 10 was the best saved non-MTF Batch A variant by net PnL in this staged pass.
- Wait 40 was dominated by wait 10 and wait 20 under the same date/cash profile.
- Zone structural 2R improved net PnL versus default run 98 but still remained materially cost-negative.

## Batch B Reference From Task 274

Task 274 executed the 61.8 wait-20 MTF branch that this matrix would use after Batch A:

| Cell | Variant | Saved run | Trades | Net PnL | Final equity | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| B1 | 61.8 wait20 + 15m MTF | 103 | 81 | -9.8838 | 656.7829 | Saved in Task 274 |
| B2 | 61.8 wait20 + 30m MTF | 105 | 20 | -2.5385 | 664.1282 | Saved in Task 274 |
| B3 | 61.8 wait20 + 1h MTF | 106 | 55 | -6.6448 | 660.0219 | Saved in Task 274 |
| B7 | 61.8 wait20 + 15m,30m,1h MTF | 107 | 14 | -1.7853 | 664.8814 | Saved in Task 274 |

Initial Batch B read:

- The stricter combined MTF branch reduced trade count and had the least negative OB net result among the executed OB variants.
- Remaining pairwise B4-B6 combinations were not expanded in this pass because B7 and B2 already reduced losses substantially and the task requires staged, not blind, expansion.

## Batch E: FAIR_VALUE_GAP Owner Profile Families

| Cell | Variant | Saved run | Trades | Gross PnL | Net PnL | Final equity | Total cost | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| E1 | FVG default owner profile | 108 | 8 | -0.0472 | -1.1014 | 665.5653 | 1.0542 | Saved in Task 274 |
| E2/E4 | FVG + local OB confluence, zone overlap | 109 | 2 | -0.0862 | -0.3401 | 666.3266 | 0.2539 | Saved in Task 274 |
| E3 | FVG + local OB confluence, entry price inside OB | 113 | 2 | -0.0862 | -0.3401 | 666.3266 | 0.2539 | Saved in this task |
| E5 | FVG + historical detector OB confluence | none | n/a | n/a | n/a | n/a | n/a | Timed out after 900.01s in Task 274 |

Initial Batch E read:

- Local OB confluence cut FVG trades from 8 to 2 and improved net PnL versus default, though still slightly negative.
- `entry_price_inside_ob` matched the zone-overlap result on this dataset.
- Historical detector mode is runtime-blocked for this profile/date range and should not be expanded until narrowed or optimized.

Commands saved in this task:

```bash
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --ob-risk-exit-mode zone_structural_2r
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --pattern-entry-mode limit_at_order_block_618_retracement --fvg-entry-max-wait-bars 10
quant-bitcoin-strategy-backtest --pattern ORDER_BLOCK --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --pattern-entry-mode limit_at_order_block_618_retracement --fvg-entry-max-wait-bars 40
quant-bitcoin-strategy-backtest --pattern FAIR_VALUE_GAP --start-time 2026-05-25T00:00:00Z --starting-cash 1000000 --position-sizing-mode cash_fraction --position-sizing-value 0.10 --fvg-require-order-block-confluence --fvg-order-block-confluence-mode entry_price_inside_ob
```

Summary:

- Task 275 acceptance criteria are satisfied: the staged matrix is defined, Batch A/E were executed or filled from exact saved references, run IDs and metrics are recorded, dominated branches are identified, and no code changes were made for this task.
- Recommended continuation is a new task for remaining Batch C/D/F/G only if the owner wants deeper sweeps after inspecting runs 103, 107, 109, and 113.
