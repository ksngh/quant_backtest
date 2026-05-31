# Task 279 Strategy Robustness Validation Matrix

Date: 2026-05-29

Status: `RESEARCH_ONLY`

## Verdict

Task 278's one-position inverse trend-hold result remains `DIAGNOSTIC_ONLY`. The Task 279 matrix persisted a broader set of BTCUSDT 1m candidate runs and no candidate passed all robustness gates.

## Predeclared Matrix

- Candidates: `7`
- Planned runs: `154`
- Persisted Task 279 runs in DB: `135`
- Sizing ladder on owner windows: `0.10`, `0.25`, `0.50`, `0.75` cash fraction
- Primary validation sizing: `0.10` cash fraction
- Secondary sizing diagnostics: `0.25`, `0.50`, `0.75` cash fraction
- Windows: owner A/B, endpoint-trim A/B, OOS 1/2, high-slippage stress, and one-candle entry delay
- Runtime note: the full 154-run plan was stopped after 135 persisted runs because the optional Order Block expansion was already strongly dominated and slow; SRLBR, FVG inverse, and LSR validation groups were persisted broadly.

## Gate Summary

| Candidate | Sample/Activity | Endpoint | Outlier | Cost | Drawdown | Exposure | Parameter | OOS | Benchmark | Execution | Persistence | Final |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | DIAGNOSTIC_ONLY |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | DIAGNOSTIC_ONLY |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6 | PASS | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | DIAGNOSTIC_ONLY |
| T279_SRLBR_SHORT_MIX_120_8R | PASS | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | DIAGNOSTIC_ONLY |
| T279_FVG_INVERSE_SIMPLE | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | DIAGNOSTIC_ONLY |
| T279_OB_618_WAIT20 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | DIAGNOSTIC_ONLY |
| T279_LSR_MARKET_1R | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | PASS | PASS | DIAGNOSTIC_ONLY |

## Primary Owner Runs

| Candidate | Window | Run | Return | Net PnL | Cost | Completed Trips | Active Days | Max Position Fraction | Cost/Gross | Ending Position |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P10 | owner_a | 159 | -0.8208pct | -8,207.56 | 9,601.67 | 25 | 9 | 0.0200 | 6.8873 | 0.0 |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P10 | owner_b | 165 | -0.1932pct | -1,931.67 | 4,135.12 | 11 | 4 | 0.0497 | 1.8767 | 0.0 |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P10 | owner_a | 183 | -0.8208pct | -8,207.56 | 9,601.67 | 25 | 9 | 0.0200 | 6.8873 | 0.0 |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P10 | owner_b | 187 | -0.1932pct | -1,931.67 | 4,135.12 | 11 | 4 | 0.0497 | 1.8767 | 0.0 |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P10 | owner_a | 205 | -0.8341pct | -8,340.90 | 9,607.42 | 25 | 9 | 0.0200 | 7.5857 | 0.0 |
| T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P10 | owner_b | 209 | -0.1932pct | -1,931.67 | 4,135.12 | 11 | 4 | 0.0497 | 1.8767 | 0.0 |
| T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P10 | owner_a | 227 | -3.0463pct | -30,462.81 | 32,915.23 | 88 | 9 | 0.0199 | 13.4216 | 0.0 |
| T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P10 | owner_b | 231 | -1.2873pct | -12,872.94 | 13,495.68 | 36 | 4 | 0.0495 | 21.6717 | 0.0 |
| T279_FVG_INVERSE_SIMPLE_owner_CF_0P10 | owner_a | 249 | -0.6283pct | -6,282.69 | 6,233.57 | 17 | 8 | 0.0002 | 126.9291 | 0.0 |
| T279_FVG_INVERSE_SIMPLE_owner_CF_0P10 | owner_b | 253 | -0.1847pct | -1,846.85 | 1,832.50 | 5 | 3 | 0.0002 | 127.7190 | 0.0 |
| T279_OB_618_WAIT20_owner_CF_0P10 | owner_a | 271 | -6.3262pct | -63,261.88 | 62,975.95 | 180 | 9 | 0.0007 | 220.2515 | 0.0 |
| T279_LSR_MARKET_1R_owner_CF_0P10 | owner_a | 274 | -0.0005pct | -4.57 | 404.25 | 1 | 1 | 0.0035 | 1.0114 | 0.0 |
| T279_LSR_MARKET_1R_owner_CF_0P10 | owner_b | 278 | -0.0005pct | -4.57 | 404.25 | 1 | 1 | 0.0087 | 1.0114 | 0.0 |

## All Persisted Validation Runs

| Group | Candidate | Window | CF | Cost Profile | Run | Return | Trips | Cost | Warnings/Error |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P10 | owner_a | 0.10 | conservative_crypto_1m | 159 | -0.8208pct | 25 | 9,601.67 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P25 | owner_a | 0.25 | conservative_crypto_1m | 160 | -2.0411pct | 25 | 23,813.21 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P50 | owner_a | 0.50 | conservative_crypto_1m | 163 | -4.0467pct | 25 | 46,996.85 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P75 | owner_a | 0.75 | conservative_crypto_1m | 164 | -6.0172pct | 25 | 69,563.85 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P10 | owner_b | 0.10 | conservative_crypto_1m | 165 | -0.1932pct | 11 | 4,135.12 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P25 | owner_b | 0.25 | conservative_crypto_1m | 166 | -0.4830pct | 11 | 10,317.43 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P50 | owner_b | 0.50 | conservative_crypto_1m | 167 | -0.9661pct | 11 | 20,567.14 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_owner_CF_0P75 | owner_b | 0.75 | conservative_crypto_1m | 168 | -1.4494pct | 11 | 30,749.46 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_endpoint_trim_CF_0P10 | trim_a | 0.10 | conservative_crypto_1m | 169 | -0.8208pct | 25 | 9,601.67 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_endpoint_trim_CF_0P50 | trim_a | 0.50 | conservative_crypto_1m | 170 | -4.0467pct | 25 | 46,996.85 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_endpoint_trim_CF_0P10 | trim_b | 0.10 | conservative_crypto_1m | 171 | -0.1932pct | 11 | 4,135.12 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_endpoint_trim_CF_0P50 | trim_b | 0.50 | conservative_crypto_1m | 172 | -0.9661pct | 11 | 20,567.14 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_oos_CF_0P10 | oos_1 | 0.10 | conservative_crypto_1m | 173 | -0.7417pct | 17 | 6,612.48 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_oos_CF_0P50 | oos_1 | 0.50 | conservative_crypto_1m | 174 | -3.6607pct | 17 | 32,521.49 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_oos_CF_0P10 | oos_2 | 0.10 | conservative_crypto_1m | 175 | -0.1975pct | 9 | 3,576.69 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_oos_CF_0P50 | oos_2 | 0.50 | conservative_crypto_1m | 176 | -0.9872pct | 9 | 17,805.05 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_cost_stress_CF_0P10 | owner_a | 0.10 | high_slippage_stress | 177 | -2.1632pct | 25 | 22,997.59 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_cost_stress_CF_0P50 | owner_a | 0.50 | high_slippage_stress | 178 | -10.3826pct | 25 | 109,691.93 | - |
| entry_delay | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_entry_delay_CF_0P10_NEXT_OPEN | owner_a | 0.10 | conservative_crypto_1m | 179 | -0.8236pct | 26 | 9,786.08 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_cost_stress_CF_0P10 | owner_b | 0.10 | high_slippage_stress | 180 | -0.7481pct | 11 | 9,676.57 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_cost_stress_CF_0P50 | owner_b | 0.50 | high_slippage_stress | 181 | -3.6936pct | 11 | 47,645.88 | - |
| entry_delay | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P4_entry_delay_CF_0P10_NEXT_OPEN | owner_b | 0.10 | conservative_crypto_1m | 182 | -0.1678pct | 11 | 4,104.90 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P10 | owner_a | 0.10 | conservative_crypto_1m | 183 | -0.8208pct | 25 | 9,601.67 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P25 | owner_a | 0.25 | conservative_crypto_1m | 184 | -2.0411pct | 25 | 23,813.21 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P50 | owner_a | 0.50 | conservative_crypto_1m | 185 | -4.0467pct | 25 | 46,996.85 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P75 | owner_a | 0.75 | conservative_crypto_1m | 186 | -6.0172pct | 25 | 69,563.85 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P10 | owner_b | 0.10 | conservative_crypto_1m | 187 | -0.1932pct | 11 | 4,135.12 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P25 | owner_b | 0.25 | conservative_crypto_1m | 188 | -0.4830pct | 11 | 10,317.43 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P50 | owner_b | 0.50 | conservative_crypto_1m | 189 | -0.9661pct | 11 | 20,567.14 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_owner_CF_0P75 | owner_b | 0.75 | conservative_crypto_1m | 190 | -1.4494pct | 11 | 30,749.46 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_endpoint_trim_CF_0P10 | trim_a | 0.10 | conservative_crypto_1m | 191 | -0.8208pct | 25 | 9,601.67 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_endpoint_trim_CF_0P50 | trim_a | 0.50 | conservative_crypto_1m | 192 | -4.0467pct | 25 | 46,996.85 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_endpoint_trim_CF_0P10 | trim_b | 0.10 | conservative_crypto_1m | 193 | -0.1932pct | 11 | 4,135.12 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_endpoint_trim_CF_0P50 | trim_b | 0.50 | conservative_crypto_1m | 194 | -0.9661pct | 11 | 20,567.14 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_oos_CF_0P10 | oos_1 | 0.10 | conservative_crypto_1m | 195 | -0.7417pct | 17 | 6,612.48 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_oos_CF_0P50 | oos_1 | 0.50 | conservative_crypto_1m | 196 | -3.6607pct | 17 | 32,521.49 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_oos_CF_0P10 | oos_2 | 0.10 | conservative_crypto_1m | 197 | -0.1975pct | 9 | 3,576.69 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_oos_CF_0P50 | oos_2 | 0.50 | conservative_crypto_1m | 198 | -0.9872pct | 9 | 17,805.05 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_cost_stress_CF_0P10 | owner_a | 0.10 | high_slippage_stress | 199 | -2.1632pct | 25 | 22,997.59 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_cost_stress_CF_0P50 | owner_a | 0.50 | high_slippage_stress | 200 | -10.3826pct | 25 | 109,691.93 | - |
| entry_delay | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_entry_delay_CF_0P10_NEXT_OPEN | owner_a | 0.10 | conservative_crypto_1m | 201 | -0.8236pct | 26 | 9,786.08 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_cost_stress_CF_0P10 | owner_b | 0.10 | high_slippage_stress | 202 | -0.7481pct | 11 | 9,676.57 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_cost_stress_CF_0P50 | owner_b | 0.50 | high_slippage_stress | 203 | -3.6936pct | 11 | 47,645.88 | - |
| entry_delay | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P5_entry_delay_CF_0P10_NEXT_OPEN | owner_b | 0.10 | conservative_crypto_1m | 204 | -0.1678pct | 11 | 4,104.90 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P10 | owner_a | 0.10 | conservative_crypto_1m | 205 | -0.8341pct | 25 | 9,607.42 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P25 | owner_a | 0.25 | conservative_crypto_1m | 206 | -2.0740pct | 25 | 23,824.87 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P50 | owner_a | 0.50 | conservative_crypto_1m | 207 | -4.1110pct | 25 | 47,011.35 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P75 | owner_a | 0.75 | conservative_crypto_1m | 208 | -6.1116pct | 25 | 69,572.85 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P10 | owner_b | 0.10 | conservative_crypto_1m | 209 | -0.1932pct | 11 | 4,135.12 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P25 | owner_b | 0.25 | conservative_crypto_1m | 210 | -0.4830pct | 11 | 10,317.43 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P50 | owner_b | 0.50 | conservative_crypto_1m | 211 | -0.9661pct | 11 | 20,567.14 | - |
| owner | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_owner_CF_0P75 | owner_b | 0.75 | conservative_crypto_1m | 212 | -1.4494pct | 11 | 30,749.46 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_endpoint_trim_CF_0P10 | trim_a | 0.10 | conservative_crypto_1m | 213 | -0.8341pct | 25 | 9,607.42 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_endpoint_trim_CF_0P50 | trim_a | 0.50 | conservative_crypto_1m | 214 | -4.1110pct | 25 | 47,011.35 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_endpoint_trim_CF_0P10 | trim_b | 0.10 | conservative_crypto_1m | 215 | -0.1932pct | 11 | 4,135.12 | - |
| endpoint_trim | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_endpoint_trim_CF_0P50 | trim_b | 0.50 | conservative_crypto_1m | 216 | -0.9661pct | 11 | 20,567.14 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_oos_CF_0P10 | oos_1 | 0.10 | conservative_crypto_1m | 217 | -0.6867pct | 16 | 6,237.83 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_oos_CF_0P50 | oos_1 | 0.50 | conservative_crypto_1m | 218 | -3.3931pct | 16 | 30,713.81 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_oos_CF_0P10 | oos_2 | 0.10 | conservative_crypto_1m | 219 | -0.1975pct | 9 | 3,576.69 | - |
| oos | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_oos_CF_0P50 | oos_2 | 0.50 | conservative_crypto_1m | 220 | -0.9872pct | 9 | 17,805.05 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_cost_stress_CF_0P10 | owner_a | 0.10 | high_slippage_stress | 221 | -2.1788pct | 25 | 23,027.10 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_cost_stress_CF_0P50 | owner_a | 0.50 | high_slippage_stress | 222 | -10.4542pct | 25 | 109,796.55 | - |
| entry_delay | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_entry_delay_CF_0P10_NEXT_OPEN | owner_a | 0.10 | conservative_crypto_1m | 223 | -0.8366pct | 26 | 9,788.43 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_cost_stress_CF_0P10 | owner_b | 0.10 | high_slippage_stress | 224 | -0.7481pct | 11 | 9,676.57 | - |
| cost_stress | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_cost_stress_CF_0P50 | owner_b | 0.50 | high_slippage_stress | 225 | -3.6936pct | 11 | 47,645.88 | - |
| entry_delay | T279_SRLBR_BREAKDOWN_240_12R_SCORE_0P6_entry_delay_CF_0P10_NEXT_OPEN | owner_b | 0.10 | conservative_crypto_1m | 226 | -0.1678pct | 11 | 4,104.90 | - |
| owner | T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P10 | owner_a | 0.10 | conservative_crypto_1m | 227 | -3.0463pct | 88 | 32,915.23 | - |
| owner | T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P25 | owner_a | 0.25 | conservative_crypto_1m | 228 | -7.4466pct | 88 | 80,394.32 | - |
| owner | T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P50 | owner_a | 0.50 | conservative_crypto_1m | 229 | -14.3511pct | 88 | 154,728.69 | - |
| owner | T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P75 | owner_a | 0.75 | conservative_crypto_1m | 230 | -20.7519pct | 88 | 223,453.66 | - |
| owner | T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P10 | owner_b | 0.10 | conservative_crypto_1m | 231 | -1.2873pct | 36 | 13,495.68 | - |
| owner | T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P25 | owner_b | 0.25 | conservative_crypto_1m | 232 | -3.1891pct | 36 | 33,356.60 | - |
| owner | T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P50 | owner_b | 0.50 | conservative_crypto_1m | 233 | -6.2826pct | 36 | 65,461.02 | - |
| owner | T279_SRLBR_SHORT_MIX_120_8R_owner_CF_0P75 | owner_b | 0.75 | conservative_crypto_1m | 234 | -9.2832pct | 36 | 96,355.70 | - |
| endpoint_trim | T279_SRLBR_SHORT_MIX_120_8R_endpoint_trim_CF_0P10 | trim_a | 0.10 | conservative_crypto_1m | 235 | -3.0463pct | 88 | 32,915.23 | - |
| endpoint_trim | T279_SRLBR_SHORT_MIX_120_8R_endpoint_trim_CF_0P50 | trim_a | 0.50 | conservative_crypto_1m | 236 | -14.3511pct | 88 | 154,728.69 | - |
| endpoint_trim | T279_SRLBR_SHORT_MIX_120_8R_endpoint_trim_CF_0P10 | trim_b | 0.10 | conservative_crypto_1m | 237 | -1.2873pct | 36 | 13,495.68 | - |
| endpoint_trim | T279_SRLBR_SHORT_MIX_120_8R_endpoint_trim_CF_0P50 | trim_b | 0.50 | conservative_crypto_1m | 238 | -6.2826pct | 36 | 65,461.02 | - |
| oos | T279_SRLBR_SHORT_MIX_120_8R_oos_CF_0P10 | oos_1 | 0.10 | conservative_crypto_1m | 239 | -1.8329pct | 50 | 18,616.77 | - |
| oos | T279_SRLBR_SHORT_MIX_120_8R_oos_CF_0P50 | oos_1 | 0.50 | conservative_crypto_1m | 240 | -8.8440pct | 50 | 89,913.00 | - |
| oos | T279_SRLBR_SHORT_MIX_120_8R_oos_CF_0P10 | oos_2 | 0.10 | conservative_crypto_1m | 241 | -1.3049pct | 38 | 14,141.57 | - |
| oos | T279_SRLBR_SHORT_MIX_120_8R_oos_CF_0P50 | oos_2 | 0.50 | conservative_crypto_1m | 242 | -6.3653pct | 38 | 68,771.53 | - |
| cost_stress | T279_SRLBR_SHORT_MIX_120_8R_cost_stress_CF_0P10 | owner_a | 0.10 | high_slippage_stress | 243 | -7.3843pct | 88 | 76,224.97 | - |
| cost_stress | T279_SRLBR_SHORT_MIX_120_8R_cost_stress_CF_0P50 | owner_a | 0.50 | high_slippage_stress | 244 | -31.9114pct | 88 | 328,894.91 | - |
| entry_delay | T279_SRLBR_SHORT_MIX_120_8R_entry_delay_CF_0P10_NEXT_OPEN | owner_a | 0.10 | conservative_crypto_1m | 245 | -3.0825pct | 91 | 33,711.36 | - |
| cost_stress | T279_SRLBR_SHORT_MIX_120_8R_cost_stress_CF_0P10 | owner_b | 0.10 | high_slippage_stress | 246 | -3.0880pct | 36 | 31,473.00 | - |
| cost_stress | T279_SRLBR_SHORT_MIX_120_8R_cost_stress_CF_0P50 | owner_b | 0.50 | high_slippage_stress | 247 | -14.5439pct | 36 | 147,400.21 | - |
| entry_delay | T279_SRLBR_SHORT_MIX_120_8R_entry_delay_CF_0P10_NEXT_OPEN | owner_b | 0.10 | conservative_crypto_1m | 248 | -1.2991pct | 37 | 13,784.25 | - |
| owner | T279_FVG_INVERSE_SIMPLE_owner_CF_0P10 | owner_a | 0.10 | conservative_crypto_1m | 249 | -0.6283pct | 17 | 6,233.57 | - |
| owner | T279_FVG_INVERSE_SIMPLE_owner_CF_0P25 | owner_a | 0.25 | conservative_crypto_1m | 250 | -1.5637pct | 17 | 15,514.85 | - |
| owner | T279_FVG_INVERSE_SIMPLE_owner_CF_0P50 | owner_a | 0.50 | conservative_crypto_1m | 251 | -3.1044pct | 17 | 30,801.11 | - |
| owner | T279_FVG_INVERSE_SIMPLE_owner_CF_0P75 | owner_a | 0.75 | conservative_crypto_1m | 252 | -4.6223pct | 17 | 45,861.94 | - |
| owner | T279_FVG_INVERSE_SIMPLE_owner_CF_0P10 | owner_b | 0.10 | conservative_crypto_1m | 253 | -0.1847pct | 5 | 1,832.50 | - |
| owner | T279_FVG_INVERSE_SIMPLE_owner_CF_0P25 | owner_b | 0.25 | conservative_crypto_1m | 254 | -0.4612pct | 5 | 4,576.19 | - |
| owner | T279_FVG_INVERSE_SIMPLE_owner_CF_0P50 | owner_b | 0.50 | conservative_crypto_1m | 255 | -0.9207pct | 5 | 9,135.51 | - |
| owner | T279_FVG_INVERSE_SIMPLE_owner_CF_0P75 | owner_b | 0.75 | conservative_crypto_1m | 256 | -1.3785pct | 5 | 13,678.03 | - |
| endpoint_trim | T279_FVG_INVERSE_SIMPLE_endpoint_trim_CF_0P10 | trim_a | 0.10 | conservative_crypto_1m | 257 | -0.6283pct | 17 | 6,233.57 | - |
| endpoint_trim | T279_FVG_INVERSE_SIMPLE_endpoint_trim_CF_0P50 | trim_a | 0.50 | conservative_crypto_1m | 258 | -3.1044pct | 17 | 30,801.11 | - |
| endpoint_trim | T279_FVG_INVERSE_SIMPLE_endpoint_trim_CF_0P10 | trim_b | 0.10 | conservative_crypto_1m | 259 | -0.1847pct | 5 | 1,832.50 | - |
| endpoint_trim | T279_FVG_INVERSE_SIMPLE_endpoint_trim_CF_0P50 | trim_b | 0.50 | conservative_crypto_1m | 260 | -0.9207pct | 5 | 9,135.51 | - |
| oos | T279_FVG_INVERSE_SIMPLE_oos_CF_0P10 | oos_1 | 0.10 | conservative_crypto_1m | 261 | -0.2210pct | 6 | 2,199.05 | - |
| oos | T279_FVG_INVERSE_SIMPLE_oos_CF_0P50 | oos_1 | 0.50 | conservative_crypto_1m | 262 | -1.1009pct | 6 | 10,954.78 | - |
| oos | T279_FVG_INVERSE_SIMPLE_oos_CF_0P10 | oos_2 | 0.10 | conservative_crypto_1m | 263 | -0.2929pct | 8 | 2,909.93 | - |
| oos | T279_FVG_INVERSE_SIMPLE_oos_CF_0P50 | oos_2 | 0.50 | conservative_crypto_1m | 264 | -1.4569pct | 8 | 14,475.22 | - |
| cost_stress | T279_FVG_INVERSE_SIMPLE_cost_stress_CF_0P10 | owner_a | 0.10 | high_slippage_stress | 265 | -1.4214pct | 17 | 14,164.78 | - |
| cost_stress | T279_FVG_INVERSE_SIMPLE_cost_stress_CF_0P50 | owner_a | 0.50 | high_slippage_stress | 266 | -6.9189pct | 17 | 68,951.03 | - |
| entry_delay | T279_FVG_INVERSE_SIMPLE_entry_delay_CF_0P10_NEXT_OPEN | owner_a | 0.10 | conservative_crypto_1m | 267 | -0.6272pct | 17 | 6,223.18 | - |
| cost_stress | T279_FVG_INVERSE_SIMPLE_cost_stress_CF_0P10 | owner_b | 0.10 | high_slippage_stress | 268 | -0.4177pct | 5 | 4,162.37 | - |
| cost_stress | T279_FVG_INVERSE_SIMPLE_cost_stress_CF_0P50 | owner_b | 0.50 | high_slippage_stress | 269 | -2.0744pct | 5 | 20,673.17 | - |
| entry_delay | T279_FVG_INVERSE_SIMPLE_entry_delay_CF_0P10_NEXT_OPEN | owner_b | 0.10 | conservative_crypto_1m | 270 | -0.1858pct | 5 | 1,843.93 | - |
| owner | T279_OB_618_WAIT20_owner_CF_0P10 | owner_a | 0.10 | conservative_crypto_1m | 271 | -6.3262pct | 180 | 62,975.95 | - |
| owner | T279_OB_618_WAIT20_owner_CF_0P25 | owner_a | 0.25 | conservative_crypto_1m | 272 | -15.0770pct | 180 | 150,056.35 | - |
| owner | T279_OB_618_WAIT20_owner_CF_0P50 | owner_a | 0.50 | conservative_crypto_1m | 273 | -27.8919pct | 180 | 277,503.91 | - |
| owner | T279_LSR_MARKET_1R_owner_CF_0P10 | owner_a | 0.10 | conservative_crypto_1m | 274 | -0.0005pct | 1 | 404.25 | - |
| owner | T279_LSR_MARKET_1R_owner_CF_0P25 | owner_a | 0.25 | conservative_crypto_1m | 275 | -0.0011pct | 1 | 1,010.63 | - |
| owner | T279_LSR_MARKET_1R_owner_CF_0P50 | owner_a | 0.50 | conservative_crypto_1m | 276 | -0.0023pct | 1 | 2,021.25 | - |
| owner | T279_LSR_MARKET_1R_owner_CF_0P75 | owner_a | 0.75 | conservative_crypto_1m | 277 | -0.0034pct | 1 | 3,031.88 | - |
| owner | T279_LSR_MARKET_1R_owner_CF_0P10 | owner_b | 0.10 | conservative_crypto_1m | 278 | -0.0005pct | 1 | 404.25 | - |
| owner | T279_LSR_MARKET_1R_owner_CF_0P25 | owner_b | 0.25 | conservative_crypto_1m | 279 | -0.0011pct | 1 | 1,010.63 | - |
| owner | T279_LSR_MARKET_1R_owner_CF_0P50 | owner_b | 0.50 | conservative_crypto_1m | 280 | -0.0023pct | 1 | 2,021.25 | - |
| owner | T279_LSR_MARKET_1R_owner_CF_0P75 | owner_b | 0.75 | conservative_crypto_1m | 281 | -0.0034pct | 1 | 3,031.88 | - |
| endpoint_trim | T279_LSR_MARKET_1R_endpoint_trim_CF_0P10 | trim_a | 0.10 | conservative_crypto_1m | 282 | -0.0005pct | 1 | 404.25 | - |
| endpoint_trim | T279_LSR_MARKET_1R_endpoint_trim_CF_0P50 | trim_a | 0.50 | conservative_crypto_1m | 283 | -0.0023pct | 1 | 2,021.25 | - |
| endpoint_trim | T279_LSR_MARKET_1R_endpoint_trim_CF_0P10 | trim_b | 0.10 | conservative_crypto_1m | 284 | -0.0005pct | 1 | 404.25 | - |
| endpoint_trim | T279_LSR_MARKET_1R_endpoint_trim_CF_0P50 | trim_b | 0.50 | conservative_crypto_1m | 285 | -0.0023pct | 1 | 2,021.25 | - |
| oos | T279_LSR_MARKET_1R_oos_CF_0P10 | oos_1 | 0.10 | conservative_crypto_1m | 286 | +0.0000pct | 0 | 0.00 | - |
| oos | T279_LSR_MARKET_1R_oos_CF_0P50 | oos_1 | 0.50 | conservative_crypto_1m | 287 | +0.0000pct | 0 | 0.00 | - |
| oos | T279_LSR_MARKET_1R_oos_CF_0P10 | oos_2 | 0.10 | conservative_crypto_1m | 288 | +0.0000pct | 0 | 0.00 | - |
| oos | T279_LSR_MARKET_1R_oos_CF_0P50 | oos_2 | 0.50 | conservative_crypto_1m | 289 | +0.0000pct | 0 | 0.00 | - |
| cost_stress | T279_LSR_MARKET_1R_cost_stress_CF_0P10 | owner_a | 0.10 | high_slippage_stress | 290 | +0.0000pct | 0 | 0.00 | - |
| cost_stress | T279_LSR_MARKET_1R_cost_stress_CF_0P50 | owner_a | 0.50 | high_slippage_stress | 291 | +0.0000pct | 0 | 0.00 | - |
| entry_delay | T279_LSR_MARKET_1R_entry_delay_CF_0P10_NEXT_OPEN | owner_a | 0.10 | conservative_crypto_1m | 292 | +0.0019pct | 1 | 381.01 | - |
| cost_stress | T279_LSR_MARKET_1R_cost_stress_CF_0P10 | owner_b | 0.10 | high_slippage_stress | 293 | +0.0000pct | 0 | 0.00 | - |
| cost_stress | T279_LSR_MARKET_1R_cost_stress_CF_0P50 | owner_b | 0.50 | high_slippage_stress | 294 | +0.0000pct | 0 | 0.00 | - |
| entry_delay | T279_LSR_MARKET_1R_entry_delay_CF_0P10_NEXT_OPEN | owner_b | 0.10 | conservative_crypto_1m | 295 | +0.0019pct | 1 | 381.01 | - |

## Task 278 Benchmark Interpretation

- Task 278 run `155` and run `156` passed the owner's raw total-return check but used one full-window simulated short position.
- Under Task 279 gates, that behavior fails sample-size, endpoint-dependence, exposure concentration, OOS, and promotion robustness requirements.
- Task 278 remains a directional benchmark, not a validated multi-trade strategy.

## Cost Verification

- Every persisted Task 279 run used a non-zero cost profile unless the run failed before persistence.
- Conservative profile runs used `conservative_crypto_1m`; stress runs used `high_slippage_stress`.
- The report rejects candidates whose gross edge is dominated by fee/spread/slippage or whose cost-to-gross-PnL ratio exceeds `0.40`.

## OOS And Data-Snooping

- Owner windows `2026-05-20+` and `2026-05-25+` remain development evidence only.
- OOS windows were predeclared from `2026-05-10` to `2026-05-14` and `2026-05-14` to `2026-05-18`.
- No result is promoted beyond `RESEARCH_ONLY`.

## Next Step

Build a new bounded multi-trade model only after defining an entry thesis that can pass these gates at `cash_fraction=0.10` before sizing is increased.
