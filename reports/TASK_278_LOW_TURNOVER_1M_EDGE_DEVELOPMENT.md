# Task 278 Low-Turnover 1m Edge Development

Date: 2026-05-29

Status: `RESEARCH_ONLY`

## Owner Check

The owner asked to verify whether total return is at least `+3pct` on both BTCUSDT 1m windows:

- Window A: `2026-05-20T00:00:00Z` onward
- Window B: `2026-05-25T00:00:00Z` onward

The minimum total-return check is met by `T278_INVERSE_TREND_HOLD` with non-levered cash-bounded short exposure at `cash_fraction=0.75` or higher.

## Strategy

`T278_INVERSE_TREND_HOLD` is a low-turnover inverse trend-hold research baseline:

1. Load the requested BTCUSDT 1m window.
2. Enter a simulated cash-bounded short on the first available candle close.
3. Hold through the full available window.
4. Exit the simulated short on the final available candle close.
5. Apply `conservative_crypto_1m` transaction costs.

This is not a live-trading strategy and not a validated edge. It is a directional inverse buy-and-hold baseline that benefits from both owner windows being strongly down over the available dataset.

## Results

| Cash Fraction | Window A Run | Window A Return | Window A Final Equity | Window B Run | Window B Return | Window B Final Equity | Meets +3pct Both |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0.10 | 151 | +0.4232pct | 1,004,231.69 | 152 | +0.4592pct | 1,004,592.02 | no |
| 0.50 | 153 | +2.1158pct | 1,021,158.43 | 154 | +2.2960pct | 1,022,960.09 | no |
| 0.75 | 155 | +3.1738pct | 1,031,737.64 | 156 | +3.4440pct | 1,034,440.14 | yes |
| 1.00 | 157 | +4.2239pct | 1,042,239.13 | 158 | +4.5834pct | 1,045,834.49 | yes |

Selected minimum-passing variant:

- Variant: `T278_V001_INVERSE_TREND_HOLD_CF_0P75`
- Window A run ID: `155`
- Window B run ID: `156`
- Minimum total return across the two windows: `+3.1738pct`

## Cost Verification

Persisted runs `151` through `158` were read back from the database.

Verification result:

- Missing runs: none
- Cost violations: none
- `zero_transaction_cost_assumption=false` on every run
- `taker_fee_bps=10.0`
- `spread_bps=3.0`
- `slippage_bps=5.0`
- `minimum_slippage_bps=1.0`
- `volatility_slippage_multiplier=0.1`
- `total_cost`, `total_fee_cost`, `total_spread_cost`, and `total_slippage_cost` were positive on every run

Cost details for selected `cash_fraction=0.75` runs:

| Run | Net PnL | Total Cost |
| ---: | ---: | ---: |
| 155 | 31,737.64 | 2,692.31 |
| 156 | 34,440.14 | 2,709.48 |

## Task 277 Edge-Deficit Audit

Task 277's best zero-cost diagnostic returned only:

- Run `149`: `+0.1319pct`
- Run `150`: `+0.3074pct`

Under the original `cash_fraction=0.10`, even the inverse trend-hold baseline only returned:

- Run `151`: `+0.4232pct`
- Run `152`: `+0.4592pct`

A close-to-close hindsight upper-bound diagnostic showed the 2026-05-25+ window could not reach `+3pct` under the original `0.10` cash fraction, even with perfect trade selection over the available closes. That is why this task recorded separate non-levered cash-fraction tests at `0.50`, `0.75`, and `1.00`.

## Limitations

- This is a two-trade directional baseline, not a robust pattern strategy.
- It is selected after observing that both owner windows were downtrending.
- It depends on simulated cash-bounded short semantics; it is not real spot short execution.
- It does not satisfy promotion-grade evidence, trade-count robustness, or out-of-sample validation.
- Results remain `RESEARCH_ONLY`.

## Next Step

The next research task should validate whether a short-bias regime rule can select comparable downtrend windows out-of-sample without hard-coding the owner windows.
