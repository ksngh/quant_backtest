# Frontend Status

## Current Purpose
Frontend dashboard integration with read-only backtest API verified in Task 078.

## Active Task
No active frontend task. Task 259 completed trade-bounded FVG v2 channel overlay clipping.

## Stack Decision Boundary
- Selected stack: Next.js App Router + React + TypeScript.
- Do not combine Next.js and Vite in the same app.
- Frontend uses backend API only via `NEXT_PUBLIC_BACKTEST_API_BASE_URL`.
- Backtest cash display distinguishes cash balance from free cash when account-state metadata is available.
- Dashboard implementation should show semantic position signals first, keep raw execution side as audit context, and render parameters/metadata as curated UI rather than raw JSON by default.
- The dashboard now includes range-inspectable charts, compact paged trade review, curated parameter/runtime panels, and strategy indicator/economic explanation sections.
- The dashboard now includes read-only Performance Diagnostics cards for saved-run risk-adjusted returns, trade lifecycle quality, exposure, turnover, and cost assumptions, with safe legacy fallbacks.
- The dashboard now includes a read-only Run Diagnosis panel for deterministic poor-performance forensic flags exposed by the backend diagnostics payload.
- The dashboard now includes a read-only Entry/Exit Timing panel for MFE/MAE, timing flags, and completed trade lifecycle path metrics exposed by diagnostics metadata.
- The Strategy Logic panel now displays saved pattern execution policy metadata, selected entry mode, rationale, and research hypothesis when available.
- The dashboard now includes a read-only Risk Management panel showing risk design metrics, realized exit-reason distribution, dominance ratios, and partial-exit PnL contribution.
- The Strategy Explanation panel now uses actual selected-run metadata and diagnostics for strategy overview, economic hypothesis, indicators, risk design, realized risk behavior, entry timing, exit timing, limitations, and bad-performance clues, with explicit fallback text for legacy rows.
- The dashboard now includes a read-only Run Conclusion panel that maps saved diagnostics into top likely failure reasons, confidence, evidence rows, and recommended next analyses without exposing execution controls.
- The dashboard now includes a read-only Research Report preview for saved-run `backtest_research_report_v1` JSON/markdown artifacts.
- The dashboard now includes a read-only Execution Assumptions panel for pattern entry fill, fill-adjusted risk, costs, intrabar ambiguity, zero-cost warnings, and short-simulation limitations.
- The dashboard now includes a read-only Pattern Geometry panel for saved pattern geometry fields, observed versus placeholder score components, and candidate-overfit diagnostics.
- The dashboard now includes a read-only FVG Retest V2 Diagnostics panel for saved trend-score, Fibonacci, liquidity-target, reaction-entry, and stop-mode metadata with legacy fallback.
- The Research Report preview now highlights saved `pattern_research_note_v1` sections for hypothesis, detector conditions, entry/risk/cost/score assumptions, no-lookahead status, regime dependence, limitations, and recommended analyses.
- The dashboard now places charts above lower diagnostics, supports drag-select zoom plus pan/zoom/reset controls, groups lower diagnostics behind click-to-open sections, filters the run list from the left sidebar, and exposes detailed fee/spread/slippage fields through per-trade expandable rows.
- The price chart can draw saved FVG v2 parallel-channel lower/upper lines, low anchors, upper touch, and entry/exit markers from API metadata while preserving drag zoom, pan, zoom in/out, and reset behavior.
- FVG v2 channel overlays are now rendered as multiple channel-specific bounded segments rather than a single first-channel overlay projected across the full viewport.
- Uptrend FVG v2 channel overlays label saved construction points as `L1`, `H1`, and `L2` from channel geometry metadata.
- FVG v2 channel overlay lines now end at the saved entry/retest point when present rather than extending to the later exit boundary.
