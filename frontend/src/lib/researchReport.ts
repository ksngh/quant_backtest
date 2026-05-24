import { asRecord, scalar, type AnyRecord } from "./valueUtils";

export type ResearchReportPreview = {
  hasReport: boolean;
  rows: { label: string; value: string }[];
  sections: string[];
  markdown: string | null;
};

export function buildResearchReportPreview(reportValue: unknown): ResearchReportPreview {
  const report = asRecord(reportValue);
  if (!report) {
    return { hasReport: false, rows: [], sections: [], markdown: null };
  }
  const note = asRecord(report.pattern_research_note);
  const entryMode = asRecord(note?.entry_mode);
  const riskPlan = asRecord(note?.risk_plan);
  const scoreReliability = asRecord(note?.score_reliability);
  const costProfile = asRecord(asRecord(note?.cost_profile)?.profile);
  const markdown = typeof report.markdown === "string" ? report.markdown : null;

  return {
    hasReport: true,
    rows: compactRows([
      row("Schema", scalar(report.schema_version)),
      row("Report Mode", "Saved-run read-only artifact"),
      row("Pattern", scalar(note?.pattern_type)),
      row("Research Status", scalar(note?.status)),
      row("Entry Mode", scalar(entryMode?.selected_entry_mode)),
      row("Fill Source", scalar(entryMode?.fill_price_source)),
      row("Risk Aligned To Fill", scalar(riskPlan?.risk_plan_aligned_to_fill)),
      row("Cost Profile", scalar(costProfile?.profile_key)),
      row("Score Reliability", scalar(scoreReliability?.inference_strength)),
    ]),
    sections: sectionNames(note),
    markdown,
  };
}

function sectionNames(note: AnyRecord | null): string[] {
  if (!note) return [];
  const labels: Record<string, string> = {
    hypothesis: "Hypothesis",
    detector_conditions: "Detector Conditions",
    windows_candles_observed: "Windows/Candles",
    entry_mode: "Entry Mode",
    risk_plan: "Risk Plan",
    cost_profile: "Cost Profile",
    score_reliability: "Score Reliability",
    no_lookahead_status: "No-Lookahead Status",
    regime_dependence: "Regime Dependence",
    top_failure_reasons: "Top Failure Reasons",
    limitations: "Limitations",
    recommended_next_analyses: "Recommended Next Analyses",
  };
  return Object.entries(labels)
    .filter(([key]) => note[key] !== undefined && note[key] !== null)
    .map(([, label]) => label);
}

function row(label: string, value: string | null | undefined): { label: string; value: string } | null {
  return value ? { label, value } : null;
}

function compactRows(rows: Array<{ label: string; value: string } | null>): { label: string; value: string }[] {
  return rows.filter((item): item is { label: string; value: string } => Boolean(item));
}
