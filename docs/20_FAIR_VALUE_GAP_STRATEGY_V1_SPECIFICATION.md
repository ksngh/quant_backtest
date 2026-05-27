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
- **Baseline boundary:** V1 defaults remain single-timeframe and backward compatible.
- **V2 research extension:** Opt-in FVG retest v2 metadata may use higher-timeframe context, but only from completed higher-timeframe candles aligned to the current 1m row. Incomplete higher-timeframe candles must not be used for trend scoring.

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
- Multi-timeframe EMA trend context is default-off. When explicitly enabled,
  FVG events may include `mtf_trend_score`, `mtf_trend_direction`,
  `mtf_trend_aligned`, and `mtf_trend_metadata`; `require_trend_alignment`
  can hard-filter misaligned or unavailable trend context. These fields are
  diagnostic research metadata by default and are not live-trading signals.
- Fibonacci retracement confluence is also default-off. When explicitly
  enabled, FVG events may include `fib_confluence_pass`,
  `fib_retracement_level`, and `fib_metadata`; `require_fibonacci_confluence`
  can hard-filter non-confluent zones. The initial anchor method is
  `DISPLACEMENT_CANDLE_RANGE`, which uses only the displacement candle already
  visible at FVG confirmation time. This is a deterministic filter/diagnostic
  feature, not an anchor optimizer or profitability claim.

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

The opt-in `FAIR_VALUE_GAP_RETEST` policy preset defaults to
`LIMIT_AT_PATTERN_MIDPOINT`, `max_wait_bars=5`, and `entry_trigger=TOUCH`.
Reaction variants can require `TOUCH_AND_REACTION_CLOSE` or
`TOUCH_AND_RECLAIM_MIDPOINT`; metadata records trigger type, touch index/time,
reaction index/time, fill index/time, bars waited, and no-fill reason. Baseline
`FAIR_VALUE_GAP` market-confirmation behavior remains unchanged unless a retest
mode/trigger is explicitly selected.

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
- Stop mode default is `FVG_BOUNDARY_ATR_BUFFER` for backward compatibility.
  Optional research variants `SWING_PIVOT` and `WIDER_OF_FVG_AND_SWING` require
  visible, precomputed swing stop input; missing swing stops produce invalid
  risk plans rather than silent fallback. Stop metadata schema `fvg_stop_mode_v1`
  records selected stop source, boundary stop, swing stop, selected stop, and
  direction.

## 12) Target Rule
- Use shared risk/exit R-multiple targets from FVG planner:
  - `r_multiples = (1.0, 2.0, 3.0)`
- Structural targets may be provided, but baseline research comparison should include standardized 1R/2R/3R reporting.
- Optional FVG liquidity targets can supply structural target candidates from
  prior confirmed pivots visible at event confirmation time. Bullish setups use
  pivot highs above entry; bearish setups use pivot lows below entry. Metadata
  schema `fvg_liquidity_targets_v1` records source, target price, estimated R,
  filtering reason, and the caveat that this is OHLCV pivot-derived structure,
  not order-book liquidity.

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
  - configured action: `SOFT_INVALIDATION_EXIT`
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
- FVG retest v2 is an opt-in research layer over the baseline, not a replacement for default `FAIR_VALUE_GAP` behavior.
- V2 trend score, Fibonacci confluence, liquidity target, reaction-entry, and stop-mode features remain offline research diagnostics/filters only. They are not live-trading approval, order-book liquidity evidence, or automatic parameter-promotion rules.
- V2 parameter search must follow `docs/29_FVG_RETEST_V2_RESEARCH_PROTOCOL.md`, keep all losing/no-fill variants, and respect locked holdout boundaries before any future paper-only decision task.
