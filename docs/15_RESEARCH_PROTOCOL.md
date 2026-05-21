# Research Protocol And Experiment Governance

## Purpose
This document defines mandatory research governance for pattern-based Bitcoin strategy experiments in this repository. The goal is to reduce false discoveries and prevent premature promotion by enforcing deterministic, auditable, and out-of-sample-first evaluation.

## Current Repository State
- Deterministic pattern detectors and event outputs are implemented for Fair Value Gap (FVG), Trendline Break, Order Block, Cup and Handle, Diamond, and Adam and Eve.
- Pattern risk/exit planning and pattern backtest CLI workflows exist for historical simulation.
- Standard candle schema and architecture boundaries are already defined and must remain authoritative.
- Live trading remains blocked; current work is research and paper-only.

## Research Boundary
This protocol governs research decisions only. It does not authorize:
- live trading,
- real exchange order execution,
- API key usage,
- signed Binance order/account requests,
- bypassing existing safety boundaries.

## Strategy Lifecycle
All strategy candidates must move through these exact states:
1. `IDEA`
2. `MECHANICAL_DEFINITION`
3. `EVENT_STUDY`
4. `GROSS_BACKTEST`
5. `NET_BACKTEST`
6. `WALK_FORWARD_VALIDATED`
7. `PAPER_ONLY_CANDIDATE`
8. `RESEARCH_ONLY`
9. `REJECTED`

Lifecycle intent:
- `IDEA` -> hypothesis is recorded but untested.
- `MECHANICAL_DEFINITION` -> exact, deterministic rules are fixed.
- `EVENT_STUDY` -> event-level validity and context are tested before PnL claims.
- `GROSS_BACKTEST` -> pre-cost simulation for structural sanity only.
- `NET_BACKTEST` -> includes explicit costs, spread/slippage, and fill assumptions.
- `WALK_FORWARD_VALIDATED` -> out-of-sample rolling validation completed.
- `PAPER_ONLY_CANDIDATE` -> eligible for paper-only runtime observation.
- `RESEARCH_ONLY` -> retained for learning, not promoted.
- `REJECTED` -> invalidated or dominated; no further testing unless a new hypothesis is logged.

## Hypothesis Definition
Before any event study or backtest, each candidate must include:
- pattern family and directionality under test,
- market regime assumptions,
- exact entry/exit logic,
- invalidation logic,
- expected edge source,
- pre-declared evaluation window,
- pre-declared metrics and pass/fail thresholds.

Hypotheses must be testable, falsifiable, and deterministic.

## Event Study Requirements
Event study is required before backtest promotion.

Minimum requirements:
- validate event labeling quality (true/false structural context sampling),
- verify no look-ahead in event construction,
- confirm standard candle schema compliance,
- record event frequency and clustering behavior,
- document edge intuition independent of net PnL.

For FVG, Order Block, and Trendline Break specifically, event study documentation must include planned treatment of costs, fill assumptions, and out-of-sample validation before any promotion.

## Backtest Requirements
Backtests must be reproducible and explicitly configured:
- fixed input dataset snapshot/version,
- deterministic parameter set,
- deterministic execution assumptions,
- explicit strategy state transitions,
- no hidden runtime randomness.

`GROSS_BACKTEST` results may be used only to detect structural issues, not to claim deployable profitability.

## Net Performance Requirements
No strategy can be considered a candidate without `NET_BACKTEST` results that include:
- transaction costs/fees,
- spread assumptions,
- slippage assumptions,
- entry fill assumptions,
- exit fill assumptions.

Net metrics must include return and drawdown-aware statistics (including tail-risk commentary), not only win-rate.

## Baseline Comparison Requirements
Every candidate must be compared against pre-declared baselines, at minimum:
- buy-and-hold over the same period,
- a naive rule baseline with comparable turnover assumptions,
- (when relevant) pattern-family sibling baseline.

A strategy that does not beat baseline on risk-adjusted and net terms should not be promoted.

## Train / Validation / Test / Holdout Policy
Data partitions must be defined before tuning:
- **Train**: used for rule fitting and bounded parameter exploration.
- **Validation**: used for model/parameter selection.
- **Test**: untouched until one final locked evaluation.
- **Holdout**: reserved for final confirmation after research convergence.

Rules:
- no leakage across splits,
- no relabeling/repartitioning after seeing test/holdout outcomes,
- split timestamps and instruments must be logged in research records.

## Parameter Search Governance
Parameter search spaces must be pre-declared before running experiments:
- parameter names, bounds, step rules,
- search method (grid/random/manual),
- maximum trial count,
- promotion criteria independent of one best run.

Post-hoc expansion of search space after weak outcomes must be treated as a new research cycle and logged as such.

## Multiple Testing And Data Snooping Policy
To control false positives:
- track total hypothesis/tests count per cycle,
- record all attempted parameter sets (not only winners),
- require robustness checks across nearby parameter neighborhoods,
- require out-of-sample confirmation before status upgrade,
- downgrade to `RESEARCH_ONLY` or `REJECTED` when repeated retuning is needed to preserve edge.

Exploring many patterns (including FVG, Order Block, Trendline Break, Cup and Handle, Diamond, Adam and Eve) without correction/discipline is considered data snooping and is not acceptable for promotion.

## Walk-Forward Validation Policy
`WALK_FORWARD_VALIDATED` requires:
- rolling or expanding walk-forward windows,
- train/validation on each origin window,
- untouched forward segment scoring,
- aggregated forward-only performance summary,
- stability analysis across windows.

Promotion is blocked when performance is concentrated in one window or one regime only.

## Strategy Promotion Criteria
A strategy can be promoted only when all are satisfied:
- no look-ahead bias,
- standard candle schema compliance,
- deterministic reproducibility,
- transaction costs included,
- slippage / spread assumptions included,
- entry fill assumptions documented,
- out-of-sample validation completed,
- baseline comparison passed,
- parameter sensitivity review completed,
- multiple testing control documented,
- drawdown and tail-risk review completed,
- no live trading behavior.

## Strategy Rejection Criteria
A strategy should be `REJECTED` when one or more apply:
- edge disappears after costs/fill/slippage,
- fails out-of-sample repeatedly,
- only profitable under narrow unstable parameters,
- cannot beat baseline with acceptable drawdown,
- requires assumptions inconsistent with realistic fills,
- relies on look-ahead or leakage.

A strategy should be `RESEARCH_ONLY` when inconclusive but still educational.

## Live Trading Blocker Reminder
Research success does **not** authorize live trading.

Live trading remains blocked until a separate explicit future task resolves and verifies:
- credential/key policy,
- sandbox/testnet policy,
- endpoint allowlist,
- kill switch design,
- safety tests for execution boundaries.

## Required Evidence Before Promotion
Before status can move to `PAPER_ONLY_CANDIDATE`, collect:
- hypothesis record with pre-declared search space,
- event study report,
- gross and net backtest reports,
- walk-forward validation report,
- baseline comparison report,
- parameter sensitivity and robustness report,
- drawdown/tail-risk summary,
- reproducibility package (commands, versions, config).

## Recommended Next Tasks
1. Create a research experiment template and registry format for reproducible run logging.
2. Add a formal baseline-comparison report schema for pattern backtest outputs.
3. Add walk-forward orchestration utilities and documentation for rolling splits.
4. Add explicit cost/slippage/fill configuration contracts to standardize net backtests.
