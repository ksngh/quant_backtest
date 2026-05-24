import assert from "node:assert/strict";

import { buildResearchReportPreview } from "../src/lib/researchReport";

const preview = buildResearchReportPreview({
  schema_version: "backtest_research_report_v1",
  pattern_research_note: {
    schema_version: "pattern_research_note_v1",
    status: "available",
    pattern_type: "FAIR_VALUE_GAP",
    hypothesis: {},
    detector_conditions: {},
    windows_candles_observed: {},
    entry_mode: {
      selected_entry_mode: "LIMIT_AT_PATTERN_MIDPOINT",
      fill_price_source: "limit_touch",
    },
    risk_plan: {
      risk_plan_aligned_to_fill: true,
    },
    cost_profile: {
      profile: { profile_key: "conservative_crypto_1m" },
    },
    score_reliability: {
      inference_strength: "PARTIAL",
    },
    no_lookahead_status: {},
    regime_dependence: {},
    top_failure_reasons: [],
    limitations: [],
    recommended_next_analyses: [],
  },
  markdown: "# Backtest Research Report: Run 7\n\n## Pattern Research Note",
});

assert.equal(preview.hasReport, true);
assert.equal(preview.rows.find((row) => row.label === "Pattern")?.value, "FAIR_VALUE_GAP");
assert.equal(preview.rows.find((row) => row.label === "Entry Mode")?.value, "LIMIT_AT_PATTERN_MIDPOINT");
assert.equal(preview.rows.find((row) => row.label === "Risk Aligned To Fill")?.value, "Yes");
assert.equal(preview.rows.find((row) => row.label === "Cost Profile")?.value, "conservative_crypto_1m");
assert.ok(preview.sections.includes("Hypothesis"));
assert.ok(preview.sections.includes("No-Lookahead Status"));
assert.ok(preview.markdown?.includes("Pattern Research Note"));

const legacy = buildResearchReportPreview(null);
assert.equal(legacy.hasReport, false);
assert.deepEqual(legacy.rows, []);
