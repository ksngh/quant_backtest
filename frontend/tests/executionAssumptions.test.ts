import assert from "node:assert/strict";

import { buildExecutionAssumptionModel } from "../src/lib/executionAssumptions";
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
      parameters: {
        pattern_execution_policy: { selected_entry_mode: "LIMIT_AT_PATTERN_MIDPOINT" },
      },
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
      trade_count: 2,
      buy_count: 1,
      sell_count: 1,
      metadata: {
        cost_profile: { profile_key: "conservative_crypto_1m", description: "Conservative 1m crypto assumptions" },
        cost_summary: {
          zero_transaction_cost_assumption: true,
          zero_cost_warning: "zero fees, spread, and slippage active",
          cost_to_gross_pnl_ratio: 0.12,
          total_cost: 3.5,
        },
        risk_exit_audit: {
          intrabar_ambiguity: {
            ambiguous_stop_target_count: 2,
            ambiguous_stop_target_pnl_contribution_ratio: -0.25,
          },
        },
        short_economics: { enabled: false },
      },
      created_at: "2026-05-24T00:01:00Z",
    },
    trades: [
      {
        id: 1,
        sequence: 1,
        candle_open_time: "2026-05-24T00:00:00Z",
        signal: "SHORT_ENTRY",
        position_signal: "SHORT_ENTRY",
        position_side: "SHORT",
        price: 101,
        quantity: 1,
        cash_after: 9899,
        position_after: -1,
        metadata: {
          entry_mode: "LIMIT_AT_PATTERN_MIDPOINT",
          fill_price_source: "limit_touch",
          fill_assumption: "historical_limit_fill",
          bars_waited: 3,
          entry_reference: 100,
          requested_price: 101,
          risk_plan_aligned_to_fill: true,
          original_risk_per_unit: 5,
          fill_adjusted_risk_per_unit: 7,
          risk_per_unit: 7,
          sizing_risk_source: "FILL_ADJUSTED",
          effective_slippage_bps: 21,
        },
      },
      {
        id: 2,
        sequence: 2,
        candle_open_time: "2026-05-24T00:04:00Z",
        signal: "SHORT_EXIT",
        position_signal: "SHORT_EXIT",
        position_side: "SHORT",
        price: 96,
        quantity: 1,
        cash_after: 10020,
        position_after: 0,
        metadata: {
          exit_metadata: {
            intrabar_policy: "CONSERVATIVE",
            ambiguous_stop_target: true,
          },
        },
      },
    ],
    graph_points: [],
    diagnostics: null,
    research_report: null,
    warnings: [],
    ...overrides,
  };
}

const model = buildExecutionAssumptionModel(detail());
assert.equal(model.hasMetadata, true);
assert.equal(model.entryRows.find((row) => row.label === "Entry Mode")?.value, "LIMIT_AT_PATTERN_MIDPOINT");
assert.equal(model.entryRows.find((row) => row.label === "Actual Fill Price")?.value, "101");
assert.equal(model.entryRows.find((row) => row.label === "Bars Waited")?.value, "3");
assert.equal(model.riskRows.find((row) => row.label === "Risk Plan Aligned To Fill")?.value, "Yes");
assert.equal(model.riskRows.find((row) => row.label === "Original Risk Per Unit")?.value, "5");
assert.equal(model.riskRows.find((row) => row.label === "Fill-Adjusted Risk Per Unit")?.value, "7");
assert.equal(model.costRows.find((row) => row.label === "Cost Profile")?.value, "conservative_crypto_1m");
assert.equal(model.costRows.find((row) => row.label === "Effective Slippage Bps")?.value, "21");
assert.equal(model.costRows.find((row) => row.label === "Cost / Gross PnL")?.value, "12.00%");
assert.equal(model.intrabarRows.find((row) => row.label === "Intrabar Policy")?.value, "CONSERVATIVE");
assert.equal(model.intrabarRows.find((row) => row.label === "Ambiguous Stop/Target Count")?.value, "2");
assert.ok(model.warnings.some((warning) => warning.includes("zero fees")));
assert.ok(model.shortLimitation?.includes("legacy cash-bounded simulation"));

const legacy = buildExecutionAssumptionModel(
  detail({
    strategy_config: { ...detail().strategy_config, parameters: {} },
    summary: { ...detail().summary, metadata: {} },
    trades: [],
  }),
);
assert.equal(legacy.hasMetadata, false);
assert.equal(legacy.shortLimitation, null);
