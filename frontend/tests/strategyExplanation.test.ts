import assert from "node:assert/strict";

import { buildStrategyExplanationModel } from "../src/lib/strategyExplanation";
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
      parameters: { pattern: "FAIR_VALUE_GAP" },
      parameters_hash: "h",
      metadata: {
        explanation: {
          algorithm_key: "FAIR_VALUE_GAP",
          algorithm_name: "Fair Value Gap",
          detection_rules: ["Three-candle imbalance"],
          design_rationale: ["Capture displacement imbalance fills."],
          stop_loss_rules: ["Stop references FVG boundary."],
          take_profit_rules: ["Targets use R multiples."],
          partial_exit_rules: ["Partial exits follow target ratios."],
          soft_invalidation_rules: ["Close when imbalance thesis fails."],
          time_stop_rules: ["Exit after no reaction."],
          known_limitations: ["Historical simulation only."],
        },
      },
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
        position_sizing: { mode: "EQUITY_RISK_FRACTION", value: 0.01 },
        cost_profile: { profile_key: "conservative_crypto_1m" },
        cost_summary: { zero_transaction_cost_assumption: false },
        pattern_execution_policy: {
          selected_entry_mode: "LIMIT_AT_PATTERN_MIDPOINT",
          economic_rationale: "imbalance_retest_or_rebalancing_entry",
          research_hypothesis: "Retests should improve reward/risk.",
        },
        risk_exit_audit: {
          completed_exit_count: 1,
          dominance: { stop_loss_dominance_ratio: 0, time_stop_dominance_ratio: 0, soft_invalidation_dominance_ratio: 0 },
          target_quality: { first_target_hit_rate: 1 },
          partial_exit: { partial_exit_net_pnl: 5 },
          flags: [],
        },
        trade_attribution: {
          trade_metrics: { hit_ratio: 1, expectancy: 20, average_r: 1.2 },
        },
        performance_diagnostics: {
          flags: [{ code: "HIGH_COST_DRAG", message: "Transaction costs consume a large share of gross edge." }],
        },
      },
      created_at: "2026-05-24T00:01:00Z",
    },
    trades: [
      {
        id: 1,
        sequence: 1,
        candle_open_time: "2026-05-24T00:00:00Z",
        signal: "LONG_ENTRY",
        position_signal: "LONG_ENTRY",
        price: 101,
        quantity: 1,
        cash_after: 9899,
        position_after: 1,
        metadata: {
          entry_mode: "LIMIT_AT_PATTERN_MIDPOINT",
          fill_price_source: "limit_touch",
          fill_assumption: "historical_limit_fill",
          risk_per_unit: 2,
          entry_reference: 101,
          original_entry_reference: 100,
          fill_adjusted_risk_per_unit: 2,
          confirmation_close: 103,
        },
      },
      {
        id: 2,
        sequence: 2,
        candle_open_time: "2026-05-24T00:04:00Z",
        signal: "LONG_EXIT",
        position_signal: "LONG_EXIT",
        price: 105,
        quantity: 1,
        cash_after: 10020,
        position_after: 0,
        metadata: {
          exit_reason: "TAKE_PROFIT",
          target_name: "TP1",
          exit_price: 105,
          realized_r_multiple: 1.2,
        },
      },
    ],
    graph_points: [],
    diagnostics: null,
    warnings: [],
    ...overrides,
  };
}

const model = buildStrategyExplanationModel(detail());
assert.equal(model.fallback, false);
assert.equal(model.subtitle, "Fair Value Gap / FAIR_VALUE_GAP");
assert.equal(model.entryTiming.find((row) => row.label === "Selected Entry Mode")?.value, "LIMIT_AT_PATTERN_MIDPOINT");
assert.equal(model.riskManagementDesign.find((row) => row.label === "Risk Per Unit")?.value, "2");
assert.equal(model.exitTiming.find((row) => row.label === "Realized Exit Reason")?.value, "TAKE_PROFIT");
assert.ok(model.badPerformanceClues.some((clue) => clue.startsWith("HIGH_COST_DRAG")));

const legacy = buildStrategyExplanationModel(
  detail({
    strategy_config: {
      ...detail().strategy_config,
      metadata: {},
    },
    summary: {
      ...detail().summary,
      metadata: {},
    },
    trades: [],
  }),
);
assert.equal(legacy.fallback, true);
assert.ok(legacy.knownLimitations.some((item) => item.includes("readiness")));
