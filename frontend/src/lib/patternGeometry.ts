import type { BacktestRunDetailResponse, BacktestTrade } from "../types/api";
import { asRecord, firstRecord, percent, scalar, type AnyRecord } from "./valueUtils";

export type PatternGeometryRow = {
  label: string;
  value: string;
};

export type PatternScoreComponent = {
  name: string;
  rawScore: string;
  weight: string;
  weightedScore: string;
  source: string;
  isPlaceholder: boolean;
  includedInExecutableScore: boolean | null;
  description: string | null;
};

export type PatternGeometryModel = {
  hasMetadata: boolean;
  patternType: string;
  sourceTradeLabel: string | null;
  geometryRows: PatternGeometryRow[];
  scoreRows: PatternGeometryRow[];
  observedComponents: PatternScoreComponent[];
  placeholderComponents: PatternScoreComponent[];
  scoreExplanation: string;
  candidateRows: PatternGeometryRow[];
  candidateWarnings: string[];
};

const GEOMETRY_FIELDS: Record<string, string[]> = {
  FAIR_VALUE_GAP: [
    "pattern_direction",
    "pattern_status",
    "zone_low",
    "zone_mid",
    "zone_high",
    "gap_size",
    "gap_size_atr",
    "gap_age",
    "state",
    "lifecycle_state",
    "volume_ratio",
    "displacement_confirmed",
    "entry_reference_distance",
    "zone_distance",
  ],
  ORDER_BLOCK: [
    "pattern_direction",
    "pattern_status",
    "zone_low",
    "zone_mid",
    "zone_high",
    "zone_size",
    "zone_size_atr",
    "source_candle_index",
    "source_candle_count",
    "cluster_candle_count",
    "mitigation_status",
    "retest_status",
    "volume_ratio",
    "displacement_confirmed",
  ],
  TRENDLINE_BREAK: [
    "pattern_direction",
    "pattern_status",
    "source_pivot_indices",
    "fit_pivot_count",
    "touch_count",
    "validation_touch_count",
    "trendline_value",
    "trendline_slope",
    "breakout_distance_atr",
    "touch_deviation_atr",
    "retest_status",
    "follow_through_status",
  ],
  CUP_AND_HANDLE: [
    "pattern_direction",
    "pattern_status",
    "left_rim_index",
    "cup_bottom_index",
    "right_rim_index",
    "handle_low_index",
    "breakout_index",
    "neckline",
    "cup_depth",
    "cup_depth_rate",
    "handle_depth_ratio",
    "bottom_zone_duration",
    "neckline_retest_status",
    "neckline_retest_wait_bars",
  ],
  DIAMOND: [
    "pattern_direction",
    "pattern_status",
    "source_pivot_indices",
    "split_position",
    "expansion_pivot_count",
    "contraction_pivot_count",
    "boundary_touch_count",
    "upper_boundary_value",
    "lower_boundary_value",
    "boundary_deviation_atr",
    "pattern_height_atr",
    "alternating_pivots_score",
  ],
  ADAM_AND_EVE: [
    "pattern_direction",
    "pattern_status",
    "adam_low_index",
    "neckline_pivot_index",
    "eve_low_index",
    "breakout_index",
    "neckline",
    "bottom_difference_rate",
    "eve_to_adam_duration_ratio",
    "pattern_height_atr",
    "adam_local_range_atr",
    "eve_bottom_zone_duration",
  ],
};

const GENERIC_FIELDS = [
  "pattern_direction",
  "position_side",
  "pattern_status",
  "event_entry_reference",
  "entry_reference",
  "stop_reference",
  "target_reference",
  "risk_reward",
];

export function buildPatternGeometryModel(detail: BacktestRunDetailResponse): PatternGeometryModel {
  const summaryMetadata = asRecord(detail.summary.metadata);
  const diagnosticsSummary = asRecord(detail.diagnostics?.summary);
  const scoreCalibration = firstRecord(summaryMetadata?.score_calibration, diagnosticsSummary?.score_calibration);
  const scoreLift = asRecord(scoreCalibration?.score_lift);
  const trade = firstPatternTrade(detail.trades);
  const metadata = asRecord(trade?.metadata);
  const patternType = normalizedPatternType(metadata, detail);
  const scoreComponents = asRecord(metadata?.score_components);
  const componentRows = scoreComponentRows(scoreComponents);
  const candidateDiagnostics = firstRecord(
    metadata?.candidate_diagnostics,
    asRecord(scoreCalibration?.candidate_diagnostics)?.representative_diagnostics,
    scoreCalibration?.candidate_diagnostics,
  );
  const geometryRows = geometryFields(patternType, metadata);
  const scoreRows = compactRows([
    row("Executable Score", scalar(metadata?.executable_pattern_score ?? metadata?.pattern_score)),
    row("Diagnostic Score", scalar(metadata?.diagnostic_pattern_score)),
    row("Minimum Score", scalar(scoreCalibration?.minimum_pattern_score)),
    row("Calibration Inference", scalar(scoreCalibration?.inference_strength)),
    row("OOS Lift", scalar(scoreLift?.high_minus_low_outcome)),
    row("OOS Lift Interpretation", scalar(scoreLift?.interpretation)),
  ]);
  const candidateRows = candidateDiagnosticRows(candidateDiagnostics);
  const candidateWarnings = candidateDiagnosticWarnings(candidateDiagnostics);

  return {
    hasMetadata: Boolean(metadata) && (geometryRows.length > 0 || componentRows.length > 0 || candidateRows.length > 0 || scoreRows.length > 0),
    patternType,
    sourceTradeLabel: trade ? `Trade #${trade.sequence} ${trade.position_signal ?? trade.signal}` : null,
    geometryRows,
    scoreRows,
    observedComponents: componentRows.filter((component) => !component.isPlaceholder),
    placeholderComponents: componentRows.filter((component) => component.isPlaceholder),
    scoreExplanation: scoreExplanation(scoreLift),
    candidateRows,
    candidateWarnings,
  };
}

function firstPatternTrade(trades: BacktestTrade[]): BacktestTrade | null {
  return (
    trades.find((trade) => {
      const metadata = asRecord(trade.metadata);
      return Boolean(metadata?.pattern_type || metadata?.score_components || metadata?.pattern_score);
    }) ?? null
  );
}

function normalizedPatternType(metadata: AnyRecord | null, detail: BacktestRunDetailResponse): string {
  const params = detail.strategy_config.parameters;
  const value =
    text(metadata?.pattern_type)
    ?? text(params.pattern)
    ?? text(params.pattern_key)
    ?? (text(params.strategy) !== "pattern" ? text(params.strategy) : null)
    ?? detail.strategy_config.name
    ?? detail.strategy_config.key;
  return String(value).toUpperCase();
}

function geometryFields(patternType: string, metadata: AnyRecord | null): PatternGeometryRow[] {
  if (!metadata) return [];
  const fields = GEOMETRY_FIELDS[patternType] ?? GENERIC_FIELDS;
  return compactRows(fields.map((key) => row(labelize(key), displayValue(metadata[key]))));
}

function scoreComponentRows(components: AnyRecord | null): PatternScoreComponent[] {
  if (!components) return [];
  return Object.entries(components).flatMap(([name, raw]) => {
    const record = asRecord(raw);
    if (!record) {
      const value = displayValue(raw);
      return value
        ? [{
            name: labelize(name),
            rawScore: value,
            weight: "Not available",
            weightedScore: "Not available",
            source: "legacy_component_value",
            isPlaceholder: false,
            includedInExecutableScore: null,
            description: null,
          }]
        : [];
    }
    return [{
      name: labelize(name),
      rawScore: displayValue(record.raw_score) ?? "Not available",
      weight: displayValue(record.weight) ?? "Not available",
      weightedScore: displayValue(record.weighted_score ?? record.executable_weighted_score) ?? "Not available",
      source: text(record.source) ?? "Not available",
      isPlaceholder: record.is_placeholder === true,
      includedInExecutableScore: typeof record.included_in_executable_score === "boolean"
        ? record.included_in_executable_score
        : null,
      description: text(record.description),
    }];
  });
}

function candidateDiagnosticRows(diagnostics: AnyRecord | null): PatternGeometryRow[] {
  if (!diagnostics) return [];
  return compactRows([
    row("Schema", scalar(diagnostics.schema_version)),
    row("Candidates Built", scalar(diagnostics.candidate_count ?? diagnostics.total_candidate_count)),
    row("Candidates Evaluated", scalar(diagnostics.evaluated_candidate_count)),
    row("Selected Rank", scalar(diagnostics.selected_rank)),
    row("Candidate Density", scalar(diagnostics.candidate_density_ratio)),
    row("Max Guard Hit", scalar(diagnostics.max_candidate_guard_hit ?? diagnostics.has_guard_hit)),
    row("Overfit Warning", scalar(diagnostics.overfit_warning ?? diagnostics.has_overfit_warning)),
    row("Diagnostic Trade Count", scalar(diagnostics.diagnostic_trade_count)),
  ]);
}

function candidateDiagnosticWarnings(diagnostics: AnyRecord | null): string[] {
  if (!diagnostics) return [];
  const warnings = list(diagnostics.warnings);
  if (diagnostics.overfit_warning === true || diagnostics.has_overfit_warning === true) {
    warnings.push("Candidate search produced an overfit-risk warning; treat selected geometry as research evidence, not a robust edge.");
  }
  if (diagnostics.max_candidate_guard_hit === true || diagnostics.has_guard_hit === true) {
    warnings.push("Candidate guard was hit; detector search space may be too dense for this configuration.");
  }
  return Array.from(new Set(warnings));
}

function scoreExplanation(scoreLift: AnyRecord | null): string {
  if (text(scoreLift?.interpretation) === "POSITIVE_LIFT") {
    return "Pattern score is still a heuristic quality score, not a calibrated probability; this run only reports positive score-lift evidence in saved calibration metadata.";
  }
  return "Pattern score is a heuristic quality score, not a calibrated probability. Treat component weights and placeholder priors as diagnostics unless out-of-sample lift is demonstrated.";
}

function row(label: string, value: string | null | undefined): PatternGeometryRow | null {
  return value ? { label, value } : null;
}

function compactRows(rows: Array<PatternGeometryRow | null>): PatternGeometryRow[] {
  return rows.filter((item): item is PatternGeometryRow => Boolean(item));
}

function displayValue(value: unknown): string | null {
  const simple = scalar(value);
  if (simple) return simple;
  const pct = percent(value);
  if (pct) return pct;
  if (Array.isArray(value)) {
    const items = value.map((item) => displayValue(item)).filter(Boolean);
    return items.length ? items.join(", ") : null;
  }
  return null;
}

function labelize(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.filter(Boolean).map(String) : [];
}

function text(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}
