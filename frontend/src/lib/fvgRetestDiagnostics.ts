import type { BacktestRunDetailResponse, BacktestTrade } from "../types/api";
import { asRecord, firstRecord, scalar, type AnyRecord } from "./valueUtils";

export type FvgRetestDiagnosticRow = {
  label: string;
  value: string;
};

export type FvgRetestDiagnosticsModel = {
  hasMetadata: boolean;
  summaryRows: FvgRetestDiagnosticRow[];
  trendRows: FvgRetestDiagnosticRow[];
  fibonacciRows: FvgRetestDiagnosticRow[];
  liquidityRows: FvgRetestDiagnosticRow[];
  entryRows: FvgRetestDiagnosticRow[];
  stopRows: FvgRetestDiagnosticRow[];
  caveats: string[];
  raw: {
    diagnostics: AnyRecord | null;
    tradeMetadata: AnyRecord | null;
  };
};

export function buildFvgRetestDiagnosticsModel(detail: BacktestRunDetailResponse): FvgRetestDiagnosticsModel {
  const summaryMetadata = asRecord(detail.summary.metadata);
  const diagnosticsSummary = asRecord(detail.diagnostics?.summary);
  const diagnostics = firstRecord(summaryMetadata?.fvg_retest_v2, diagnosticsSummary?.fvg_retest_v2);
  const settings = asRecord(diagnostics?.settings) ?? asRecord(detail.strategy_config.parameters?.fvg_v2);
  const trendSettings = asRecord(settings?.trend_score);
  const fibSettings = asRecord(settings?.fibonacci_confluence);
  const liquiditySettings = asRecord(settings?.liquidity_targets);
  const counts = asRecord(diagnostics?.counts);
  const trade = firstFvgTrade(detail.trades);
  const tradeMetadata = asRecord(trade?.metadata);
  const entryPolicy = asRecord(tradeMetadata?.pattern_entry_policy);
  const targetSemantics = asRecord(tradeMetadata?.target_semantics);
  const trendMetadata = asRecord(tradeMetadata?.mtf_trend_metadata);
  const fibMetadata = asRecord(tradeMetadata?.fib_metadata);
  const riskPlanAtrMetadata = asRecord(tradeMetadata?.risk_plan_atr_metadata);
  const atrMetadata = asRecord(tradeMetadata?.atr_metadata);
  const stopMetadata = asRecord(riskPlanAtrMetadata?.fvg_stop_mode) ?? asRecord(atrMetadata?.fvg_stop_mode);

  const summaryRows = compactRows([
    row("Schema", text(diagnostics?.schema_version)),
    row("Enabled", scalar(settings?.enabled)),
    row("Scope", text(diagnostics?.experimental_scope) ?? text(settings?.experimental_scope)),
    row("Entry Trigger", text(diagnostics?.entry_trigger) ?? text(settings?.entry_trigger) ?? text(entryPolicy?.entry_trigger) ?? text(tradeMetadata?.entry_trigger)),
    row("Stop Mode", text(diagnostics?.stop_mode) ?? text(settings?.stop_mode) ?? text(stopMetadata?.stop_mode)),
    row("Filled Entries", scalar(counts?.filled_entry_count)),
    row("Skipped Entries", scalar(counts?.skipped_entry_count)),
  ]);

  const trendRows = compactRows([
    row("Trend Filter Enabled", scalar(trendSettings?.enabled)),
    row("Signed Score", scalar(tradeMetadata?.mtf_trend_score)),
    row("Direction", text(tradeMetadata?.mtf_trend_direction)),
    row("Aligned", scalar(tradeMetadata?.mtf_trend_aligned)),
    row("Fast EMA", scalar(trendSettings?.fast_period)),
    row("Slow EMA", scalar(trendSettings?.slow_period)),
    row("Weights", weightsText(asRecord(trendSettings?.weights))),
    row("Minimum Bullish Score", scalar(trendSettings?.minimum_bullish_trend_score)),
    row("Trend Metadata Schema", text(trendMetadata?.schema_version)),
  ]);

  const fibonacciRows = compactRows([
    row("Fib Filter Enabled", scalar(fibSettings?.enabled)),
    row("Confluence Pass", scalar(tradeMetadata?.fib_confluence_pass)),
    row("Retracement Level", scalar(tradeMetadata?.fib_retracement_level)),
    row("Anchor Method", text(fibMetadata?.anchor_method)),
    row("Overlap Mode", text(fibMetadata?.overlap_mode)),
    row("Band Min", scalar(fibMetadata?.band_min_level)),
    row("Band Max", scalar(fibMetadata?.band_max_level)),
    row("Fib Metadata Schema", text(fibMetadata?.schema_version)),
  ]);

  const liquidityRows = compactRows([
    row("Liquidity Target Required", scalar(liquiditySettings?.require_liquidity_target)),
    row("Risk Targets", targetListText(targetSemantics?.risk_targets)),
    row("Structural Targets", targetListText(targetSemantics?.structural_targets)),
    row("Target Schema", text(targetSemantics?.schema_version)),
  ]);

  const entryRows = compactRows([
    row("Entry Status", text(entryPolicy?.entry_status) ?? text(tradeMetadata?.entry_status)),
    row("Entry Mode", text(entryPolicy?.entry_mode) ?? text(tradeMetadata?.entry_mode)),
    row("Fill Source", text(entryPolicy?.fill_price_source) ?? text(tradeMetadata?.fill_price_source)),
    row("Bars Waited", scalar(entryPolicy?.bars_waited ?? tradeMetadata?.bars_waited)),
    row("Touch Index", scalar(entryPolicy?.touch_candle_index ?? tradeMetadata?.touch_candle_index)),
    row("Reaction Index", scalar(entryPolicy?.reaction_candle_index ?? tradeMetadata?.reaction_candle_index)),
    row("Reaction Timestamp", text(entryPolicy?.reaction_timestamp) ?? text(tradeMetadata?.reaction_timestamp)),
  ]);

  const stopRows = compactRows([
    row("Stop Metadata Schema", text(stopMetadata?.schema_version)),
    row("Selected Stop Mode", text(stopMetadata?.stop_mode)),
    row("Selected Stop Source", text(stopMetadata?.selected_source)),
    row("FVG Boundary Stop", scalar(stopMetadata?.fvg_boundary_stop)),
    row("Swing Stop", scalar(stopMetadata?.swing_stop)),
    row("Selected Stop", scalar(stopMetadata?.selected_stop)),
  ]);
  const hasFvgV2Evidence = Boolean(
    diagnostics
    || settings
    || tradeMetadata?.mtf_trend_metadata
    || tradeMetadata?.fib_metadata
    || tradeMetadata?.reaction_candle_index !== undefined
    || stopMetadata,
  );

  return {
    hasMetadata: hasFvgV2Evidence && (
      summaryRows.length
      + trendRows.length
      + fibonacciRows.length
      + liquidityRows.length
      + entryRows.length
      + stopRows.length
    ) > 0,
    summaryRows,
    trendRows,
    fibonacciRows,
    liquidityRows,
    entryRows,
    stopRows,
    caveats: [
      "FVG v2 diagnostics are saved-run metadata from completed-candle backtests only.",
      "Trend, Fibonacci, and liquidity fields are OHLCV-derived proxies, not order-book or live-routing evidence.",
      "This dashboard does not start backtests, place orders, access exchange accounts, or handle API keys.",
    ],
    raw: { diagnostics, tradeMetadata },
  };
}

function firstFvgTrade(trades: BacktestTrade[]): BacktestTrade | null {
  return (
    trades.find((trade) => {
      const metadata = asRecord(trade.metadata);
      return Boolean(
        metadata?.pattern_type === "FAIR_VALUE_GAP"
        || metadata?.mtf_trend_metadata
        || metadata?.fib_metadata
        || metadata?.entry_trigger
        || metadata?.pattern_entry_policy,
      );
    }) ?? null
  );
}

function targetListText(value: unknown): string | null {
  if (!Array.isArray(value) || !value.length) return null;
  const prices = value.flatMap((item) => {
    const record = asRecord(item);
    const price = record?.price ?? record?.target_price ?? item;
    const label = record?.name ? `${String(record.name)} ` : "";
    const rendered = scalar(price);
    return rendered ? [`${label}${rendered}`] : [];
  });
  return prices.length ? prices.join(", ") : null;
}

function weightsText(weights: AnyRecord | null): string | null {
  if (!weights) return null;
  const values = Object.entries(weights).flatMap(([key, value]) => {
    const rendered = scalar(value);
    return rendered ? [`${key}: ${rendered}`] : [];
  });
  return values.length ? values.join(", ") : null;
}

function row(label: string, value: string | null | undefined): FvgRetestDiagnosticRow | null {
  return value ? { label, value } : null;
}

function compactRows(rows: Array<FvgRetestDiagnosticRow | null>): FvgRetestDiagnosticRow[] {
  return rows.filter((item): item is FvgRetestDiagnosticRow => Boolean(item));
}

function text(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}
