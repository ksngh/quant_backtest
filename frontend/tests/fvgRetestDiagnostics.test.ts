import assert from "node:assert/strict";

import { buildFvgRetestDiagnosticsModel } from "../src/lib/fvgRetestDiagnostics";
import type { BacktestRunDetailResponse } from "../src/types/api";

function detail(overrides: Partial<BacktestRunDetailResponse> = {}): BacktestRunDetailResponse {
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
      parameters: {},
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
      metadata: {},
      created_at: "2026-05-24T00:01:00Z",
    },
    trades: [],
    graph_points: [],
    diagnostics: null,
    research_report: null,
    warnings: [],
    ...overrides,
  };
}

const present = buildFvgRetestDiagnosticsModel(
  detail({
    summary: {
      ...detail().summary,
      metadata: {
        fvg_retest_v2: {
          schema_version: "fvg_retest_v2_diagnostics_v1",
          entry_trigger: "TOUCH_AND_REACTION_CLOSE",
          stop_mode: "WIDER_OF_FVG_AND_SWING",
          experimental_scope: "offline_research_only",
          counts: { filled_entry_count: 1, skipped_entry_count: 2 },
          settings: {
            schema_version: "fvg_retest_v2_settings_v1",
            enabled: true,
            trend_score: {
              enabled: true,
              fast_period: 9,
              slow_period: 21,
              weights: { "1m": 0.2, "5m": 0.3, "15m": 0.5 },
              minimum_bullish_trend_score: 0.1,
            },
            fibonacci_confluence: { enabled: true },
            liquidity_targets: { require_liquidity_target: true },
          },
        },
      },
    },
    trades: [
      {
        id: 1,
        sequence: 1,
        candle_open_time: "2026-05-24T00:00:00Z",
        signal: "LONG_ENTRY",
        position_signal: "LONG_ENTRY",
        position_side: "LONG",
        price: 101,
        quantity: 1,
        cash_after: 9899,
        position_after: 1,
        metadata: {
          pattern_type: "FAIR_VALUE_GAP",
          mtf_trend_score: 0.42,
          mtf_trend_direction: "BULLISH",
          mtf_trend_aligned: true,
          mtf_trend_metadata: { schema_version: "multitimeframe_trend_score_v1" },
          fib_confluence_pass: true,
          fib_retracement_level: 0.5,
          fib_metadata: {
            schema_version: "fibonacci_retracement_confluence_v1",
            anchor_method: "DISPLACEMENT_CANDLE_RANGE",
            overlap_mode: "MIDPOINT",
            band_min_level: 0.382,
            band_max_level: 0.618,
          },
          pattern_entry_policy: {
            entry_mode: "LIMIT_AT_PATTERN_MIDPOINT",
            fill_price_source: "reaction_close",
            entry_status: "FILLED",
            bars_waited: 2,
            touch_candle_index: 0,
            reaction_candle_index: 1,
            reaction_timestamp: "2026-05-24T00:02:00Z",
          },
          target_semantics: {
            schema_version: "target_semantics_v1",
            risk_targets: [{ name: "LIQUIDITY", price: 113 }],
          },
          risk_plan_atr_metadata: {
            fvg_stop_mode: {
              schema_version: "fvg_stop_mode_v1",
              stop_mode: "WIDER_OF_FVG_AND_SWING",
              selected_source: "SWING_PIVOT",
              fvg_boundary_stop: 98,
              swing_stop: 97,
              selected_stop: 97,
            },
          },
        },
      },
    ],
  }),
);

assert.equal(present.hasMetadata, true);
assert.equal(present.summaryRows.find((row) => row.label === "Entry Trigger")?.value, "TOUCH_AND_REACTION_CLOSE");
assert.equal(present.summaryRows.find((row) => row.label === "Skipped Entries")?.value, "2");
assert.equal(present.trendRows.find((row) => row.label === "Signed Score")?.value, "0.42");
assert.equal(present.trendRows.find((row) => row.label === "Weights")?.value, "1m: 0.2, 5m: 0.3, 15m: 0.5");
assert.equal(present.fibonacciRows.find((row) => row.label === "Retracement Level")?.value, "0.5");
assert.equal(present.liquidityRows.find((row) => row.label === "Risk Targets")?.value, "LIQUIDITY 113");
assert.equal(present.entryRows.find((row) => row.label === "Reaction Index")?.value, "1");
assert.equal(present.stopRows.find((row) => row.label === "Selected Stop")?.value, "97");
assert.ok(present.caveats.some((item) => item.includes("does not start backtests")));

const legacy = buildFvgRetestDiagnosticsModel(detail());
assert.equal(legacy.hasMetadata, false);
assert.deepEqual(legacy.summaryRows, []);
