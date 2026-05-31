# Task 285 Regime-Robust Multi-Window Strategy Repair

Status: `ROBUSTNESS_REJECTED_RESEARCH_ONLY`

## Purpose

- Repair or reject the Task 283/284 candidate using configurable, gap-aware, non-overlapping BTCUSDT 1m validation windows.
- Result scope: offline research-only, no live trading, no exchange orders, no futures/leverage.

## Data Coverage

- Requested April-20-forward start: `2026-04-20T00:00:00Z`.
- Local available start: `2026-05-10T00:00:00Z`.
- Local available end: `2026-05-28T08:26:00Z`.
- Closed candle count from requested start: `23027`.
- Continuity gaps: `1`.
- April-20-forward complete: `False`.

| Gap Previous Candle | Gap Next Candle | Missing 1m Candles |
| --- | --- | ---: |
| `2026-05-17T15:19:00Z` | `2026-05-20T00:00:00Z` | 3400 |

### Complete Local Ranges

| Start | End | Candles |
| --- | --- | ---: |
| `2026-05-10T00:00:00Z` | `2026-05-17T15:19:00Z` | 11000 |
| `2026-05-20T00:00:00Z` | `2026-05-28T08:26:00Z` | 12027 |

## Candidate Repair Set

| Candidate | Family | Repair Mode | Thesis |
| --- | --- | --- | --- |
| `T285_BASE_LOCKED_B2` | `BASELINE_LOCKED_TASK283_B2` | `baseline_no_repair` | Locked Task 283/284 candidate replayed as the rejected baseline. |
| `T285_R1_SHORT_ONLY_B2` | `SINGLE_SIDE_FAILED_RALLY_SHORT` | `short_only` | Task 284 showed the edge was short-side concentrated, so this repair turns off the losing long sleeve and retests the thesis as a declared single-side failed-rally short model. |
| `T285_R2_SHORT_REGIME_B2` | `REGIME_FILTERED_FAILED_RALLY_SHORT` | `short_regime_filter` | Short only when completed 15m/1h return pressure is not bullish and participation is adequate, reducing shorts in rebound or thin-drift regimes. |
| `T285_R3_CORE_SHORT_ONLY_B2` | `CORE_ONLY_BEARISH_LIQUIDITY_SWEEP_SHORT` | `core_short_only` | Keep only the full-size core short layer and remove the small activity scout sleeve to test whether the signal survives without turnover padding. |

## Persisted Runs

- Task 285 run IDs: `1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050, 1051, 1052`.

| Candidate | Group | Window | Role | Cost | Run | Return | Trips | Win | PF | Gross | Net | Cost | Cost/Gross | Formula MM | Summary MM | Status |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| T285_BASE_LOCKED_B2 | independent_primary | available_pre_owner_0510_0517 | independent | conservative_crypto_1m | 1001 | -2.6638pct | 54 | 0.1667 | 0.6199 | 20,150.20 | -26,638.39 | 46,788.59 | 2.3220 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_BASE_LOCKED_B2 | independent_primary | owner_segment_0520_0522 | independent | conservative_crypto_1m | 1002 | +0.0644pct | 14 | 0.0714 | 1.5002 | 5,265.19 | 643.64 | 4,621.54 | 0.8778 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_BASE_LOCKED_B2 | independent_primary | owner_segment_0522_0524 | independent | conservative_crypto_1m | 1003 | +2.3701pct | 11 | 0.3636 | 31.0540 | 31,595.22 | 23,700.57 | 7,894.66 | 0.2499 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_BASE_LOCKED_B2 | independent_primary | owner_segment_0524_0526 | independent | conservative_crypto_1m | 1004 | -0.1210pct | 15 | 0.0667 | 0.0173 | -103.53 | -1,209.68 | 1,106.16 | 10.6847 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_BASE_LOCKED_B2 | independent_primary | owner_segment_0526_latest | independent | conservative_crypto_1m | 1005 | +2.8464pct | 10 | 0.4000 | 56.2325 | 43,788.90 | 28,464.42 | 15,324.47 | 0.3500 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R1_SHORT_ONLY_B2 | independent_primary | available_pre_owner_0510_0517 | independent | conservative_crypto_1m | 1006 | -2.4856pct | 32 | 0.1875 | 0.6346 | 20,356.83 | -24,855.91 | 45,212.74 | 2.2210 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R1_SHORT_ONLY_B2 | independent_primary | owner_segment_0520_0522 | independent | conservative_crypto_1m | 1007 | +0.1365pct | 5 | 0.2000 | 3.4130 | 5,329.46 | 1,365.31 | 3,964.15 | 0.7438 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R1_SHORT_ONLY_B2 | independent_primary | owner_segment_0522_0524 | independent | conservative_crypto_1m | 1008 | +2.3770pct | 6 | 0.3333 | 44.8084 | 31,290.99 | 23,770.32 | 7,520.67 | 0.2403 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R1_SHORT_ONLY_B2 | independent_primary | owner_segment_0524_0526 | independent | conservative_crypto_1m | 1009 | -0.0565pct | 6 | 0.0000 | 0.0000 | -123.94 | -564.55 | 440.61 | 3.5549 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R1_SHORT_ONLY_B2 | independent_primary | owner_segment_0526_latest | independent | conservative_crypto_1m | 1010 | +2.8464pct | 10 | 0.4000 | 56.2325 | 43,788.90 | 28,464.42 | 15,324.47 | 0.3500 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R2_SHORT_REGIME_B2 | independent_primary | available_pre_owner_0510_0517 | independent | conservative_crypto_1m | 1011 | -5.0368pct | 19 | 0.1053 | 0.1396 | -17,072.60 | -50,367.63 | 33,295.04 | 1.9502 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R2_SHORT_REGIME_B2 | independent_primary | owner_segment_0520_0522 | independent | conservative_crypto_1m | 1012 | -0.0447pct | 3 | 0.0000 | 0.0000 | -224.91 | -447.44 | 222.53 | 0.9895 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R2_SHORT_REGIME_B2 | independent_primary | owner_segment_0522_0524 | independent | conservative_crypto_1m | 1013 | -0.0224pct | 1 | 0.0000 | 0.0000 | -150.83 | -223.85 | 73.02 | 0.4841 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R2_SHORT_REGIME_B2 | independent_primary | owner_segment_0524_0526 | independent | conservative_crypto_1m | 1014 | -0.0189pct | 2 | 0.0000 | 0.0000 | -41.44 | -188.92 | 147.48 | 3.5586 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R2_SHORT_REGIME_B2 | independent_primary | owner_segment_0526_latest | independent | conservative_crypto_1m | 1015 | +1.7457pct | 4 | 0.5000 | 127.0900 | 24,932.43 | 17,456.70 | 7,475.73 | 0.2998 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | independent_primary | available_pre_owner_0510_0517 | independent | conservative_crypto_1m | 1016 | -2.3490pct | 12 | 0.2500 | 0.6473 | 20,265.25 | -23,490.17 | 43,755.42 | 2.1591 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | independent_primary | owner_segment_0520_0522 | independent | conservative_crypto_1m | 1017 | +0.1932pct | 1 | 1.0000 | - | 5,600.31 | 1,931.58 | 3,668.72 | 0.6551 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | independent_primary | owner_segment_0522_0524 | independent | conservative_crypto_1m | 1018 | +2.4315pct | 2 | 1.0000 | - | 31,545.37 | 24,315.05 | 7,230.32 | 0.2292 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | independent_primary | owner_segment_0524_0526 | independent | conservative_crypto_1m | 1019 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | independent_primary | owner_segment_0526_latest | independent | conservative_crypto_1m | 1020 | +2.8981pct | 4 | 1.0000 | - | 43,860.62 | 28,980.55 | 14,880.07 | 0.3393 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | owner_overlap_diagnostic | owner_0520_full | diagnostic | conservative_crypto_1m | 1041 | +6.1764pct | 10 | 0.9000 | 40.2016 | 98,535.63 | 61,764.02 | 36,771.61 | 0.3732 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | owner_overlap_diagnostic | owner_0525_full | diagnostic | conservative_crypto_1m | 1042 | +3.6703pct | 5 | 1.0000 | - | 55,255.84 | 36,703.37 | 18,552.47 | 0.3358 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | available_pre_owner_0510_0517 | independent | cost_2x | 1043 | -6.6079pct | 12 | 0.2500 | 0.3238 | 19,506.42 | -66,079.36 | 85,585.79 | 4.3876 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | owner_segment_0520_0522 | independent | cost_2x | 1044 | -0.1734pct | 1 | 0.0000 | 0.0000 | 5,590.18 | -1,734.00 | 7,324.18 | 1.3102 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | owner_segment_0522_0524 | independent | cost_2x | 1045 | +1.7061pct | 2 | 1.0000 | - | 31,508.25 | 17,060.81 | 14,447.45 | 0.4585 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | owner_segment_0524_0526 | independent | cost_2x | 1046 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | owner_segment_0526_latest | independent | cost_2x | 1047 | +1.4067pct | 4 | 0.7500 | 9.2463 | 43,734.10 | 14,066.52 | 29,667.58 | 0.6784 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | available_pre_owner_0510_0517 | independent | cost_3x | 1048 | -10.6811pct | 12 | 0.2500 | 0.1626 | 18,765.19 | -106,810.62 | 125,575.81 | 6.6920 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | owner_segment_0520_0522 | independent | cost_3x | 1049 | -0.5386pct | 1 | 0.0000 | 0.0000 | 5,580.09 | -5,386.35 | 10,966.44 | 1.9653 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | owner_segment_0522_0524 | independent | cost_3x | 1050 | +0.9820pct | 2 | 1.0000 | - | 31,471.27 | 9,819.80 | 21,651.47 | 0.6880 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | owner_segment_0524_0526 | independent | cost_3x | 1051 | +0.0000pct | 0 | - | - | 0.00 | 0.00 | 0.00 | - | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| T285_R3_CORE_SHORT_ONLY_B2 | cost_stress | owner_segment_0526_latest | independent | cost_3x | 1052 | -0.0837pct | 4 | 0.2500 | 0.9073 | 43,335.04 | -837.27 | 44,172.32 | 1.0193 | 0 | 0 | COMPLETED_RESEARCH_ONLY |

## Candidate Aggregates

| Candidate | Windows | Positive | Return | Trips | Gross | Net | Cost | Max Window Contrib | No Top3 Return | Long Net | Short Net | Cost MM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T285_BASE_LOCKED_B2 | 5 | 0.6000 | +2.4961pct | 104 | 100,695.98 | 24,960.56 | 75,735.42 | 0.5390 | -2.9257pct | -3,225.52 | 28,186.09 | 0 |
| T285_R1_SHORT_ONLY_B2 | 5 | 0.6000 | +2.8180pct | 59 | 100,642.24 | 28,179.59 | 72,462.65 | 0.5311 | -2.6072pct | 0.00 | 28,179.59 | 0 |
| T285_R2_SHORT_REGIME_B2 | 5 | 0.2000 | -3.3771pct | 29 | 7,442.65 | -33,771.15 | 41,213.80 | 1.0000 | -5.9511pct | 0.00 | -33,771.15 | 0 |
| T285_R3_CORE_SHORT_ONLY_B2 | 5 | 0.6000 | +3.1737pct | 19 | 101,271.55 | 31,737.02 | 69,534.53 | 0.5248 | -2.2531pct | 0.00 | 31,737.02 | 0 |

## Gate Check

- Selected candidate: `T285_R3_CORE_SHORT_ONLY_B2`.

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Independent complete windows | >= 4 when data allows | 5 | `PASS` |
| Total completed round trips | >= 50 | 19 | `FAIL` |
| Positive independent windows | >= 75pct | 0.6000 | `FAIL` |
| Aggregate independent return | >= +3pct | +3.1737pct | `PASS` |
| Single-window net contribution | <= 60pct | 0.5248 | `PASS` |
| Return without top-three winners | > 0pct | -2.2531pct | `FAIL` |
| Cost audit mismatches | 0 | 0 | `PASS` |
| Earliest OOS cost domination | not gross positive / net negative | True | `FAIL` |
| Side classification | single-side declared or both sleeves healthy | SHORT | `PASS` |
| 2x cost stress | > -1pct aggregate | -3.6686pct | `FAIL` |
| 3x cost stress | reported | -10.3214pct | `PASS` |
| Formula and summary cost audit | 0 mismatches | 0 | `PASS` |
| Fixed owner windows not sole proof | independent windows used | 5 | `PASS` |

## Cost Audit

- Run `1001` `T285_BASE_LOCKED_B2` `available_pre_owner_0510_0517` `conservative_crypto_1m`: notional `25,137,760.50`, fee `25,137.76`, spread `7,541.33`, slippage `14,109.50`, total `46,788.59`, one-way cost `18.6129` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1002` `T285_BASE_LOCKED_B2` `owner_segment_0520_0522` `conservative_crypto_1m`: notional `2,509,649.50`, fee `2,509.65`, spread `752.89`, slippage `1,359.00`, total `4,621.54`, one-way cost `18.4151` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1003` `T285_BASE_LOCKED_B2` `owner_segment_0522_0524` `conservative_crypto_1m`: notional `4,325,129.59`, fee `4,325.13`, spread `1,297.54`, slippage `2,271.99`, total `7,894.66`, one-way cost `18.2530` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1004` `T285_BASE_LOCKED_B2` `owner_segment_0524_0526` `conservative_crypto_1m`: notional `600,144.36`, fee `600.14`, spread `180.04`, slippage `325.97`, total `1,106.16`, one-way cost `18.4315` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1005` `T285_BASE_LOCKED_B2` `owner_segment_0526_latest` `conservative_crypto_1m`: notional `8,192,110.56`, fee `8,192.11`, spread `2,457.63`, slippage `4,674.73`, total `15,324.47`, one-way cost `18.7064` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1006` `T285_R1_SHORT_ONLY_B2` `available_pre_owner_0510_0517` `conservative_crypto_1m`: notional `24,289,605.36`, fee `24,289.61`, spread `7,286.88`, slippage `13,636.26`, total `45,212.74`, one-way cost `18.6140` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1007` `T285_R1_SHORT_ONLY_B2` `owner_segment_0520_0522` `conservative_crypto_1m`: notional `2,150,576.62`, fee `2,150.58`, spread `645.17`, slippage `1,168.40`, total `3,964.15`, one-way cost `18.4330` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1008` `T285_R1_SHORT_ONLY_B2` `owner_segment_0522_0524` `conservative_crypto_1m`: notional `4,124,825.36`, fee `4,124.83`, spread `1,237.45`, slippage `2,158.40`, total `7,520.67`, one-way cost `18.2327` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1009` `T285_R1_SHORT_ONLY_B2` `owner_segment_0524_0526` `conservative_crypto_1m`: notional `240,123.94`, fee `240.12`, spread `72.04`, slippage `128.45`, total `440.61`, one-way cost `18.3493` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1010` `T285_R1_SHORT_ONLY_B2` `owner_segment_0526_latest` `conservative_crypto_1m`: notional `8,192,110.56`, fee `8,192.11`, spread `2,457.63`, slippage `4,674.73`, total `15,324.47`, one-way cost `18.7064` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1011` `T285_R2_SHORT_REGIME_B2` `available_pre_owner_0510_0517` `conservative_crypto_1m`: notional `17,867,541.53`, fee `17,867.54`, spread `5,360.26`, slippage `10,067.23`, total `33,295.04`, one-way cost `18.6344` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1012` `T285_R2_SHORT_REGIME_B2` `owner_segment_0520_0522` `conservative_crypto_1m`: notional `120,224.91`, fee `120.22`, spread `36.07`, slippage `66.24`, total `222.53`, one-way cost `18.5098` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1013` `T285_R2_SHORT_REGIME_B2` `owner_segment_0522_0524` `conservative_crypto_1m`: notional `40,150.83`, fee `40.15`, spread `12.05`, slippage `20.82`, total `73.02`, one-way cost `18.1854` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1014` `T285_R2_SHORT_REGIME_B2` `owner_segment_0524_0526` `conservative_crypto_1m`: notional `80,041.44`, fee `80.04`, spread `24.01`, slippage `43.43`, total `147.48`, one-way cost `18.4255` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1015` `T285_R2_SHORT_REGIME_B2` `owner_segment_0526_latest` `conservative_crypto_1m`: notional `4,051,164.44`, fee `4,051.16`, spread `1,215.35`, slippage `2,209.22`, total `7,475.73`, one-way cost `18.4533` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1016` `T285_R3_CORE_SHORT_ONLY_B2` `available_pre_owner_0510_0517` `conservative_crypto_1m`: notional `23,505,170.28`, fee `23,505.17`, spread `7,051.55`, slippage `13,198.70`, total `43,755.42`, one-way cost `18.6152` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1017` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0520_0522` `conservative_crypto_1m`: notional `1,990,777.05`, fee `1,990.78`, spread `597.23`, slippage `1,080.71`, total `3,668.72`, one-way cost `18.4286` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1018` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0522_0524` `conservative_crypto_1m`: notional `3,964,824.17`, fee `3,964.82`, spread `1,189.45`, slippage `2,076.04`, total `7,230.32`, one-way cost `18.2362` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1019` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0524_0526` `conservative_crypto_1m`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, one-way cost `-` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1020` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0526_latest` `conservative_crypto_1m`: notional `7,952,393.92`, fee `7,952.39`, spread `2,385.72`, slippage `4,541.96`, total `14,880.07`, one-way cost `18.7114` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1041` `T285_R3_CORE_SHORT_ONLY_B2` `owner_0520_full` `conservative_crypto_1m`: notional `19,894,873.84`, fee `19,894.87`, spread `5,968.46`, slippage `10,908.27`, total `36,771.61`, one-way cost `18.4830` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1042` `T285_R3_CORE_SHORT_ONLY_B2` `owner_0525_full` `conservative_crypto_1m`: notional `9,938,732.61`, fee `9,938.73`, spread `2,981.62`, slippage `5,632.12`, total `18,552.47`, one-way cost `18.6668` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1043` `T285_R3_CORE_SHORT_ONLY_B2` `available_pre_owner_0510_0517` `cost_2x`: notional `22,986,746.15`, fee `45,973.49`, spread `13,792.05`, slippage `25,820.25`, total `85,585.79`, one-way cost `37.2327` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1044` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0520_0522` `cost_2x`: notional `1,987,177.63`, fee `3,974.36`, spread `1,192.31`, slippage `2,157.52`, total `7,324.18`, one-way cost `36.8572` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1045` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0522_0524` `cost_2x`: notional `3,961,243.98`, fee `7,922.49`, spread `2,376.75`, slippage `4,148.21`, total `14,447.45`, one-way cost `36.4720` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1046` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0524_0526` `cost_2x`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, one-way cost `-` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1047` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0526_latest` `cost_2x`: notional `7,927,780.57`, fee `15,855.56`, spread `4,756.67`, slippage `9,055.35`, total `29,667.58`, one-way cost `37.4223` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1048` `T285_R3_CORE_SHORT_ONLY_B2` `available_pre_owner_0510_0517` `cost_3x`: notional `22,483,510.37`, fee `67,450.53`, spread `20,235.16`, slippage `37,890.12`, total `125,575.81`, one-way cost `55.8524` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1049` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0520_0522` `cost_3x`: notional `1,983,591.20`, fee `5,950.77`, spread `1,785.23`, slippage `3,230.44`, total `10,966.44`, one-way cost `55.2858` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1050` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0522_0524` `cost_3x`: notional `3,957,676.74`, fee `11,873.03`, spread `3,561.91`, slippage `6,216.53`, total `21,651.47`, one-way cost `54.7075` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1051` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0524_0526` `cost_3x`: notional `0.00`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, one-way cost `-` bps, formula mismatch `0`, summary mismatch `0`.
- Run `1052` `T285_R3_CORE_SHORT_ONLY_B2` `owner_segment_0526_latest` `cost_3x`: notional `7,869,265.33`, fee `23,607.80`, spread `7,082.34`, slippage `13,482.18`, total `44,172.32`, one-way cost `56.1327` bps, formula mismatch `0`, summary mismatch `0`.

## Selected Candidate Attribution

### Side Aggregate

| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SHORT | 19 | 0.5263 | 101,271.55 | 69,534.53 | 31,737.02 | 1,670.37 |

### Session Aggregate

| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ASIA | 9 | 0.4444 | 27,069.93 | 32,909.22 | -5,839.29 | -648.81 |
| EUROPE | 2 | 0.5000 | 24,955.66 | 7,120.70 | 17,834.97 | 8,917.48 |
| LATE_US | 2 | 1.0000 | 31,110.69 | 7,207.30 | 23,903.39 | 11,951.70 |
| US | 6 | 0.5000 | 18,135.26 | 22,297.32 | -4,162.06 | -693.68 |

### Regime Aggregate

| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| trend_ALIGNED | 8 | 0.3750 | 10,087.58 | 29,751.81 | -19,664.23 | -2,458.03 |
| trend_COUNTER | 11 | 0.6364 | 91,183.97 | 39,782.72 | 51,401.25 | 4,672.84 |
| vol_HIGH | 10 | 0.5000 | 40,891.41 | 36,983.78 | 3,907.63 | 390.76 |
| vol_LOW | 9 | 0.5556 | 60,380.13 | 32,550.75 | 27,829.38 | 3,092.15 |
| volume_EXPANSION | 11 | 0.3636 | 19,893.27 | 40,448.53 | -20,555.25 | -1,868.66 |
| volume_NORMAL | 8 | 0.7500 | 81,378.27 | 29,086.00 | 52,292.27 | 6,536.53 |

## Bias And Safety Checks

- Signal/entry separation: inherited Task 283 B2 next-open entry and next-open-after-exit-condition behavior.
- Completed-candle factors: inherited Task 283 factor snapshots; no future candle fields are used for entries.
- Incomplete windows: skipped unless a window explicitly allows incomplete diagnostics.
- Fixed owner windows: diagnostic-only in Task 285 gate logic.
- Cost handling: entry/exit taker fees, spread, slippage, minimum slippage, and volatility slippage are included.
- Stress handling: selected repair candidate is retested at 2x and 3x cost assumptions.
- Live trading safety: no execution client imports, no signed requests, no API keys, no `.env` handling, no order/account endpoints.

## Conclusion

- Final status: `ROBUSTNESS_REJECTED_RESEARCH_ONLY`.
- Failed gates: `Total completed round trips, Positive independent windows, Return without top-three winners, Earliest OOS cost domination, 2x cost stress`.
- Interpretation: selected `T285_R3_CORE_SHORT_ONLY_B2` with aggregate independent return +3.1737pct; 19 independent trips; complete April-20-forward data remains unavailable; failed gates: Total completed round trips, Positive independent windows, Return without top-three winners, Earliest OOS cost domination, 2x cost stress.
- No Task 285 result is promoted beyond research-only unless the status is explicitly `ROBUST_MULTI_WINDOW_RESEARCH_CANDIDATE` and a later task assigns paper-trading design.
