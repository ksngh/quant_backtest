# Task 281 Owner Window 0520 High-Activity Target Return Search

Status: `PROMISING_RESEARCH_ONLY`

## Iteration State

- Batch: `batch1`
- Planned candidates in batch: `5`
- Persisted runs in this invocation: `5`
- Task 281 run IDs: `890, 891, 892, 893, 894`
- Primary window: `2026-05-20T00:00:00Z` through latest locally available BTCUSDT 1m candle.
- Actual local end note: see DB actual_end_time per run; local candle load ended at 2026-05-28T08:26:00Z in this dataset.
- Loop policy: continue inside Task 281 if primary gates fail; this batch found a passing research-only candidate.

## Strategy Thesis

- Core sleeve: bearish failed range-break/fade after medium-term downside pressure. It enters SHORT only from completed candles when the current candle sweeps above the prior 60-bar high but closes back below it, while 240-minute return is negative and the entry has enough remaining candles for the 480-bar hold geometry.
- Safety/consistency filters: skip the incomplete endpoint and skip Sunday 12:00-18:00 UTC core entries, which were isolated as a poor-liquidity reversal pocket in this fixed research window.
- Activity scout sleeve: low-notional deterministic trend/momentum scout using prior 60-minute, prior 720-minute, and prior 15-minute returns. It recycles capital with fixed target/stop/time exits and exits immediately when a core signal appears so the core can enter on the same completed candle.
- Sizing: core uses fixed notional equal to configured cash fraction of starting quote cash; scout uses a small fixed notional fraction. No leverage, futures, borrow, funding, liquidation, live orders, or exchange private endpoints are used.

## Candidate Runs

| Variant | Family | Run | Return | Trips | Active Days | Core | Scout | Preempt | Gross | Cost | Cost/Gross | Top1 | Top3 | Max DD | Status | Reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| T281_B1_ACTIVITY_SCOUT_H120_T150_S75_FF002 | ACTIVITY_TREND_SCOUT | 890 | -0.5876pct | 88 | 9 | 0 | 88 | 0 | 668.57 | 6,544.79 | 9.7893 | - | - | -0.5932pct | REJECTED_RESEARCH_ONLY | return_lt_3pct,cost_to_gross_gt_0p60,largest_winner_gt_0p40,top_three_winners_gt_0p70 |
| T281_B1_FILTERED_CORE_RANGE_FADE_CF100 | LIQUIDITY_RANGE_FADE_CORE | 891 | +6.1706pct | 10 | 6 | 10 | 0 | 0 | 98,535.85 | 36,829.54 | 0.3738 | 0.2179 | 0.5312 | -1.2827pct | REJECTED_RESEARCH_ONLY | round_trips_lt_50 |
| T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002 | PRIORITY_CORE_ACTIVITY_SCOUT | 892 | +5.7295pct | 62 | 9 | 10 | 52 | 7 | 97,963.67 | 40,668.89 | 0.4151 | 0.2248 | 0.5483 | -1.3248pct | PROMISING_RESEARCH_ONLY | all_task281_primary_gates_passed |
| T281_B1_PRIORITY_ENSEMBLE_H90_T90_S50_CF100_FF002 | PRIORITY_CORE_ACTIVITY_SCOUT | 893 | +5.6032pct | 83 | 9 | 10 | 73 | 7 | 98,288.81 | 42,256.86 | 0.4299 | 0.2262 | 0.5517 | -1.3449pct | PROMISING_RESEARCH_ONLY | all_task281_primary_gates_passed |
| T281_B1_PRIORITY_ENSEMBLE_H60_T70_S40_CF100_FF002 | PRIORITY_CORE_ACTIVITY_SCOUT | 894 | +5.4030pct | 108 | 9 | 10 | 98 | 6 | 98,144.20 | 44,114.30 | 0.4495 | 0.2294 | 0.5595 | -1.3948pct | PROMISING_RESEARCH_ONLY | all_task281_primary_gates_passed |

## Best Candidate

- Best passing run: `892` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Net total return: `+5.7295pct`.
- Completed round trips: `62`.
- Active trade days: `9`.
- Final equity: `1,057,294.78`.
- Closed-trade net PnL after all costs: `57,294.78`.
- Open-position contribution at final equity: `0.00`.
- Result status: `PROMISING_RESEARCH_ONLY`.

## Gate Check

| Gate | Required | Best | Status |
| --- | ---: | ---: | --- |
| Total return | >= +3.0000pct | +5.7295pct | `PASS` |
| Completed round trips | >= 50 | 62 | `PASS` |
| Active trade days | >= 5 | 9 | `PASS` |
| Cost/gross PnL | <= 0.60 | 0.4151 | `PASS` |
| Largest winner/net | <= 0.40 | 0.2248 | `PASS` |
| Top three winners/net | <= 0.70 | 0.5483 | `PASS` |
| Cost readback | fee/spread/slippage > 0 | True | `PASS` |

## Cost Accounting

- Cost profile: `conservative_crypto_1m`.
- Fee cost: `21,970.38`.
- Spread cost: `6,591.12`.
- Slippage cost: `12,107.39`.
- Total cost: `40,668.89`.
- Cost verification: `PASS`.
- DB readback verification: `PASS`.

## Fee Audit Addendum

- Audit target: run `892`.
- Audit source: persisted trade metadata `cost_breakdown` plus summary `cost_summary`.
- Cost profile settings read from DB summary metadata:
  - liquidity role: `TAKER`
  - taker fee: `10.0` bps per execution
  - spread: `3.0` bps per execution
  - configured slippage: `5.0` bps plus `0.1 * candle_range_bps`
  - zero-cost assumption: `False`
- Loaded executions: `124`.
- Completed round trips: `62`.
- Total executed notional: `21,970,384.07`.
- Fee formula check: `sum(gross_notional * fee_bps / 10000) = 21,970.38`; stored fee sum is `21,970.38`.
- Spread formula check: `sum(gross_notional * spread_bps / 10000) = 6,591.12`; stored spread sum is `6,591.12`.
- Slippage formula check: stored slippage sum is `12,107.39`; effective slippage average is `5.5108` bps.
- Stored total cost: `40,668.89`; recomputed total cost from fee/spread/slippage is `40,668.89`.
- Effective one-way total cost: `18.5108` bps; approximate round-trip cost: `37.0216` bps.
- Layer notional split:
  - scout: `104` executions, `2,080,880.18` notional, `2,080.88` fee, `3,849.19` total cost.
  - core: `20` executions, `19,889,503.89` notional, `19,889.50` fee, `36,819.70` total cost.
- Mismatch count between stored costs and formula recomputation: `0`.

## Research Risk

- This is `RESEARCH_ONLY` and fixed-window tuned. The Sunday/session filter and scout geometry were selected after inspecting the 2026-05-20+ owner window, so the result is data-snooping-prone until a future locked OOS/walk-forward task validates it unchanged.
- The strategy remains offline-only and does not imply live readiness.
