# Task 283 Principle-First BTC Microstructure Strategy Development

Status: `TARGET_PASSED_RESEARCH_ONLY`

## I. Bitcoin Market Principles First

- Trend continuation: BTC can keep moving after directional pressure because momentum traders, stop cascades, and cross-session participation reinforce the move. Observable factors are prior returns, EMA slope, body/range, volume expansion, and completed 15m/1h trend context.
- Mean reversion after forced movement: sharp stop-driven candles can revert when wick rejection, close-back-inside, volume spike, and volatility contraction show exhaustion. The main failure mode is a true trend/liquidation cascade.
- Volatility clustering/compression: compressed range can lead to expansion; high-volatility regimes need wider stops and stricter cost gates.
- Liquidity sweep/stop hunting: prior highs/lows and session ranges concentrate stops; a sweep plus reclaim can reverse, while confirmed displacement can continue.
- Market structure change: swing/range breaks matter only when followed by displacement or successful reclaim/retest. Over-filtering can destroy sample size.
- Session/time effects: BTC is 24/7, but Asia/Europe/US liquidity and weekend pockets behave differently. Session filters are diagnostics, not proof of edge.
- Volume confirmation: Binance candle volume is only a proxy, but volume ratio helps separate participation from low-volume drift.

## II. Factor Candidate List

| Factor | Rationale | Formula | Direction | Risk |
| --- | --- | --- | --- | --- |
| Multi-horizon return | Momentum/cascade pressure | close[t-1]/close[t-n-1]-1 | trend continuation or exhaustion context | can lag reversals |
| ATR/range percentile | volatility clustering | TR and rolling percentile | wider stops and breakout filters | noisy in gaps |
| Sweep/reclaim flags | stop cluster behavior | high > prior high and close back inside, or low < prior low and close back inside | fade failed break | real breakout failure |
| Wick/body/CLV | rejection versus displacement | wick/range, body/range, close location | reversal or breakout quality | candle-only proxy |
| Volume ratio | participation proxy | current volume / prior rolling mean | confirms flow or exhaustion | exchange-volume noise |
| 15m/1h trend proxy | MTF alignment | prior 15/60m returns | trend pullback filter | coarse from 1m data |
| Session tag | liquidity regime | UTC hour bucket | filter/trap behavior | regime shifts |

## III. Strategy Candidate List

| Priority | Candidate | Family | Thesis |
| ---: | --- | --- | --- |
| 1 | `T283_B1_LSR_V2_RECLAIM_R18` | `LIQUIDITY_SWEEP_REVERSAL_V2` | Stops cluster near recent swing/session highs and lows; a sweep that closes back inside with rejection can reverse after forced flow exhausts. |
| 2 | `T283_B1_VCB_COMP60_BODY35_R20` | `VOLATILITY_COMPRESSION_BREAKOUT` | BTC volatility clusters; low realized range followed by body/volume displacement can continue as breakout traders and stops reinforce direction. |
| 3 | `T283_B1_MTF_PULLBACK_15M_1H_R16` | `MTF_TREND_PULLBACK_CONTINUATION` | When completed 15m and 1h trend pressure agree, 1m pullbacks into short EMAs can resume as momentum and forced exits reinforce direction. |
| 4 | `T283_B1_VOLUME_CLIMAX_REVERT_R12` | `VOLUME_CLIMAX_MEAN_REVERSION` | Liquidation-like candles can exhaust when range, volume, wick rejection, and close-location reversal align. |
| 5 | `T283_B1_SESSION_RANGE_TRAP_R15` | `SESSION_RANGE_LIQUIDITY_TRAP` | Session highs and lows attract breakout orders; a failed break/reclaim can mean-revert, while confirmed breaks may continue. |
| 6 | `T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002` | `PRINCIPLE_FIRST_PRIORITY_ENSEMBLE` | A liquidity-sweep reversal core should take full-notional priority when failed range breaks occur inside a bearish regime, while a tiny MTF activity sleeve supplies enough turnover without dominating risk. |
| 7 | `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `PRINCIPLE_FIRST_PRIORITY_ENSEMBLE` | Same liquidity-sweep reversal core and MTF activity sleeve, but both entry and exit are executed on the next candle open after the signal or exit condition, keeping signal/execution separation while retaining the original structural stop/target condition sequence. |

### Stop/Target Template

- Entry Price: next candle open after the completed signal candle.
- Stop Loss: structural level or sweep extreme plus ATR/noise buffer.
- Take Profit: R multiple or opposite liquidity, admitted only when estimated round-trip cost leaves positive net reward.
- Risk per Trade: cash-bounded fixed fraction, no leverage.
- Expected R: variant-specific 1.2R to 2.0R for pure families; fixed bps geometry for the priority ensemble.
- Required Win Rate: computed from net reward/risk after fee/spread/slippage; strategies with net R below gate are rejected before entry.
- Fee-adjusted Break-even: entry and exit taker fee are included through `conservative_crypto_1m`.
- Slippage-adjusted Break-even: spread, base slippage, minimum slippage, and volatility slippage are included.
- Invalid Setup Condition: cost gate rejection, invalid stop/target geometry, missing factors, or candle continuity gap.
- Early Exit Condition: stop, target, conservative stop-first ambiguity, time exit, or ensemble scout preemption.

## IV. Backtest Design

- Data availability: requested from `2026-04-20T00:00:00Z`, actual local start `2026-05-10T00:00:00Z`, actual local end `2026-05-28T08:26:00Z`.
- Timeframe: BTCUSDT 1m primary; 15m/1h context is computed from completed prior 1m history.
- Costs: primary `conservative_crypto_1m`; stress `high_slippage_stress`; zero-cost runs are diagnostic only.
- Execution: signal on completed candle, entry on next candle open, no overlapping positions, cash-bounded sizing, simulated short research-only.
- Intrabar ambiguity: if stop and target are both touched in the same candle, stop fills first.
- Persistence: every completed decision-driving run is saved to DB with `research.task_id = TASK_283`.

## V. Priority And Run Results

- Persisted Task 283 run IDs: `917, 919, 920, 921, 922, 923, 924, 925, 926, 927, 928, 929, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959`.
- Best variant by primary target-window score: `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`.

| Variant | Family | Window | Group | Cost | Run | Return | Trips | Win | PF | Gross | Net | Cost | Cost/Gross | Top1 | Top3 | DD | Status |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| T283_B1_LSR_V2_RECLAIM_R18 | LIQUIDITY_SWEEP_REVERSAL_V2 | owner_0520_latest | primary_candidate_comparison | conservative_crypto_1m | 917 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | - | - | +0.0000pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_LSR_V2_RECLAIM_R18 | LIQUIDITY_SWEEP_REVERSAL_V2 | owner_0525_latest | primary_candidate_comparison | conservative_crypto_1m | 919 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | - | - | +0.0000pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_VCB_COMP60_BODY35_R20 | VOLATILITY_COMPRESSION_BREAKOUT | owner_0520_latest | primary_candidate_comparison | conservative_crypto_1m | 920 | -4.7475pct | 49 | 0.2245 | 0.1617 | -938.45 | -47,475.06 | 46,536.60 | 49.5886 | - | - | -4.8358pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_VCB_COMP60_BODY35_R20 | VOLATILITY_COMPRESSION_BREAKOUT | owner_0525_latest | primary_candidate_comparison | conservative_crypto_1m | 921 | -1.8686pct | 22 | 0.2273 | 0.1714 | 1,981.00 | -18,685.54 | 20,666.53 | 10.4324 | - | - | -1.9568pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_MTF_PULLBACK_15M_1H_R16 | MTF_TREND_PULLBACK_CONTINUATION | owner_0520_latest | primary_candidate_comparison | conservative_crypto_1m | 922 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | - | - | +0.0000pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_MTF_PULLBACK_15M_1H_R16 | MTF_TREND_PULLBACK_CONTINUATION | owner_0525_latest | primary_candidate_comparison | conservative_crypto_1m | 923 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | - | - | +0.0000pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_VOLUME_CLIMAX_REVERT_R12 | VOLUME_CLIMAX_MEAN_REVERSION | owner_0520_latest | primary_candidate_comparison | conservative_crypto_1m | 924 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | - | - | +0.0000pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_VOLUME_CLIMAX_REVERT_R12 | VOLUME_CLIMAX_MEAN_REVERSION | owner_0525_latest | primary_candidate_comparison | conservative_crypto_1m | 925 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | - | - | +0.0000pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_SESSION_RANGE_TRAP_R15 | SESSION_RANGE_LIQUIDITY_TRAP | owner_0520_latest | primary_candidate_comparison | conservative_crypto_1m | 926 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | - | - | +0.0000pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_SESSION_RANGE_TRAP_R15 | SESSION_RANGE_LIQUIDITY_TRAP | owner_0525_latest | primary_candidate_comparison | conservative_crypto_1m | 927 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | - | - | +0.0000pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0520_latest | primary_candidate_comparison | conservative_crypto_1m | 928 | +3.1105pct | 79 | 0.1646 | 3.9902 | 58,887.97 | 31,104.70 | 27,783.27 | 0.4718 | 0.4002 | 0.9384 | -1.5589pct | COMPLETED_RESEARCH_ONLY |
| T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0525_latest | primary_candidate_comparison | conservative_crypto_1m | 929 | +1.4767pct | 23 | 0.2609 | 3.3868 | 31,290.42 | 14,767.08 | 16,523.34 | 0.5281 | 0.6033 | 1.3955 | -1.2180pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0520_latest | primary_candidate_comparison | conservative_crypto_1m | 950 | +5.7327pct | 62 | 0.1935 | 10.2198 | 97,920.81 | 57,327.32 | 40,593.49 | 0.4146 | 0.2729 | 0.6474 | -1.3279pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0525_latest | primary_candidate_comparison | conservative_crypto_1m | 951 | +3.5337pct | 17 | 0.2941 | 27.0253 | 54,769.80 | 35,337.20 | 19,432.60 | 0.3548 | 0.4426 | 0.8592 | -1.1977pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0520_drop_first_12h | endpoint_trim | conservative_crypto_1m | 952 | +5.7776pct | 56 | 0.2143 | 11.0101 | 97,935.10 | 57,776.32 | 40,158.77 | 0.4101 | 0.2707 | 0.6424 | -1.3279pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0520_drop_last_12h | endpoint_trim | conservative_crypto_1m | 953 | +3.5991pct | 61 | 0.1803 | 6.7037 | 69,194.57 | 35,990.93 | 33,203.63 | 0.4799 | 0.3473 | 0.8041 | -1.3279pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0520_drop_last_24h | endpoint_trim | conservative_crypto_1m | 954 | +3.0529pct | 58 | 0.1552 | 6.0963 | 59,832.81 | 30,528.73 | 29,304.09 | 0.4898 | 0.4094 | 0.9480 | -1.3279pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0525_drop_last_12h | endpoint_trim | conservative_crypto_1m | 955 | +1.4001pct | 16 | 0.2500 | 10.6550 | 26,043.55 | 14,000.81 | 12,042.74 | 0.4624 | 0.6396 | 1.1022 | -1.1977pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0520_latest | cost_stress | high_slippage_stress | 956 | +0.4570pct | 62 | 0.1290 | 1.2051 | 96,813.43 | 4,570.47 | 92,242.96 | 0.9528 | 2.3582 | 4.9597 | -2.4202pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0525_latest | cost_stress | high_slippage_stress | 957 | +0.9603pct | 17 | 0.2353 | 2.4771 | 54,448.63 | 9,602.54 | 44,846.08 | 0.8236 | 1.1280 | 1.6390 | -1.6990pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | owner_0520_latest | no_cost_diagnostic | zero | 958 | +9.7958pct | 62 | 0.5161 | 57.1012 | 97,958.01 | 97,958.01 | 0.00 | 0.0000 | 0.1971 | 0.4909 | -0.8635pct | COMPLETED_RESEARCH_ONLY |
| T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002 | PRINCIPLE_FIRST_PRIORITY_ENSEMBLE | available_pre_owner_0510_0517 | pre_owner_check | conservative_crypto_1m | 959 | -2.6638pct | 54 | 0.1667 | 0.6199 | 20,150.20 | -26,638.39 | 46,788.59 | 2.3220 | - | - | -4.0795pct | COMPLETED_RESEARCH_ONLY |

## Gate Check

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| 0520 owner return | >= +3.0000pct | +5.7327pct | `PASS` |
| 0525 owner return | >= +3.0000pct | +3.5337pct | `PASS` |
| 0520 completed round trips | >= 50 | 62 | `PASS` |
| Cost audit mismatch count | 0 | 0 | `PASS` |
| Non-zero realistic costs | fee/spread/slippage > 0 | fee=21,970.33, spread=6,591.10, slippage=12,032.06 | `PASS` |
| 0520 largest winner contribution | <= 0.40 | 0.2729 | `PASS` |
| 0520 top-three winner contribution | <= 0.70 | 0.6474 | `PASS` |
| 0520 cost/gross PnL | <= 0.75 | 0.4146 | `PASS` |
| Endpoint trim | all diagnostic trims positive | 4/4 | `PASS` |
| High-cost stress | all stress returns > -3pct | 2/2 | `PASS` |
| Conservative intrabar policy | stop first | True | `PASS` |
| April-20 data coverage | record blocker if missing | DATA_BLOCKED_0420_COVERAGE | `PASS` |

## Cost Audit

- Run `917` `T283_B1_LSR_V2_RECLAIM_R18` `owner_0520_latest` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `-` bps, mismatch count `0`.
- Run `919` `T283_B1_LSR_V2_RECLAIM_R18` `owner_0525_latest` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `-` bps, mismatch count `0`.
- Run `920` `T283_B1_VCB_COMP60_BODY35_R20` `owner_0520_latest` `conservative_crypto_1m`: notional `24,501,148.72`, fee `24,501.15`, spread `7,350.34`, slippage `14,685.11`, total `46,536.60`, effective one-way cost `18.9936` bps, mismatch count `0`.
- Run `921` `T283_B1_VCB_COMP60_BODY35_R20` `owner_0525_latest` `conservative_crypto_1m`: notional `10,997,609.49`, fee `10,997.61`, spread `3,299.28`, slippage `6,369.64`, total `20,666.53`, effective one-way cost `18.7918` bps, mismatch count `0`.
- Run `922` `T283_B1_MTF_PULLBACK_15M_1H_R16` `owner_0520_latest` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `-` bps, mismatch count `0`.
- Run `923` `T283_B1_MTF_PULLBACK_15M_1H_R16` `owner_0525_latest` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `-` bps, mismatch count `0`.
- Run `924` `T283_B1_VOLUME_CLIMAX_REVERT_R12` `owner_0520_latest` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `-` bps, mismatch count `0`.
- Run `925` `T283_B1_VOLUME_CLIMAX_REVERT_R12` `owner_0525_latest` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `-` bps, mismatch count `0`.
- Run `926` `T283_B1_SESSION_RANGE_TRAP_R15` `owner_0520_latest` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `-` bps, mismatch count `0`.
- Run `927` `T283_B1_SESSION_RANGE_TRAP_R15` `owner_0525_latest` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `-` bps, mismatch count `0`.
- Run `928` `T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002` `owner_0520_latest` `conservative_crypto_1m`: notional `14,852,939.21`, fee `14,852.94`, spread `4,455.88`, slippage `8,474.45`, total `27,783.27`, effective one-way cost `18.7056` bps, mismatch count `0`.
- Run `929` `T283_B1_LSR_MTF_ACTIVITY_ENSEMBLE_CF100_SCOUT002` `owner_0525_latest` `conservative_crypto_1m`: notional `8,709,113.38`, fee `8,709.11`, spread `2,612.73`, slippage `5,201.49`, total `16,523.34`, effective one-way cost `18.9725` bps, mismatch count `0`.
- Run `950` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0520_latest` `conservative_crypto_1m`: notional `21,970,331.56`, fee `21,970.33`, spread `6,591.10`, slippage `12,032.06`, total `40,593.49`, effective one-way cost `18.4765` bps, mismatch count `0`.
- Run `951` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0525_latest` `conservative_crypto_1m`: notional `10,416,282.34`, fee `10,416.28`, spread `3,124.88`, slippage `5,891.43`, total `19,432.60`, effective one-way cost `18.6560` bps, mismatch count `0`.
- Run `952` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0520_drop_first_12h` `conservative_crypto_1m`: notional `21,732,834.88`, fee `21,732.83`, spread `6,519.85`, slippage `11,906.09`, total `40,158.77`, effective one-way cost `18.4784` bps, mismatch count `0`.
- Run `953` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0520_drop_last_12h` `conservative_crypto_1m`: notional `18,039,057.80`, fee `18,039.06`, spread `5,411.72`, slippage `9,752.86`, total `33,203.63`, effective one-way cost `18.4065` bps, mismatch count `0`.
- Run `954` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0520_drop_last_24h` `conservative_crypto_1m`: notional `15,968,496.92`, fee `15,968.50`, spread `4,790.55`, slippage `8,545.04`, total `29,304.09`, effective one-way cost `18.3512` bps, mismatch count `0`.
- Run `955` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0525_drop_last_12h` `conservative_crypto_1m`: notional `6,485,008.58`, fee `6,485.01`, spread `1,945.50`, slippage `3,612.23`, total `12,042.74`, effective one-way cost `18.5701` bps, mismatch count `0`.
- Run `956` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0520_latest` `high_slippage_stress`: notional `21,764,901.02`, fee `21,764.90`, spread `21,764.90`, slippage `48,713.16`, total `92,242.96`, effective one-way cost `42.3815` bps, mismatch count `0`.
- Run `957` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0525_latest` `high_slippage_stress`: notional `10,362,017.48`, fee `10,362.02`, spread `10,362.02`, slippage `24,122.05`, total `44,846.08`, effective one-way cost `43.2793` bps, mismatch count `0`.
- Run `958` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0520_latest` `zero`: notional `21,982,182.57`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, effective one-way cost `0.0000` bps, mismatch count `0`.
- Run `959` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `available_pre_owner_0510_0517` `conservative_crypto_1m`: notional `25,137,760.50`, fee `25,137.76`, spread `7,541.33`, slippage `14,109.50`, total `46,788.59`, effective one-way cost `18.6129` bps, mismatch count `0`.

## VI. Implementation Checklist

- Look-ahead bias: factor snapshots use completed signal candles and prior rolling windows; entry is placed on the next candle.
- Candle close signal: yes.
- Next candle execution: yes, next candle open.
- Stop/take intrabar ambiguity: conservative stop-first.
- Long/short separation: attribution recorded.
- Fee both ways: engine cost metadata and persisted cost audit verified.
- Slippage/spread: non-zero primary profile; stress profile also run for the best candidate.
- Position overlap: blocked by sequential action generation and engine open-position guard.
- Data gaps: April 20 coverage remains blocked by local data availability; no fabrication.
- Factor snapshot saved: trade metadata includes `task283_factor_snapshot` and cost gate details.
- Research-only: no live orders, no keys, no private endpoints.

## Conclusion

- Final status: `TARGET_PASSED_RESEARCH_ONLY`.
- Best 0520 run: `950` with return `+5.7327pct` and `62` round trips.
- Failed gates: `-`.
- Overfit/robustness note: full April-20-forward OOS is data-blocked; available pre-owner slice is negative; zero-cost diagnostic gap on 0520 is +4.0631pct; target-window gates pass, but the result remains research-only because the windows are fixed and previously inspected.
- No Task 283 result is promoted beyond `RESEARCH_ONLY`.
