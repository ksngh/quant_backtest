# Project History Archive: Task Window 151-200

Archived from root `PROJECT_HISTORY.md` during Task 225 final pattern
research batch reconciliation so root ledgers can stay focused on the latest
active window.

## Archived Completion Notes
- 2026-05-24: Completed Task 151 `ENTRY_FILL_EQUITY_AND_CONSERVATIVE_SIZING_SEMANTICS`; corrected entry-candle equity valuation and conservative sizing semantics.
- 2026-05-24: Completed Task 152 `PATTERN_SIZING_PROPAGATION_CONTRACT`; made pattern lifecycle entries engine-sized by default while preserving explicit overrides.
- 2026-05-24: Completed Task 153 `PARTIAL_EXIT_QUANTITY_RATIO_CONTRACT`; added position-ratio quantity semantics for partial exits.
- 2026-05-24: Completed Task 154 `ENTRY_FILL_PRICE_MODEL_SEPARATION`; separated market confirmation fills from reference/limit fills.
- 2026-05-24: Completed Task 155 `RISK_PLAN_INVALID_ACTION_SAFETY`; invalid or skipped risk plans now emit non-executable SKIP diagnostics only.
- 2026-05-24: Completed Task 156 `CANONICAL_SOFT_INVALIDATION_INTEGRATION`; wired supported close-based soft invalidation into canonical action expansion.
- 2026-05-24: Completed Task 157 `INTRABAR_SEQUENCING_POLICY_INTEGRATION`; added reusable intrabar sequencing policy metadata for stop/target ambiguity.
- 2026-05-24: Completed Task 158 `CANDLE_DATA_INTEGRITY_AND_GAP_VALIDATION`; added candle schema and continuity validation.
- 2026-05-24: Completed Task 159 `NO_LOOKAHEAD_PATTERN_DETECTION_CONTRACT`; hardened current-index pattern detector helpers and no-lookahead tests.
- 2026-05-24: Completed Task 160 `TRANSACTION_COST_AND_SLIPPAGE_REALISM`; added simulated transaction-cost slippage and cost summary metadata.
- 2026-05-24: Completed Task 161 `RISK_PER_TRADE_SIZING_AND_GUARDRAILS`; added equity-risk-fraction sizing and backtest-only guardrails.
- 2026-05-24: Completed Task 162 `SHORT_ECONOMICS_MARGIN_FUNDING_LIMITATIONS`; documented and surfaced short simulation limitations.
- 2026-05-24: Completed Task 163 `PERFORMANCE_ATTRIBUTION_METRICS_CUBE`; added lifecycle-based performance attribution and exposure metrics.
- 2026-05-24: Completed Task 164 `MARKET_REGIME_AND_INDICATOR_EXPANSION`; added market-regime indicator tags and optional engine metadata.
- 2026-05-24: Completed Task 165 `PATTERN_SCORE_FEATURE_AUDIT_AND_CALIBRATION`; added heuristic score metadata and calibration caveats.
- 2026-05-24: Completed Task 166 `WALK_FORWARD_OOS_MONTE_CARLO_VALIDATION`; added deterministic WFO and bootstrap validation utilities.
- 2026-05-24: Completed Task 167 `RSI_AND_MEAN_REVERSION_SIGNAL_CONTRACT_REVIEW`; added optional RSI Wilder/crossing modes while preserving defaults.
- 2026-05-24: Completed Task 168 `RESEARCH_DIAGNOSTICS_PERSISTENCE_AND_API_REPORTING`; persisted and exposed read-only research diagnostics.
- 2026-05-24: Completed Task 169 `BACKTEST_REPRODUCIBILITY_RUN_METADATA`; added reproducibility metadata and secret redaction.
- 2026-05-24: Completed Task 170 `EXECUTION_READINESS_SAFETY_BOUNDARY_AUDIT`; documented live-trading blockers and required guard tasks.
- 2026-05-24: Completed Task 171 `REFACTOR_DOCUMENTATION_LEDGER_RECONCILIATION`; archived Tasks 101-150 and reconciled root ledgers.
- 2026-05-24: Completed Task 172 `FVG_ACTUAL_FILL_RISK_PLAN_ALIGNMENT`; rebuilt FVG risk/targets from actual fill price.
- 2026-05-24: Completed Task 173 `BACKTEST_METRIC_FRONTEND_REPORTING_AND_INTERPRETATION`; added read-only performance diagnostics dashboard panel.
- 2026-05-24: Completed Task 174 `BACKTEST_POOR_PERFORMANCE_FORENSIC_DIAGNOSTICS`; added deterministic poor-performance classification.
- 2026-05-24: Completed Task 175 `ENTRY_EXIT_TIMING_FORENSICS_AND_MFE_MAE_METRICS`; added trade timing, MFE, and MAE diagnostics.
- 2026-05-24: Completed Task 176 `FVG_ENTRY_MODE_RETEST_VERSUS_MOMENTUM_EXPERIMENTS`; added FVG entry-mode controls and comparison diagnostics.
- 2026-05-24: Completed Task 177 `PATTERN_SPECIFIC_ENTRY_EXIT_POLICY_MATRIX`; added pattern execution policy metadata and frontend display.
- 2026-05-24: Completed Task 178 `RISK_REWARD_TARGET_STOP_VALIDITY_AND_DOMINANCE_AUDIT`; added risk/exit audit diagnostics.
- 2026-05-24: Completed Task 179 `CANONICAL_REGIME_GUARDRAIL_AND_CONTINUITY_CLI_WIRING`; wired continuity, regime, and guardrail CLI options.
- 2026-05-24: Completed Task 180 `COST_PROFILE_PRESETS_AND_SENSITIVITY_REPORTING`; added named cost profiles and sensitivity reporting.
- 2026-05-24: Completed Task 181 `PATTERN_SCORE_CALIBRATION_ABLATION_AND_THRESHOLDS`; added score calibration, ablation, and threshold diagnostics.
- 2026-05-24: Completed Task 182 `PATTERN_WALK_FORWARD_OOS_VALIDATION_RUNNER`; extended WFO validation to pattern strategies.
- 2026-05-24: Completed Task 183 `FRONTEND_STRATEGY_RISK_ENTRY_EXIT_DEEP_EXPLANATION`; upgraded read-only frontend strategy/risk explanation panels.
- 2026-05-24: Completed Task 184 `BAD_RUN_EXPLAINER_AND_RECOMMENDED_NEXT_ANALYSIS_FRONTEND`; added deterministic run conclusion and next-analysis hints.
- 2026-05-24: Completed Task 185 `LIQUIDITY_SPREAD_AND_SESSION_FILTER_RESEARCH_FEATURES`; added OHLCV tradability proxies and attribution.
- 2026-05-24: Completed Task 186 `SAVED_RUN_RESEARCH_REPORT_ARTIFACT`; added saved-run research report JSON/markdown artifacts.
- 2026-05-24: Completed Task 187 `REFACTOR_DOCUMENTATION_LEDGER_RECONCILIATION_AFTER_BACKTEST_ANALYTICS`; reconciled docs and ledgers after Tasks 173-186.
- 2026-05-24: Completed Task 188 `PATTERN_EXECUTION_PATH_UNIFICATION`; unified canonical pattern execution metadata around fill-aware actions.
- 2026-05-24: Completed Task 189 `PATTERN_REQUESTED_PRICE_AND_ENTRY_POLICY_CONTRACT`; added explicit requested-price and entry-policy metadata.
- 2026-05-24: Completed Task 190 `ENTRY_EXIT_INTRABAR_COMBINED_SEQUENCING`; added policy-driven combined entry/exit intrabar sequencing.
- 2026-05-24: Completed Task 191 `FVG_AND_ORDER_BLOCK_ENTRY_MODE_POLICY_EXPERIMENTS`; added explicit FVG/Order Block chase and retest entry policies.
- 2026-05-24: Completed Task 192 `FVG_LIFECYCLE_AND_SOFT_INVALIDATION_INTEGRATION`; integrated FVG post-entry reaction failure soft invalidation.
- 2026-05-24: Completed Task 193 `ORDER_BLOCK_RETEST_MITIGATION_AND_CLUSTER_DETECTOR`; added Order Block retest/mitigation and cluster diagnostics.
- 2026-05-24: Completed Task 194 `TRENDLINE_THREE_TOUCH_AND_RETEST_FILTERS`; added stricter trendline validation and retest filters.
- 2026-05-24: Completed Task 195 `CUP_AND_HANDLE_LOCAL_TREND_AND_BREAKOUT_RETEST`; added local trend and neckline retest behavior.
- 2026-05-24: Completed Task 196 `DIAMOND_PIVOT_SPLIT_AND_BOUNDARY_VALIDATION`; validated Diamond pivot split and contraction boundaries.
- 2026-05-24: Completed Task 197 `ADAM_AND_EVE_STOP_MODE_AND_LOCAL_DOWNTREND`; aligned Adam/Eve stop mode and local downtrend metadata.
- 2026-05-24: Completed Task 198 `PLACEHOLDER_SCORE_COMPONENT_REMOVAL`; removed placeholder score components from executable scores.
- 2026-05-24: Completed Task 199 `PATTERN_SCORE_OOS_LIFT_AND_COMPONENT_ABLATION`; added OOS lift and component ablation diagnostics.
- 2026-05-24: Completed Task 200 `SUPPORT_RESISTANCE_SWING_STRUCTURE_SCORE_FEATURES`; added support/resistance and swing-structure score features.
