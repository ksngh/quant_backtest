import type { BacktestRunDetailResponse, BacktestTrade } from "../types/api";
import { asRecord, firstRecord, percent, scalar, type AnyRecord } from "./valueUtils";

export type ExplanationRow = {
  label: string;
  value: string;
};

export type StrategyExplanationModel = {
  title: string;
  subtitle: string;
  fallback: boolean;
  overview: ExplanationRow[];
  economicHypothesis: string[];
  indicatorsUsed: string[];
  riskManagementDesign: ExplanationRow[];
  actualRiskBehavior: ExplanationRow[];
  entryTiming: ExplanationRow[];
  exitTiming: ExplanationRow[];
  knownLimitations: string[];
  badPerformanceClues: string[];
};

type PatternKnowledge = {
  indicators: string[];
  economicMeaning: string[];
};

const PATTERN_KNOWLEDGE: Record<string, PatternKnowledge> = {
  FAIR_VALUE_GAP: {
    indicators: ["Displacement candle", "Volume ratio", "Three-candle imbalance", "ATR risk buffer"],
    economicMeaning: [
      "Targets price gaps created by aggressive directional order flow.",
      "Tests whether unfilled imbalance zones behave as continuation or retest levels.",
    ],
  },
  ORDER_BLOCK: {
    indicators: ["Source candle zone", "Displacement confirmation", "ATR risk buffer", "Volume context"],
    economicMeaning: [
      "Models a price zone where a prior opposing candle preceded a strong directional move.",
      "Tests whether retests or continuation after that zone reveal defended inventory.",
    ],
  },
  TRENDLINE_BREAK: {
    indicators: ["Pivot highs/lows", "Trendline slope", "ATR breakout buffer", "Breakout close"],
    economicMeaning: ["Tests whether a confirmed trendline break unlocks stop-driven momentum continuation."],
  },
  CUP_AND_HANDLE: {
    indicators: ["Swing pivots", "Cup depth", "Handle pullback", "Neckline breakout"],
    economicMeaning: ["Tests continuation after accumulation, pullback, and neckline recovery."],
  },
  DIAMOND: {
    indicators: ["Expansion pivots", "Contraction pivots", "Boundary break", "Measured move height"],
    economicMeaning: ["Tests whether volatility compression after expansion resolves directionally."],
  },
  ADAM_AND_EVE: {
    indicators: ["Spike low", "Rounded retest", "Neckline breakout", "Measured move depth"],
    economicMeaning: ["Tests reversal confirmation after capitulation and slower accumulation retest."],
  },
};

export function buildStrategyExplanationModel(detail: BacktestRunDetailResponse): StrategyExplanationModel {
  const summaryMetadata = asRecord(detail.summary.metadata);
  const diagnosticsSummary = asRecord(detail.diagnostics?.summary);
  const explanation = asRecord(detail.strategy_config.metadata?.explanation);
  const policy = firstRecord(
    detail.strategy_config.parameters?.pattern_execution_policy,
    summaryMetadata?.pattern_execution_policy,
    diagnosticsSummary?.pattern_execution_policy,
  );
  const fvgEntry = firstRecord(summaryMetadata?.fvg_entry_mode, diagnosticsSummary?.fvg_entry_mode);
  const riskAudit = firstRecord(summaryMetadata?.risk_exit_audit, diagnosticsSummary?.risk_exit_audit);
  const attribution = firstRecord(summaryMetadata?.trade_attribution, diagnosticsSummary?.trade_attribution);
  const performanceDiagnosis = firstRecord(summaryMetadata?.performance_diagnostics, diagnosticsSummary?.performance_diagnostics);
  const positionSizing = asRecord(summaryMetadata?.position_sizing);
  const costProfile = asRecord(summaryMetadata?.cost_profile);
  const costSummary = asRecord(summaryMetadata?.cost_summary);
  const firstEntry = firstEntryTrade(detail.trades);
  const firstExit = firstExitTrade(detail.trades);
  const entryMetadata = asRecord(firstEntry?.metadata);
  const exitMetadata = asRecord(firstExit?.metadata);
  const pattern = patternKey(detail);
  const knowledge = PATTERN_KNOWLEDGE[pattern];
  const fallback = !explanation;
  const algorithmName = text(explanation?.algorithm_name) ?? detail.strategy_config.name;
  const algorithmKey = text(explanation?.algorithm_key) ?? pattern;

  return {
    title: "Strategy Explanation",
    subtitle: `${algorithmName} / ${algorithmKey}`,
    fallback,
    overview: compactRows([
      row("Strategy", detail.strategy_config.name),
      row("Version", detail.strategy_config.version),
      row("Pattern", pattern),
      row("Market", `${detail.run.market.symbol} ${detail.run.market.interval}`),
      row("Run Source", detail.run.market.source),
      row("Metadata Source", fallback ? "Fallback/static explanation plus run metadata" : "Persisted strategy explanation metadata"),
    ]),
    economicHypothesis: list(explanation?.design_rationale, policy?.economic_rationale, policy?.research_hypothesis)
      .concat(knowledge?.economicMeaning ?? ["Economic hypothesis metadata is unavailable for this strategy."]),
    indicatorsUsed: list(explanation?.detection_rules).concat(knowledge?.indicators ?? ["Indicator metadata is unavailable for this strategy."]),
    riskManagementDesign: compactRows([
      row("Sizing Mode", text(positionSizing?.mode) ?? "Unavailable"),
      row("Sizing Value", scalar(positionSizing?.value)),
      row("Risk Per Unit", scalar(entryMetadata?.risk_per_unit)),
      row("Entry Reference", scalar(entryMetadata?.entry_reference)),
      row("Original Entry Reference", scalar(entryMetadata?.original_entry_reference)),
      row("Fill-Adjusted Risk", scalar(entryMetadata?.fill_adjusted_risk_per_unit)),
      row("Stop Design", firstText(explanation?.stop_loss_rules, "Unavailable")),
      row("Target Design", firstText(explanation?.take_profit_rules, "Unavailable")),
      row("Partial Exit", firstText(explanation?.partial_exit_rules, "Unavailable")),
      row("Cost Profile", text(costProfile?.profile_key) ?? "Unavailable"),
      row("Zero Cost Assumption", scalar(costSummary?.zero_transaction_cost_assumption)),
    ]),
    actualRiskBehavior: actualRiskRows(riskAudit, attribution),
    entryTiming: compactRows([
      row("Selected Entry Mode", text(policy?.selected_entry_mode) ?? text(fvgEntry?.selected_entry_mode) ?? text(entryMetadata?.entry_mode) ?? "Unavailable"),
      row("Fill Price Source", text(entryMetadata?.fill_price_source) ?? "Unavailable"),
      row("Fill Assumption", text(entryMetadata?.fill_assumption) ?? "Unavailable"),
      row("Confirmation Close", scalar(entryMetadata?.confirmation_close)),
      row("Entry Status", text(entryMetadata?.entry_status) ?? "FILLED when an entry execution exists"),
      row("Bars Waited", scalar(entryMetadata?.bars_waited)),
      row("Policy Rationale", text(policy?.economic_rationale) ?? "Unavailable"),
    ]),
    exitTiming: compactRows([
      row("Realized Exit Reason", text(exitMetadata?.exit_reason) ?? text(firstExit?.signal) ?? "No completed exit in selected run"),
      row("Target Name", text(exitMetadata?.target_name)),
      row("Stop Price", scalar(exitMetadata?.stop_price)),
      row("Exit Price", scalar(exitMetadata?.exit_price) ?? scalar(firstExit?.price)),
      row("Realized R", scalar(exitMetadata?.realized_r_multiple)),
      row("Soft Invalidation", firstText(explanation?.soft_invalidation_rules, "Unavailable")),
      row("Time Stop", firstText(explanation?.time_stop_rules, "Unavailable")),
    ]),
    knownLimitations: list(explanation?.known_limitations).concat([
      "Dashboard is read-only and does not imply live trading readiness.",
      fallback ? "Some explanation text is static fallback because persisted strategy explanation metadata is missing." : "",
    ]).filter(Boolean),
    badPerformanceClues: diagnosisClues(performanceDiagnosis, riskAudit),
  };
}

function actualRiskRows(riskAudit: AnyRecord | null, attribution: AnyRecord | null): ExplanationRow[] {
  const dominance = asRecord(riskAudit?.dominance);
  const targetQuality = asRecord(riskAudit?.target_quality);
  const partialExit = asRecord(riskAudit?.partial_exit);
  const tradeMetrics = asRecord(attribution?.trade_metrics);
  return compactRows([
    row("Completed Exits", scalar(riskAudit?.completed_exit_count)),
    row("Hit Ratio", percent(tradeMetrics?.hit_ratio)),
    row("Expectancy", scalar(tradeMetrics?.expectancy)),
    row("Average R", scalar(tradeMetrics?.average_r)),
    row("Stop Dominance", percent(dominance?.stop_loss_dominance_ratio)),
    row("Time Stop Dominance", percent(dominance?.time_stop_dominance_ratio)),
    row("Soft Invalidation Dominance", percent(dominance?.soft_invalidation_dominance_ratio)),
    row("First Target Hit Rate", percent(targetQuality?.first_target_hit_rate)),
    row("Partial Exit PnL", scalar(partialExit?.partial_exit_net_pnl)),
  ]);
}

function diagnosisClues(performanceDiagnosis: AnyRecord | null, riskAudit: AnyRecord | null): string[] {
  const flags = [
    ...flagLabels(performanceDiagnosis?.flags),
    ...flagLabels(riskAudit?.flags),
  ];
  const warnings = list(performanceDiagnosis?.warnings, riskAudit?.warnings);
  return [...flags, ...warnings].slice(0, 8);
}

function flagLabels(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map(asRecord).filter(Boolean).map((flag) => `${String(flag?.code ?? "FLAG")}: ${String(flag?.message ?? "")}`)
    : [];
}

function patternKey(detail: BacktestRunDetailResponse): string {
  const params = detail.strategy_config.parameters;
  const value =
    text(params.pattern)
    ?? text(params.pattern_key)
    ?? (text(params.strategy) !== "pattern" ? text(params.strategy) : null)
    ?? detail.strategy_config.key
    ?? detail.strategy_config.name;
  return String(value).toUpperCase();
}

function firstEntryTrade(trades: BacktestTrade[]): BacktestTrade | null {
  return trades.find((trade) => String(trade.position_signal ?? trade.signal).includes("ENTRY")) ?? null;
}

function firstExitTrade(trades: BacktestTrade[]): BacktestTrade | null {
  return trades.find((trade) => String(trade.position_signal ?? trade.signal).includes("EXIT")) ?? null;
}

function list(...values: unknown[]): string[] {
  return values.flatMap((value) => {
    if (Array.isArray(value)) return value.filter(Boolean).map(String);
    if (typeof value === "string" && value) return [value];
    return [];
  });
}

function row(label: string, value: string | null | undefined): ExplanationRow | null {
  return value ? { label, value } : null;
}

function compactRows(rows: Array<ExplanationRow | null>): ExplanationRow[] {
  return rows.filter((item): item is ExplanationRow => Boolean(item));
}

function firstText(value: unknown, fallback: string): string {
  const values = list(value);
  return values[0] ?? fallback;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}
