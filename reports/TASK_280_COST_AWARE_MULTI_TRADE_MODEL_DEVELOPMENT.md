# Task 280 Cost-Aware Multi-Trade Model Development

Status: `HARD_DATA_CONSTRAINT_RESEARCH_ONLY`

## Scope

- Offline-only BTCUSDT 1m strategy research.
- No live trading, no exchange orders, no API keys, no futures/leverage assumptions.
- Primary sizing remained `cash_fraction=0.10` with `conservative_crypto_1m` costs.

## Persistence Summary

- Persisted Task 280 runs: `576` (`296`-`889`).
- Owner windows: `owner_a=2026-05-20T00:00:00Z..2026-05-28T08:26:00Z`, `owner_b=2026-05-25T00:00:00Z..2026-05-28T08:26:00Z`.
- Batches attempted: `batch1` through `batch9`.

## Best Combined Candidate

- Variant: `T280_B9_PULLBACK_TW720_TH30P0_CW360_TG250P0_ST120P0` (`batch9`).
- Window A run `864`: return `+0.2057%`, trips `9`, cost/gross `0.6190`.
- Window B run `865`: return `+0.3001%`, trips `4`, cost/gross `0.3308`.
- Costs A: fee `1,795.14`, spread `538.54`, slippage `1,007.89`, total `3,341.57`.
- Costs B: fee `796.24`, spread `238.87`, slippage `448.22`, total `1,483.33`.

## Acceptance Gate Check

| Gate | Required | Best Candidate | Result |
| --- | ---: | ---: | --- |
| Window A return | `+3.0000%` | `+0.2057%` | `FAIL` |
| Window B return | `+3.0000%` | `+0.3001%` | `FAIL` |
| Window A trips | `>=20` | `9` | `FAIL` |
| Window B trips | `>=8` | `4` | `FAIL` |
| Window A cost/gross | `<0.40` | `0.6190` | `FAIL` |
| Window B cost/gross | `<0.40` | `0.3308` | `PASS` |

## Hard Data Constraint Check

- Perfect-hindsight close-to-close long/short switching upper-bound at 10% sizing, after an approximate 38bps round-trip cost: Window A `+4.3053%` across `101` switches.
- The same upper-bound for Window B is `+1.9146%` across `48` switches, below the required `+3.0000%` before adding implementable signal constraints.
- This is why continuing to tune deterministic non-levered 10% sizing variants against the same two windows is not trustworthy as a promotion path.

## Top Owner-Window Variants

| Variant | Batch | Run A | Ret A | Trips A | Cost/Gross A | Run B | Ret B | Trips B | Cost/Gross B |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `T280_B9_PULLBACK_TW720_TH30P0_CW360_TG250P0_ST120P0` | `batch9` | `864` | `+0.2057%` | `9` | `0.6190` | `865` | `+0.3001%` | `4` | `0.3308` |
| `T280_B9_MOMENTUM_TW720_TH30P0_CW360_TG250P0_ST120P0` | `batch9` | `888` | `+0.2050%` | `9` | `0.6203` | `889` | `+0.3001%` | `4` | `0.3308` |
| `T280_B9_MOMENTUM_TW240_TH15P0_CW360_TG180P0_ST90P0` | `batch9` | `874` | `+0.1931%` | `11` | `0.6820` | `875` | `+0.3079%` | `5` | `0.3829` |
| `T280_B9_PULLBACK_TW240_TH15P0_CW360_TG180P0_ST90P0` | `batch9` | `850` | `+0.1901%` | `11` | `0.6852` | `851` | `+0.3049%` | `5` | `0.3851` |
| `T280_B9_PULLBACK_TW720_TH30P0_CW0_TG250P0_ST120P0` | `batch9` | `858` | `+0.1803%` | `9` | `0.6498` | `859` | `+0.3001%` | `4` | `0.3308` |
| `T280_B9_MOMENTUM_TW720_TH30P0_CW0_TG250P0_ST120P0` | `batch9` | `882` | `+0.1803%` | `9` | `0.6498` | `883` | `+0.3001%` | `4` | `0.3308` |
| `T280_B7_IMPULSE_CW360_CB20P0_TG250P0_ST120P0_H720` | `batch7` | `710` | `+0.1737%` | `10` | `0.6843` | `711` | `+0.2903%` | `5` | `0.3903` |
| `T280_B9_MOMENTUM_TW720_TH30P0_CW360_TG180P0_ST90P0` | `batch9` | `886` | `+0.1647%` | `10` | `0.7055` | `887` | `+0.2786%` | `5` | `0.4073` |
| `T280_B9_PULLBACK_TW720_TH30P0_CW360_TG180P0_ST90P0` | `batch9` | `862` | `+0.1624%` | `10` | `0.7085` | `863` | `+0.2765%` | `5` | `0.4092` |
| `T280_B9_MOMENTUM_TW720_TH30P0_CW0_TG180P0_ST90P0` | `batch9` | `880` | `+0.1528%` | `11` | `0.7319` | `881` | `+0.2786%` | `5` | `0.4073` |
| `T280_B9_PULLBACK_TW720_TH30P0_CW0_TG180P0_ST90P0` | `batch9` | `856` | `+0.1507%` | `11` | `0.7347` | `857` | `+0.2765%` | `5` | `0.4092` |
| `T280_B9_MOMENTUM_TW720_TH30P0_CW0_TG120P0_ST60P0` | `batch9` | `878` | `+0.1675%` | `11` | `0.7209` | `879` | `+0.2247%` | `5` | `0.4655` |
| `T280_B9_PULLBACK_TW720_TH30P0_CW0_TG120P0_ST60P0` | `batch9` | `854` | `+0.1652%` | `11` | `0.7237` | `855` | `+0.2226%` | `5` | `0.4679` |
| `T280_B9_MOMENTUM_TW240_TH15P0_CW0_TG180P0_ST90P0` | `batch9` | `868` | `+0.1157%` | `12` | `0.7963` | `869` | `+0.2452%` | `6` | `0.4818` |
| `T280_B9_MOMENTUM_TW720_TH30P0_CW360_TG120P0_ST60P0` | `batch9` | `884` | `+0.0864%` | `10` | `0.8199` | `885` | `+0.2247%` | `5` | `0.4655` |
| `T280_B9_PULLBACK_TW720_TH30P0_CW360_TG120P0_ST60P0` | `batch9` | `860` | `+0.0841%` | `10` | `0.8238` | `861` | `+0.2226%` | `5` | `0.4679` |
| `T280_B9_MOMENTUM_TW240_TH15P0_CW360_TG250P0_ST120P0` | `batch9` | `876` | `-0.0431%` | `10` | `1.1317` | `877` | `+0.3293%` | `4` | `0.3099` |
| `T280_B9_PULLBACK_TW240_TH15P0_CW360_TG250P0_ST120P0` | `batch9` | `852` | `-0.0432%` | `10` | `1.1324` | `853` | `+0.3285%` | `4` | `0.3103` |
| `T280_B7_IMPULSE_CW360_CB20P0_TG180P0_ST90P0_H720` | `batch7` | `704` | `+0.0301%` | `10` | `0.9290` | `705` | `+0.2409%` | `5` | `0.4440` |
| `T280_B7_IMPULSE_CW360_CB20P0_TG120P0_ST60P0_H720` | `batch7` | `698` | `+0.0408%` | `14` | `0.9303` | `699` | `+0.2030%` | `7` | `0.5642` |
| `T280_B7_BREAKDOWN_CW360_CB20P0_TG250P0_ST120P0_H720` | `batch7` | `746` | `+0.0385%` | `10` | `0.9086` | `747` | `+0.1877%` | `5` | `0.5030` |
| `T280_B9_MOMENTUM_TW240_TH15P0_CW0_TG250P0_ST120P0` | `batch9` | `870` | `-0.0677%` | `11` | `1.1983` | `871` | `+0.2795%` | `5` | `0.4000` |
| `T280_B7_BREAKDOWN_CW360_CB20P0_TG180P0_ST90P0_H720` | `batch7` | `740` | `+0.0117%` | `10` | `0.9720` | `741` | `+0.1336%` | `5` | `0.5945` |
| `T280_B6_IMPULSE_TW240_TH15P0_TG250P0_ST120P0_H720` | `batch6` | `600` | `+0.0794%` | `13` | `0.8589` | `601` | `+0.0539%` | `7` | `0.8281` |
| `T280_B7_BREAKDOWN_CW720_CB40P0_TG180P0_ST90P0_H720` | `batch7` | `758` | `-0.0225%` | `11` | `1.0557` | `759` | `+0.1527%` | `5` | `0.5604` |

## Iteration State

- No candidate is promoted.
- The task is stopped on a hard data constraint under the current mandatory assumptions, not on an untested failure summary.
