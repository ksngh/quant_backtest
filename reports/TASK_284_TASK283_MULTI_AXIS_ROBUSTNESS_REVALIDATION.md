# Task 284 Task 283 Multi-Axis Robustness Revalidation

Status: `ROBUSTNESS_REJECTED_RESEARCH_ONLY`

## Locked Model

- Parent task: `TASK_283`.
- Locked candidate: `T283_B2_LSR_MTF_ACTIVITY_SHIFTED_EXIT_CF100_SCOUT002`.
- Retune policy: no entry threshold, exit threshold, sizing, or signal logic retuning in primary validation.
- Diagnostic-only variants are excluded from promotion decisions.
- Result scope: offline research-only, no live trading.

## Data Coverage

- Requested April-20-forward start: `2026-04-20T00:00:00Z`.
- Local available start: `2026-05-10T00:00:00Z`.
- Local available end: `2026-05-28T08:26:00Z`.
- Closed candle count from requested start: `23027`.
- Continuity gap count: `1`.
- April-20-forward complete: `False`.

| Gap Previous Candle | Gap Next Candle | Missing 1m Candles |
| --- | --- | ---: |
| `2026-05-17T15:19:00Z` | `2026-05-20T00:00:00Z` | 3400 |

## Persisted Validation Runs

- Task 284 run IDs: `960, 961, 962, 963, 964, 965, 966, 967, 968, 969, 970, 971, 972, 973, 974, 975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985, 986, 987, 988, 989, 990, 991, 992, 993`.

| Axis | Group | Window | Action Mode | Cost | Run | Return | Trips | Win | PF | Gross | Net | Cost | Cost/Gross | Cost bps | Formula MM | Summary MM | Status |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| owner_replay | owner_replay | owner_0520_latest | locked_b2 | conservative_crypto_1m | 960 | +5.7327pct | 62 | 0.1935 | 10.2198 | 97,920.81 | 57,327.32 | 40,593.49 | 0.4146 | 18.4765 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| owner_replay | owner_replay | owner_0525_latest | locked_b2 | conservative_crypto_1m | 961 | +3.5337pct | 17 | 0.2941 | 27.0253 | 54,769.80 | 35,337.20 | 19,432.60 | 0.3548 | 18.6560 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| pre_owner | pre_owner | available_pre_owner_0510_0517 | locked_b2 | conservative_crypto_1m | 962 | -2.6638pct | 54 | 0.1667 | 0.6199 | 20,150.20 | -26,638.39 | 46,788.59 | 2.3220 | 18.6129 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0520_latest_drop_first_6h | locked_b2 | conservative_crypto_1m | 963 | +5.7599pct | 59 | 0.2203 | 10.6644 | 97,976.50 | 57,598.74 | 40,377.76 | 0.4121 | 18.4779 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0520_latest_drop_last_6h | locked_b2 | conservative_crypto_1m | 964 | +4.1774pct | 62 | 0.1774 | 7.8153 | 78,777.52 | 41,773.79 | 37,003.73 | 0.4697 | 18.4746 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0520_latest_drop_first_12h | locked_b2 | conservative_crypto_1m | 965 | +5.7776pct | 56 | 0.2143 | 11.0101 | 97,935.10 | 57,776.32 | 40,158.77 | 0.4101 | 18.4784 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0520_latest_drop_last_12h | locked_b2 | conservative_crypto_1m | 966 | +3.5991pct | 61 | 0.1803 | 6.7037 | 69,194.57 | 35,990.93 | 33,203.63 | 0.4799 | 18.4065 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0520_latest_drop_first_24h | locked_b2 | conservative_crypto_1m | 967 | +5.6064pct | 53 | 0.2075 | 11.1104 | 92,396.31 | 56,063.78 | 36,332.53 | 0.3932 | 18.4844 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0520_latest_drop_last_24h | locked_b2 | conservative_crypto_1m | 968 | +3.0529pct | 58 | 0.1552 | 6.0963 | 59,832.81 | 30,528.73 | 29,304.09 | 0.4898 | 18.3512 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_split | endpoint_split | owner_0520_latest_first_half | locked_b2 | conservative_crypto_1m | 969 | +2.3201pct | 29 | 0.2069 | 7.4574 | 43,166.69 | 23,201.21 | 19,965.48 | 0.4625 | 18.3078 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_split | endpoint_split | owner_0520_latest_second_half | locked_b2 | conservative_crypto_1m | 970 | +3.4753pct | 26 | 0.1923 | 18.9513 | 54,846.07 | 34,753.42 | 20,092.64 | 0.3663 | 18.6487 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0525_latest_drop_first_6h | locked_b2 | conservative_crypto_1m | 971 | +3.7545pct | 15 | 0.3333 | 34.2455 | 56,807.45 | 37,544.60 | 19,262.85 | 0.3391 | 18.6312 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0525_latest_drop_last_6h | locked_b2 | conservative_crypto_1m | 972 | +1.9784pct | 17 | 0.2353 | 16.5848 | 35,626.51 | 19,783.67 | 15,842.84 | 0.4447 | 18.6927 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0525_latest_drop_first_12h | locked_b2 | conservative_crypto_1m | 973 | +3.4806pct | 14 | 0.2857 | 30.7305 | 50,418.97 | 34,805.73 | 15,613.24 | 0.3097 | 18.7117 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0525_latest_drop_last_12h | locked_b2 | conservative_crypto_1m | 974 | +1.4001pct | 16 | 0.2500 | 10.6550 | 26,043.55 | 14,000.81 | 12,042.74 | 0.4624 | 18.5701 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0525_latest_drop_first_24h | locked_b2 | conservative_crypto_1m | 975 | +2.8464pct | 10 | 0.4000 | 56.2325 | 43,788.90 | 28,464.42 | 15,324.47 | 0.3500 | 18.7064 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_trim | endpoint_trim | owner_0525_latest_drop_last_24h | locked_b2 | conservative_crypto_1m | 976 | +0.8539pct | 13 | 0.1538 | 8.5542 | 16,681.80 | 8,538.61 | 8,143.19 | 0.4881 | 18.4467 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_split | endpoint_split | owner_0525_latest_first_half | locked_b2 | conservative_crypto_1m | 977 | -0.0148pct | 9 | 0.2222 | 0.8373 | 4,117.31 | -147.83 | 4,265.14 | 1.0359 | 18.4553 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| endpoint_split | endpoint_split | owner_0525_latest_second_half | locked_b2 | conservative_crypto_1m | 978 | +1.5089pct | 9 | 0.2222 | 9.0562 | 23,085.18 | 15,089.44 | 7,995.74 | 0.3464 | 18.8363 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0520_latest | locked_b2 | fee_2x | 979 | +3.5297pct | 62 | 0.1290 | 4.0586 | 97,772.22 | 35,296.74 | 62,475.48 | 0.6390 | 28.4767 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0520_latest | locked_b2 | slippage_2x | 980 | +4.5266pct | 62 | 0.1613 | 6.2014 | 97,855.86 | 45,265.51 | 52,590.35 | 0.5374 | 23.9532 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0520_latest | locked_b2 | fee_slippage_2x | 981 | +2.3229pct | 62 | 0.1290 | 2.4667 | 97,635.38 | 23,229.28 | 74,406.10 | 0.7621 | 33.9536 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0520_latest | locked_b2 | high_slippage_stress | 982 | +0.4570pct | 62 | 0.1290 | 1.2051 | 96,813.43 | 4,570.47 | 92,242.96 | 0.9528 | 42.3815 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0520_latest | locked_b2 | zero | 983 | +9.7958pct | 62 | 0.5161 | 57.1012 | 97,958.01 | 97,958.01 | 0.00 | 0.0000 | 0.0000 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0525_latest | locked_b2 | fee_2x | 984 | +2.4900pct | 17 | 0.2353 | 8.9965 | 54,723.71 | 24,899.58 | 29,824.13 | 0.5450 | 28.6562 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0525_latest | locked_b2 | slippage_2x | 985 | +2.9432pct | 17 | 0.2353 | 15.8111 | 54,744.31 | 29,431.77 | 25,312.54 | 0.4624 | 24.3122 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0525_latest | locked_b2 | fee_slippage_2x | 986 | +1.9000pct | 17 | 0.2353 | 5.2652 | 54,683.72 | 18,999.73 | 35,683.99 | 0.6526 | 34.3124 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0525_latest | locked_b2 | high_slippage_stress | 987 | +0.9603pct | 17 | 0.2353 | 2.4771 | 54,448.63 | 9,602.54 | 44,846.08 | 0.8236 | 43.2793 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | cost_sensitivity | owner_0525_latest | locked_b2 | zero | 988 | +5.4805pct | 17 | 0.5294 | 92.1787 | 54,804.99 | 54,804.99 | 0.00 | 0.0000 | 0.0000 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| cost_sensitivity | pre_owner_cost_stress | available_pre_owner_0510_0517 | locked_b2 | high_slippage_stress | 989 | -8.6028pct | 54 | 0.0926 | 0.2469 | 19,083.69 | -86,027.52 | 105,111.21 | 5.5079 | 43.0713 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| execution_assumption | execution_assumption | owner_0520_latest | b1_same_candle_exit | conservative_crypto_1m | 990 | +3.1105pct | 79 | 0.1646 | 3.9902 | 58,887.97 | 31,104.70 | 27,783.27 | 0.4718 | 18.7056 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| execution_assumption | execution_assumption | owner_0525_latest | b1_same_candle_exit | conservative_crypto_1m | 991 | +1.4767pct | 23 | 0.2609 | 3.3868 | 31,290.42 | 14,767.08 | 16,523.34 | 0.5281 | 18.9725 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| execution_assumption | execution_assumption | owner_0520_latest | one_candle_delayed_entry | conservative_crypto_1m | 992 | +5.1750pct | 75 | 0.1600 | 6.9168 | 82,905.77 | 51,749.65 | 31,156.12 | 0.3758 | 18.7364 | 0 | 0 | COMPLETED_RESEARCH_ONLY |
| execution_assumption | execution_assumption | owner_0525_latest | one_candle_delayed_entry | conservative_crypto_1m | 993 | +3.3091pct | 19 | 0.2632 | 8.4369 | 52,984.11 | 33,091.44 | 19,892.67 | 0.3754 | 18.9629 | 0 | 0 | COMPLETED_RESEARCH_ONLY |

## Gate Check

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| 0520 locked replay return | >= +3pct | +5.7327pct | `PASS` |
| 0525 locked replay return | >= +3pct | +3.5337pct | `PASS` |
| 0520 locked replay trips | >= 50 | 62 | `PASS` |
| All cost audit mismatches | 0 | 0 | `PASS` |
| Non-zero base costs | fee/spread/slippage > 0 | fee=21,970.33, spread=6,591.10, slippage=12,032.06 | `PASS` |
| Pre-owner return | >= 0pct for robustness | -2.6638pct | `FAIL` |
| Endpoint diagnostics positive | all > 0pct | 15/16 | `FAIL` |
| Cost stress survives | all > -3pct | 8/8 | `PASS` |
| Execution diagnostics available | >= 2 | 4 | `PASS` |
| Outlier top-three 0520 | <= 0.70 | 0.6474 | `PASS` |
| Return without top-three 0520 winners | > 0pct | +2.0213pct | `PASS` |
| April-20 coverage | complete data required for April claim | DATA_BLOCKED | `FAIL` |
| Baseline diagnostics generated | >= 3 | 3 | `PASS` |

## Cost Audit

- Run `960` `owner_0520_latest` `conservative_crypto_1m`: notional `21,970,331.56`, fee `21,970.33`, spread `6,591.10`, slippage `12,032.06`, total `40,593.49`, one-way cost `18.4765` bps, formula mismatch `0`, summary mismatch `0`.
- Run `961` `owner_0525_latest` `conservative_crypto_1m`: notional `10,416,282.34`, fee `10,416.28`, spread `3,124.88`, slippage `5,891.43`, total `19,432.60`, one-way cost `18.6560` bps, formula mismatch `0`, summary mismatch `0`.
- Run `962` `available_pre_owner_0510_0517` `conservative_crypto_1m`: notional `25,137,760.50`, fee `25,137.76`, spread `7,541.33`, slippage `14,109.50`, total `46,788.59`, one-way cost `18.6129` bps, formula mismatch `0`, summary mismatch `0`.
- Run `963` `owner_0520_latest_drop_first_6h` `conservative_crypto_1m`: notional `21,851,931.81`, fee `21,851.93`, spread `6,555.58`, slippage `11,970.25`, total `40,377.76`, one-way cost `18.4779` bps, formula mismatch `0`, summary mismatch `0`.
- Run `964` `owner_0520_latest_drop_last_6h` `conservative_crypto_1m`: notional `20,029,474.85`, fee `20,029.47`, spread `6,008.84`, slippage `10,965.42`, total `37,003.73`, one-way cost `18.4746` bps, formula mismatch `0`, summary mismatch `0`.
- Run `965` `owner_0520_latest_drop_first_12h` `conservative_crypto_1m`: notional `21,732,834.88`, fee `21,732.83`, spread `6,519.85`, slippage `11,906.09`, total `40,158.77`, one-way cost `18.4784` bps, formula mismatch `0`, summary mismatch `0`.
- Run `966` `owner_0520_latest_drop_last_12h` `conservative_crypto_1m`: notional `18,039,057.80`, fee `18,039.06`, spread `5,411.72`, slippage `9,752.86`, total `33,203.63`, one-way cost `18.4065` bps, formula mismatch `0`, summary mismatch `0`.
- Run `967` `owner_0520_latest_drop_first_24h` `conservative_crypto_1m`: notional `19,655,785.19`, fee `19,655.79`, spread `5,896.74`, slippage `10,780.01`, total `36,332.53`, one-way cost `18.4844` bps, formula mismatch `0`, summary mismatch `0`.
- Run `968` `owner_0520_latest_drop_last_24h` `conservative_crypto_1m`: notional `15,968,496.92`, fee `15,968.50`, spread `4,790.55`, slippage `8,545.04`, total `29,304.09`, one-way cost `18.3512` bps, formula mismatch `0`, summary mismatch `0`.
- Run `969` `owner_0520_latest_first_half` `conservative_crypto_1m`: notional `10,905,425.68`, fee `10,905.43`, spread `3,271.63`, slippage `5,788.42`, total `19,965.48`, one-way cost `18.3078` bps, formula mismatch `0`, summary mismatch `0`.
- Run `970` `owner_0520_latest_second_half` `conservative_crypto_1m`: notional `10,774,269.50`, fee `10,774.27`, spread `3,232.28`, slippage `6,086.09`, total `20,092.64`, one-way cost `18.6487` bps, formula mismatch `0`, summary mismatch `0`.
- Run `971` `owner_0525_latest_drop_first_6h` `conservative_crypto_1m`: notional `10,339,046.25`, fee `10,339.05`, spread `3,101.71`, slippage `5,822.09`, total `19,262.85`, one-way cost `18.6312` bps, formula mismatch `0`, summary mismatch `0`.
- Run `972` `owner_0525_latest_drop_last_6h` `conservative_crypto_1m`: notional `8,475,425.63`, fee `8,475.43`, spread `2,542.63`, slippage `4,824.79`, total `15,842.84`, one-way cost `18.6927` bps, formula mismatch `0`, summary mismatch `0`.
- Run `973` `owner_0525_latest_drop_first_12h` `conservative_crypto_1m`: notional `8,344,124.91`, fee `8,344.12`, spread `2,503.24`, slippage `4,765.88`, total `15,613.24`, one-way cost `18.7117` bps, formula mismatch `0`, summary mismatch `0`.
- Run `974` `owner_0525_latest_drop_last_12h` `conservative_crypto_1m`: notional `6,485,008.58`, fee `6,485.01`, spread `1,945.50`, slippage `3,612.23`, total `12,042.74`, one-way cost `18.5701` bps, formula mismatch `0`, summary mismatch `0`.
- Run `975` `owner_0525_latest_drop_first_24h` `conservative_crypto_1m`: notional `8,192,110.56`, fee `8,192.11`, spread `2,457.63`, slippage `4,674.73`, total `15,324.47`, one-way cost `18.7064` bps, formula mismatch `0`, summary mismatch `0`.
- Run `976` `owner_0525_latest_drop_last_24h` `conservative_crypto_1m`: notional `4,414,447.70`, fee `4,414.45`, spread `1,324.33`, slippage `2,404.41`, total `8,143.19`, one-way cost `18.4467` bps, formula mismatch `0`, summary mismatch `0`.
- Run `977` `owner_0525_latest_first_half` `conservative_crypto_1m`: notional `2,311,065.49`, fee `2,311.07`, spread `693.32`, slippage `1,260.76`, total `4,265.14`, one-way cost `18.4553` bps, formula mismatch `0`, summary mismatch `0`.
- Run `978` `owner_0525_latest_second_half` `conservative_crypto_1m`: notional `4,244,866.23`, fee `4,244.87`, spread `1,273.46`, slippage `2,477.41`, total `7,995.74`, one-way cost `18.8363` bps, formula mismatch `0`, summary mismatch `0`.
- Run `979` `owner_0520_latest` `fee_2x`: notional `21,939,178.31`, fee `43,878.36`, spread `6,581.75`, slippage `12,015.37`, total `62,475.48`, one-way cost `28.4767` bps, formula mismatch `0`, summary mismatch `0`.
- Run `980` `owner_0520_latest` `slippage_2x`: notional `21,955,481.91`, fee `21,955.48`, spread `6,586.64`, slippage `24,048.22`, total `52,590.35`, one-way cost `23.9532` bps, formula mismatch `0`, summary mismatch `0`.
- Run `981` `owner_0520_latest` `fee_slippage_2x`: notional `21,914,063.13`, fee `43,828.13`, spread `6,574.22`, slippage `24,003.76`, total `74,406.10`, one-way cost `33.9536` bps, formula mismatch `0`, summary mismatch `0`.
- Run `982` `owner_0520_latest` `high_slippage_stress`: notional `21,764,901.02`, fee `21,764.90`, spread `21,764.90`, slippage `48,713.16`, total `92,242.96`, one-way cost `42.3815` bps, formula mismatch `0`, summary mismatch `0`.
- Run `983` `owner_0520_latest` `zero`: notional `21,982,182.57`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, one-way cost `0.0000` bps, formula mismatch `0`, summary mismatch `0`.
- Run `984` `owner_0525_latest` `fee_2x`: notional `10,407,582.65`, fee `20,815.17`, spread `3,122.27`, slippage `5,886.69`, total `29,824.13`, one-way cost `28.6562` bps, formula mismatch `0`, summary mismatch `0`.
- Run `985` `owner_0525_latest` `slippage_2x`: notional `10,411,477.73`, fee `10,411.48`, spread `3,123.44`, slippage `11,777.62`, total `25,312.54`, one-way cost `24.3122` bps, formula mismatch `0`, summary mismatch `0`.
- Run `986` `owner_0525_latest` `fee_slippage_2x`: notional `10,399,740.17`, fee `20,799.48`, spread `3,119.92`, slippage `11,764.59`, total `35,683.99`, one-way cost `34.3124` bps, formula mismatch `0`, summary mismatch `0`.
- Run `987` `owner_0525_latest` `high_slippage_stress`: notional `10,362,017.48`, fee `10,362.02`, spread `10,362.02`, slippage `24,122.05`, total `44,846.08`, one-way cost `43.2793` bps, formula mismatch `0`, summary mismatch `0`.
- Run `988` `owner_0525_latest` `zero`: notional `10,424,510.80`, fee `0.00`, spread `0.00`, slippage `0.00`, total `0.00`, one-way cost `0.0000` bps, formula mismatch `0`, summary mismatch `0`.
- Run `989` `available_pre_owner_0510_0517` `high_slippage_stress`: notional `24,404,000.34`, fee `24,404.00`, spread `24,404.00`, slippage `56,303.21`, total `105,111.21`, one-way cost `43.0713` bps, formula mismatch `0`, summary mismatch `0`.
- Run `990` `owner_0520_latest` `conservative_crypto_1m`: notional `14,852,939.21`, fee `14,852.94`, spread `4,455.88`, slippage `8,474.45`, total `27,783.27`, one-way cost `18.7056` bps, formula mismatch `0`, summary mismatch `0`.
- Run `991` `owner_0525_latest` `conservative_crypto_1m`: notional `8,709,113.38`, fee `8,709.11`, spread `2,612.73`, slippage `5,201.49`, total `16,523.34`, one-way cost `18.9725` bps, formula mismatch `0`, summary mismatch `0`.
- Run `992` `owner_0520_latest` `conservative_crypto_1m`: notional `16,628,674.11`, fee `16,628.67`, spread `4,988.60`, slippage `9,538.84`, total `31,156.12`, one-way cost `18.7364` bps, formula mismatch `0`, summary mismatch `0`.
- Run `993` `owner_0525_latest` `conservative_crypto_1m`: notional `10,490,324.64`, fee `10,490.32`, spread `3,147.10`, slippage `6,255.25`, total `19,892.67`, one-way cost `18.9629` bps, formula mismatch `0`, summary mismatch `0`.

## Attribution: 0520 Locked Replay

### Side

| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LONG | 31 | 0.0968 | 155.48 | 2,280.63 | -2,125.15 | -68.55 |
| SHORT | 31 | 0.2903 | 97,765.32 | 38,312.86 | 59,452.47 | 1,917.82 |

### Session

| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ASIA | 22 | 0.1818 | 34,464.10 | 15,981.24 | 18,482.87 | 840.13 |
| EUROPE | 9 | 0.1111 | -348.60 | 662.70 | -1,011.31 | -112.37 |
| LATE_US | 7 | 0.2857 | 25,854.57 | 11,278.66 | 14,575.91 | 2,082.27 |
| US | 24 | 0.2083 | 37,950.74 | 12,670.89 | 25,279.85 | 1,053.33 |

### Regime

| Bucket | Trips | Win | Gross | Cost | Net | Avg Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| vol_HIGH | 31 | 0.1935 | 65,645.86 | 20,351.82 | 45,294.04 | 1,461.10 |
| vol_LOW | 31 | 0.1935 | 32,274.95 | 20,241.67 | 12,033.28 | 388.17 |
| trend_ALIGNED | 55 | 0.1091 | 40,769.75 | 14,965.17 | 25,804.58 | 469.17 |
| trend_COUNTER | 7 | 0.8571 | 57,151.06 | 25,628.32 | 31,522.74 | 4,503.25 |
| volume_EXPANSION | 26 | 0.1923 | 37,746.72 | 16,350.78 | 21,395.94 | 822.92 |
| volume_NORMAL | 36 | 0.1944 | 60,174.09 | 24,242.71 | 35,931.38 | 998.09 |

### Outlier Dependence

- Largest winner contribution: `0.2729`.
- Top-three winner contribution: `0.6474`.
- Return without largest winner: `+4.1685pct`.
- Return without top-three winners: `+2.0213pct`.

## Baselines

| Window | Baseline | Return | Trips | Note |
| --- | --- | ---: | ---: | --- |
| owner_0520_latest | `buy_and_hold_long` | -4.5907pct | 1 | full notional long, no cost diagnostic |
| owner_0520_latest | `ma20_120_flip_no_cost` | +2.3710pct | 11906 | close-to-close diagnostic, no execution costs |
| owner_0520_latest | `random_entry_seed284` | -7.6597pct | 62 | sum of full-notional random trade returns, no cost diagnostic |
| owner_0525_latest | `buy_and_hold_long` | -4.9533pct | 1 | full notional long, no cost diagnostic |
| owner_0525_latest | `ma20_120_flip_no_cost` | -0.3471pct | 4706 | close-to-close diagnostic, no execution costs |
| owner_0525_latest | `random_entry_seed284` | -1.2052pct | 17 | sum of full-notional random trade returns, no cost diagnostic |

## Bias And Safety Checks

- Signal/entry separation: Task 283 locked model enters on next candle open; B2 exits on next candle open after the exit condition.
- Completed-candle factors: reused Task 283 factor snapshots, which are prior/completed-candle only.
- MTF context: prior 15m/1h return proxies from completed 1m history; no incomplete higher-timeframe candle is fetched.
- Intrabar ambiguity: stop-first when stop and target are both touched in the same candle.
- Position overlap: action generation advances past the resolved exit and the engine has an open-position guard.
- Live trading safety: no execution client imports, no signed requests, no API keys, no `.env` handling, no order/account endpoints.

## Conclusion

- Final status: `ROBUSTNESS_REJECTED_RESEARCH_ONLY`.
- Failed gates: `Pre-owner return, Endpoint diagnostics positive, April-20 coverage`.
- Interpretation: available pre-owner replay is negative; complete April-20-forward OOS remains data-blocked; zero-cost gap on 0520 is +4.0631pct.
- No Task 284 result is promoted beyond `RESEARCH_ONLY`.
