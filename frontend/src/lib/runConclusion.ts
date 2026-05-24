import type { BacktestRunDetailResponse } from "../types/api";
import { asRecord, firstRecord, numberValue, percent, scalar, type AnyRecord } from "./valueUtils";

export type RunConclusionReason = {
  category: string;
  title: string;
  severity: "critical" | "warning" | "info" | "neutral";
  evidence: string;
  recommendedNextAnalysis: string;
};

export type RunConclusionModel = {
  status: "not_enough_data" | "weak_run" | "healthy_or_inconclusive";
  confidence: "Not enough data" | "Low" | "Medium" | "High";
  completedTradeCount: number | null;
  headline: string;
  reasons: RunConclusionReason[];
  evidenceRows: { label: string; value: string }[];
  rawEvidence: Record<string, unknown>;
};

export function buildRunConclusionModel(detail: BacktestRunDetailResponse): RunConclusionModel {
  const summaryMetadata = asRecord(detail.summary.metadata);
  const diagnosticsSummary = asRecord(detail.diagnostics?.summary);
  const performanceDiagnostics = firstRecord(summaryMetadata?.performance_diagnostics, diagnosticsSummary?.performance_diagnostics);
  const timingDiagnostics = firstRecord(summaryMetadata?.timing_diagnostics, diagnosticsSummary?.timing_diagnostics);
  const riskAudit = firstRecord(summaryMetadata?.risk_exit_audit, diagnosticsSummary?.risk_exit_audit);
  const scoreCalibration = firstRecord(summaryMetadata?.score_calibration, diagnosticsSummary?.score_calibration);
  const attribution = firstRecord(summaryMetadata?.trade_attribution, diagnosticsSummary?.trade_attribution);
  const costSummary = firstRecord(summaryMetadata?.cost_summary, diagnosticsSummary?.cost_summary);
  const tradeMetrics = asRecord(attribution?.trade_metrics);
  const completedTradeCount = numberValue(tradeMetrics?.completed_trade_count) ?? numberValue(scoreCalibration?.total_completed_trade_count);
  const flags = [
    ...flagRows(performanceDiagnostics?.flags),
    ...flagRows(timingDiagnostics?.flags),
    ...flagRows(riskAudit?.flags),
    ...flagRows(scoreCalibration?.flags),
  ];
  const reasons = topReasons([
    ...mechanicalReasons(flags),
    ...costReasons(flags, costSummary),
    ...entryTimingReasons(flags),
    ...riskReasons(flags, riskAudit),
    ...scoreReasons(flags, scoreCalibration),
    ...edgeReasons(flags, tradeMetrics),
    ...sampleReasons(flags, completedTradeCount),
  ]);
  const confidence = confidenceLabel(completedTradeCount, flags);
  const status = conclusionStatus(completedTradeCount, reasons, tradeMetrics);

  return {
    status,
    confidence,
    completedTradeCount,
    headline: headline(status, confidence),
    reasons: reasons.length ? reasons : [neutralReason()],
    evidenceRows: evidenceRows(tradeMetrics, costSummary, riskAudit, scoreCalibration),
    rawEvidence: {
      performanceDiagnostics,
      timingDiagnostics,
      riskAudit,
      scoreCalibration,
      attribution,
      costSummary,
      flags,
    },
  };
}

function mechanicalReasons(flags: FlagRow[]): RunConclusionReason[] {
  return flags
    .filter((flag) => ["TAKE_PROFIT_NEGATIVE_PNL_ANOMALY", "ENTRY_FILL_REFERENCE_DIVERGENCE", "RISK_PER_UNIT_NOT_POSITIVE", "LONG_TARGET_NOT_ABOVE_FILL", "SHORT_TARGET_NOT_BELOW_FILL"].includes(flag.code))
    .map((flag) => reason("mechanical", "Mechanical anomaly detected", "critical", flag.message, "Inspect fill/reference alignment, target prices, and risk-plan metadata before interpreting edge."));
}

function costReasons(flags: FlagRow[], costSummary: AnyRecord | null): RunConclusionReason[] {
  const reasons = flags
    .filter((flag) => flag.code === "HIGH_COST_DRAG" || flag.code === "ZERO_COST_ASSUMPTION")
    .map((flag) => reason("cost", flag.code === "ZERO_COST_ASSUMPTION" ? "Cost assumptions are incomplete" : "Costs are consuming edge", flag.code === "HIGH_COST_DRAG" ? "warning" : "info", flag.message, "Enable a realistic cost profile and rerun cost sensitivity."));
  const costRatio = numberValue(costSummary?.cost_to_gross_pnl_ratio);
  if (costRatio !== null && costRatio > 0.2 && !reasons.some((item) => item.category === "cost")) {
    reasons.push(reason("cost", "Costs are consuming edge", "warning", `Cost-to-gross-PnL ratio is ${(costRatio * 100).toFixed(2)}%.`, "Compare zero, baseline, conservative, and high-slippage cost profiles."));
  }
  return reasons;
}

function entryTimingReasons(flags: FlagRow[]): RunConclusionReason[] {
  return flags
    .filter((flag) => ["ENTRY_WAS_LATE_CHASING", "IMMEDIATE_ADVERSE_EXCURSION"].includes(flag.code))
    .map((flag) => reason("entry", "Entry timing is hurting the run", "warning", flag.message, "Try FVG retest/limit entry modes and inspect MFE/MAE timing diagnostics."));
}

function riskReasons(flags: FlagRow[], riskAudit: AnyRecord | null): RunConclusionReason[] {
  const reasons = flags
    .filter((flag) => ["STOP_LOSS_DOMINANT", "TIME_STOP_DOMINANT", "SOFT_INVALIDATION_DOMINANT"].includes(flag.code))
    .map((flag) => reason("risk", "Exit behavior dominates losses", "warning", flag.message, "Inspect stop dominance, time-stop settings, target distance, and partial-exit contribution."));
  const dominance = asRecord(riskAudit?.dominance);
  const stopDominance = numberValue(dominance?.stop_loss_dominance_ratio);
  if (stopDominance !== null && stopDominance >= 0.5 && !reasons.some((item) => item.category === "risk")) {
    reasons.push(reason("risk", "Stop exits dominate the run", "warning", `Stop-loss dominance is ${(stopDominance * 100).toFixed(2)}%.`, "Inspect stop placement, entry timing, and same-candle sequencing assumptions."));
  }
  return reasons;
}

function scoreReasons(flags: FlagRow[], scoreCalibration: AnyRecord | null): RunConclusionReason[] {
  const reasons = flags
    .filter((flag) => ["NO_MONOTONIC_SCORE_IMPROVEMENT", "PLACEHOLDER_COMPONENT_DOMINATES_SCORE", "HIGH_SCORE_NEGATIVE_EXPECTANCY"].includes(flag.code))
    .map((flag) => reason("score", "Score filter is not proving edge", "warning", flag.message, "Inspect score bucket calibration and run walk-forward validation before changing thresholds."));
  if (scoreCalibration?.inference_strength === "PARTIAL" && !reasons.some((item) => item.category === "score")) {
    reasons.push(reason("score", "Score evidence is incomplete", "info", "Score calibration is partial or missing for this run.", "Run a scored pattern backtest with completed trade lifecycles."));
  }
  return reasons;
}

function edgeReasons(flags: FlagRow[], tradeMetrics: AnyRecord | null): RunConclusionReason[] {
  const reasons = flags
    .filter((flag) => ["NEGATIVE_EXPECTANCY", "LOW_HIT_RATE", "POOR_PAYOFF_RATIO"].includes(flag.code))
    .map((flag) => reason("edge", "The strategy edge is weak in this sample", "warning", flag.message, "Run walk-forward validation and inspect side/regime attribution before tuning parameters."));
  const expectancy = numberValue(tradeMetrics?.expectancy);
  if (expectancy !== null && expectancy < 0 && !reasons.some((item) => item.category === "edge")) {
    reasons.push(reason("edge", "The strategy edge is weak in this sample", "warning", `Expectancy is ${expectancy}.`, "Compare pattern, side, and regime attribution."));
  }
  return reasons;
}

function sampleReasons(flags: FlagRow[], completedTradeCount: number | null): RunConclusionReason[] {
  if (completedTradeCount === null || completedTradeCount === 0) {
    return [reason("sample", "Not enough completed trades", "info", "No completed trade lifecycle is available for a reliable conclusion.", "Extend the sample window or inspect no-fill/open-position behavior.")];
  }
  if (completedTradeCount < 5 || flags.some((flag) => flag.code === "SCORE_BUCKET_SAMPLE_TOO_SMALL")) {
    return [reason("sample", "Sample size is small", "info", `${completedTradeCount} completed trades limits confidence.`, "Run a longer sample and walk-forward validation.")];
  }
  return [];
}

function topReasons(reasons: RunConclusionReason[]): RunConclusionReason[] {
  const rank = { critical: 0, warning: 1, info: 2, neutral: 3 };
  const seen = new Set<string>();
  return reasons
    .sort((left, right) => rank[left.severity] - rank[right.severity])
    .filter((item) => {
      const key = `${item.category}:${item.title}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 3);
}

function confidenceLabel(completedTradeCount: number | null, flags: FlagRow[]): RunConclusionModel["confidence"] {
  if (completedTradeCount === null || completedTradeCount === 0) return "Not enough data";
  if (completedTradeCount < 5 || flags.some((flag) => flag.code.includes("SAMPLE_TOO_SMALL"))) return "Low";
  if (completedTradeCount < 20) return "Medium";
  return "High";
}

function conclusionStatus(completedTradeCount: number | null, reasons: RunConclusionReason[], tradeMetrics: AnyRecord | null): RunConclusionModel["status"] {
  if (completedTradeCount === null || completedTradeCount === 0) return "not_enough_data";
  if (reasons.some((item) => item.severity === "critical" || item.severity === "warning")) return "weak_run";
  const expectancy = numberValue(tradeMetrics?.expectancy);
  return expectancy !== null && expectancy < 0 ? "weak_run" : "healthy_or_inconclusive";
}

function headline(status: RunConclusionModel["status"], confidence: RunConclusionModel["confidence"]): string {
  if (status === "not_enough_data") return "Not enough completed trade data to explain this run reliably.";
  if (status === "weak_run") return `Likely weak run. Confidence: ${confidence}.`;
  return `No critical deterministic failure reason found. Confidence: ${confidence}.`;
}

function neutralReason(): RunConclusionReason {
  return reason("summary", "No major deterministic failure reason", "neutral", "Diagnostics did not identify a critical or warning-level failure driver.", "Use walk-forward validation before making strategy changes.");
}

function evidenceRows(tradeMetrics: AnyRecord | null, costSummary: AnyRecord | null, riskAudit: AnyRecord | null, scoreCalibration: AnyRecord | null) {
  const dominance = asRecord(riskAudit?.dominance);
  return compactRows([
    row("Completed Trades", scalar(tradeMetrics?.completed_trade_count)),
    row("Hit Ratio", percent(tradeMetrics?.hit_ratio)),
    row("Expectancy", scalar(tradeMetrics?.expectancy)),
    row("Average R", scalar(tradeMetrics?.average_r)),
    row("Cost / Gross PnL", percent(costSummary?.cost_to_gross_pnl_ratio)),
    row("Stop Dominance", percent(dominance?.stop_loss_dominance_ratio)),
    row("Score Inference", scalar(scoreCalibration?.inference_strength)),
    row("Score Flags", scalar(scoreCalibration?.flag_count)),
  ]);
}

type FlagRow = { code: string; message: string; severity: string };

function flagRows(value: unknown): FlagRow[] {
  return Array.isArray(value)
    ? value.map(asRecord).filter(Boolean).map((flag) => ({
        code: String(flag?.code ?? ""),
        message: String(flag?.message ?? flag?.code ?? ""),
        severity: String(flag?.severity ?? "INFO"),
      }))
    : [];
}

function reason(category: string, title: string, severity: RunConclusionReason["severity"], evidence: string, recommendedNextAnalysis: string): RunConclusionReason {
  return { category, title, severity, evidence, recommendedNextAnalysis };
}

function row(label: string, value: string | null): { label: string; value: string } | null {
  return value ? { label, value } : null;
}

function compactRows(rows: Array<{ label: string; value: string } | null>) {
  return rows.filter((item): item is { label: string; value: string } => Boolean(item));
}
