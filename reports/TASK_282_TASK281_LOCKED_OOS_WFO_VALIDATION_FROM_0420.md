# Task 282 Task 281 Locked OOS/WFO Validation From 2026-04-20

Status: `LIKELY_OVERFIT_RESEARCH_ONLY`

## Locked Strategy

- Source task: `TASK_281`.
- Source run: `892`.
- Locked variant: `T281_B1_PRIORITY_ENSEMBLE_H120_T150_S75_CF100_FF002`.
- No-retune declaration: `True`.
- Validation scope: offline simulated BTCUSDT 1m only; no live/order/private exchange endpoints.

## Data Availability

- Requested validation start: `2026-04-20T00:00:00Z`.
- Local available start: `2026-05-10T00:00:00Z`.
- Local available end: `2026-05-28T08:26:00Z`.
- Local closed candles from requested start onward: `23027`.
- Data note: April 20-2026 through local available start is not fabricated; windows report actual persisted candle starts.

## Run IDs

- Task 282 persisted run IDs: `900, 901, 902, 903, 904, 905, 906, 907, 908, 909`.

## Validation Runs

| Window | Group | Cost | Run | Requested | Actual | Return | Trips | Active Days | Gross | Net | Cost | Cost/Gross | Top1 | Top3 | Max DD | Notional | Cost bps | Status | Anomalies |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| full_0420_latest | primary | conservative_crypto_1m | - | 2026-04-20..2026-05-28 | 2026-05-10..2026-05-28 | - | 0 | 0 | - | - | - | - | - | - | - | - | - | local_candles_have_internal_1m_gap_or_duplicate | candle_continuity_gap |
| pre_owner_0420_0519 | primary | conservative_crypto_1m | 900 | 2026-04-20..2026-05-19 | 2026-05-10..2026-05-17 | -2.7997pct | 54 | 8 | 19,332.84 | -27,997.09 | 47,329.92 | 2.4482 | - | - | -4.1634pct | 25,114,353.91 | 18.8458 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| owner_replay_0520_latest | primary | conservative_crypto_1m | 901 | 2026-05-20..2026-05-28 | 2026-05-20..2026-05-28 | +5.7295pct | 62 | 9 | 97,963.67 | 57,294.78 | 40,668.89 | 0.4151 | 0.2721 | 0.6459 | -1.3248pct | 21,970,384.07 | 18.5108 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| w1_0420_0426 | weekly | conservative_crypto_1m | - | 2026-04-20..2026-04-26 | - | - | 0 | 0 | - | - | - | - | - | - | - | - | - | no_local_candles_for_requested_window | - |
| w2_0427_0503 | weekly | conservative_crypto_1m | - | 2026-04-27..2026-05-03 | - | - | 0 | 0 | - | - | - | - | - | - | - | - | - | no_local_candles_for_requested_window | - |
| w3_0504_0510 | weekly | conservative_crypto_1m | 902 | 2026-05-04..2026-05-10 | 2026-05-10..2026-05-10 | -0.0475pct | 5 | 1 | -94.35 | -474.76 | 380.41 | 4.0317 | - | - | -0.0678pct | 200,205.65 | 19.0009 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| w4_0511_0517 | weekly | conservative_crypto_1m | 903 | 2026-05-11..2026-05-17 | 2026-05-11..2026-05-17 | -0.1760pct | 43 | 7 | 37,833.07 | -1,760.10 | 39,593.17 | 1.0465 | - | - | -2.5177pct | 21,223,443.34 | 18.6554 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| w5_0518_0524 | weekly | conservative_crypto_1m | 904 | 2026-05-18..2026-05-24 | 2026-05-20..2026-05-24 | +2.2370pct | 38 | 5 | 43,030.33 | 22,370.20 | 20,660.13 | 0.4801 | 0.5561 | 1.1029 | -1.3248pct | 11,265,474.92 | 18.3393 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| w6_0525_latest | weekly | conservative_crypto_1m | 905 | 2026-05-25..2026-05-28 | 2026-05-25..2026-05-28 | +3.5308pct | 17 | 4 | 54,784.33 | 35,307.72 | 19,476.61 | 0.3555 | 0.4416 | 0.8599 | -1.2010pct | 10,416,123.91 | 18.6985 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| full_0420_latest_drop_first_day | endpoint_trim | conservative_crypto_1m | - | 2026-04-21..2026-05-28 | 2026-05-10..2026-05-28 | - | 0 | 0 | - | - | - | - | - | - | - | - | - | local_candles_have_internal_1m_gap_or_duplicate | candle_continuity_gap |
| full_0420_latest_drop_last_day | endpoint_trim | conservative_crypto_1m | - | 2026-04-20..2026-05-27 | 2026-05-10..2026-05-27 | - | 0 | 0 | - | - | - | - | - | - | - | - | - | local_candles_have_internal_1m_gap_or_duplicate | candle_continuity_gap |
| owner_0520_latest_drop_last_12h | endpoint_trim | conservative_crypto_1m | 906 | 2026-05-20..2026-05-27 | 2026-05-20..2026-05-27 | +3.6004pct | 61 | 8 | 69,246.49 | 36,003.50 | 33,242.99 | 0.4801 | 0.3455 | 0.8022 | -1.3248pct | 18,039,101.25 | 18.4283 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| owner_0520_latest_drop_last_24h | endpoint_trim | conservative_crypto_1m | 907 | 2026-05-20..2026-05-27 | 2026-05-20..2026-05-27 | +3.0506pct | 58 | 8 | 59,900.62 | 30,506.44 | 29,394.18 | 0.4907 | 0.4078 | 0.9468 | -1.3248pct | 15,968,561.69 | 18.4075 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| full_0420_latest | primary | high_slippage_stress | - | 2026-04-20..2026-05-28 | 2026-05-10..2026-05-28 | - | 0 | 0 | - | - | - | - | - | - | - | - | - | local_candles_have_internal_1m_gap_or_duplicate | candle_continuity_gap |
| pre_owner_0420_0519 | primary | high_slippage_stress | 908 | 2026-04-20..2026-05-19 | 2026-05-10..2026-05-17 | -8.9497pct | 54 | 8 | 18,224.15 | -89,496.99 | 107,721.14 | 5.9109 | - | - | -8.9497pct | 24,346,167.65 | 44.2456 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |
| owner_replay_0520_latest | primary | high_slippage_stress | 909 | 2026-05-20..2026-05-28 | 2026-05-20..2026-05-28 | +0.4238pct | 62 | 9 | 96,837.52 | 4,237.91 | 92,599.61 | 0.9562 | 2.4826 | 5.2197 | -2.4568pct | 21,761,265.30 | 42.5525 | COMPLETED_VALIDATION_RESEARCH_ONLY | - |

## Gate Check

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Data before owner window | available_start < 2026-05-20 | 2026-05-10T00:00:00Z | `PASS` |
| Owner replay reproducibility | return/trips match run 892 | +5.7295pct / 62 | `PASS` |
| Full 0420-latest return | > 0 | - | `FAIL` |
| Pre-owner return | > 0 | -2.7997pct | `FAIL` |
| Weekly consistency | >= half positive among >=10-trip weeks | 2/3 | `PASS` |
| Full largest winner contribution | <= 0.40 | - | `FAIL` |
| Full top-three winner contribution | <= 0.70 | - | `FAIL` |
| Full cost/gross PnL | <= 0.60 | - | `FAIL` |
| Full high-slippage stress | > -3pct | - | `FAIL` |
| Pre-owner high-slippage stress | > -3pct | -8.9497pct | `FAIL` |
| Accounting/anomaly checks | no anomalies | - | `PASS` |

## Cost Audit

- Run `900` `pre_owner_0420_0519` `conservative_crypto_1m`: notional `25,114,353.91`, fee `25,114.35`, spread `7,534.31`, slippage `14,681.26`, total `47,329.92`, one-way cost `18.8458` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `901` `owner_replay_0520_latest` `conservative_crypto_1m`: notional `21,970,384.07`, fee `21,970.38`, spread `6,591.12`, slippage `12,107.39`, total `40,668.89`, one-way cost `18.5108` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `902` `w3_0504_0510` `conservative_crypto_1m`: notional `200,205.65`, fee `200.21`, spread `60.06`, slippage `120.14`, total `380.41`, one-way cost `19.0009` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `903` `w4_0511_0517` `conservative_crypto_1m`: notional `21,223,443.34`, fee `21,223.44`, spread `6,367.03`, slippage `12,002.70`, total `39,593.17`, one-way cost `18.6554` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `904` `w5_0518_0524` `conservative_crypto_1m`: notional `11,265,474.92`, fee `11,265.47`, spread `3,379.64`, slippage `6,015.01`, total `20,660.13`, one-way cost `18.3393` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `905` `w6_0525_latest` `conservative_crypto_1m`: notional `10,416,123.91`, fee `10,416.12`, spread `3,124.84`, slippage `5,935.65`, total `19,476.61`, one-way cost `18.6985` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `906` `owner_0520_latest_drop_last_12h` `conservative_crypto_1m`: notional `18,039,101.25`, fee `18,039.10`, spread `5,411.73`, slippage `9,792.15`, total `33,242.99`, one-way cost `18.4283` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `907` `owner_0520_latest_drop_last_24h` `conservative_crypto_1m`: notional `15,968,561.69`, fee `15,968.56`, spread `4,790.57`, slippage `8,635.05`, total `29,394.18`, one-way cost `18.4075` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `908` `pre_owner_0420_0519` `high_slippage_stress`: notional `24,346,167.65`, fee `24,346.17`, spread `24,346.17`, slippage `59,028.81`, total `107,721.14`, one-way cost `44.2456` bps, mismatch count `0`, max mismatch `0.0000000000`.
- Run `909` `owner_replay_0520_latest` `high_slippage_stress`: notional `21,761,265.30`, fee `21,761.27`, spread `21,761.27`, slippage `49,077.08`, total `92,599.61`, one-way cost `42.5525` bps, mismatch count `0`, max mismatch `0.0000000000`.

## Attribution Checks

- Run `900` `pre_owner_0420_0519`: core net `-24,854.34` over `12` trips, scout net `-3,142.75` over `42` trips, LONG net `-1,771.08`, SHORT net `-26,226.01`, Sunday core executions `0`.
- Run `901` `owner_replay_0520_latest`: core net `61,701.22` over `10` trips, scout net `-4,406.44` over `52` trips, LONG net `-2,132.15`, SHORT net `59,426.93`, Sunday core executions `0`.
- Run `902` `w3_0504_0510`: core net `0.00` over `0` trips, scout net `-474.76` over `5` trips, LONG net `-243.58`, SHORT net `-231.19`, Sunday core executions `0`.
- Run `903` `w4_0511_0517`: core net `446.23` over `10` trips, scout net `-2,206.33` over `33` trips, LONG net `-1,080.56`, SHORT net `-679.54`, Sunday core executions `0`.
- Run `904` `w5_0518_0524`: core net `25,028.04` over `5` trips, scout net `-2,657.84` over `33` trips, LONG net `-1,391.73`, SHORT net `23,761.93`, Sunday core executions `0`.
- Run `905` `w6_0525_latest`: core net `36,652.96` over `5` trips, scout net `-1,345.24` over `12` trips, LONG net `-531.91`, SHORT net `35,839.64`, Sunday core executions `0`.
- Run `906` `owner_0520_latest_drop_last_12h`: core net `40,476.43` over `8` trips, scout net `-4,472.92` over `53` trips, LONG net `-2,132.15`, SHORT net `38,135.65`, Sunday core executions `0`.
- Run `907` `owner_0520_latest_drop_last_24h`: core net `34,660.62` over `7` trips, scout net `-4,154.18` over `51` trips, LONG net `-2,149.22`, SHORT net `32,655.66`, Sunday core executions `0`.
- Run `908` `pre_owner_0420_0519`: core net `-82,277.59` over `12` trips, scout net `-7,219.40` over `42` trips, LONG net `-3,891.09`, SHORT net `-85,605.90`, Sunday core executions `0`.
- Run `909` `owner_replay_0520_latest`: core net `13,636.73` over `10` trips, scout net `-9,398.81` over `52` trips, LONG net `-5,105.80`, SHORT net `9,343.71`, Sunday core executions `0`.

## Conclusion

- Final interpretation: `LIKELY_OVERFIT_RESEARCH_ONLY`.
- Failed gates: `Full 0420-latest return, Pre-owner return, Full largest winner contribution, Full top-three winner contribution, Full cost/gross PnL, Full high-slippage stress, Pre-owner high-slippage stress`.
- The validation does not retune the model and does not promote the strategy beyond research-only.
