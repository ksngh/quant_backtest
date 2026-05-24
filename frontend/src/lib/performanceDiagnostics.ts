import { asRecord, booleanFrom, numberFrom, type AnyRecord } from "./valueUtils";

export type MetricTone = "good" | "bad" | "neutral";

export type MetricDefinition = {
  key: string;
  label: string;
  value: number | boolean | null;
  format: "number" | "percent" | "periods" | "boolean";
  displayValue?: string;
  helper: string;
  tone: MetricTone;
};

export type InterpretationLabel =
  | "Poor risk-adjusted return"
  | "Cost drag high"
  | "Low hit rate"
  | "Negative expectancy"
  | "Drawdown recovery weak"
  | "No completed trade lifecycle"
  | "Zero-cost assumption active";

export type PerformanceDiagnostics = {
  metrics: MetricDefinition[];
  labels: InterpretationLabel[];
  hasMetrics: boolean;
  zeroCostAssumption: boolean | null;
};

function ratioTone(value: number | null, goodAtOrAbove = 0): MetricTone {
  if (value === null) return "neutral";
  return value >= goodAtOrAbove ? "good" : "bad";
}

function drawdownTone(value: number | null): MetricTone {
  if (value === null) return "neutral";
  return value <= -0.2 ? "bad" : "neutral";
}

function positiveCostTone(value: number | null): MetricTone {
  if (value === null) return "neutral";
  return value > 0.2 ? "bad" : "neutral";
}

export function extractPerformanceDiagnostics(summaryMetadata: unknown): PerformanceDiagnostics {
  const metadata = asRecord(summaryMetadata);
  const performance = asRecord(metadata?.performance_metrics);
  const attribution = asRecord(metadata?.trade_attribution);
  const tradeMetrics = asRecord(attribution?.trade_metrics);
  const exposure = asRecord(attribution?.exposure);
  const turnover = asRecord(attribution?.turnover);
  const costSummary = asRecord(metadata?.cost_summary);

  const metrics: MetricDefinition[] = [
    {
      key: "total_return",
      label: "Total Return",
      value: numberFrom(performance, "total_return"),
      format: "percent",
      helper: "Total equity change over the saved run.",
      tone: ratioTone(numberFrom(performance, "total_return")),
    },
    {
      key: "annualized_return",
      label: "Annualized Return",
      value: numberFrom(performance, "annualized_return"),
      format: "percent",
      helper: "Run return scaled to an annual rate using the candle interval.",
      tone: ratioTone(numberFrom(performance, "annualized_return")),
    },
    {
      key: "annualized_volatility",
      label: "Annualized Volatility",
      value: numberFrom(performance, "annualized_volatility"),
      format: "percent",
      helper: "Annualized variation of period-to-period equity returns.",
      tone: "neutral",
    },
    {
      key: "sharpe_ratio",
      label: "Sharpe Ratio",
      value: numberFrom(performance, "sharpe_ratio"),
      format: "number",
      helper: "Risk-adjusted return using total volatility.",
      tone: ratioTone(numberFrom(performance, "sharpe_ratio"), 0.5),
    },
    {
      key: "sortino_ratio",
      label: "Sortino Ratio",
      value: numberFrom(performance, "sortino_ratio"),
      format: "number",
      helper: "Risk-adjusted return using downside volatility only.",
      tone: ratioTone(numberFrom(performance, "sortino_ratio"), 0.5),
    },
    {
      key: "calmar_ratio",
      label: "Calmar Ratio",
      value: numberFrom(performance, "calmar_ratio"),
      format: "number",
      helper: "Annualized return divided by absolute maximum drawdown.",
      tone: ratioTone(numberFrom(performance, "calmar_ratio"), 0.5),
    },
    {
      key: "max_drawdown",
      label: "Max Drawdown",
      value: numberFrom(performance, "max_drawdown"),
      format: "percent",
      helper: "Worst peak-to-trough equity decline in the run.",
      tone: drawdownTone(numberFrom(performance, "max_drawdown")),
    },
    {
      key: "max_drawdown_duration_periods",
      label: "Max Drawdown Duration",
      value: numberFrom(performance, "max_drawdown_duration_periods"),
      format: "periods",
      helper: "Longest number of candle periods spent below the prior equity peak.",
      tone: numberFrom(performance, "max_drawdown_duration_periods") && numberFrom(performance, "max_drawdown_duration_periods")! > 20 ? "bad" : "neutral",
    },
    {
      key: "hit_ratio",
      label: "Hit Ratio",
      value: numberFrom(tradeMetrics, "hit_ratio"),
      format: "percent",
      helper: "Share of completed trade lifecycles with positive net PnL.",
      tone: ratioTone(numberFrom(tradeMetrics, "hit_ratio"), 0.4),
    },
    {
      key: "payoff_ratio",
      label: "Payoff Ratio",
      value: numberFrom(tradeMetrics, "payoff_ratio"),
      format: "number",
      helper: "Average win divided by average loss.",
      tone: ratioTone(numberFrom(tradeMetrics, "payoff_ratio"), 1),
    },
    {
      key: "expectancy",
      label: "Expectancy",
      value: numberFrom(tradeMetrics, "expectancy"),
      format: "number",
      helper: "Average expected net PnL per completed trade lifecycle.",
      tone: ratioTone(numberFrom(tradeMetrics, "expectancy")),
    },
    {
      key: "profit_factor",
      label: "Profit Factor",
      value: booleanFrom(tradeMetrics, "profit_factor_is_infinite") ? null : numberFrom(tradeMetrics, "profit_factor"),
      format: "number",
      displayValue: booleanFrom(tradeMetrics, "profit_factor_is_infinite") ? "Infinite" : undefined,
      helper: "Gross profit divided by gross loss; unavailable when gross loss is zero.",
      tone: booleanFrom(tradeMetrics, "profit_factor_is_infinite") ? "good" : ratioTone(numberFrom(tradeMetrics, "profit_factor"), 1),
    },
    {
      key: "average_r",
      label: "Average R",
      value: numberFrom(tradeMetrics, "average_r"),
      format: "number",
      helper: "Average realized R multiple across completed trade lifecycles.",
      tone: ratioTone(numberFrom(tradeMetrics, "average_r")),
    },
    {
      key: "median_r",
      label: "Median R",
      value: numberFrom(tradeMetrics, "median_r"),
      format: "number",
      helper: "Median realized R multiple across completed trade lifecycles.",
      tone: ratioTone(numberFrom(tradeMetrics, "median_r")),
    },
    {
      key: "max_consecutive_losses",
      label: "Max Consecutive Losses",
      value: numberFrom(tradeMetrics, "max_consecutive_losses"),
      format: "number",
      helper: "Longest streak of losing completed trade lifecycles.",
      tone: numberFrom(tradeMetrics, "max_consecutive_losses") && numberFrom(tradeMetrics, "max_consecutive_losses")! >= 3 ? "bad" : "neutral",
    },
    {
      key: "exposure_fraction",
      label: "Exposure Fraction",
      value: numberFrom(exposure, "exposure_fraction"),
      format: "percent",
      helper: "Share of graph points with a non-zero position.",
      tone: "neutral",
    },
    {
      key: "turnover_ratio",
      label: "Turnover Ratio",
      value: numberFrom(turnover, "turnover_ratio"),
      format: "number",
      helper: "Total filled notional divided by initial equity.",
      tone: "neutral",
    },
    {
      key: "cost_to_gross_pnl_ratio",
      label: "Cost / Gross PnL",
      value: numberFrom(costSummary, "cost_to_gross_pnl_ratio"),
      format: "percent",
      helper: "Fees, spread, and slippage as a share of absolute gross PnL.",
      tone: positiveCostTone(numberFrom(costSummary, "cost_to_gross_pnl_ratio")),
    },
    {
      key: "zero_transaction_cost_assumption",
      label: "Zero-Cost Assumption",
      value: booleanFrom(costSummary, "zero_transaction_cost_assumption"),
      format: "boolean",
      helper: "Whether this run assumed no fees, spread, or slippage.",
      tone: booleanFrom(costSummary, "zero_transaction_cost_assumption") ? "bad" : "neutral",
    },
  ];

  const labels = classifyPerformanceDiagnostics({
    sharpeRatio: numberFrom(performance, "sharpe_ratio"),
    sortinoRatio: numberFrom(performance, "sortino_ratio"),
    calmarRatio: numberFrom(performance, "calmar_ratio"),
    costToGrossPnlRatio: numberFrom(costSummary, "cost_to_gross_pnl_ratio"),
    hitRatio: numberFrom(tradeMetrics, "hit_ratio"),
    expectancy: numberFrom(tradeMetrics, "expectancy"),
    maxDrawdownDurationPeriods: numberFrom(performance, "max_drawdown_duration_periods"),
    completedTradeCount: numberFrom(tradeMetrics, "completed_trade_count"),
    zeroCostAssumption: booleanFrom(costSummary, "zero_transaction_cost_assumption"),
  });

  return {
    metrics,
    labels,
    hasMetrics: metrics.some((metric) => metric.value !== null),
    zeroCostAssumption: booleanFrom(costSummary, "zero_transaction_cost_assumption"),
  };
}

export function classifyPerformanceDiagnostics(values: {
  sharpeRatio: number | null;
  sortinoRatio: number | null;
  calmarRatio: number | null;
  costToGrossPnlRatio: number | null;
  hitRatio: number | null;
  expectancy: number | null;
  maxDrawdownDurationPeriods: number | null;
  completedTradeCount: number | null;
  zeroCostAssumption: boolean | null;
}): InterpretationLabel[] {
  const labels: InterpretationLabel[] = [];
  if (
    (values.sharpeRatio !== null && values.sharpeRatio < 0.5)
    || (values.sortinoRatio !== null && values.sortinoRatio < 0.5)
    || (values.calmarRatio !== null && values.calmarRatio < 0)
  ) {
    labels.push("Poor risk-adjusted return");
  }
  if (values.costToGrossPnlRatio !== null && values.costToGrossPnlRatio > 0.2) {
    labels.push("Cost drag high");
  }
  if (values.hitRatio !== null && values.hitRatio < 0.4) {
    labels.push("Low hit rate");
  }
  if (values.expectancy !== null && values.expectancy < 0) {
    labels.push("Negative expectancy");
  }
  if (values.maxDrawdownDurationPeriods !== null && values.maxDrawdownDurationPeriods > 20) {
    labels.push("Drawdown recovery weak");
  }
  if (values.completedTradeCount !== null && values.completedTradeCount === 0) {
    labels.push("No completed trade lifecycle");
  }
  if (values.zeroCostAssumption === true) {
    labels.push("Zero-cost assumption active");
  }
  return labels;
}
