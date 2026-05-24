import assert from "node:assert/strict";

import {
  classifyPerformanceDiagnostics,
  extractPerformanceDiagnostics,
} from "../src/lib/performanceDiagnostics";

const diagnostics = extractPerformanceDiagnostics({
  performance_metrics: {
    total_return: -0.12,
    annualized_return: -0.2,
    annualized_volatility: 0.35,
    sharpe_ratio: -0.4,
    sortino_ratio: -0.5,
    calmar_ratio: -1.2,
    max_drawdown: -0.24,
    max_drawdown_duration_periods: 31,
  },
  trade_attribution: {
    trade_metrics: {
      completed_trade_count: 3,
      hit_ratio: 0.2,
      payoff_ratio: 0.8,
      expectancy: -15,
      profit_factor: 0.7,
      average_r: -0.3,
      median_r: -0.2,
      max_consecutive_losses: 4,
    },
    exposure: {
      exposure_fraction: 0.45,
    },
    turnover: {
      turnover_ratio: 2.3,
    },
  },
  cost_summary: {
    cost_to_gross_pnl_ratio: 0.35,
    zero_transaction_cost_assumption: false,
  },
});

assert.equal(diagnostics.hasMetrics, true);
assert.equal(
  diagnostics.metrics.find((metric) => metric.key === "sharpe_ratio")?.value,
  -0.4,
);
assert.equal(
  diagnostics.metrics.find((metric) => metric.key === "cost_to_gross_pnl_ratio")?.tone,
  "bad",
);
assert.deepEqual(diagnostics.labels, [
  "Poor risk-adjusted return",
  "Cost drag high",
  "Low hit rate",
  "Negative expectancy",
  "Drawdown recovery weak",
]);

const legacy = extractPerformanceDiagnostics({});
assert.equal(legacy.hasMetrics, false);
assert.equal(legacy.zeroCostAssumption, null);

assert.deepEqual(
  classifyPerformanceDiagnostics({
    sharpeRatio: 1.1,
    sortinoRatio: 1.4,
    calmarRatio: 0.8,
    costToGrossPnlRatio: null,
    hitRatio: 0.6,
    expectancy: 5,
    maxDrawdownDurationPeriods: 3,
    completedTradeCount: 0,
    zeroCostAssumption: true,
  }),
  ["No completed trade lifecycle", "Zero-cost assumption active"],
);
