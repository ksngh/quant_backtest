import assert from "node:assert/strict";

import { buildPatternGeometryModel } from "../src/lib/patternGeometry";
import type { BacktestRunDetailResponse, BacktestTrade } from "../src/types/api";

function detail(patternType: string, metadata: Record<string, unknown>): BacktestRunDetailResponse {
  return {
    run: {
      id: 1,
      run_key: "rk",
      engine_name: "strategy_engine",
      engine_version: "v1",
      status: "completed",
      market: {
        source: "csv",
        symbol: "BTCUSDT",
        interval: "1m",
        requested_start_time: null,
        requested_end_time: null,
        actual_start_time: null,
        actual_end_time: null,
        candle_count: 10,
      },
      starting_cash: 10000,
      trade_quantity: 1,
      created_at: "2026-05-24T00:00:00Z",
      completed_at: "2026-05-24T00:01:00Z",
      metadata: {},
    },
    strategy_config: {
      id: 1,
      key: "pattern",
      name: `${patternType}_STRATEGY`,
      version: "v1",
      parameters: { pattern: patternType },
      parameters_hash: "h",
      metadata: {},
    },
    summary: {
      starting_cash: 10000,
      ending_cash: 10020,
      ending_position: 0,
      final_price: 100,
      final_equity: 10020,
      total_return: 0.002,
      trade_count: 1,
      buy_count: 1,
      sell_count: 0,
      metadata: {
        score_calibration: {
          minimum_pattern_score: 0.7,
          inference_strength: "PARTIAL",
          score_lift: {
            high_minus_low_outcome: 0.4,
            interpretation: "POSITIVE_LIFT",
          },
        },
      },
      created_at: "2026-05-24T00:01:00Z",
    },
    trades: [trade({ pattern_type: patternType, ...metadata })],
    graph_points: [],
    diagnostics: null,
    warnings: [],
    research_report: null,
  };
}

function trade(metadata: Record<string, unknown>): BacktestTrade {
  return {
    id: 1,
    sequence: 1,
    candle_open_time: "2026-05-24T00:00:00Z",
    signal: "LONG_ENTRY",
    position_signal: "LONG_ENTRY",
    price: 100,
    quantity: 1,
    cash_after: 9900,
    position_after: 1,
    metadata: {
      pattern_score: 0.8,
      diagnostic_pattern_score: 0.95,
      executable_pattern_score: 0.8,
      score_components: components(),
      ...metadata,
    },
  };
}

function components() {
  return {
    observed_edge: {
      raw_score: 0.8,
      weight: 0.4,
      weighted_score: 0.32,
      source: "observed_geometry",
      is_placeholder: false,
      included_in_executable_score: true,
      description: "Observed geometric feature.",
    },
    placeholder_prior: {
      raw_score: 1,
      weight: 0.2,
      weighted_score: 0.2,
      executable_weighted_score: 0,
      source: "placeholder_policy",
      is_placeholder: true,
      included_in_executable_score: false,
    },
  };
}

const cases: Array<[string, Record<string, unknown>, string]> = [
  ["FAIR_VALUE_GAP", { zone_low: 99, zone_mid: 100, zone_high: 101, gap_size_atr: 1.2 }, "Zone Low"],
  ["ORDER_BLOCK", { zone_low: 97, zone_high: 103, mitigation_status: "RETESTED" }, "Mitigation Status"],
  ["TRENDLINE_BREAK", { source_pivot_indices: [1, 4, 7], trendline_slope: 0.2 }, "Source Pivot Indices"],
  ["CUP_AND_HANDLE", { left_rim_index: 1, cup_bottom_index: 3, neckline: 105 }, "Left Rim Index"],
  ["DIAMOND", { source_pivot_indices: [1, 2, 3, 4], split_position: 2, pattern_height_atr: 3 }, "Split Position"],
  ["ADAM_AND_EVE", { adam_low_index: 2, neckline_pivot_index: 4, eve_low_index: 6 }, "Adam Low Index"],
];

for (const [patternType, metadata, expectedLabel] of cases) {
  const model = buildPatternGeometryModel(detail(patternType, metadata));
  assert.equal(model.hasMetadata, true);
  assert.equal(model.patternType, patternType);
  assert.ok(model.geometryRows.some((row) => row.label === expectedLabel), `${patternType} should expose ${expectedLabel}`);
  assert.equal(model.observedComponents.length, 1);
  assert.equal(model.placeholderComponents.length, 1);
  assert.equal(model.placeholderComponents[0].includedInExecutableScore, false);
  assert.ok(model.scoreExplanation.includes("not a calibrated probability"));
}

const candidateModel = buildPatternGeometryModel(
  detail("DIAMOND", {
    split_position: 2,
    candidate_diagnostics: {
      schema_version: "chart_pattern_candidate_diagnostics_v1",
      candidate_count: 30,
      evaluated_candidate_count: 10,
      selected_rank: 2,
      max_candidate_guard_hit: true,
      overfit_warning: true,
    },
  }),
);
assert.ok(candidateModel.candidateRows.some((row) => row.label === "Candidates Built" && row.value === "30"));
assert.ok(candidateModel.candidateWarnings.some((warning) => warning.includes("overfit-risk")));

const legacyModel = buildPatternGeometryModel({
  ...detail("FAIR_VALUE_GAP", {}),
  trades: [],
  summary: { ...detail("FAIR_VALUE_GAP", {}).summary, metadata: {} },
});
assert.equal(legacyModel.hasMetadata, false);
assert.equal(legacyModel.geometryRows.length, 0);
