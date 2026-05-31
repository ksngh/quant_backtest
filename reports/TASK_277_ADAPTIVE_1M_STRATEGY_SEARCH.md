# Task 277 Adaptive 1m Strategy Search

Date: 2026-05-29

Status: `RESEARCH_ONLY`

## Objective

Search for a deterministic offline BTCUSDT 1m strategy candidate that returns at least 5pct net on both fixed owner windows:

- Window A: `2026-05-20T00:00:00Z` onward
- Window B: `2026-05-25T00:00:00Z` onward

Target-qualification runs used:

- `--starting-cash 1000000`
- `--starting-cash-currency USDT`
- `--position-sizing-mode cash_fraction`
- `--position-sizing-value 0.10`
- `--cost-profile conservative_crypto_1m`

The search is exploratory. Repeatedly tuning against these exact windows is data-snooping prone, so no result from this task is validated for live or paper-trading promotion.

## Strategy Implemented

The new model added in this task is `SESSION_RANGE_LIQUIDITY_BREAKOUT_REVERSAL`.

Core idea:

1. Use only completed candles.
2. Build a prior rolling session/range from completed candles before the current signal candle.
3. Detect liquidity events around that prior range:
   - failed upside breakout, then short reversal;
   - failed downside breakout, then long reversal;
   - downside breakdown continuation for short-only variants.
4. Require configurable volume, candle body, range-width, and score gates.
5. Enter on the completed confirmation candle close.
6. Place stops beyond the relevant range boundary with an ATR buffer.
7. Place targets by fixed R multiple and optionally time-stop stale trades.
8. Route actions through the existing strategy engine so fees, spread, slippage, sizing, skips, trades, and equity are persisted.

The best SRLBR family member in this search was `T277_V017_SRLBR_BREAKDOWN_240_12R_HIGH_GATE`, but it still failed the target.

## Result

No candidate met the 5pct target on both windows.

Summary:

- Target candidate variants attempted: 18 (`T277_V001` through `T277_V018`)
- Completed persisted target-qualification runs: 34 (`115` through `148`)
- Zero-cost diagnostic runs: 2 (`149`, `150`)
- Winning target candidate: none
- Best Window A qualifying run: `T277_V005_LSR_MARKET_1R`, run `121`, `-0.0544pct`
- Best Window B qualifying run by total return: `T277_V017_SRLBR_BREAKDOWN_240_12R_HIGH_GATE`, run `146`, `+0.0222pct`
- Best combined candidate by average total return: `T277_V005_LSR_MARKET_1R`, runs `121`/`122`, average `-0.0666pct`, but Window B had only 2 trades and is diagnostic-quality.

Window B run `146` had positive final mark-to-market total return but negative net PnL metadata and an open ending short position, so it does not satisfy the target definition.

## Cost Verification

All qualifying target-window runs `115` through `148` were read back from the database and checked for non-zero realistic cost assumptions.

Verified fields:

- `zero_transaction_cost_assumption = false`
- `taker_fee_bps = 10.0`
- `spread_bps = 3.0`
- `slippage_bps = 5.0`
- `minimum_slippage_bps = 1.0`
- `volatility_slippage_multiplier = 0.1`
- for every run with trades, `total_cost`, `total_fee_cost`, `total_spread_cost`, and `total_slippage_cost` were positive.

Zero-cost diagnostic runs `149` and `150` correctly recorded `zero_transaction_cost_assumption = true` and `total_cost = 0.0`; they are excluded from target qualification.

## Saved Runs

| Variant | Family | Window A Run | Window A Return | Window A Trades | Window A Cost | Window B Run | Window B Return | Window B Trades | Window B Cost | Target Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| T277_V001_FVG_OWNER_DEFAULT | FAIR_VALUE_GAP | timed out | n/a | n/a | n/a | timed out | n/a | n/a | n/a | failed runtime/no persisted run |
| T277_V002_FVG_INVERSE_SIMPLE | FAIR_VALUE_GAP | 115 | -0.6283pct | 34 | 6233.57 | 116 | -0.1847pct | 10 | 1832.50 | failed return |
| T277_V003_OB_PREV_1R | ORDER_BLOCK | 117 | -9.5984pct | 507 | 91653.22 | 118 | -3.6465pct | 197 | 36765.42 | failed return/cost drag |
| T277_V004_OB_618_WAIT20 | ORDER_BLOCK | 119 | -6.3262pct | 354 | 62975.95 | 120 | -2.2817pct | 126 | 22918.80 | failed return/cost drag |
| T277_V005_LSR_MARKET_1R | LIQUIDITY_SWEEP_REVERSAL | 121 | -0.0544pct | 6 | 1193.32 | 122 | -0.0789pct | 2 | 382.78 | failed return/low B trades |
| T277_V006_LSR_LIMIT_15R | LIQUIDITY_SWEEP_REVERSAL | 123 | -0.0763pct | 2 | 381.03 | 124 | -0.0763pct | 2 | 381.03 | failed return/low trades |
| T277_V007_SRLBR_FAILED_BOTH_120_4R | SRLBR | 125 | -0.9303pct | 52 | 10331.37 | 126 | -0.5603pct | 24 | 4771.86 | failed return |
| T277_V008_SRLBR_SHORT_MIX_60_4R | SRLBR | 127 | -4.0363pct | 202 | 38281.83 | 128 | -1.4349pct | 78 | 14811.87 | failed return/cost drag |
| T277_V009_SRLBR_BREAKDOWN_60_4R | SRLBR | 129 | -3.2428pct | 170 | 32143.75 | 130 | -1.2102pct | 70 | 13282.08 | failed return/cost drag |
| T277_V010_SRLBR_SHORT_MIX_20_8R | SRLBR | 131 | -7.0223pct | 385 | 70784.70 | 132 | -2.4974pct | 155 | 29110.91 | failed return/cost drag |
| T277_V011_SRLBR_SHORT_MIX_120_8R | SRLBR | 133 | -2.9388pct | 152 | 28702.22 | 134 | -0.9894pct | 50 | 9437.74 | failed return |
| T277_V012_SRLBR_FAILED_SHORT_60_6R | SRLBR | 135 | -1.0515pct | 54 | 10506.00 | 136 | -0.3059pct | 12 | 2297.76 | failed return |
| T277_V013_SRLBR_FAILED_LONG_60_6R | SRLBR | 137 | -1.6158pct | 70 | 13640.72 | 138 | -0.8108pct | 32 | 6318.98 | failed return |
| T277_V014_SRLBR_FAILED_LONG_20_8R | SRLBR | 139 | -2.4352pct | 134 | 25539.41 | 140 | -1.2032pct | 56 | 10786.73 | failed return |
| T277_V015_SRLBR_FAILED_BOTH_20_8R | SRLBR | 141 | -3.9630pct | 220 | 41542.88 | 142 | -1.6973pct | 88 | 16774.44 | failed return |
| T277_V016_SRLBR_SHORT_MIX_60_8R_HIGH_GATE | SRLBR | 143 | -3.4194pct | 180 | 34448.88 | 144 | -1.3415pct | 74 | 14197.50 | failed return |
| T277_V017_SRLBR_BREAKDOWN_240_12R_HIGH_GATE | SRLBR | 145 | -0.7002pct | 43 | 8299.03 | 146 | +0.0222pct | 15 | 2847.43 | failed A/failed net PnL |
| T277_V018_SRLBR_FAILED_SHORT_240_12R_HIGH_GATE | SRLBR | 147 | -0.7447pct | 30 | 5803.14 | 148 | -0.0524pct | 2 | 386.84 | failed return/low B trades |

## Zero-Cost Diagnostic

| Variant | Window A Run | Window A Return | Window A Cost | Window B Run | Window B Return | Window B Cost | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| T277_D001_ZERO_COST_SRLBR_BREAKDOWN_240_12R | 149 | +0.1319pct | 0.00 | 150 | +0.3074pct | 0.00 | excluded diagnostic |

Even with fees, spread, and slippage removed, the best diagnostic variant did not approach 5pct on either window.

## Top Combined Variants

Ranked by average total return across Window A and Window B:

| Rank | Variant | Runs | Average Return | Minimum Window Return | Notes |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | T277_V005_LSR_MARKET_1R | 121/122 | -0.0666pct | -0.0789pct | least negative, but Window B had 2 trades |
| 2 | T277_V006_LSR_LIMIT_15R | 123/124 | -0.0763pct | -0.0763pct | only 2 trades per window |
| 3 | T277_V017_SRLBR_BREAKDOWN_240_12R_HIGH_GATE | 145/146 | -0.3390pct | -0.7002pct | best SRLBR; Window B positive mark-to-market but negative net PnL |
| 4 | T277_V018_SRLBR_FAILED_SHORT_240_12R_HIGH_GATE | 147/148 | -0.3985pct | -0.7447pct | low Window B trade count |
| 5 | T277_V002_FVG_INVERSE_SIMPLE | 115/116 | -0.4065pct | -0.6283pct | best completed FVG pair |

## Baseline Comparison

| Reference | Window | Result |
| --- | --- | --- |
| Task 276 run 114 | 2026-05-20+ | 0 fills, 0.0 net PnL, final equity unchanged at 666.67 effective USDT |
| Task 274 run 107 | Task 274 sweep | 14 trades, -1.79 net PnL on 666.67 effective USDT |
| Task 274 run 109 | Task 274 sweep | 2 trades, -0.34 net PnL on 666.67 effective USDT |
| Task 275 run 113 | Task 275 sweep | same comparable FVG local OB confluence family as run 109; still low trade count and negative |
| Buy and hold, Window A | 2026-05-20 to 2026-05-28 08:26 UTC | -4.5907pct |
| Buy and hold, Window B | 2026-05-25 to 2026-05-28 08:26 UTC | -4.9533pct |

Some Task 277 variants lost less than buy-and-hold, but none produced the required positive 5pct net return.

## Rejections

Primary rejection causes:

- Return below 5pct on at least one window.
- Net PnL below zero after transaction costs.
- Low trade count on some least-negative variants.
- Cost drag overwhelmed small gross edge on high-turnover variants.
- Some SRLBR variants ended with an open short; positive mark-to-market equity without positive net PnL was not accepted.
- `T277_V001_FVG_OWNER_DEFAULT` was recorded as a timed-out attempt and excluded from target qualification because no completed persisted run ID was created.

## Drawdown And Tail Risk

- Max drawdown was recorded in result metadata for persisted runs.
- High-turnover OB/SRLBR variants showed fee/spread/slippage drag large enough to dominate gross PnL.
- The best SRLBR Window B run had open short exposure at the dataset end, so the result is sensitive to endpoint mark-to-market.

## Conclusion

Task 277 did not find a target-qualified 5pct candidate on both owner windows.

The strongest conclusion is not that the model is deployable; it is that the tested 1m pattern families are dominated by realistic costs and do not have enough net edge on the fixed May 2026 windows. Any next search should first reduce turnover, lock untouched validation windows, and predeclare acceptance criteria before more tuning.
