import assert from "node:assert/strict";

import { buildRunConclusionModel } from "../src/lib/runConclusion";
import type { BacktestRunDetailResponse } from "../src/types/api";

function baseDetail(metadata: Record<string, unknown>): BacktestRunDetailResponse {
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
      name: "FAIR_VALUE_GAP_PATTERN_STRATEGY",
      version: "v1",
      parameters: { pattern: "FAIR_VALUE_GAP" },
      parameters_hash: "h",
      metadata: {},
    },
    summary: {
      starting_cash: 10000,
      ending_cash: 9000,
      ending_position: 0,
      final_price: 100,
      final_equity: 9000,
      total_return: -0.1,
      trade_count: 8,
      buy_count: 4,
      sell_count: 4,
      metadata,
      created_at: "2026-05-24T00:01:00Z",
    },
    trades: [],
    graph_points: [],
    diagnostics: null,
    warnings: [],
  };
}

const bad = buildRunConclusionModel(
  baseDetail({
    performance_diagnostics: {
      flags: [
        { code: "NEGATIVE_EXPECTANCY", severity: "WARNING", message: "Completed trade lifecycle expectancy is negative." },
        { code: "HIGH_COST_DRAG", severity: "WARNING", message: "Transaction costs consume a large share of gross edge." },
      ],
    },
    timing_diagnostics: {
      flags: [{ code: "ENTRY_WAS_LATE_CHASING", severity: "WARNING", message: "Entry arrived after most favorable excursion." }],
    },
    trade_attribution: {
      trade_metrics: { completed_trade_count: 8, hit_ratio: 0.25, expectancy: -12, average_r: -0.4 },
    },
    cost_summary: { cost_to_gross_pnl_ratio: 0.35 },
  }),
);

assert.equal(bad.status, "weak_run");
assert.equal(bad.confidence, "Medium");
assert.equal(bad.reasons.length, 3);
assert.ok(bad.reasons.some((reason) => reason.category === "cost"));
assert.ok(bad.reasons.some((reason) => reason.category === "entry"));

const good = buildRunConclusionModel(
  baseDetail({
    performance_diagnostics: { flags: [] },
    trade_attribution: {
      trade_metrics: { completed_trade_count: 25, hit_ratio: 0.6, expectancy: 20, average_r: 0.8 },
    },
    cost_summary: { cost_to_gross_pnl_ratio: 0.05 },
  }),
);

assert.equal(good.status, "healthy_or_inconclusive");
assert.equal(good.confidence, "High");
assert.equal(good.reasons[0].severity, "neutral");

const legacy = buildRunConclusionModel(baseDetail({}));
assert.equal(legacy.status, "not_enough_data");
assert.equal(legacy.confidence, "Not enough data");
assert.ok(legacy.reasons[0].title.includes("Not enough"));
