import type { BacktestRunDetailResponse, BacktestTrade } from "../types/api";
import { asRecord, firstRecord, percent, scalar, type AnyRecord } from "./valueUtils";

export type AssumptionRow = {
  label: string;
  value: string;
};

export type ExecutionAssumptionModel = {
  hasMetadata: boolean;
  entryRows: AssumptionRow[];
  riskRows: AssumptionRow[];
  costRows: AssumptionRow[];
  intrabarRows: AssumptionRow[];
  warnings: string[];
  shortLimitation: string | null;
};

export function buildExecutionAssumptionModel(detail: BacktestRunDetailResponse): ExecutionAssumptionModel {
  const summaryMetadata = asRecord(detail.summary.metadata);
  const diagnosticsSummary = asRecord(detail.diagnostics?.summary);
  const firstEntry = firstEntryTrade(detail.trades);
  const firstExit = firstExitTrade(detail.trades);
  const entryMetadata = asRecord(firstEntry?.metadata);
  const exitMetadata = asRecord(firstExit?.metadata);
  const nestedExitMetadata = asRecord(exitMetadata?.exit_metadata);
  const entryPolicy = firstRecord(entryMetadata?.pattern_entry_policy, entryMetadata);
  const policy = firstRecord(
    detail.strategy_config.parameters?.pattern_execution_policy,
    summaryMetadata?.pattern_execution_policy,
    diagnosticsSummary?.pattern_execution_policy,
  );
  const fvgEntry = firstRecord(summaryMetadata?.fvg_entry_mode, diagnosticsSummary?.fvg_entry_mode);
  const costProfile = firstRecord(summaryMetadata?.cost_profile, diagnosticsSummary?.cost_profile);
  const costSummary = firstRecord(summaryMetadata?.cost_summary, diagnosticsSummary?.cost_summary);
  const riskAudit = firstRecord(summaryMetadata?.risk_exit_audit, diagnosticsSummary?.risk_exit_audit);
  const intrabar = asRecord(riskAudit?.intrabar_ambiguity);
  const shortEconomics = firstRecord(summaryMetadata?.short_economics, diagnosticsSummary?.short_economics);
  const hasShort = hasShortTrade(detail.trades);

  const entryRows = compactRows([
    row("Entry Mode", text(entryPolicy?.entry_mode) ?? text(policy?.selected_entry_mode) ?? text(fvgEntry?.selected_entry_mode)),
    row("Fill Assumption", text(entryPolicy?.fill_assumption)),
    row("Fill Price Source", text(entryPolicy?.fill_price_source)),
    row("Bars Waited", scalar(entryPolicy?.bars_waited)),
    row("Entry Reference", scalar(entryPolicy?.entry_reference)),
    row("Actual Fill Price", scalar(firstEntry?.price) ?? scalar(entryPolicy?.fill_price) ?? scalar(entryPolicy?.requested_price)),
    row("Requested Fill Price", scalar(entryPolicy?.requested_price)),
  ]);

  const riskRows = compactRows([
    row("Risk Plan Aligned To Fill", scalar(entryMetadata?.risk_plan_aligned_to_fill)),
    row("Original Risk Per Unit", scalar(entryMetadata?.original_risk_per_unit)),
    row("Fill-Adjusted Risk Per Unit", scalar(entryMetadata?.fill_adjusted_risk_per_unit)),
    row("Executable Risk Per Unit", scalar(entryMetadata?.risk_per_unit)),
    row("Sizing Risk Source", text(entryMetadata?.sizing_risk_source)),
    row("Original Entry Reference", scalar(entryMetadata?.original_entry_reference)),
  ]);

  const costRows = compactRows([
    row("Cost Profile", text(costProfile?.profile_key)),
    row("Profile Description", text(costProfile?.description)),
    row("Zero-Cost Assumption", scalar(costSummary?.zero_transaction_cost_assumption)),
    row("Effective Slippage Bps", scalar(firstNumber(entryMetadata, "effective_slippage_bps", exitMetadata, "effective_slippage_bps"))),
    row("Cost / Gross PnL", percent(costSummary?.cost_to_gross_pnl_ratio)),
    row("Total Cost", scalar(costSummary?.total_cost)),
  ]);

  const intrabarRows = compactRows([
    row("Intrabar Policy", text(nestedExitMetadata?.intrabar_policy) ?? text(exitMetadata?.intrabar_policy) ?? text(entryMetadata?.intrabar_policy)),
    row("Ambiguous Stop/Target Count", scalar(intrabar?.ambiguous_stop_target_count)),
    row("Ambiguous PnL Contribution", percent(intrabar?.ambiguous_stop_target_pnl_contribution_ratio)),
    row("Last Exit Ambiguous", scalar(nestedExitMetadata?.ambiguous_stop_target ?? exitMetadata?.ambiguous_stop_target)),
  ]);

  const warnings = compactText([
    booleanValue(costSummary?.zero_transaction_cost_assumption) === true
      ? text(costSummary?.zero_cost_warning) ?? "Zero-cost assumption active: fees, spread, and slippage were not charged."
      : null,
  ]);

  return {
    hasMetadata: entryRows.length + riskRows.length + costRows.length + intrabarRows.length > 0,
    entryRows,
    riskRows,
    costRows,
    intrabarRows,
    warnings,
    shortLimitation: shortLimitationText(hasShort, shortEconomics),
  };
}

function firstEntryTrade(trades: BacktestTrade[]): BacktestTrade | null {
  return trades.find((trade) => String(trade.position_signal ?? trade.signal).includes("ENTRY")) ?? null;
}

function firstExitTrade(trades: BacktestTrade[]): BacktestTrade | null {
  return trades.find((trade) => String(trade.position_signal ?? trade.signal).includes("EXIT")) ?? null;
}

function hasShortTrade(trades: BacktestTrade[]): boolean {
  return trades.some((trade) => {
    const signal = String(trade.position_signal ?? trade.signal ?? "").toUpperCase();
    const side = String(trade.position_side ?? asRecord(trade.metadata)?.position_side ?? "").toUpperCase();
    return side === "SHORT" || signal.includes("SHORT");
  });
}

function shortLimitationText(hasShort: boolean, shortEconomics: AnyRecord | null): string | null {
  if (!hasShort) return null;
  if (!shortEconomics) {
    return "Short trades are simulated accounting research only; borrow, funding, maintenance margin, and liquidation assumptions may be unavailable.";
  }
  if (booleanValue(shortEconomics.enabled) === true) {
    return "Short economics are research-only assumptions; they do not mean live margin, futures support, or exchange liquidation execution is enabled.";
  }
  return "Short trades use legacy cash-bounded simulation; borrow fees, funding, maintenance margin, and liquidation are not modeled as live exchange behavior.";
}

function firstNumber(
  first: AnyRecord | null,
  firstKey: string,
  second: AnyRecord | null,
  secondKey: string,
): number | null {
  const firstValue = numberValue(first?.[firstKey]);
  return firstValue ?? numberValue(second?.[secondKey]);
}

function row(label: string, value: string | null | undefined): AssumptionRow | null {
  return value ? { label, value } : null;
}

function compactRows(rows: Array<AssumptionRow | null>): AssumptionRow[] {
  return rows.filter((item): item is AssumptionRow => Boolean(item));
}

function compactText(values: Array<string | null | undefined>): string[] {
  return values.filter((item): item is string => Boolean(item));
}

function text(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}
