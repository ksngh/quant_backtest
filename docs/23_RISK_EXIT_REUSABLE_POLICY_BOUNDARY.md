# Risk/Exit Reusable Policy Boundary (Task 083)

## Summary

Task 083 extracts generic risk/exit contracts and simulation out of `quant_bitcoin/patterns/` into `quant_bitcoin/risk/` so pattern detection and trade-management policy ownership are separated.

## New Ownership

- Generic risk/exit plan contracts live in `quant_bitcoin/risk/exit_plan.py`.
- Generic exit simulation lives in `quant_bitcoin/risk/exit_simulation.py`.
- Pattern modules remain detection-focused and may keep pattern-specific adapters that call shared risk contracts.

## Compatibility

To avoid broad import breakage during transition:

- `quant_bitcoin/patterns/risk_exit.py` re-exports from `quant_bitcoin.risk.exit_plan`.
- `quant_bitcoin/patterns/exit_simulation.py` re-exports from `quant_bitcoin.risk.exit_simulation`.

This preserves existing call sites while enabling strategies/backtests to import from `quant_bitcoin.risk` directly.

## Reusability Direction

This boundary supports future composition such as:

- any pattern strategy + shared R-multiple target policies
- any pattern strategy + shared ATR stop policies
- pattern-specific invalidation adapters on top of shared plan/simulation contracts
