# Multiple Testing and Data Snooping Control Protocol

## Purpose
This protocol defines mandatory controls for pattern strategy research when many hypotheses, pattern families, and parameter combinations are tested. Its purpose is to reduce false discoveries, overfitting, and post-hoc promotion bias.

This document applies to research on:
- Fair Value Gap (FVG)
- Order Block
- Trendline Break
- Cup and Handle
- Diamond
- Adam and Eve
- RSI filter variants layered on pattern signals
- Multi-signal confluence studies across any combination of the above

## Why Multiple Testing Matters
When many strategy variants are tested, some will appear profitable purely by chance. If researchers only keep the top result and ignore the total number of attempts, estimated edge is biased upward and likely non-repeatable.

In pattern strategy workflows, false discovery pressure is high because each family can generate many threshold/filter combinations. Typical examples include:
- pattern-specific geometric thresholds,
- confirmation window lengths,
- stop/target multipliers,
- RSI filter thresholds and windows,
- confluence rules requiring two or more simultaneous conditions,
- cost/slippage/fill sensitivity toggles.

Testing many variants without explicit correction is data snooping. Promotion decisions made under snooping are invalid.

## Core Definitions

### Experiment Family
A bounded research campaign with one declared objective, one dataset partition policy, one pre-declared search space, and one shared decision date.

Examples:
- "FVG + RSI filter variants on BTCUSDT 1m, 2024-01 to 2025-12"
- "Confluence study: Trendline Break + Order Block across fixed net-cost assumptions"

### Strategy Variant
One uniquely identifiable configuration (pattern + parameters + filters + execution/cost assumptions + split policy).

A variant must have a deterministic `variant_id` or canonical parameter hash.

### Parameter Search Space
The complete pre-declared set of candidate values or ranges that may be explored inside one experiment family.

Must include:
- parameter names,
- bounds/levels,
- step sizes or explicit enumerations,
- search method (grid/random/manual),
- maximum trial count,
- stopping rules.

### Primary Metric
The single decision-driving metric declared before execution. Suggested options include net risk-adjusted outcome metrics (for example net Sharpe-equivalent) with required minimum trade count.

### Secondary Metrics
Supporting metrics used for diagnostics and rejection gating, not for post-hoc primary-metric substitution.

### Baseline Strategies
Pre-declared comparators required for context. Minimum baseline set:
- buy-and-hold over the same time interval,
- naive turnover-comparable baseline,
- sibling baseline when comparing within the same pattern family.

### Validation Period
Out-of-sample segment used for model/parameter selection after training.

### Holdout Period
Locked final segment reserved for one final confirmation after research convergence. Holdout outcomes must not drive repeated retuning.

### Family-wise Tested Variant Count
Total count of distinct strategy variants executed in an experiment family, including failed, discarded, and intermediate runs.

## Mandatory Split Protection
Research must pre-declare and preserve:
- train,
- validation,
- test,
- holdout.

Rules:
1. Train: fitting and bounded search only.
2. Validation: selection only.
3. Test: one locked evaluation after selection.
4. Holdout: final confirmation, inspected only after test-stage convergence.

Prohibited behavior:
- repartitioning after seeing test or holdout outcomes,
- repeated holdout peeking during tuning,
- relabeling the same period as new holdout after failure,
- selective reporting of only successful windows.

## Pre-Declaration Requirement
Before running sweeps, every experiment family must record:
- family name and objective,
- universe/timeframe/instrument,
- train/validation/test/holdout date boundaries,
- full parameter search space,
- primary metric,
- secondary metrics,
- baseline list,
- variant counting rule,
- rejection and promotion rules.

No strategy may be promoted based only on best in-sample performance.

## Variant Counting Rules
Variant counts must include every distinct tested configuration. Count at minimum cross-products of:
- pattern family choice,
- parameter tuple,
- filter tuple (including RSI/confluence toggles),
- entry/exit and fill-assumption mode,
- cost/slippage/spread assumptions when varied,
- split scheme when varied (if permitted by protocol).

If a run is executed and produces output (success, failure, or poor quality), it still counts.

## Metric Governance
Suggested minimum metric set for net evaluations:
- net total return,
- max drawdown,
- net Sharpe (or equivalent risk-adjusted metric),
- mean realized R,
- profit factor,
- trade count minimum,
- drawdown duration.

Primary metric must be fixed before experiment execution. Secondary metrics may trigger rejection even if primary metric looks strong.

## Multiple-Testing Controls
Use conservative controls proportionate to family size and claim type:

1. **Pre-declared grid/search space** (mandatory)
2. **Validation-only model selection** (mandatory)
3. **Locked holdout test** (mandatory)
4. **Bonferroni-style conservative threshold** where strong family-wise error control is required
5. **Benjamini-Hochberg FDR control** where broader discovery screening is acceptable
6. **Stress-test requirement** on cost/slippage/fill assumptions before promotion
7. **Bootstrap reality check** reserved for later implementation task
8. **Deflated Sharpe ratio** reserved for later implementation task

Selection framework note:
- use stricter family-wise controls when claiming promotion-grade edge;
- use FDR-style controls for exploratory prioritization, but require stricter confirmation before promotion.

## Minimum Report Fields (Per Experiment Family)
Each experiment family report must include at minimum:
1. Family identifier and objective
2. Pattern families included (explicitly naming FVG/Order Block/Trendline Break/Cup and Handle/Diamond/Adam and Eve where relevant)
3. RSI/confluence usage declaration
4. Dataset snapshot identifier and candle schema confirmation
5. Train/validation/test/holdout boundaries (timestamps)
6. Pre-declared search space
7. Total family-wise tested variant count
8. Primary metric and threshold
9. Secondary metrics and thresholds
10. Baseline strategy definitions
11. Net cost/slippage/spread/fill assumptions
12. Selected variant identifier with full parameterization
13. Test and holdout outcomes
14. Decision: promoted/research-only/rejected
15. Reason codes for rejection or conditional acceptance

## Rejection Rules
A strategy candidate in a family must be rejected or downgraded to `RESEARCH_ONLY` if any applies:
- promotion case depends only on best in-sample run,
- search space was not pre-declared before sweeps,
- family-wise tested variant count is missing or incomplete,
- test/holdout was repeatedly inspected during tuning,
- holdout was reused after adverse outcomes,
- baseline comparisons fail on net risk-adjusted terms,
- edge collapses under conservative cost/slippage/fill stress,
- performance is unstable across nearby parameter neighborhoods,
- evidence relies on optimistic-only assumptions.

## Promotion Rules (Paper-Only Candidate)
A strategy may be promoted to `PAPER_ONLY_CANDIDATE` only when all are true:
1. Pre-declared experiment family and search space were followed.
2. Family-wise tested variant count is fully reported.
3. Selection occurred on validation only.
4. Test and locked holdout both confirm acceptable net risk-adjusted behavior.
5. Candidate outperforms pre-declared baselines with acceptable drawdown profile.
6. Stress tests for cost/slippage/fill assumptions do not invalidate edge.
7. Evidence is reproducible and auditable.

Required evidence package before paper-only promotion:
- complete family report with all minimum fields,
- test and holdout results with conservative interpretation,
- baseline comparison summary,
- robustness summary across nearby parameters,
- explicit statement that no live trading authorization is implied.

## Holdout Inspection Policy
Holdout is a one-way gate.
- Do not repeatedly inspect holdout after each tweak.
- Do not retune against holdout outcomes.
- If holdout fails, open a new experiment family with newly pre-declared search space and fresh decision log.

Repeated holdout peeking is a protocol violation and invalidates promotion claims.

## Operational Checklist (Before Claiming Results)
- Is the search space pre-declared and timestamped?
- Are train/validation/test/holdout boundaries locked?
- Is variant count complete and family-wise?
- Were baselines evaluated on identical net assumptions?
- Was selection done without touching holdout?
- Are rejection/promotions decisions consistent with this protocol?

## Safety and Scope Reminder
This protocol governs research interpretation only. It does not authorize live trading, real Binance order execution, API key handling, or exchange order/account endpoint usage.
