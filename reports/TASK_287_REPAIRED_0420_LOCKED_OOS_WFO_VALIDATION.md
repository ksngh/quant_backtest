# Task 287 Repaired 0420 Locked OOS/WFO Validation

Status: `LOCKED_PRIMARY_REJECTED_RESEARCH_ONLY`

## Scope

- Purpose: replay locked research candidates unchanged on the repaired BTCUSDT 1m April-20-forward dataset.
- Retune policy: `no_retune`; no entry, exit, sizing, filter, or parameter search is allowed in this task.
- Result scope: `RESEARCH_ONLY`; no live trading, no private exchange endpoints, no futures, no leverage.
- Primary candidate: `T285_R3_CORE_SHORT_ONLY_B2`.
- Comparators: `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`, `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- Korean failure analysis document: `docs/research/TASK_287_STRATEGY_FAILURE_ANALYSIS_KO.md`.

## Repaired Data Coverage

- Requested start: `2026-04-20T00:00:00Z`.
- Available start: `2026-04-20T00:00:00Z`.
- Available end: `2026-05-28T08:26:00Z`.
- Closed candle count: `55227`.
- Expected continuous count: `55227`.
- Continuity gaps: `0`.
- Duplicate open-time groups: `0`.
- April-20-forward complete: `True`.
- Coverage guard: `PASS` `-`.

## Locked Strategy Rationale

- `T285_R3_CORE_SHORT_ONLY_B2`: failed-rally/liquidity-sweep short core. The market thesis is that recent highs concentrate stop and breakout liquidity; when BTC sweeps that area, closes back inside, and broader short-term pressure is bearish, forced buying may exhaust and price can revert downward. Task 285 locked this as a core-only short repair because prior validation showed profits were concentrated in the short core while long/scout sleeves diluted results.
- `T283_B2...`: same principle-first LSR/MTF ensemble before Task 285 side/layer repair, kept as a baseline comparator.
- `T281_B1...`: earlier owner-window high-activity core/scout model, kept as a legacy comparator to detect whether the repaired data changes the prior overfit diagnosis.

## Validation Design

- Base cost: `conservative_crypto_1m` with taker fee, spread, base/minimum slippage, and volatility slippage.
- Stress costs: `cost_2x`, `cost_3x`, and `high_slippage_stress` on full/pre-owner windows.
- Signal/execution: completed signal candle, next-candle execution where inherited from Task 283 B2; conservative stop-first if stop and target hit the same candle.
- Windows: full 0420-latest, pre-owner 0420-0519, owner replays 0520/0525, six non-overlapping weekly independent windows, WFO reporting partitions, and endpoint trims.
- Persistence: every completed run is saved with `research.task_id = TASK_287`, `research.validation_mode = repaired_0420_locked_oos_wfo`, `no_retune = true`, repaired-data metadata, candidate/window/cost metadata, and source-reference run IDs.

## Persisted Runs

- Task 287 run IDs: `1085, 1086, 1087, 1088, 1089, 1090, 1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1110, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119, 1120, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1128, 1129, 1130, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 1140, 1141, 1142, 1143, 1144, 1145, 1146, 1147, 1148, 1149, 1150, 1151, 1152, 1153, 1154, 1155, 1156, 1157, 1158, 1159`.

| Candidate | Source | Window | Role | Cost | Run | Return | Trips | Win | PF | Gross | Net | Cost | Cost/Gross | Fee | Spread | Slippage | Cost MM | Readback | Status |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `full_0420_latest` | full | `conservative_crypto_1m` | 1085 | -13.0706pct | 50 | 0.3400 | 0.4558 | 34,307.78 | -130,705.56 | 165,013.34 | 4.8098 | 87,713.79 | 26,314.14 | 50,985.41 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `pre_owner_0420_0519` | pre_owner | `conservative_crypto_1m` | 1086 | -17.4283pct | 39 | 0.2051 | 0.2446 | -42,914.00 | -174,283.25 | 131,369.25 | 3.0612 | 69,496.15 | 20,848.85 | 41,024.25 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `owner_replay_0520_latest` | owner_replay | `conservative_crypto_1m` | 1087 | +6.1764pct | 10 | 0.9000 | 40.2016 | 98,535.63 | 61,764.02 | 36,771.61 | 0.3732 | 19,894.87 | 5,968.46 | 10,908.27 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `owner_replay_0525_latest` | owner_replay | `conservative_crypto_1m` | 1088 | +3.6703pct | 5 | 1.0000 | - | 55,255.84 | 36,703.37 | 18,552.47 | 0.3358 | 9,938.73 | 2,981.62 | 5,632.12 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `w1_0420_0426` | independent | `conservative_crypto_1m` | 1089 | -6.1071pct | 7 | 0.1429 | 0.0589 | -35,239.18 | -61,071.42 | 25,832.24 | 0.7331 | 13,626.74 | 4,088.02 | 8,117.48 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `w2_0427_0503` | independent | `conservative_crypto_1m` | 1090 | -3.2146pct | 7 | 0.2857 | 0.2194 | -6,556.33 | -32,145.83 | 25,589.49 | 3.9030 | 13,835.75 | 4,150.72 | 7,603.02 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `w3_0504_0510` | independent | `conservative_crypto_1m` | 1091 | -2.4801pct | 7 | 0.1429 | 0.1957 | 679.43 | -24,800.53 | 25,479.96 | 37.5019 | 13,782.25 | 4,134.68 | 7,563.03 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `w4_0511_0517` | independent | `conservative_crypto_1m` | 1092 | +0.1067pct | 10 | 0.3000 | 1.0248 | 37,928.58 | 1,067.22 | 36,861.36 | 0.9719 | 19,911.49 | 5,973.45 | 10,976.42 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `w5_0518_0524` | independent | `conservative_crypto_1m` | 1093 | -0.1856pct | 8 | 0.5000 | 0.9335 | 26,929.94 | -1,856.16 | 28,786.10 | 1.0689 | 15,670.75 | 4,701.23 | 8,414.12 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `w6_0525_latest` | independent | `conservative_crypto_1m` | 1094 | +3.6703pct | 5 | 1.0000 | - | 55,255.84 | 36,703.37 | 18,552.47 | 0.3358 | 9,938.73 | 2,981.62 | 5,632.12 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `wfo_0420_0503` | wfo | `conservative_crypto_1m` | 1095 | -8.4396pct | 15 | 0.2667 | 0.1436 | -30,740.71 | -84,396.38 | 53,655.67 | 1.7454 | 28,568.12 | 8,570.44 | 16,517.11 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `wfo_0504_0517` | wfo | `conservative_crypto_1m` | 1096 | -4.7708pct | 19 | 0.2105 | 0.5019 | 20,442.09 | -47,708.13 | 68,150.22 | 3.3338 | 36,704.48 | 11,011.34 | 20,434.39 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `wfo_0518_latest` | wfo | `conservative_crypto_1m` | 1097 | +3.4829pct | 13 | 0.6923 | 2.2469 | 82,154.21 | 34,829.25 | 47,324.96 | 0.5761 | 25,602.10 | 7,680.63 | 14,042.22 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `full_0420_drop_first_6h` | endpoint | `conservative_crypto_1m` | 1098 | -13.0706pct | 50 | 0.3400 | 0.4558 | 34,307.78 | -130,705.56 | 165,013.34 | 4.8098 | 87,713.79 | 26,314.14 | 50,985.41 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `full_0420_drop_first_24h` | endpoint | `conservative_crypto_1m` | 1099 | -13.0175pct | 49 | 0.3469 | 0.4569 | 31,309.78 | -130,174.89 | 161,484.67 | 5.1576 | 85,790.44 | 25,737.13 | 49,957.09 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `full_0420_drop_last_6h` | endpoint | `conservative_crypto_1m` | 1100 | -14.4069pct | 49 | 0.3265 | 0.4001 | 17,814.41 | -144,068.64 | 161,883.05 | 9.0872 | 86,021.66 | 25,806.50 | 50,054.89 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `full_0420_drop_last_24h` | endpoint | `conservative_crypto_1m` | 1101 | -15.3712pct | 47 | 0.2979 | 0.3600 | 1,772.53 | -153,712.33 | 155,484.87 | 87.7190 | 82,649.13 | 24,794.74 | 48,041.00 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `owner_0520_drop_last_12h` | endpoint | `conservative_crypto_1m` | 1102 | +4.0501pct | 8 | 0.8750 | 26.7062 | 69,807.20 | 40,501.39 | 29,305.80 | 0.4198 | 15,923.60 | 4,777.08 | 8,605.12 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `owner_0520_drop_last_24h` | endpoint | `conservative_crypto_1m` | 1103 | +3.4738pct | 7 | 0.8571 | 23.0482 | 60,292.92 | 34,737.93 | 25,554.99 | 0.4238 | 13,933.12 | 4,179.93 | 7,441.94 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `full_0420_latest` | full | `conservative_crypto_1m` | 1104 | -15.0301pct | 318 | 0.1730 | 0.4225 | 32,803.71 | -150,300.71 | 183,104.41 | 5.5818 | 97,480.11 | 29,244.03 | 56,380.27 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `pre_owner_0420_0519` | pre_owner | `conservative_crypto_1m` | 1105 | -18.8410pct | 252 | 0.1667 | 0.2348 | -42,338.15 | -188,409.81 | 146,071.67 | 3.4501 | 77,426.40 | 23,227.92 | 45,417.34 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `owner_replay_0520_latest` | owner_replay | `conservative_crypto_1m` | 1106 | +5.7327pct | 62 | 0.1935 | 10.2198 | 97,920.81 | 57,327.32 | 40,593.49 | 0.4146 | 21,970.33 | 6,591.10 | 12,032.06 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `owner_replay_0525_latest` | owner_replay | `conservative_crypto_1m` | 1107 | +3.5337pct | 17 | 0.2941 | 27.0253 | 54,769.80 | 35,337.20 | 19,432.60 | 0.3548 | 10,416.28 | 3,124.88 | 5,891.43 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `w1_0420_0426` | independent | `conservative_crypto_1m` | 1108 | -6.4800pct | 63 | 0.1429 | 0.0641 | -34,815.96 | -64,800.42 | 29,984.46 | 0.8612 | 15,850.35 | 4,755.11 | 9,379.00 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `w2_0427_0503` | independent | `conservative_crypto_1m` | 1109 | -3.5536pct | 55 | 0.2000 | 0.2084 | -6,441.08 | -35,535.93 | 29,094.85 | 4.5171 | 15,741.55 | 4,722.47 | 8,630.83 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `w3_0504_0510` | independent | `conservative_crypto_1m` | 1110 | -2.8325pct | 52 | 0.1346 | 0.1821 | 441.04 | -28,325.28 | 28,766.32 | 65.2239 | 15,569.06 | 4,670.72 | 8,526.54 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `w4_0511_0517` | independent | `conservative_crypto_1m` | 1111 | -0.1641pct | 48 | 0.1875 | 0.9645 | 38,022.31 | -1,640.91 | 39,663.21 | 1.0432 | 21,424.19 | 6,427.26 | 11,811.77 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `w5_0518_0524` | independent | `conservative_crypto_1m` | 1112 | -0.5770pct | 54 | 0.1667 | 0.8200 | 26,361.09 | -5,769.67 | 32,130.76 | 1.2189 | 17,484.35 | 5,245.31 | 9,401.11 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `w6_0525_latest` | independent | `conservative_crypto_1m` | 1113 | +3.5337pct | 17 | 0.2941 | 27.0253 | 54,769.80 | 35,337.20 | 19,432.60 | 0.3548 | 10,416.28 | 3,124.88 | 5,891.43 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `wfo_0420_0503` | wfo | `conservative_crypto_1m` | 1114 | -9.1390pct | 122 | 0.1885 | 0.1421 | -29,951.38 | -91,389.83 | 61,438.45 | 2.0513 | 32,758.64 | 9,827.59 | 18,852.23 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `wfo_0504_0517` | wfo | `conservative_crypto_1m` | 1115 | -5.4284pct | 106 | 0.1509 | 0.4716 | 20,048.01 | -54,284.19 | 74,332.19 | 3.7077 | 40,052.09 | 12,015.63 | 22,264.48 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `wfo_0518_latest` | wfo | `conservative_crypto_1m` | 1116 | +2.9100pct | 78 | 0.1795 | 1.8605 | 81,135.04 | 29,100.27 | 52,034.77 | 0.6413 | 28,156.27 | 8,446.88 | 15,431.63 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `full_0420_drop_first_6h` | endpoint | `conservative_crypto_1m` | 1117 | -15.0182pct | 315 | 0.1714 | 0.4227 | 32,714.05 | -150,182.07 | 182,896.12 | 5.5908 | 97,371.98 | 29,211.60 | 56,312.54 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `full_0420_drop_first_24h` | endpoint | `conservative_crypto_1m` | 1118 | -14.9306pct | 309 | 0.1748 | 0.4244 | 29,764.37 | -149,305.68 | 179,070.05 | 6.0163 | 95,282.94 | 28,584.88 | 55,202.23 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `full_0420_drop_last_6h` | endpoint | `conservative_crypto_1m` | 1119 | -16.3278pct | 318 | 0.1698 | 0.3725 | 16,839.80 | -163,278.28 | 180,118.07 | 10.6960 | 95,865.44 | 28,759.63 | 55,493.00 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `full_0420_drop_last_24h` | endpoint | `conservative_crypto_1m` | 1120 | -17.2568pct | 314 | 0.1656 | 0.3364 | 1,146.59 | -172,568.43 | 173,715.02 | 151.5059 | 92,487.98 | 27,746.39 | 53,480.64 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `owner_0520_drop_last_12h` | endpoint | `conservative_crypto_1m` | 1121 | +3.5991pct | 61 | 0.1803 | 6.7037 | 69,194.57 | 35,990.93 | 33,203.63 | 0.4799 | 18,039.06 | 5,411.72 | 9,752.86 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `owner_0520_drop_last_24h` | endpoint | `conservative_crypto_1m` | 1122 | +3.0529pct | 58 | 0.1552 | 6.0963 | 59,832.81 | 30,528.73 | 29,304.09 | 0.4898 | 15,968.50 | 4,790.55 | 8,545.04 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `full_0420_latest` | full | `conservative_crypto_1m` | 1123 | -14.7305pct | 318 | 0.1730 | 0.4271 | 37,813.89 | -147,304.91 | 185,118.80 | 4.8955 | 97,725.92 | 29,317.78 | 58,075.10 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `pre_owner_0420_0519` | pre_owner | `conservative_crypto_1m` | 1124 | -18.5517pct | 252 | 0.1667 | 0.2366 | -37,627.67 | -185,516.62 | 147,888.95 | 3.9303 | 77,609.13 | 23,282.74 | 46,997.08 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `owner_replay_0520_latest` | owner_replay | `conservative_crypto_1m` | 1125 | +5.7295pct | 62 | 0.1935 | 10.2250 | 97,963.67 | 57,294.78 | 40,668.89 | 0.4151 | 21,970.38 | 6,591.12 | 12,107.39 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `owner_replay_0525_latest` | owner_replay | `conservative_crypto_1m` | 1126 | +3.5308pct | 17 | 0.2941 | 27.2464 | 54,784.33 | 35,307.72 | 19,476.61 | 0.3555 | 10,416.12 | 3,124.84 | 5,935.65 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `w1_0420_0426` | independent | `conservative_crypto_1m` | 1127 | -6.4032pct | 63 | 0.1429 | 0.0627 | -33,597.45 | -64,032.25 | 30,434.79 | 0.9059 | 15,856.69 | 4,757.01 | 9,821.09 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `w2_0427_0503` | independent | `conservative_crypto_1m` | 1128 | -3.5853pct | 55 | 0.2000 | 0.2051 | -6,493.85 | -35,852.95 | 29,359.10 | 4.5211 | 15,738.86 | 4,721.66 | 8,898.58 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `w3_0504_0510` | independent | `conservative_crypto_1m` | 1129 | -2.8315pct | 52 | 0.1346 | 0.1835 | 452.11 | -28,314.72 | 28,766.83 | 63.6273 | 15,569.01 | 4,670.70 | 8,527.12 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `w4_0511_0517` | independent | `conservative_crypto_1m` | 1130 | -0.2222pct | 48 | 0.1875 | 0.9523 | 37,743.59 | -2,222.07 | 39,965.66 | 1.0589 | 21,423.27 | 6,426.98 | 12,115.40 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `w5_0518_0524` | independent | `conservative_crypto_1m` | 1131 | -0.5855pct | 54 | 0.1667 | 0.8178 | 26,378.02 | -5,855.27 | 32,233.30 | 1.2220 | 17,483.24 | 5,244.97 | 9,505.08 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `w6_0525_latest` | independent | `conservative_crypto_1m` | 1132 | +3.5308pct | 17 | 0.2941 | 27.2464 | 54,784.33 | 35,307.72 | 19,476.61 | 0.3555 | 10,416.12 | 3,124.84 | 5,935.65 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `wfo_0420_0503` | wfo | `conservative_crypto_1m` | 1133 | -9.0985pct | 122 | 0.1885 | 0.1402 | -28,796.26 | -90,985.44 | 62,189.18 | 2.1596 | 32,773.97 | 9,832.19 | 19,583.03 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `wfo_0504_0517` | wfo | `conservative_crypto_1m` | 1134 | -5.5601pct | 106 | 0.1509 | 0.4644 | 19,258.00 | -55,600.50 | 74,858.50 | 3.8871 | 40,029.38 | 12,008.81 | 22,820.31 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `wfo_0518_latest` | wfo | `conservative_crypto_1m` | 1135 | +2.8989pct | 78 | 0.1795 | 1.8555 | 81,168.72 | 28,988.88 | 52,179.84 | 0.6429 | 28,154.68 | 8,446.40 | 15,578.76 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `full_0420_drop_first_6h` | endpoint | `conservative_crypto_1m` | 1136 | -14.7186pct | 315 | 0.1714 | 0.4273 | 37,724.90 | -147,186.42 | 184,911.33 | 4.9016 | 97,617.77 | 29,285.33 | 58,008.22 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `full_0420_drop_first_24h` | endpoint | `conservative_crypto_1m` | 1137 | -14.6410pct | 309 | 0.1748 | 0.4288 | 34,752.08 | -146,409.86 | 181,161.94 | 5.2130 | 95,518.67 | 28,655.60 | 56,987.66 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `full_0420_drop_last_6h` | endpoint | `conservative_crypto_1m` | 1138 | -16.0270pct | 318 | 0.1698 | 0.3764 | 21,809.57 | -160,269.56 | 182,079.14 | 8.3486 | 96,105.33 | 28,831.60 | 57,142.20 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `full_0420_drop_last_24h` | endpoint | `conservative_crypto_1m` | 1139 | -16.9639pct | 314 | 0.1656 | 0.3396 | 6,069.20 | -169,639.18 | 175,708.37 | 28.9509 | 92,716.32 | 27,814.90 | 55,177.15 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `owner_0520_drop_last_12h` | endpoint | `conservative_crypto_1m` | 1140 | +3.6004pct | 61 | 0.1803 | 6.7191 | 69,246.49 | 36,003.50 | 33,242.99 | 0.4801 | 18,039.10 | 5,411.73 | 9,792.15 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `owner_0520_drop_last_24h` | endpoint | `conservative_crypto_1m` | 1141 | +3.0506pct | 58 | 0.1552 | 6.1197 | 59,900.62 | 30,506.44 | 29,394.18 | 0.4907 | 15,968.56 | 4,790.57 | 8,635.05 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `full_0420_latest` | full | `cost_2x` | 1142 | -27.9587pct | 50 | 0.2800 | 0.1599 | 22,155.30 | -279,587.16 | 301,742.46 | 13.6194 | 160,314.88 | 48,094.46 | 93,333.13 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `pre_owner_0420_0519` | pre_owner | `cost_2x` | 1143 | -28.7571pct | 39 | 0.1795 | 0.0906 | -42,719.22 | -287,570.99 | 244,851.77 | 5.7317 | 129,506.44 | 38,851.93 | 76,493.40 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `full_0420_latest` | full | `cost_3x` | 1144 | -40.2970pct | 50 | 0.1400 | 0.0561 | 12,088.69 | -402,970.39 | 415,059.08 | 34.3345 | 220,414.11 | 66,124.23 | 128,520.74 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `pre_owner_0420_0519` | pre_owner | `cost_3x` | 1145 | -38.5316pct | 39 | 0.0769 | 0.0371 | -42,416.85 | -385,316.26 | 342,899.41 | 8.0840 | 181,332.90 | 54,399.87 | 107,166.64 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `full_0420_latest` | full | `high_slippage_stress` | 1146 | -32.4273pct | 50 | 0.2200 | 0.1109 | 18,523.30 | -324,272.72 | 342,796.02 | 18.5062 | 77,686.78 | 77,686.78 | 187,422.46 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | `pre_owner_0420_0519` | pre_owner | `high_slippage_stress` | 1147 | -32.3848pct | 39 | 0.1026 | 0.0649 | -42,588.38 | -323,847.84 | 281,259.46 | 6.6041 | 63,148.40 | 63,148.40 | 154,962.67 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `full_0420_latest` | full | `cost_2x` | 1148 | -31.5244pct | 318 | 0.0723 | 0.1414 | 19,360.35 | -315,244.04 | 334,604.39 | 17.2830 | 178,075.30 | 53,422.59 | 103,106.51 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `pre_owner_0420_0519` | pre_owner | `cost_2x` | 1149 | -31.4163pct | 252 | 0.0595 | 0.0829 | -42,076.70 | -314,162.67 | 272,085.97 | 6.4664 | 144,216.70 | 43,265.01 | 84,604.25 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `full_0420_latest` | full | `cost_3x` | 1150 | -45.1718pct | 318 | 0.0377 | 0.0478 | 8,248.62 | -451,718.01 | 459,966.63 | 55.7629 | 244,715.22 | 73,414.57 | 141,836.84 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `pre_owner_0420_0519` | pre_owner | `cost_3x` | 1151 | -42.2498pct | 252 | 0.0278 | 0.0326 | -41,694.22 | -422,498.38 | 380,804.16 | 9.1333 | 201,837.28 | 60,551.18 | 118,415.69 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `full_0420_latest` | full | `high_slippage_stress` | 1152 | -36.4073pct | 318 | 0.0566 | 0.0969 | 15,396.96 | -364,073.36 | 379,470.31 | 24.6458 | 86,320.07 | 86,320.07 | 206,830.17 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | `pre_owner_0420_0519` | pre_owner | `high_slippage_stress` | 1153 | -35.3759pct | 252 | 0.0397 | 0.0586 | -41,921.25 | -353,758.65 | 311,837.40 | 7.4386 | 70,338.57 | 70,338.57 | 171,160.26 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `full_0420_latest` | full | `cost_2x` | 1154 | -31.4028pct | 318 | 0.0692 | 0.1407 | 23,963.34 | -314,027.67 | 337,991.01 | 14.1045 | 178,366.14 | 53,509.84 | 106,115.04 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `pre_owner_0420_0519` | pre_owner | `cost_2x` | 1155 | -31.2855pct | 252 | 0.0556 | 0.0817 | -37,618.27 | -312,854.60 | 275,236.33 | 7.3166 | 144,454.01 | 43,336.20 | 87,446.12 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `full_0420_latest` | full | `cost_3x` | 1156 | -45.1739pct | 318 | 0.0346 | 0.0472 | 12,503.73 | -451,738.83 | 464,242.56 | 37.1283 | 244,912.29 | 73,473.69 | 145,856.58 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `pre_owner_0420_0519` | pre_owner | `cost_3x` | 1157 | -42.2374pct | 252 | 0.0238 | 0.0324 | -37,473.15 | -422,373.73 | 384,900.58 | 10.2714 | 202,032.50 | 60,609.75 | 122,258.34 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `full_0420_latest` | full | `high_slippage_stress` | 1158 | -36.6468pct | 318 | 0.0566 | 0.0963 | 19,568.56 | -366,467.61 | 386,036.17 | 19.7274 | 86,250.51 | 86,250.51 | 213,535.15 | 0 | True | COMPLETED_RESEARCH_ONLY |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | `pre_owner_0420_0519` | pre_owner | `high_slippage_stress` | 1159 | -35.5861pct | 252 | 0.0397 | 0.0584 | -37,572.92 | -355,860.60 | 318,287.68 | 8.4712 | 70,318.27 | 70,318.27 | 177,651.14 | 0 | True | COMPLETED_RESEARCH_ONLY |

## Candidate Aggregates

| Candidate | Source | Independent Windows | Positive | Indep Return | Full Return | Full Trips | Pre-owner | 0520 | 0525 | 2x Full | 3x Full | High Slip Full | Cost/Gross Full | Cost/Gross Indep | No Top3 Indep | No Top3 Full | Cost MM | Classification |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `T285_R3_CORE_SHORT_ONLY_B2` | `TASK_285` | 6 | 0.3333 | -8.2103pct | -13.0706pct | 50 | -17.4283pct | +6.1764pct | +3.6703pct | -27.9587pct | -40.2970pct | -32.4273pct | 4.8098 | 2.0393 | -13.3426pct | -17.3957pct | 0 | COST_FRAGILE |
| `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` | `TASK_283` | 6 | 0.1667 | -10.0735pct | -15.0301pct | 318 | -18.8410pct | +5.7327pct | +3.5337pct | -31.5244pct | -45.1718pct | -36.4073pct | 5.5818 | 2.2859 | -15.2031pct | -19.2831pct | 0 | COST_FRAGILE |
| `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` | `TASK_281` | 6 | 0.1667 | -10.0970pct | -14.7305pct | 318 | -18.5517pct | +5.7295pct | +3.5308pct | -31.4028pct | -45.1739pct | -36.6468pct | 4.8955 | 2.2738 | -15.1924pct | -18.9725pct | 0 | COST_FRAGILE |

## Gate Check

### `T285_R3_CORE_SHORT_ONLY_B2`

- Status: `OOS_REJECTED_RESEARCH_ONLY`.
- Classification: `COST_FRAGILE`.
- Failed gates: `Full 0420 latest return, Pre-owner 0420-0519 return, Independent positive fraction, Independent aggregate return, Single-window winner concentration, Independent return without top-three winners, Full return without top-three winners, Full top-three winner contribution, Full cost/gross PnL, Independent cost/gross PnL, 2x cost full return, 3x cost full return`.

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Full 0420 latest return | >= +3pct | -13.0706pct | `FAIL` |
| Full 0420 latest round trips | >= 50 | 50 | `PASS` |
| Pre-owner 0420-0519 return | > 0pct | -17.4283pct | `FAIL` |
| Independent weekly windows | >= 4 | 6 | `PASS` |
| Independent positive fraction | >= 75pct | 0.3333 | `FAIL` |
| Independent aggregate return | >= +3pct | -8.2103pct | `FAIL` |
| Single-window winner concentration | <= 60pct | 0.9717 | `FAIL` |
| Independent return without top-three winners | > 0pct | -13.3426pct | `FAIL` |
| Full return without top-three winners | > 0pct | -17.3957pct | `FAIL` |
| Full top-three winner contribution | <= 70pct | - | `FAIL` |
| Full cost/gross PnL | <= 0.60 | 4.8098 | `FAIL` |
| Independent cost/gross PnL | <= 0.60 | 2.0393 | `FAIL` |
| 2x cost full return | > -1pct | -27.9587pct | `FAIL` |
| 3x cost full return | reported and > -3pct | -40.2970pct | `FAIL` |
| High slippage full return | reported | -32.4273pct | `PASS` |
| Cost audit mismatches | 0 | 0 | `PASS` |
| DB readback | all task287 metadata read back | True | `PASS` |
| Candle quality | all runs continuous | True | `PASS` |

### `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`

- Status: `OOS_REJECTED_RESEARCH_ONLY`.
- Classification: `COST_FRAGILE`.
- Failed gates: `Full 0420 latest return, Pre-owner 0420-0519 return, Independent positive fraction, Independent aggregate return, Single-window winner concentration, Independent return without top-three winners, Full return without top-three winners, Full top-three winner contribution, Full cost/gross PnL, Independent cost/gross PnL, 2x cost full return, 3x cost full return`.

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Full 0420 latest return | >= +3pct | -15.0301pct | `FAIL` |
| Full 0420 latest round trips | >= 50 | 318 | `PASS` |
| Pre-owner 0420-0519 return | > 0pct | -18.8410pct | `FAIL` |
| Independent weekly windows | >= 4 | 6 | `PASS` |
| Independent positive fraction | >= 75pct | 0.1667 | `FAIL` |
| Independent aggregate return | >= +3pct | -10.0735pct | `FAIL` |
| Single-window winner concentration | <= 60pct | 1.0000 | `FAIL` |
| Independent return without top-three winners | > 0pct | -15.2031pct | `FAIL` |
| Full return without top-three winners | > 0pct | -19.2831pct | `FAIL` |
| Full top-three winner contribution | <= 70pct | - | `FAIL` |
| Full cost/gross PnL | <= 0.60 | 5.5818 | `FAIL` |
| Independent cost/gross PnL | <= 0.60 | 2.2859 | `FAIL` |
| 2x cost full return | > -1pct | -31.5244pct | `FAIL` |
| 3x cost full return | reported and > -3pct | -45.1718pct | `FAIL` |
| High slippage full return | reported | -36.4073pct | `PASS` |
| Cost audit mismatches | 0 | 0 | `PASS` |
| DB readback | all task287 metadata read back | True | `PASS` |
| Candle quality | all runs continuous | True | `PASS` |

### `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`

- Status: `OOS_REJECTED_RESEARCH_ONLY`.
- Classification: `COST_FRAGILE`.
- Failed gates: `Full 0420 latest return, Pre-owner 0420-0519 return, Independent positive fraction, Independent aggregate return, Single-window winner concentration, Independent return without top-three winners, Full return without top-three winners, Full top-three winner contribution, Full cost/gross PnL, Independent cost/gross PnL, 2x cost full return, 3x cost full return`.

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Full 0420 latest return | >= +3pct | -14.7305pct | `FAIL` |
| Full 0420 latest round trips | >= 50 | 318 | `PASS` |
| Pre-owner 0420-0519 return | > 0pct | -18.5517pct | `FAIL` |
| Independent weekly windows | >= 4 | 6 | `PASS` |
| Independent positive fraction | >= 75pct | 0.1667 | `FAIL` |
| Independent aggregate return | >= +3pct | -10.0970pct | `FAIL` |
| Single-window winner concentration | <= 60pct | 1.0000 | `FAIL` |
| Independent return without top-three winners | > 0pct | -15.1924pct | `FAIL` |
| Full return without top-three winners | > 0pct | -18.9725pct | `FAIL` |
| Full top-three winner contribution | <= 70pct | - | `FAIL` |
| Full cost/gross PnL | <= 0.60 | 4.8955 | `FAIL` |
| Independent cost/gross PnL | <= 0.60 | 2.2738 | `FAIL` |
| 2x cost full return | > -1pct | -31.4028pct | `FAIL` |
| 3x cost full return | reported and > -3pct | -45.1739pct | `FAIL` |
| High slippage full return | reported | -36.6468pct | `PASS` |
| Cost audit mismatches | 0 | 0 | `PASS` |
| DB readback | all task287 metadata read back | True | `PASS` |
| Candle quality | all runs continuous | True | `PASS` |

## Baselines

| Window | Baseline | Return | Trades | Note |
| --- | --- | ---: | ---: | --- |
| `full_0420_latest` | `buy_and_hold_long` | -0.7356pct | 1 | full notional long, no cost diagnostic |
| `full_0420_latest` | `ma20_120_flip_no_cost` | -8.0028pct | 55106 | close-to-close diagnostic, no execution costs |
| `full_0420_latest` | `random_entry_seed284` | -1.5953pct | 50 | sum of full-notional random trade returns, no cost diagnostic |
| `pre_owner_0420_0519` | `buy_and_hold_long` | +4.0682pct | 1 | full notional long, no cost diagnostic |
| `pre_owner_0420_0519` | `ma20_120_flip_no_cost` | -9.0321pct | 43079 | close-to-close diagnostic, no execution costs |
| `pre_owner_0420_0519` | `random_entry_seed284` | +2.5124pct | 39 | sum of full-notional random trade returns, no cost diagnostic |
| `owner_replay_0520_latest` | `buy_and_hold_long` | -4.5907pct | 1 | full notional long, no cost diagnostic |
| `owner_replay_0520_latest` | `ma20_120_flip_no_cost` | +2.3710pct | 11906 | close-to-close diagnostic, no execution costs |
| `owner_replay_0520_latest` | `random_entry_seed284` | -0.7899pct | 10 | sum of full-notional random trade returns, no cost diagnostic |
| `owner_replay_0525_latest` | `buy_and_hold_long` | -4.9533pct | 1 | full notional long, no cost diagnostic |
| `owner_replay_0525_latest` | `ma20_120_flip_no_cost` | -0.3471pct | 4706 | close-to-close diagnostic, no execution costs |
| `owner_replay_0525_latest` | `random_entry_seed284` | +0.1913pct | 5 | sum of full-notional random trade returns, no cost diagnostic |

## Cost Verification

- Every persisted run is audited from trade metadata against the summary cost fields.
- A valid run must have zero formula mismatches and zero summary mismatches.
- Base and stress costs are decision-driving; zero-cost diagnostics are intentionally not used in Task 287.
- Run `1085` `T285_R3_CORE_SHORT_ONLY_B2` `full_0420_latest` `conservative_crypto_1m`: notional `87,713,793.76`, fee `87,713.79`, spread `26,314.14`, slippage `50,985.41`, total `165,013.34`, effective one-way cost `18.8127` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1086` `T285_R3_CORE_SHORT_ONLY_B2` `pre_owner_0420_0519` `conservative_crypto_1m`: notional `69,496,154.82`, fee `69,496.15`, spread `20,848.85`, slippage `41,024.25`, total `131,369.25`, effective one-way cost `18.9031` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1087` `T285_R3_CORE_SHORT_ONLY_B2` `owner_replay_0520_latest` `conservative_crypto_1m`: notional `19,894,873.84`, fee `19,894.87`, spread `5,968.46`, slippage `10,908.27`, total `36,771.61`, effective one-way cost `18.4830` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1088` `T285_R3_CORE_SHORT_ONLY_B2` `owner_replay_0525_latest` `conservative_crypto_1m`: notional `9,938,732.61`, fee `9,938.73`, spread `2,981.62`, slippage `5,632.12`, total `18,552.47`, effective one-way cost `18.6668` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1089` `T285_R3_CORE_SHORT_ONLY_B2` `w1_0420_0426` `conservative_crypto_1m`: notional `13,626,738.89`, fee `13,626.74`, spread `4,088.02`, slippage `8,117.48`, total `25,832.24`, effective one-way cost `18.9570` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1090` `T285_R3_CORE_SHORT_ONLY_B2` `w2_0427_0503` `conservative_crypto_1m`: notional `13,835,746.45`, fee `13,835.75`, spread `4,150.72`, slippage `7,603.02`, total `25,589.49`, effective one-way cost `18.4952` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1091` `T285_R3_CORE_SHORT_ONLY_B2` `w3_0504_0510` `conservative_crypto_1m`: notional `13,782,252.25`, fee `13,782.25`, spread `4,134.68`, slippage `7,563.03`, total `25,479.96`, effective one-way cost `18.4875` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1092` `T285_R3_CORE_SHORT_ONLY_B2` `w4_0511_0517` `conservative_crypto_1m`: notional `19,911,490.80`, fee `19,911.49`, spread `5,973.45`, slippage `10,976.42`, total `36,861.36`, effective one-way cost `18.5126` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1093` `T285_R3_CORE_SHORT_ONLY_B2` `w5_0518_0524` `conservative_crypto_1m`: notional `15,670,753.27`, fee `15,670.75`, spread `4,701.23`, slippage `8,414.12`, total `28,786.10`, effective one-way cost `18.3693` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1094` `T285_R3_CORE_SHORT_ONLY_B2` `w6_0525_latest` `conservative_crypto_1m`: notional `9,938,732.61`, fee `9,938.73`, spread `2,981.62`, slippage `5,632.12`, total `18,552.47`, effective one-way cost `18.6668` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1095` `T285_R3_CORE_SHORT_ONLY_B2` `wfo_0420_0503` `conservative_crypto_1m`: notional `28,568,124.52`, fee `28,568.12`, spread `8,570.44`, slippage `16,517.11`, total `53,655.67`, effective one-way cost `18.7817` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1096` `T285_R3_CORE_SHORT_ONLY_B2` `wfo_0504_0517` `conservative_crypto_1m`: notional `36,704,481.91`, fee `36,704.48`, spread `11,011.34`, slippage `20,434.39`, total `68,150.22`, effective one-way cost `18.5673` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1097` `T285_R3_CORE_SHORT_ONLY_B2` `wfo_0518_latest` `conservative_crypto_1m`: notional `25,602,103.98`, fee `25,602.10`, spread `7,680.63`, slippage `14,042.22`, total `47,324.96`, effective one-way cost `18.4848` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1098` `T285_R3_CORE_SHORT_ONLY_B2` `full_0420_drop_first_6h` `conservative_crypto_1m`: notional `87,713,793.76`, fee `87,713.79`, spread `26,314.14`, slippage `50,985.41`, total `165,013.34`, effective one-way cost `18.8127` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1099` `T285_R3_CORE_SHORT_ONLY_B2` `full_0420_drop_first_24h` `conservative_crypto_1m`: notional `85,790,441.57`, fee `85,790.44`, spread `25,737.13`, slippage `49,957.09`, total `161,484.67`, effective one-way cost `18.8232` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1100` `T285_R3_CORE_SHORT_ONLY_B2` `full_0420_drop_last_6h` `conservative_crypto_1m`: notional `86,021,662.27`, fee `86,021.66`, spread `25,806.50`, slippage `50,054.89`, total `161,883.05`, effective one-way cost `18.8189` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1101` `T285_R3_CORE_SHORT_ONLY_B2` `full_0420_drop_last_24h` `conservative_crypto_1m`: notional `82,649,129.78`, fee `82,649.13`, spread `24,794.74`, slippage `48,041.00`, total `155,484.87`, effective one-way cost `18.8126` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1102` `T285_R3_CORE_SHORT_ONLY_B2` `owner_0520_drop_last_12h` `conservative_crypto_1m`: notional `15,923,602.27`, fee `15,923.60`, spread `4,777.08`, slippage `8,605.12`, total `29,305.80`, effective one-way cost `18.4040` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1103` `T285_R3_CORE_SHORT_ONLY_B2` `owner_0520_drop_last_24h` `conservative_crypto_1m`: notional `13,933,116.55`, fee `13,933.12`, spread `4,179.93`, slippage `7,441.94`, total `25,554.99`, effective one-way cost `18.3412` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1104` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `full_0420_latest` `conservative_crypto_1m`: notional `97,480,108.68`, fee `97,480.11`, spread `29,244.03`, slippage `56,380.27`, total `183,104.41`, effective one-way cost `18.7838` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1105` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `pre_owner_0420_0519` `conservative_crypto_1m`: notional `77,426,403.60`, fee `77,426.40`, spread `23,227.92`, slippage `45,417.34`, total `146,071.67`, effective one-way cost `18.8659` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1106` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_replay_0520_latest` `conservative_crypto_1m`: notional `21,970,331.56`, fee `21,970.33`, spread `6,591.10`, slippage `12,032.06`, total `40,593.49`, effective one-way cost `18.4765` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1107` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_replay_0525_latest` `conservative_crypto_1m`: notional `10,416,282.34`, fee `10,416.28`, spread `3,124.88`, slippage `5,891.43`, total `19,432.60`, effective one-way cost `18.6560` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1108` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `w1_0420_0426` `conservative_crypto_1m`: notional `15,850,352.48`, fee `15,850.35`, spread `4,755.11`, slippage `9,379.00`, total `29,984.46`, effective one-way cost `18.9172` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1109` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `w2_0427_0503` `conservative_crypto_1m`: notional `15,741,552.39`, fee `15,741.55`, spread `4,722.47`, slippage `8,630.83`, total `29,094.85`, effective one-way cost `18.4828` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1110` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `w3_0504_0510` `conservative_crypto_1m`: notional `15,569,059.54`, fee `15,569.06`, spread `4,670.72`, slippage `8,526.54`, total `28,766.32`, effective one-way cost `18.4766` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1111` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `w4_0511_0517` `conservative_crypto_1m`: notional `21,424,185.38`, fee `21,424.19`, spread `6,427.26`, slippage `11,811.77`, total `39,663.21`, effective one-way cost `18.5133` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1112` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `w5_0518_0524` `conservative_crypto_1m`: notional `17,484,351.37`, fee `17,484.35`, spread `5,245.31`, slippage `9,401.11`, total `32,130.76`, effective one-way cost `18.3769` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1113` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `w6_0525_latest` `conservative_crypto_1m`: notional `10,416,282.34`, fee `10,416.28`, spread `3,124.88`, slippage `5,891.43`, total `19,432.60`, effective one-way cost `18.6560` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1114` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `wfo_0420_0503` `conservative_crypto_1m`: notional `32,758,635.09`, fee `32,758.64`, spread `9,827.59`, slippage `18,852.23`, total `61,438.45`, effective one-way cost `18.7549` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1115` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `wfo_0504_0517` `conservative_crypto_1m`: notional `40,052,089.97`, fee `40,052.09`, spread `12,015.63`, slippage `22,264.48`, total `74,332.19`, effective one-way cost `18.5589` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1116` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `wfo_0518_latest` `conservative_crypto_1m`: notional `28,156,267.16`, fee `28,156.27`, spread `8,446.88`, slippage `15,431.63`, total `52,034.77`, effective one-way cost `18.4807` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1117` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `full_0420_drop_first_6h` `conservative_crypto_1m`: notional `97,371,984.57`, fee `97,371.98`, spread `29,211.60`, slippage `56,312.54`, total `182,896.12`, effective one-way cost `18.7832` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1118` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `full_0420_drop_first_24h` `conservative_crypto_1m`: notional `95,282,939.34`, fee `95,282.94`, spread `28,584.88`, slippage `55,202.23`, total `179,070.05`, effective one-way cost `18.7935` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1119` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `full_0420_drop_last_6h` `conservative_crypto_1m`: notional `95,865,438.84`, fee `95,865.44`, spread `28,759.63`, slippage `55,493.00`, total `180,118.07`, effective one-way cost `18.7886` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1120` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `full_0420_drop_last_24h` `conservative_crypto_1m`: notional `92,487,979.68`, fee `92,487.98`, spread `27,746.39`, slippage `53,480.64`, total `173,715.02`, effective one-way cost `18.7824` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1121` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0520_drop_last_12h` `conservative_crypto_1m`: notional `18,039,057.80`, fee `18,039.06`, spread `5,411.72`, slippage `9,752.86`, total `33,203.63`, effective one-way cost `18.4065` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1122` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `owner_0520_drop_last_24h` `conservative_crypto_1m`: notional `15,968,496.92`, fee `15,968.50`, spread `4,790.55`, slippage `8,545.04`, total `29,304.09`, effective one-way cost `18.3512` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1123` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `full_0420_latest` `conservative_crypto_1m`: notional `97,725,921.35`, fee `97,725.92`, spread `29,317.78`, slippage `58,075.10`, total `185,118.80`, effective one-way cost `18.9427` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1124` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `pre_owner_0420_0519` `conservative_crypto_1m`: notional `77,609,132.00`, fee `77,609.13`, spread `23,282.74`, slippage `46,997.08`, total `147,888.95`, effective one-way cost `19.0556` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1125` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `owner_replay_0520_latest` `conservative_crypto_1m`: notional `21,970,384.07`, fee `21,970.38`, spread `6,591.12`, slippage `12,107.39`, total `40,668.89`, effective one-way cost `18.5108` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1126` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `owner_replay_0525_latest` `conservative_crypto_1m`: notional `10,416,123.91`, fee `10,416.12`, spread `3,124.84`, slippage `5,935.65`, total `19,476.61`, effective one-way cost `18.6985` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1127` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `w1_0420_0426` `conservative_crypto_1m`: notional `15,856,692.25`, fee `15,856.69`, spread `4,757.01`, slippage `9,821.09`, total `30,434.79`, effective one-way cost `19.1937` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1128` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `w2_0427_0503` `conservative_crypto_1m`: notional `15,738,856.13`, fee `15,738.86`, spread `4,721.66`, slippage `8,898.58`, total `29,359.10`, effective one-way cost `18.6539` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1129` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `w3_0504_0510` `conservative_crypto_1m`: notional `15,569,007.15`, fee `15,569.01`, spread `4,670.70`, slippage `8,527.12`, total `28,766.83`, effective one-way cost `18.4770` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1130` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `w4_0511_0517` `conservative_crypto_1m`: notional `21,423,273.32`, fee `21,423.27`, spread `6,426.98`, slippage `12,115.40`, total `39,965.66`, effective one-way cost `18.6553` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1131` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `w5_0518_0524` `conservative_crypto_1m`: notional `17,483,244.60`, fee `17,483.24`, spread `5,244.97`, slippage `9,505.08`, total `32,233.30`, effective one-way cost `18.4367` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1132` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `w6_0525_latest` `conservative_crypto_1m`: notional `10,416,123.91`, fee `10,416.12`, spread `3,124.84`, slippage `5,935.65`, total `19,476.61`, effective one-way cost `18.6985` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1133` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `wfo_0420_0503` `conservative_crypto_1m`: notional `32,773,966.87`, fee `32,773.97`, spread `9,832.19`, slippage `19,583.03`, total `62,189.18`, effective one-way cost `18.9752` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1134` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `wfo_0504_0517` `conservative_crypto_1m`: notional `40,029,380.30`, fee `40,029.38`, spread `12,008.81`, slippage `22,820.31`, total `74,858.50`, effective one-way cost `18.7009` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1135` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `wfo_0518_latest` `conservative_crypto_1m`: notional `28,154,682.61`, fee `28,154.68`, spread `8,446.40`, slippage `15,578.76`, total `52,179.84`, effective one-way cost `18.5333` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1136` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `full_0420_drop_first_6h` `conservative_crypto_1m`: notional `97,617,774.53`, fee `97,617.77`, spread `29,285.33`, slippage `58,008.22`, total `184,911.33`, effective one-way cost `18.9424` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1137` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `full_0420_drop_first_24h` `conservative_crypto_1m`: notional `95,518,674.75`, fee `95,518.67`, spread `28,655.60`, slippage `56,987.66`, total `181,161.94`, effective one-way cost `18.9661` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1138` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `full_0420_drop_last_6h` `conservative_crypto_1m`: notional `96,105,334.10`, fee `96,105.33`, spread `28,831.60`, slippage `57,142.20`, total `182,079.14`, effective one-way cost `18.9458` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1139` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `full_0420_drop_last_24h` `conservative_crypto_1m`: notional `92,716,324.91`, fee `92,716.32`, spread `27,814.90`, slippage `55,177.15`, total `175,708.37`, effective one-way cost `18.9512` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1140` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `owner_0520_drop_last_12h` `conservative_crypto_1m`: notional `18,039,101.25`, fee `18,039.10`, spread `5,411.73`, slippage `9,792.15`, total `33,242.99`, effective one-way cost `18.4283` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1141` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `owner_0520_drop_last_24h` `conservative_crypto_1m`: notional `15,968,561.69`, fee `15,968.56`, spread `4,790.57`, slippage `8,635.05`, total `29,394.18`, effective one-way cost `18.4075` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1142` `T285_R3_CORE_SHORT_ONLY_B2` `full_0420_latest` `cost_2x`: notional `80,157,437.85`, fee `160,314.88`, spread `48,094.46`, slippage `93,333.13`, total `301,742.46`, effective one-way cost `37.6437` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1143` `T285_R3_CORE_SHORT_ONLY_B2` `pre_owner_0420_0519` `cost_2x`: notional `64,753,219.14`, fee `129,506.44`, spread `38,851.93`, slippage `76,493.40`, total `244,851.77`, effective one-way cost `37.8131` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1144` `T285_R3_CORE_SHORT_ONLY_B2` `full_0420_latest` `cost_3x`: notional `73,471,369.40`, fee `220,414.11`, spread `66,124.23`, slippage `128,520.74`, total `415,059.08`, effective one-way cost `56.4926` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1145` `T285_R3_CORE_SHORT_ONLY_B2` `pre_owner_0420_0519` `cost_3x`: notional `60,444,300.17`, fee `181,332.90`, spread `54,399.87`, slippage `107,166.64`, total `342,899.41`, effective one-way cost `56.7298` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1146` `T285_R3_CORE_SHORT_ONLY_B2` `full_0420_latest` `high_slippage_stress`: notional `77,686,782.62`, fee `77,686.78`, spread `77,686.78`, slippage `187,422.46`, total `342,796.02`, effective one-way cost `44.1254` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1147` `T285_R3_CORE_SHORT_ONLY_B2` `pre_owner_0420_0519` `high_slippage_stress`: notional `63,148,395.52`, fee `63,148.40`, spread `63,148.40`, slippage `154,962.67`, total `281,259.46`, effective one-way cost `44.5394` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1148` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `full_0420_latest` `cost_2x`: notional `89,037,648.28`, fee `178,075.30`, spread `53,422.59`, slippage `103,106.51`, total `334,604.39`, effective one-way cost `37.5801` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1149` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `pre_owner_0420_0519` `cost_2x`: notional `72,108,352.04`, fee `144,216.70`, spread `43,265.01`, slippage `84,604.25`, total `272,085.97`, effective one-way cost `37.7329` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1150` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `full_0420_latest` `cost_3x`: notional `81,571,739.16`, fee `244,715.22`, spread `73,414.57`, slippage `141,836.84`, total `459,966.63`, effective one-way cost `56.3880` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1151` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `pre_owner_0420_0519` `cost_3x`: notional `67,279,093.20`, fee `201,837.28`, spread `60,551.18`, slippage `118,415.69`, total `380,804.16`, effective one-way cost `56.6007` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1152` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `full_0420_latest` `high_slippage_stress`: notional `86,320,069.95`, fee `86,320.07`, spread `86,320.07`, slippage `206,830.17`, total `379,470.31`, effective one-way cost `43.9608` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1153` `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002` `pre_owner_0420_0519` `high_slippage_stress`: notional `70,338,569.80`, fee `70,338.57`, spread `70,338.57`, slippage `171,160.26`, total `311,837.40`, effective one-way cost `44.3338` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1154` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `full_0420_latest` `cost_2x`: notional `89,183,068.20`, fee `178,366.14`, spread `53,509.84`, slippage `106,115.04`, total `337,991.01`, effective one-way cost `37.8986` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1155` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `pre_owner_0420_0519` `cost_2x`: notional `72,227,004.60`, fee `144,454.01`, spread `43,336.20`, slippage `87,446.12`, total `275,236.33`, effective one-way cost `38.1071` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1156` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `full_0420_latest` `cost_3x`: notional `81,637,430.83`, fee `244,912.29`, spread `73,473.69`, slippage `145,856.58`, total `464,242.56`, effective one-way cost `56.8664` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1157` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `pre_owner_0420_0519` `cost_3x`: notional `67,344,165.24`, fee `202,032.50`, spread `60,609.75`, slippage `122,258.34`, total `384,900.58`, effective one-way cost `57.1543` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1158` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `full_0420_latest` `high_slippage_stress`: notional `86,250,513.57`, fee `86,250.51`, spread `86,250.51`, slippage `213,535.15`, total `386,036.17`, effective one-way cost `44.7576` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.
- Run `1159` `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002` `pre_owner_0420_0519` `high_slippage_stress`: notional `70,318,267.76`, fee `70,318.27`, spread `70,318.27`, slippage `177,651.14`, total `318,287.68`, effective one-way cost `45.2639` bps, formula mismatch `0`, summary mismatch `0`, max mismatch `0.00000000`.

## Overfit And Failure Diagnostics

- Owner windows are reported but do not promote a model by themselves.
- The independent promotion evidence is the six weekly windows from 2026-04-20 forward plus the separate pre-owner gate.
- Return concentration is checked by removing the top three event winners from full and weekly aggregates.
- Cost fragility is checked by 2x/3x/high-slippage stress on the full repaired window.
- A candidate with fewer than 50 completed round trips on the full window is rejected as insufficient sample even if return is high.

## Implementation Checklist

- Look-ahead bias: inherited completed-candle factor construction; no future candle fields are used for entry signals.
- Candle close signal: yes for inherited signal candidates.
- Next candle execution: inherited Task 283 B2 shifted execution for Task 283/285 candidates.
- Stop/take intrabar ambiguity: conservative stop-first inherited from source runners.
- Long/short separation: side attribution recorded for every persisted run.
- Fee both ways: engine cost summary and trade-level audit recorded.
- Slippage/spread: base, 2x, 3x, and high-slippage stress profiles recorded.
- Position overlap: inherited deterministic action generation and engine open-position guard.
- Data gaps and duplicates: checked before simulation and per-window during each run.
- Trade log, entry/exit reason, factor snapshot: persisted through strategy-engine trade metadata.
- Paper/live trading: not performed.

## Conclusion

- Final status: `LOCKED_PRIMARY_REJECTED_RESEARCH_ONLY`.
- Interpretation: Primary Task 285 candidate did not pass locked repaired-data validation: Full 0420 latest return, Pre-owner 0420-0519 return, Independent positive fraction, Independent aggregate return, Single-window winner concentration, Independent return without top-three winners, Full return without top-three winners, Full top-three winner contribution, Full cost/gross PnL, Independent cost/gross PnL, 2x cost full return, 3x cost full return.
- No strategy is promoted to live or paper trading by this task; this is a locked offline validation record.
