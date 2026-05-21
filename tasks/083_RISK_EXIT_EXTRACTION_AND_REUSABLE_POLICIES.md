# Task 083: Risk/Exit Extraction And Reusable Policies

## Area

Backtest/Core + Quant Research

## Goal

Separate stop-loss, take-profit, partial-exit, time-stop, break-even, trailing-stop, and soft-invalidation logic from pattern detector modules so that risk/exit methods can be mixed with different pattern strategies.

## Source Requirement

The owner wants stop-loss and take-profit logic removed from pattern ownership and moved into `risk` or another non-pattern package. Later, patterns and risk/exit methods should be composable.

## Current Problems To Address

Current code has risk/exit logic under `quant_bitcoin/patterns/`, for example:

```text
quant_bitcoin/patterns/risk_exit.py
quant_bitcoin/patterns/exit_simulation.py
quant_bitcoin/patterns/diamond_risk_exit.py
```

This makes pattern detection and trade management too tightly coupled.

## Required Reading

- `AGENTS.md`
- `STATUS.md`
- `BACKLOG.md`
- `PROJECT_HISTORY.md`
- this task document
- `docs/22_STRATEGY_BACKTEST_ARCHITECTURE.md` from Task 080
- `quant_bitcoin/patterns/risk_exit.py`
- `quant_bitcoin/patterns/exit_simulation.py`
- `quant_bitcoin/patterns/*_risk_exit.py`
- `tests/patterns/test_*risk_exit*.py`
- `tests/patterns/test_exit_simulation.py`

## Scope

Create a reusable risk/exit package boundary.

Recommended target layout:

```text
quant_bitcoin/risk/
  __init__.py
  exit_plan.py
  exit_simulation.py
  policies.py
  pattern_adapters/
    __init__.py
    fair_value_gap.py
    trendline_break.py
    order_block.py
    cup_and_handle.py
    diamond.py
    adam_and_eve.py
```

Allowed alternatives are acceptable if they preserve the boundary:

```text
pattern detectors remain in quant_bitcoin/patterns/
risk and exit policies move out of quant_bitcoin/patterns/
strategies import risk policies through the new risk package
```

## Required Concepts

The new risk package should support:

```text
RiskExitPlan
RiskExitConfig
RiskExitTarget
RiskExitDirection
RiskExitPlanStatus
BreakEvenSettings
TrailingStopSettings
TimeStopSettings
PartialExitSettings
SoftInvalidationRule
PatternExitSimulationResult
```

## Reusability Requirement

Risk/exit methods must be composable.

Examples the future architecture should allow:

```text
DiamondPatternStrategy + DiamondStructuralRiskPolicy
DiamondPatternStrategy + GenericRMultipleRiskPolicy
FairValueGapStrategy + FairValueGapMidpointInvalidationPolicy
FairValueGapStrategy + GenericATRStopPolicy
```

The task does not need to implement all possible combinations, but the architecture must not prevent them.

## Backward Compatibility

If moving modules would break many imports, keep compatibility shims:

```python
# quant_bitcoin/patterns/risk_exit.py
from quant_bitcoin.risk.exit_plan import ...
```

Same for exit simulation and pattern-specific risk adapters if needed.

## Out of Scope

- No new strategy implementation beyond required import updates.
- No live trading.
- No real order execution.
- No exchange APIs.
- No frontend/backend dashboard work.
- No major detector rewrite.
- No statistical research reports.

## Execution Steps

1. Create the new risk package boundary.
2. Move or re-export generic risk/exit contracts.
3. Move or re-export exit simulation.
4. Move or adapt pattern-specific risk planners into reusable risk adapters.
5. Update imports in pattern strategy and tests.
6. Preserve existing behavior.
7. Ensure old imports still pass during transition if possible.
8. Document the new boundary.

## Acceptance Criteria

- Pattern detector modules no longer own generic stop-loss/take-profit/exit simulation contracts.
- Strategies can import risk/exit logic from `quant_bitcoin.risk`.
- Existing pattern risk/exit tests still pass or are updated to the new import path.
- Behavior remains deterministic.
- No exchange order/account calls are introduced.
- No live trading behavior is introduced.

## Verification

Run:

```bash
pytest -q tests/patterns/test_exit_simulation.py
pytest -q tests/patterns/test_diamond_risk_exit.py
pytest -q tests/patterns
pytest -q
git diff --check
```

If environment limits full tests, record exact limitation in `STATUS.md`.

## Required State Updates

- Update `STATUS.md`.
- Append completion to `PROJECT_HISTORY.md`.
- Update `BACKLOG.md` if stale risk/exit candidates are discovered.

## Completion Summary Required

Include:

- files changed
- modules moved or re-exported
- compatibility shims added
- tests run
- known limitations
- recommended next task
