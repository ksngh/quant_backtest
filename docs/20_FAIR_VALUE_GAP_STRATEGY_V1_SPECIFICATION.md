# Fair Value Gap Strategy V1 Specification

## 1) Strategy Identity and Research Lifecycle State
- **Strategy candidate name:** `FAIR_VALUE_GAP_STRATEGY_V1`
- **Pattern family:** `FAIR_VALUE_GAP`
- **Current lifecycle state:** `MECHANICAL_DEFINITION`
- **Approval status:** **Not approved for live trading** and not approved for real-order execution.
- **Research boundary:** This specification supports event-study and backtest research only.

## 2) Hypothesis
On `1m` BTC candle data, newly confirmed Fair Value Gap (FVG) events represent short-horizon imbalance zones where price may mean-revert into the gap (entry area) and then continue directionally away from the opposing boundary often enough to produce positive expectancy after realistic fills and costs.

## 3) Economic Rationale
- Displacement candles can leave transient liquidity voids between non-overlapping candle ranges.
- Later price revisits into the gap can reflect re-pricing and liquidity rebalancing.
- If the original displacement reflects directional urgency, defended zones may provide favorable risk-defined continuation opportunities.

## 4) Behavioral Finance Rationale
- Fast displacement can create fear-of-missing-out momentum participation and delayed pullback entries.
- Mean-reversion into the gap can trigger both trapped-chaser exits and value-seeking re-entries.
- The retest + reaction sequence can encode repeatable crowd behavior when filtered to quality events.

## 5) Market Microstructure Interpretation
- FVG zones are treated as candles where matching was thin relative to adjacent price ranges.
- Midpoint retests represent potential liquidity re-engagement.
- Failure to hold midpoint reaction within a bounded time window is treated as edge decay and soft invalidation risk.

## 6) Eligible Timeframe and Instrument Scope
- **Initial research timeframe:** `1m`.
- **Symbol scope:** BTC spot-like candle streams using the repository standard candle schema.
- **Future extension note:** Higher-timeframe context filters may be added in later strategy versions, not in V1.

## 7) Data Requirements
Required fields per candle (ascending `timestamp`):
- `timestamp`, `open`, `high`, `low`, `close`, `volume`

Research dataset requirements:
- Completed candles only.
- Deterministic dataset snapshot/versioning for reproducibility.
- No look-ahead in pattern extraction, entry simulation, or label generation.

## 8) Pattern Detection Rule (Frozen V1)
Use existing deterministic FVG detection contract:
- Detector: `quant_bitcoin.patterns.fair_value_gap.detect_fair_value_gaps(...)`
- Configuration baseline: `FairValueGapConfig()` defaults unless pre-declared experiment variants.
- Directional support: **both bullish and bearish** events are supported by current implementation.
- Event eligibility for strategy logic: event must be newly confirmed on current candle in rolling-prefix evaluation (`end_index == current_index`).

## 9) Entry Rule (Frozen V1)
Implemented baseline entry mode:
- `MARKET_ON_CONFIRMATION_CLOSE` remains the default for backward-compatible
  canonical strategy-engine runs. Economically, this is a momentum-continuation
  interpretation after the confirmation candle.

Explicit research variants:
- `MARKET_ON_NEXT_OPEN`
- `LIMIT_AT_ENTRY_REFERENCE`
- `LIMIT_AT_PATTERN_MIDPOINT`
- `LIMIT_AT_PATTERN_BOUNDARY`
- `LIMIT_AT_CUSTOM_PRICE`

Retest/limit variants model imbalance rebalancing into the FVG reference,
midpoint, boundary, or declared custom price. They can emit `ENTRY_NOT_FILLED`
SKIP diagnostics when the selected level is not touched before expiry.

Implementation alignment:
- Entry simulation contract: `quant_bitcoin.patterns.entry_simulation`.
- CLI controls: `--fvg-entry-mode`, `--fvg-entry-max-wait-bars`,
  `--fvg-entry-expire-status`, optional `--fvg-entry-custom-price`, and
  `--compare-fvg-entry-modes`.
- JSON output records selected entry mode, fill source, bars waited, fill rate,
  missed-trade count, and comparative mode diagnostics when requested.

## 10) No-Fill Rule
- Default max wait: **5 bars** after confirmation.
- If limit not touched within `max_wait_bars`, entry status becomes `NOT_FILLED` (or explicit configured cancel state).
- No-fill events are retained for diagnostics but do not create trades.

## 11) Stop Rule
- Stop construction uses existing FVG risk/exit planner:
  - module: `quant_bitcoin.patterns.fair_value_gap_risk_exit`
  - config: `FairValueGapRiskExitConfig(atr_buffer_multiplier=0.2)` default
- Structural stop source:
  - bullish: FVG lower boundary (`zone_low`) + shared ATR buffering contract
  - bearish: FVG upper boundary (`zone_high`) + shared ATR buffering contract

## 12) Target Rule
- Use shared risk/exit R-multiple targets from FVG planner:
  - `r_multiples = (1.0, 2.0, 3.0)`
- Structural targets may be provided, but baseline research comparison should include standardized 1R/2R/3R reporting.

## 13) Partial Exit Rule
- Default partial exit allocation:
  - 1R: `0.33`
  - 2R: `0.33`
  - 3R: `0.34`
- This matches current FVG risk/exit defaults and is frozen for V1 baseline.

## 14) Break-Even Rule
- Break-even behavior follows shared risk/exit defaults via `BreakEvenSettings` in FVG risk/exit config.
- V1 baseline requires explicit recording of whether and when break-even activation occurs (commonly after first target milestone such as 1R under shared contract usage).

## 15) Soft Invalidation Rule
- Use midpoint reaction-failure concept from FVG planner metadata:
  - reaction window default: `5` bars post-entry
  - bullish favorable reaction condition: close above midpoint
  - bearish favorable reaction condition: close below midpoint
- If reaction condition fails by deadline, mark as soft invalidation candidate per exit simulator policy.

## 16) Intrabar Ambiguity Policy
- Promotion-grade decisions must use **conservative intrabar sequencing policy**.
- Optimistic/stress variants can be reported as sensitivity bounds only.
- Any promotion claim that depends on optimistic-only sequencing is invalid.

## 17) Transaction Cost Assumptions
- Gross-only results are insufficient for promotion.
- Net evaluation must use the repository transaction-cost contract:
  - `quant_bitcoin.backtesting.costs.TransactionCostConfig`
- Required net assumptions include:
  - maker/taker fee basis points,
  - spread basis points,
  - slippage basis points,
  - fill model assumptions.

## 18) Excluded Market Conditions (V1)
Exclude or separately flag windows where at least one applies:
- severely degraded data quality (schema/order/interval violations),
- exchange outage-like candle discontinuities,
- extreme volatility regimes outside pre-declared research bounds,
- conditions requiring unavailable live microstructure inputs not modeled by current backtest contracts.

## 19) Required Event Study Evidence
Before strategy promotion beyond definition:
- Event extraction must satisfy no-look-ahead constraints.
- Event frequency, clustering, and direction balance must be reported.
- Forward-label evidence (fixed horizons + MFE/MAE + R-hit ordering) must be generated on extracted events.
- Evidence must be reproducible with fixed dataset snapshots.

## 20) Required Net Backtest Evidence
Promotion requires cost-adjusted, fill-aware backtests that include:
- explicit entry no-fill accounting,
- explicit intrabar sequencing mode,
- explicit transaction-cost configuration,
- drawdown and tail-risk commentary,
- comparison against pre-declared baselines.

## 21) Required Out-of-Sample Evidence
- Walk-forward validation is mandatory.
- Pre-declared train/validation/test/holdout splits must be respected.
- Final status cannot advance without forward-only aggregate stability across windows.

## 22) Multiple-Testing Control Requirement
- Parameter ranges and trial counts must be pre-declared.
- All attempted variants must be logged (not winners only).
- Robustness across nearby parameter neighborhoods is required.
- Post-hoc retuning after weak OOS results must be treated as a new research cycle.

## 23) Strategy Promotion Criteria (V1 Candidate)
A move toward `PAPER_ONLY_CANDIDATE` is allowed only if all are true:
1. Deterministic no-look-ahead mechanics validated.
2. Event-study evidence supports non-random directional behavior.
3. Net (cost/slippage/fill-aware) backtests beat pre-declared baselines on risk-adjusted terms.
4. Conservative intrabar mode remains acceptable.
5. Walk-forward OOS performance is stable and not single-window concentrated.
6. Multiple-testing controls and robustness checks are documented.

## 24) Strategy Rejection Criteria
Reject (`REJECTED`) when one or more apply:
- edge vanishes after realistic costs/fills,
- repeated OOS failures,
- profitability depends on narrow unstable tuning,
- baseline underperformance on risk-adjusted net basis,
- reliance on ambiguous optimistic intrabar assumptions,
- evidence of leakage/look-ahead.

## 25) Implementation/Research Notes
- This V1 document freezes a baseline candidate definition only.
- It does not authorize live trading or exchange order endpoints.
- Future versions (for example V2) may add higher-timeframe context, but must be separately specified and versioned before parameter search.
