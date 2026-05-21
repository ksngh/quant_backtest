# Pattern Event Study Schema

## Why this document exists

Before promoting any chart pattern into an entry/exit strategy, we separate:
1. pattern detection output (what happened), and
2. forward labels (what happened next).

This supports reproducible event studies that can test predictive information without strategy-rule leakage.

## Boundary definitions

- **Pattern detection**: deterministic extraction of pattern events from completed candles only.
- **Event study**: research dataset that joins event records with forward-looking labels at fixed horizons (no trading simulation rules).
- **Trade backtest**: simulation with entry, stop, target, sizing, costs, and state transitions.
- **Strategy promotion**: decision gate from research-only to strategy-level testing after event-study evidence and protocol checks.

## Pattern event-study record schema

Canonical record fields:
- `event_id`
- `pattern_type`
- `direction`
- `pattern_status`
- `symbol`
- `timeframe`
- `timestamp`
- `start_index`
- `end_index`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `risk_reward`
- `pattern_score`
- `volume_ratio`
- `displacement_confirmed`
- `metadata` (optional pattern-specific dictionary)

Notes:
- `metadata` stores pattern-specific values such as zone geometry, pivot sets, or reason text.
- Required identity and timing fields are normalized across pattern types.

## Forward label schema

Forward-label fields (not computed in this task):
- `forward_return_1`, `forward_return_3`, `forward_return_5`, `forward_return_15`, `forward_return_60`
- `mfe_5`, `mae_5`, `mfe_15`, `mae_15`, `mfe_60`, `mae_60`
- `hit_1r_before_minus_1r`, `hit_2r_before_minus_1r`
- `time_to_invalidation`

## No-look-ahead requirements

1. Event records must be produced from information available at the event timestamp only.
2. Forward labels must be calculated strictly from candles **after** the event timestamp/index.
3. No strategy entry/exit fill assumptions are allowed in event-study labeling.
4. Label generation must use fixed, pre-declared horizons and definitions to prevent post-hoc selection bias.
5. Dataset serialization must remain deterministic for reproducible research runs.
