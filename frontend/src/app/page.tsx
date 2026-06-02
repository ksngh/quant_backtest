"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import type { PointerEvent, ReactNode } from "react";

import { getBacktestRun, getHealth, listBacktestRuns } from "../lib/api";
import { buildChartSamplingNotice } from "../lib/chartSampling";
import { buildExecutionAssumptionModel } from "../lib/executionAssumptions";
import {
  buildFvgChannelOverlays,
  channelOverlayValues,
  projectChannelSegments,
  type FvgChannelOverlayModel,
} from "../lib/fvgChannelOverlay";
import { configuredStartingCash, hasStartingCashMismatch, listItemStartingCash } from "../lib/runDisplay";
import { buildFvgRetestDiagnosticsModel } from "../lib/fvgRetestDiagnostics";
import { extractPerformanceDiagnostics, type MetricDefinition } from "../lib/performanceDiagnostics";
import { buildPatternGeometryModel, type PatternScoreComponent } from "../lib/patternGeometry";
import { buildResearchReportPreview } from "../lib/researchReport";
import { buildRunConclusionModel } from "../lib/runConclusion";
import { buildStrategyExplanationModel } from "../lib/strategyExplanation";
import type {
  BacktestGraphPoint,
  BacktestRunDetailResponse,
  BacktestRunListFilters,
  BacktestRunListItem,
  BacktestTrade,
  HealthResponse,
} from "../types/api";

type AnyRecord = Record<string, unknown>;

function asRecord(value: unknown): AnyRecord | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as AnyRecord) : null;
}

function fmtNum(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return value.toLocaleString(undefined, { maximumFractionDigits: 6 });
}

function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return `${(value * 100).toFixed(3)}%`;
}

function fmtTime(value: string | null): string {
  return value ?? "-";
}

function fmtDurationMs(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  if (value < 1000) return `${value.toFixed(0)} ms`;
  const seconds = value / 1000;
  if (seconds < 60) return `${seconds.toFixed(2)} s`;
  const minutes = Math.floor(seconds / 60);
  const remSeconds = seconds % 60;
  return `${minutes}m ${remSeconds.toFixed(1)}s`;
}

function labelize(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function scalarText(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number") return fmtNum(value);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    const items = value
      .filter((item) => item !== null && item !== undefined && item !== "")
      .map((item) => (typeof item === "object" ? JSON.stringify(item) : String(item)));
    return items.length ? items.join(", ") : null;
  }
  return null;
}

function valueNum(record: AnyRecord | null | undefined, key: string): number | undefined {
  const value = record?.[key];
  return typeof value === "number" ? value : undefined;
}

function valueText(record: AnyRecord | null | undefined, key: string): string | undefined {
  const value = record?.[key];
  return typeof value === "string" ? value : undefined;
}

function listText(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item) => item !== null && item !== undefined).map((item) => String(item))
    : [];
}

function getRuntimeBreakdown(detail: BacktestRunDetailResponse | null) {
  const runtime = detail?.run.metadata?.runtime;
  return asRecord(runtime);
}

function accountState(summaryMetadata: AnyRecord | null | undefined) {
  return asRecord(summaryMetadata?.account_state);
}

function tradeFreeCash(trade: BacktestTrade): number | undefined {
  return trade.free_cash_after ?? valueNum(trade.metadata, "free_cash_after");
}

function tradeBuyingPower(trade: BacktestTrade): number | undefined {
  return trade.available_buying_power_after ?? valueNum(trade.metadata, "available_buying_power_after") ?? tradeFreeCash(trade);
}

function tradeCashBalance(trade: BacktestTrade): number | undefined {
  return trade.cash_balance_after ?? valueNum(trade.metadata, "cash_balance_after") ?? trade.cash_after;
}

function tradePositionSignal(trade: BacktestTrade): string {
  return trade.position_signal ?? valueText(trade.metadata, "position_signal") ?? trade.signal;
}

function tradeExecutionSide(trade: BacktestTrade): string {
  return trade.execution_side ?? valueText(trade.metadata, "execution_side") ?? valueText(trade.metadata, "side") ?? "-";
}

function tradeEquity(trade: BacktestTrade): number | undefined {
  const signal = tradePositionSignal(trade);
  if (signal.includes("ENTRY")) {
    return trade.execution_equity_after ?? valueNum(trade.metadata, "execution_equity_after");
  }
  return (
    trade.mark_to_market_equity_after
    ?? valueNum(trade.metadata, "mark_to_market_equity_after")
    ?? trade.execution_equity_after
    ?? valueNum(trade.metadata, "execution_equity_after")
  );
}

function tradePnl(trade: BacktestTrade): number | undefined {
  return valueNum(trade.metadata, "net_pnl") ?? valueNum(trade.metadata, "gross_pnl");
}

function tradeRawPrice(trade: BacktestTrade): number | undefined {
  return trade.raw_price ?? valueNum(trade.metadata, "raw_price") ?? trade.price;
}

function tradeEffectivePrice(trade: BacktestTrade): number | undefined {
  return trade.effective_price ?? valueNum(trade.metadata, "effective_price");
}

function tradeCostBreakdown(trade: BacktestTrade): AnyRecord | null {
  return asRecord(trade.cost_breakdown) ?? asRecord(asRecord(trade.metadata)?.cost_breakdown);
}

function tradeCost(trade: BacktestTrade, key: string): number | undefined {
  return valueNum(tradeCostBreakdown(trade), key) ?? valueNum(trade.metadata, key);
}

function signalClass(signal: string): string {
  if (signal.includes("LONG") && signal.includes("ENTRY")) return "signal long-entry";
  if (signal.includes("LONG")) return "signal long-exit";
  if (signal.includes("SHORT") && signal.includes("ENTRY")) return "signal short-entry";
  if (signal.includes("SHORT")) return "signal short-exit";
  return "signal legacy";
}

function markerColor(signal: string): string {
  if (signal.includes("LONG") && signal.includes("ENTRY")) return "#16a34a";
  if (signal.includes("LONG")) return "#0f766e";
  if (signal.includes("SHORT") && signal.includes("ENTRY")) return "#dc2626";
  if (signal.includes("SHORT")) return "#7c3aed";
  return "#64748b";
}

function parameterRows(value: unknown, prefix = ""): { label: string; value: string }[] {
  const record = asRecord(value);
  if (!record) return [];
  return Object.entries(record).flatMap(([key, item]) => {
    if (item === null || item === undefined || item === "") return [];
    const label = prefix ? `${labelize(prefix)} / ${labelize(key)}` : labelize(key);
    const nested = asRecord(item);
    if (nested) return parameterRows(nested, prefix ? `${prefix}.${key}` : key);
    const text = scalarText(item);
    return text ? [{ label, value: text }] : [];
  });
}

type RunFilterDraft = {
  source: string;
  symbol: string;
  interval: string;
  strategy_key: string;
  actual_start_time: string;
  actual_end_time: string;
  created_start_time: string;
  created_end_time: string;
  min_total_return: string;
  max_total_return: string;
  cost_profile: string;
  limit: string;
};

const emptyFilterDraft: RunFilterDraft = {
  source: "",
  symbol: "",
  interval: "",
  strategy_key: "",
  actual_start_time: "",
  actual_end_time: "",
  created_start_time: "",
  created_end_time: "",
  min_total_return: "",
  max_total_return: "",
  cost_profile: "",
  limit: "20",
};

function cleanText(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

function cleanNumber(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function draftToFilters(draft: RunFilterDraft): BacktestRunListFilters {
  return {
    source: cleanText(draft.source),
    symbol: cleanText(draft.symbol),
    interval: cleanText(draft.interval),
    strategy_key: cleanText(draft.strategy_key),
    actual_start_time: cleanText(draft.actual_start_time),
    actual_end_time: cleanText(draft.actual_end_time),
    created_start_time: cleanText(draft.created_start_time),
    created_end_time: cleanText(draft.created_end_time),
    min_total_return: cleanNumber(draft.min_total_return),
    max_total_return: cleanNumber(draft.max_total_return),
    cost_profile: cleanText(draft.cost_profile),
    limit: cleanNumber(draft.limit) ?? 20,
  };
}

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="section-header">
      <h2>{title}</h2>
      {subtitle && <p>{subtitle}</p>}
    </div>
  );
}

function PanelGroupDisclosure({
  title,
  subtitle,
  children,
  defaultOpen = false,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details className="panel-group-disclosure" open={defaultOpen}>
      <summary>
        <span>{title}</span>
        {subtitle && <small>{subtitle}</small>}
      </summary>
      <div className="panel-group-body">{children}</div>
    </details>
  );
}

function MetricCard({
  label,
  value,
  tone,
  helper,
}: {
  label: string;
  value: string;
  tone?: "good" | "bad" | "neutral";
  helper?: string;
}) {
  return (
    <div className={`metric-card ${tone ?? "neutral"}`} title={helper}>
      <span>{label}</span>
      <strong>{value}</strong>
      {helper && <small>{helper}</small>}
    </div>
  );
}

function KeyValueGrid({ rows }: { rows: { label: string; value: string }[] }) {
  if (!rows.length) return <p className="muted">No values available.</p>;
  return (
    <div className="kv-grid">
      {rows.map((row) => (
        <div className="kv-row" key={`${row.label}-${row.value}`}>
          <span>{row.label}</span>
          <strong>{row.value}</strong>
        </div>
      ))}
    </div>
  );
}

function CompactList({ items }: { items: string[] }) {
  if (!items.length) return <p className="muted">No values available.</p>;
  return (
    <ul className="compact-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

function RunSelector({
  runs,
  selectedId,
  onSelect,
}: {
  runs: BacktestRunListItem[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  if (!runs.length) return <p className="muted">No completed runs found.</p>;
  return (
    <div className="run-list">
      {runs.map((run) => (
        <button
          className={`run-item ${selectedId === run.id ? "selected" : ""}`}
          key={run.id}
          onClick={() => onSelect(run.id)}
          type="button"
        >
          <span className="run-title">{run.strategy.name}</span>
          <span className="run-meta">
            #{run.id} / {run.market.symbol} / {run.market.interval} / {run.market.candle_count} candles
          </span>
          {listItemStartingCash(run) !== null && (
            <span className="run-meta">Start cash {fmtNum(listItemStartingCash(run))}</span>
          )}
          <span className={run.summary.total_return >= 0 ? "return good" : "return bad"}>
            {fmtPct(run.summary.total_return)}
          </span>
        </button>
      ))}
    </div>
  );
}

function RunFilters({
  draft,
  loading,
  onApply,
  onChange,
  onReset,
}: {
  draft: RunFilterDraft;
  loading: boolean;
  onApply: () => void;
  onChange: (draft: RunFilterDraft) => void;
  onReset: () => void;
}) {
  const setField = (key: keyof RunFilterDraft, value: string) => onChange({ ...draft, [key]: value });
  return (
    <form
      className="run-filter-form"
      onSubmit={(event) => {
        event.preventDefault();
        onApply();
      }}
    >
      <div className="run-filter-grid">
        <label>
          Symbol
          <input placeholder="BTCUSDT" value={draft.symbol} onChange={(event) => setField("symbol", event.target.value)} />
        </label>
        <label>
          Interval
          <input placeholder="1m" value={draft.interval} onChange={(event) => setField("interval", event.target.value)} />
        </label>
        <label>
          Source
          <input placeholder="binance_spot" value={draft.source} onChange={(event) => setField("source", event.target.value)} />
        </label>
        <label>
          Strategy
          <input placeholder="pattern_strategy" value={draft.strategy_key} onChange={(event) => setField("strategy_key", event.target.value)} />
        </label>
        <label>
          Cost Profile
          <input placeholder="conservative_crypto_1m" value={draft.cost_profile} onChange={(event) => setField("cost_profile", event.target.value)} />
        </label>
        <label>
          Limit
          <input min={1} max={100} type="number" value={draft.limit} onChange={(event) => setField("limit", event.target.value)} />
        </label>
        <label>
          Actual From
          <input placeholder="2026-05-20T00:00:00Z" value={draft.actual_start_time} onChange={(event) => setField("actual_start_time", event.target.value)} />
        </label>
        <label>
          Actual To
          <input placeholder="2026-05-21T00:00:00Z" value={draft.actual_end_time} onChange={(event) => setField("actual_end_time", event.target.value)} />
        </label>
        <label>
          Created From
          <input placeholder="2026-05-20T00:00:00Z" value={draft.created_start_time} onChange={(event) => setField("created_start_time", event.target.value)} />
        </label>
        <label>
          Created To
          <input placeholder="2026-05-28T00:00:00Z" value={draft.created_end_time} onChange={(event) => setField("created_end_time", event.target.value)} />
        </label>
        <label>
          Min Return
          <input placeholder="-0.05" value={draft.min_total_return} onChange={(event) => setField("min_total_return", event.target.value)} />
        </label>
        <label>
          Max Return
          <input placeholder="0.05" value={draft.max_total_return} onChange={(event) => setField("max_total_return", event.target.value)} />
        </label>
      </div>
      <div className="filter-actions">
        <button className="small-button primary" disabled={loading} type="submit">
          Apply
        </button>
        <button className="small-button" disabled={loading} onClick={onReset} type="button">
          Reset
        </button>
      </div>
    </form>
  );
}

function Chart({
  title,
  points,
  valueKey,
  trades,
  startingValue,
  color,
  channelOverlays,
}: {
  title: string;
  points: BacktestGraphPoint[];
  valueKey: "close_price" | "equity";
  trades?: BacktestTrade[];
  startingValue?: number;
  color: string;
  channelOverlays?: FvgChannelOverlayModel[];
}) {
  const [viewStart, setViewStart] = useState(0);
  const [viewEnd, setViewEnd] = useState(Math.max(points.length - 1, 0));
  const [dragStartIndex, setDragStartIndex] = useState<number | null>(null);
  const [dragCurrentIndex, setDragCurrentIndex] = useState<number | null>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  useEffect(() => {
    setViewStart(0);
    setViewEnd(Math.max(points.length - 1, 0));
    setHoverIndex(null);
    setDragStartIndex(null);
    setDragCurrentIndex(null);
  }, [points.length]);

  const maxIndex = Math.max(points.length - 1, 0);
  const fromIndex = Math.max(0, Math.min(viewStart, maxIndex));
  const toIndex = Math.max(fromIndex, Math.min(viewEnd, maxIndex));
  const visible = points.slice(fromIndex, toIndex + 1);
  const hoverPoint = hoverIndex === null ? null : visible[hoverIndex];

  if (!points.length || !visible.length) {
    return (
      <section className="panel">
        <SectionHeader title={title} />
        <p className="muted">No points available.</p>
      </section>
    );
  }

  const width = 960;
  const height = 300;
  const padLeft = 58;
  const padRight = 18;
  const padTop = 18;
  const padBottom = 42;
  const activeChannelOverlays = valueKey === "close_price" ? channelOverlays ?? [] : [];
  const values = visible.map((point) => point[valueKey]);
  const overlayValues = channelOverlayValues(activeChannelOverlays, fromIndex, toIndex);
  const referenceValues = startingValue === undefined ? values : [...values, startingValue];
  const min = Math.min(...referenceValues, ...overlayValues);
  const max = Math.max(...referenceValues, ...overlayValues);
  const range = max - min || 1;

  const toX = (idx: number): number =>
    padLeft + (idx / Math.max(visible.length - 1, 1)) * (width - padLeft - padRight);
  const toY = (value: number): number =>
    height - padBottom - ((value - min) / range) * (height - padTop - padBottom);

  const path = visible
    .map((point, idx) => `${idx === 0 ? "M" : "L"} ${toX(idx)} ${toY(point[valueKey])}`)
    .join(" ");
  const tickValues = [min, min + range / 2, max];
  const xTicks = [0, Math.floor((visible.length - 1) / 2), visible.length - 1].filter(
    (item, index, arr) => arr.indexOf(item) === index,
  );
  const baselineY = startingValue === undefined ? null : toY(startingValue);
  const visibleChannelSegments = projectChannelSegments(activeChannelOverlays, fromIndex, toIndex);
  const tradesByTime = new Map<string, BacktestTrade[]>();
  trades?.forEach((trade) => {
    const bucket = tradesByTime.get(trade.candle_open_time) ?? [];
    bucket.push(trade);
    tradesByTime.set(trade.candle_open_time, bucket);
  });
  const viewSize = Math.max(toIndex - fromIndex + 1, 1);
  const canZoom = points.length > 2 && viewSize > 3;
  const canReset = fromIndex > 0 || toIndex < maxIndex;
  const indexFromPointer = (event: PointerEvent<SVGSVGElement>): number => {
    const rect = event.currentTarget.getBoundingClientRect();
    const svgX = ((event.clientX - rect.left) / Math.max(rect.width, 1)) * width;
    const plotWidth = width - padLeft - padRight;
    const ratio = Math.max(0, Math.min(1, (svgX - padLeft) / Math.max(plotWidth, 1)));
    return Math.max(fromIndex, Math.min(toIndex, fromIndex + Math.round(ratio * (visible.length - 1))));
  };
  const setHoverFromGlobalIndex = (index: number) => setHoverIndex(Math.max(0, Math.min(visible.length - 1, index - fromIndex)));
  const resetRange = () => {
    setViewStart(0);
    setViewEnd(maxIndex);
    setHoverIndex(null);
  };
  const zoomByFactor = (factor: number) => {
    const nextSize = Math.max(3, Math.min(points.length, Math.round(viewSize * factor)));
    const center = Math.round((fromIndex + toIndex) / 2);
    const nextStart = Math.max(0, Math.min(maxIndex - nextSize + 1, center - Math.floor(nextSize / 2)));
    setViewStart(nextStart);
    setViewEnd(Math.min(maxIndex, nextStart + nextSize - 1));
    setHoverIndex(null);
  };
  const panBy = (delta: number) => {
    const nextStart = Math.max(0, Math.min(maxIndex - viewSize + 1, fromIndex + delta));
    setViewStart(nextStart);
    setViewEnd(Math.min(maxIndex, nextStart + viewSize - 1));
    setHoverIndex(null);
  };
  const dragSelection =
    dragStartIndex !== null && dragCurrentIndex !== null && Math.abs(dragCurrentIndex - dragStartIndex) >= 1
      ? {
          start: Math.min(dragStartIndex, dragCurrentIndex) - fromIndex,
          end: Math.max(dragStartIndex, dragCurrentIndex) - fromIndex,
        }
      : null;

  return (
    <section className="panel chart-panel">
      <div className="chart-heading">
        <SectionHeader title={title} subtitle={`${fmtNum(min)} to ${fmtNum(max)}`} />
        <button
          className="small-button"
          disabled={!canReset}
          onClick={resetRange}
          type="button"
        >
          Reset
        </button>
      </div>
      <svg
        className="chart"
        onPointerCancel={() => {
          setDragStartIndex(null);
          setDragCurrentIndex(null);
        }}
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture(event.pointerId);
          const index = indexFromPointer(event);
          setDragStartIndex(index);
          setDragCurrentIndex(index);
          setHoverFromGlobalIndex(index);
        }}
        onPointerLeave={() => {
          if (dragStartIndex === null) setHoverIndex(null);
        }}
        onPointerMove={(event) => {
          const index = indexFromPointer(event);
          setHoverFromGlobalIndex(index);
          if (dragStartIndex !== null) setDragCurrentIndex(index);
        }}
        onPointerUp={(event) => {
          const index = indexFromPointer(event);
          if (dragStartIndex !== null && Math.abs(index - dragStartIndex) >= 2) {
            setViewStart(Math.min(index, dragStartIndex));
            setViewEnd(Math.max(index, dragStartIndex));
            setHoverIndex(null);
          }
          setDragStartIndex(null);
          setDragCurrentIndex(null);
        }}
        viewBox={`0 0 ${width} ${height}`}
      >
        <rect className="plot-bg" x={padLeft} y={padTop} width={width - padLeft - padRight} height={height - padTop - padBottom} />
        {tickValues.map((tick) => (
          <g key={`y-${tick}`}>
            <line className="grid-line" x1={padLeft} x2={width - padRight} y1={toY(tick)} y2={toY(tick)} />
            <text className="axis-label" x={8} y={toY(tick) + 4}>
              {fmtNum(tick)}
            </text>
          </g>
        ))}
        {xTicks.map((idx) => (
          <text className="axis-label" key={`x-${idx}`} x={toX(idx)} y={height - 14} textAnchor="middle">
            {visible[idx]?.candle_open_time?.slice(0, 16).replace("T", " ") ?? "-"}
          </text>
        ))}
        {baselineY !== null && (
          <g>
            <line className="baseline" x1={padLeft} x2={width - padRight} y1={baselineY} y2={baselineY} />
            <text className="baseline-label" x={width - padRight - 96} y={baselineY - 6}>
              start equity
            </text>
          </g>
        )}
        {visibleChannelSegments.length > 0 && (
          <g className="channel-overlay">
            {visibleChannelSegments.map((segment, segmentIndex) => (
              <g key={`${segment.overlay.channelId ?? "channel"}-${segment.overlay.segmentStartIndex}-${segmentIndex}`}>
                <line
                  className="channel-line lower"
                  x1={toX(segment.lowerLine.x1Index - fromIndex)}
                  x2={toX(segment.lowerLine.x2Index - fromIndex)}
                  y1={toY(segment.lowerLine.y1)}
                  y2={toY(segment.lowerLine.y2)}
                />
                <line
                  className="channel-line upper"
                  x1={toX(segment.upperLine.x1Index - fromIndex)}
                  x2={toX(segment.upperLine.x2Index - fromIndex)}
                  y1={toY(segment.upperLine.y1)}
                  y2={toY(segment.upperLine.y2)}
                />
                {segment.points.map((point, index) => (
                  <g className={`channel-point ${point.kind}`} key={`${point.kind}-${point.index}-${index}`}>
                    <circle cx={toX(point.index - fromIndex)} cy={toY(point.price)} r={point.kind === "entry" || point.kind === "exit" ? 5 : 4} />
                    <text x={toX(point.index - fromIndex) + 7} y={toY(point.price) - 7}>
                      {point.label}
                    </text>
                  </g>
                ))}
              </g>
            ))}
          </g>
        )}
        <path className="line" d={path} stroke={color} />
        {dragSelection && (
          <rect
            className="drag-selection"
            x={toX(dragSelection.start)}
            y={padTop}
            width={Math.max(2, toX(dragSelection.end) - toX(dragSelection.start))}
            height={height - padTop - padBottom}
          />
        )}
        {trades &&
          visible.map((point, idx) => {
            const signal = point.position_signal ?? point.signal;
            if (!signal) return null;
            const trade = tradesByTime.get(point.candle_open_time)?.[0];
            const markerSignal = trade ? tradePositionSignal(trade) : signal;
            return (
              <circle
                className="trade-marker"
                cx={toX(idx)}
                cy={toY(point[valueKey])}
                fill={markerColor(markerSignal)}
                key={`${point.id}-${point.sequence}`}
                r={4.5}
              >
                <title>
                  {`${point.candle_open_time}\n${markerSignal}\nexecution: ${
                    trade ? tradeExecutionSide(trade) : point.execution_side ?? "-"
                  }\nfree cash: ${fmtNum(trade ? tradeFreeCash(trade) : undefined)}\nequity: ${fmtNum(point.equity)}`}
                </title>
              </circle>
            );
          })}
        {hoverPoint && hoverIndex !== null && (
          <g>
            <line className="crosshair" x1={toX(hoverIndex)} x2={toX(hoverIndex)} y1={padTop} y2={height - padBottom} />
            <circle cx={toX(hoverIndex)} cy={toY(hoverPoint[valueKey])} fill={color} r={4} />
          </g>
        )}
      </svg>
      <div className="chart-controls">
        <button className="small-button" disabled={fromIndex === 0} onClick={() => panBy(-Math.max(1, Math.floor(viewSize / 3)))} type="button">
          Pan Left
        </button>
        <button className="small-button" disabled={!canZoom} onClick={() => zoomByFactor(0.5)} type="button">
          Zoom In
        </button>
        <button className="small-button" disabled={!canReset} onClick={() => zoomByFactor(2)} type="button">
          Zoom Out
        </button>
        <button className="small-button" disabled={toIndex >= maxIndex} onClick={() => panBy(Math.max(1, Math.floor(viewSize / 3)))} type="button">
          Pan Right
        </button>
        <span className="muted">
          Drag over the chart to zoom: {fmtTime(visible[0]?.candle_open_time ?? null)} to {fmtTime(visible[visible.length - 1]?.candle_open_time ?? null)}
        </span>
        {activeChannelOverlays.length > 0 && (
          <span className="muted">
            FVG channels: {activeChannelOverlays.length} bounded segment{activeChannelOverlays.length === 1 ? "" : "s"}
          </span>
        )}
      </div>
      {hoverPoint && (
        <div className="hover-readout">
          <span>{fmtTime(hoverPoint.candle_open_time)}</span>
          <strong>{fmtNum(hoverPoint[valueKey])}</strong>
          <span>Equity {fmtNum(hoverPoint.equity)}</span>
          <span>Free cash {fmtNum(hoverPoint.free_cash)}</span>
        </div>
      )}
    </section>
  );
}

function StrategyExplanation({ detail }: { detail: BacktestRunDetailResponse }) {
  const model = buildStrategyExplanationModel(detail);

  return (
    <section className="panel">
      <SectionHeader title={model.title} subtitle={model.subtitle} />
      {model.fallback && (
        <p className="diagnostic-warning">
          Persisted explanation metadata is missing; this section combines static strategy knowledge with actual run metadata.
        </p>
      )}
      <div className="strategy-grid">
        <div className="info-block">
          <h3>Strategy Overview</h3>
          <KeyValueGrid rows={model.overview} />
        </div>
        <div className="info-block">
          <h3>Economic Hypothesis</h3>
          <CompactList items={model.economicHypothesis} />
        </div>
        <div className="info-block">
          <h3>Indicators Used</h3>
          <CompactList items={model.indicatorsUsed} />
        </div>
        <div className="info-block">
          <h3>Bad Performance Clues</h3>
          {model.badPerformanceClues.length ? <CompactList items={model.badPerformanceClues} /> : <p className="muted">No deterministic diagnostic clue is available for this run.</p>}
        </div>
      </div>
      <div className="rules-grid">
        <div className="rule-card">
          <h3>Risk Management Design</h3>
          <KeyValueGrid rows={model.riskManagementDesign} />
        </div>
        <div className="rule-card">
          <h3>Actual Risk Behavior</h3>
          <KeyValueGrid rows={model.actualRiskBehavior} />
        </div>
        <div className="rule-card">
          <h3>Entry Timing</h3>
          <KeyValueGrid rows={model.entryTiming} />
        </div>
        <div className="rule-card">
          <h3>Exit Timing</h3>
          <KeyValueGrid rows={model.exitTiming} />
        </div>
        <div className="rule-card">
          <h3>Known Limitations</h3>
          <CompactList items={model.knownLimitations} />
        </div>
      </div>
    </section>
  );
}

function AccountStatePanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const state = accountState(detail.summary.metadata);
  return (
    <section className="panel">
      <SectionHeader title="Account State" subtitle="Free cash and buying power are primary for open short exposure." />
      <div className="metric-grid">
        <MetricCard label="Free Cash" value={fmtNum(valueNum(state, "free_cash_after"))} />
        <MetricCard label="Buying Power" value={fmtNum(valueNum(state, "available_buying_power_after"))} />
        <MetricCard label="Cash Balance" value={fmtNum(detail.summary.ending_cash)} />
        <MetricCard label="Locked Short Proceeds" value={fmtNum(valueNum(state, "short_proceeds_locked_after"))} />
        <MetricCard label="Short Collateral" value={fmtNum(valueNum(state, "short_collateral_locked_after"))} />
        <MetricCard label="Margin Used" value={fmtNum(valueNum(state, "margin_used_after"))} />
      </div>
      {valueText(state, "cash_after_semantics") && <p className="muted">{valueText(state, "cash_after_semantics")}</p>}
    </section>
  );
}

function ExecutionAssumptionsPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const model = buildExecutionAssumptionModel(detail);

  return (
    <section className="panel">
      <SectionHeader
        title="Execution Assumptions"
        subtitle="Read-only fill, risk, cost, intrabar, and short-simulation assumptions saved with this run."
      />
      {!model.hasMetadata ? (
        <p className="muted">No execution-assumption metadata is available for this run. Legacy rows should not be interpreted as zero-cost or live-ready.</p>
      ) : (
        <>
          {model.warnings.map((warning) => (
            <p className="diagnostic-warning" key={warning}>{warning}</p>
          ))}
          {model.shortLimitation && <p className="diagnostic-warning">{model.shortLimitation}</p>}
          <div className="strategy-grid">
            <div className="info-block">
              <h3>Entry Fill</h3>
              <KeyValueGrid rows={model.entryRows} />
            </div>
            <div className="info-block">
              <h3>Risk Alignment</h3>
              <KeyValueGrid rows={model.riskRows} />
            </div>
            <div className="info-block">
              <h3>Cost Assumptions</h3>
              <KeyValueGrid rows={model.costRows} />
            </div>
            <div className="info-block">
              <h3>Intrabar Policy</h3>
              <KeyValueGrid rows={model.intrabarRows} />
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function formatMetricValue(metric: MetricDefinition): string {
  if (metric.displayValue) return metric.displayValue;
  if (metric.value === null || metric.value === undefined) return "No metric available";
  if (metric.format === "boolean") return metric.value ? "Yes" : "No";
  if (typeof metric.value !== "number") return String(metric.value);
  if (metric.format === "percent") return fmtPct(metric.value);
  if (metric.format === "periods") return `${fmtNum(metric.value)} periods`;
  return fmtNum(metric.value);
}

function PerformanceDiagnosticsPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const diagnostics = extractPerformanceDiagnostics(detail.summary.metadata);
  const costProfile = asRecord(detail.summary.metadata?.cost_profile);
  const topMetrics = diagnostics.metrics.filter((metric) =>
    [
      "total_return",
      "annualized_return",
      "annualized_volatility",
      "sharpe_ratio",
      "sortino_ratio",
      "calmar_ratio",
      "max_drawdown",
      "max_drawdown_duration_periods",
      "hit_ratio",
      "expectancy",
      "profit_factor",
      "cost_to_gross_pnl_ratio",
    ].includes(metric.key),
  );
  const secondaryMetrics = diagnostics.metrics.filter((metric) =>
    [
      "payoff_ratio",
      "average_r",
      "median_r",
      "max_consecutive_losses",
      "exposure_fraction",
      "turnover_ratio",
      "zero_transaction_cost_assumption",
    ].includes(metric.key),
  );

  return (
    <section className="panel">
      <SectionHeader
        title="Performance Diagnostics"
        subtitle="Risk-adjusted return, trade lifecycle quality, cost drag, exposure, and turnover from saved metadata."
      />
      {!diagnostics.hasMetrics ? (
        <p className="muted">No metric available for this run. Legacy runs may not include research diagnostics metadata.</p>
      ) : (
        <>
          {diagnostics.zeroCostAssumption === true && (
            <p className="diagnostic-warning">
              Zero-cost assumption active: fees, spread, and slippage were not charged, so live-like performance is likely overstated.
            </p>
          )}
          <div className="diagnostic-labels">
            {diagnostics.labels.length ? (
              diagnostics.labels.map((label) => (
                <span className="interpretation-pill" key={label}>
                  {label}
                </span>
              ))
            ) : (
              <span className="interpretation-pill neutral">No major diagnostic flag</span>
            )}
          </div>
          <div className="metric-grid diagnostics-grid">
            <MetricCard label="Cost Profile" value={String(costProfile?.profile_key ?? "Unavailable")} helper={String(costProfile?.description ?? "Named cost profile metadata is unavailable.")} />
            {topMetrics.map((metric) => (
              <MetricCard
                helper={metric.helper}
                key={metric.key}
                label={metric.label}
                tone={metric.tone}
                value={formatMetricValue(metric)}
              />
            ))}
          </div>
          <div className="diagnostic-table">
            <KeyValueGrid
              rows={secondaryMetrics.map((metric) => ({
                label: metric.label,
                value: `${formatMetricValue(metric)} - ${metric.helper}`,
              }))}
            />
          </div>
        </>
      )}
    </section>
  );
}

function RunDiagnosisPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const diagnosis = asRecord(asRecord(detail.diagnostics?.summary)?.performance_diagnostics);
  const flags = Array.isArray(diagnosis?.flags) ? diagnosis.flags.map(asRecord).filter((flag): flag is AnyRecord => Boolean(flag)) : [];
  const warnings = listText(diagnosis?.warnings);

  return (
    <section className="panel">
      <SectionHeader
        title="Run Diagnosis"
        subtitle="Deterministic forensic flags from saved metadata, trades, and graph points."
      />
      {!diagnosis ? (
        <p className="muted">No run diagnosis available.</p>
      ) : (
        <>
          <div className="diagnosis-summary">
            <MetricCard label="Highest Severity" value={String(diagnosis.highest_severity ?? "None")} tone={diagnosis.highest_severity === "CRITICAL" ? "bad" : diagnosis.highest_severity === "WARNING" ? "bad" : "neutral"} />
            <MetricCard label="Flag Count" value={fmtNum(valueNum(diagnosis, "flag_count"))} />
            <MetricCard label="Inference Strength" value={String(diagnosis.inference_strength ?? "Partial")} />
          </div>
          {warnings.length > 0 && <p className="diagnostic-warning">{warnings.join(" / ")}</p>}
          {flags.length ? (
            <div className="diagnosis-list">
              {flags.slice(0, 8).map((flag) => (
                <div className={`diagnosis-card ${String(flag.severity ?? "INFO").toLowerCase()}`} key={String(flag.code)}>
                  <div>
                    <strong>{String(flag.code)}</strong>
                    <span>{String(flag.category ?? "general")} / {String(flag.severity ?? "INFO")}</span>
                  </div>
                  <p>{String(flag.message ?? "")}</p>
                  <small>{String(flag.suggested_next_analysis ?? "")}</small>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No deterministic poor-performance flag was detected.</p>
          )}
          <details className="debug-details">
            <summary>Raw diagnosis details</summary>
            <pre>{JSON.stringify(diagnosis, null, 2)}</pre>
          </details>
        </>
      )}
    </section>
  );
}

function RunConclusionPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const conclusion = buildRunConclusionModel(detail);

  return (
    <section className="panel">
      <SectionHeader
        title="Run Conclusion"
        subtitle="Deterministic diagnosis of likely failure reasons and next analysis steps."
      />
      <div className="diagnosis-summary">
        <MetricCard label="Conclusion" value={conclusion.status.replace(/_/g, " ")} tone={conclusion.status === "weak_run" ? "bad" : "neutral"} />
        <MetricCard label="Confidence" value={conclusion.confidence} />
        <MetricCard label="Completed Trades" value={fmtNum(conclusion.completedTradeCount)} />
      </div>
      <p className={conclusion.status === "weak_run" ? "diagnostic-warning" : "muted"}>{conclusion.headline}</p>
      <div className="diagnosis-list">
        {conclusion.reasons.map((reason) => (
          <div className={`diagnosis-card ${reason.severity}`} key={`${reason.category}-${reason.title}`}>
            <div>
              <strong>{reason.title}</strong>
              <span>{reason.category} / {reason.severity}</span>
            </div>
            <p>{reason.evidence}</p>
            <small>{reason.recommendedNextAnalysis}</small>
          </div>
        ))}
      </div>
      <div className="diagnostic-table">
        <KeyValueGrid rows={conclusion.evidenceRows} />
      </div>
      <details className="debug-details">
        <summary>Raw conclusion evidence</summary>
        <pre>{JSON.stringify(conclusion.rawEvidence, null, 2)}</pre>
      </details>
    </section>
  );
}

function TimingDiagnosticsPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const timing = asRecord(asRecord(detail.diagnostics?.summary)?.timing_diagnostics ?? detail.summary.metadata?.timing_diagnostics);
  const aggregate = asRecord(timing?.aggregate);
  const flags = Array.isArray(timing?.flags) ? timing.flags.map(asRecord).filter((flag): flag is AnyRecord => Boolean(flag)) : [];
  const trades = Array.isArray(timing?.trades) ? timing.trades.map(asRecord).filter((trade): trade is AnyRecord => Boolean(trade)) : [];
  const warnings = listText(timing?.warnings);
  const codes = new Set(flags.map((flag) => String(flag.code ?? "")));
  const labels = [
    codes.has("ENTRY_WAS_LATE_CHASING") ? "Entry was late/chasing" : null,
    codes.has("EXIT_LEFT_MONEY_ON_TABLE") ? "Exit left money on table" : null,
    codes.has("IMMEDIATE_ADVERSE_EXCURSION") ? "Immediate adverse excursion" : null,
  ].filter((label): label is string => Boolean(label));

  return (
    <section className="panel">
      <SectionHeader
        title="Entry/Exit Timing"
        subtitle="MFE, MAE, entry-reference divergence, and post-entry reaction diagnostics from the saved trade path."
      />
      {!timing ? (
        <p className="muted">No timing diagnosis available.</p>
      ) : (
        <>
          <div className="metric-grid diagnostics-grid">
            <MetricCard label="Completed Trades" value={fmtNum(valueNum(timing, "completed_trade_count"))} />
            <MetricCard label="Path Mode" value={String(timing.path_mode ?? "Unknown")} helper={String(timing.partial_exit_policy ?? "")} />
            <MetricCard label="Avg MFE R" value={fmtNum(valueNum(aggregate, "average_mfe_r"))} helper="Best unrealized R multiple reached before final exit." />
            <MetricCard label="Avg MAE R" value={fmtNum(valueNum(aggregate, "average_mae_r"))} helper="Worst adverse R multiple reached before final exit." />
          </div>
          <div className="diagnostic-labels">
            {labels.length ? (
              labels.map((label) => (
                <span className="interpretation-pill" key={label}>
                  {label}
                </span>
              ))
            ) : (
              <span className="interpretation-pill neutral">No major timing flag</span>
            )}
          </div>
          {warnings.length > 0 && <p className="diagnostic-warning">{warnings.join(" / ")}</p>}
          {trades.length ? (
            <div className="timing-trade-list">
              {trades.slice(0, 6).map((trade, index) => (
                <div className="timing-trade-card" key={`${String(trade.entry_timestamp ?? "entry")}-${index}`}>
                  <strong>{String(trade.position_side ?? "Trade")} {String(trade.exit_reason ?? "exit")}</strong>
                  <span>MFE {fmtNum(valueNum(trade, "mfe_r"))}R / MAE {fmtNum(valueNum(trade, "mae_r"))}R / Realized {fmtNum(valueNum(trade, "realized_r"))}R</span>
                  <small>Bars to MFE {fmtNum(valueNum(trade, "bars_to_mfe"))}, MAE {fmtNum(valueNum(trade, "bars_to_mae"))}, exit {fmtNum(valueNum(trade, "bars_to_exit"))}</small>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No completed trade lifecycle could be matched to a price path.</p>
          )}
          <details className="debug-details">
            <summary>Raw timing details</summary>
            <pre>{JSON.stringify(timing, null, 2)}</pre>
          </details>
        </>
      )}
    </section>
  );
}

function RiskAuditPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const audit = asRecord(asRecord(detail.diagnostics?.summary)?.risk_exit_audit ?? detail.summary.metadata?.risk_exit_audit);
  const dominance = asRecord(audit?.dominance);
  const targetQuality = asRecord(audit?.target_quality);
  const partialExit = asRecord(audit?.partial_exit);
  const distribution = asRecord(audit?.exit_reason_distribution);
  const flags = Array.isArray(audit?.flags) ? audit.flags.map(asRecord).filter((flag): flag is AnyRecord => Boolean(flag)) : [];
  const rows = distribution
    ? Object.entries(distribution).map(([reason, raw]) => {
        const value = asRecord(raw);
        return {
          label: reason,
          value: `${fmtNum(valueNum(value, "count"))} exits / ${fmtPct(valueNum(value, "ratio"))} / avg R ${fmtNum(valueNum(value, "average_r"))}`,
        };
      })
    : [];

  return (
    <section className="panel">
      <SectionHeader title="Risk Management" subtitle="Configured risk design versus realized exit behavior." />
      {!audit ? (
        <p className="muted">No risk audit available.</p>
      ) : (
        <>
          <div className="metric-grid diagnostics-grid">
            <MetricCard label="Completed Exits" value={fmtNum(valueNum(audit, "completed_exit_count"))} />
            <MetricCard label="Stop Dominance" value={fmtPct(valueNum(dominance, "stop_loss_dominance_ratio"))} />
            <MetricCard label="Soft Invalidation" value={fmtPct(valueNum(dominance, "soft_invalidation_dominance_ratio"))} />
            <MetricCard label="Time Stop" value={fmtPct(valueNum(dominance, "time_stop_dominance_ratio"))} />
          </div>
          {flags.length > 0 && (
            <div className="diagnostic-labels">
              {flags.map((flag) => (
                <span className="interpretation-pill" key={String(flag.code)}>
                  {String(flag.code)}
                </span>
              ))}
            </div>
          )}
          <div className="strategy-grid">
            <div className="info-block">
              <h3>Risk Design</h3>
              <KeyValueGrid
                rows={[
                  { label: "Take-Profit Avg R", value: fmtNum(valueNum(targetQuality, "take_profit_average_r")) },
                  { label: "Hard-Stop Avg R", value: fmtNum(valueNum(targetQuality, "hard_stop_average_r")) },
                  { label: "First Target Hit Rate", value: fmtPct(valueNum(targetQuality, "first_target_hit_rate")) },
                  { label: "Final Target Hit Rate", value: fmtPct(valueNum(targetQuality, "final_target_hit_rate")) },
                  { label: "Avg Target Distance R", value: fmtNum(valueNum(targetQuality, "average_target_distance_r")) },
                  { label: "Avg Target Distance Price", value: fmtNum(valueNum(targetQuality, "average_target_distance_price")) },
                ]}
              />
            </div>
            <div className="info-block">
              <h3>Realized Outcomes</h3>
              <KeyValueGrid rows={rows} />
              <KeyValueGrid
                rows={[
                  { label: "Partial Exit PnL", value: fmtNum(valueNum(partialExit, "partial_exit_net_pnl")) },
                  { label: "Partial Contribution", value: fmtPct(valueNum(partialExit, "partial_exit_pnl_contribution_ratio")) },
                ]}
              />
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function ScoreCalibrationPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const calibration = asRecord(asRecord(detail.diagnostics?.summary)?.score_calibration ?? detail.summary.metadata?.score_calibration);
  const componentAnalysis = asRecord(calibration?.component_analysis);
  const buckets = Array.isArray(calibration?.buckets)
    ? calibration.buckets.map(asRecord).filter((bucket): bucket is AnyRecord => Boolean(bucket))
    : [];
  const thresholds = Array.isArray(calibration?.threshold_sensitivity)
    ? calibration.threshold_sensitivity.map(asRecord).filter((row): row is AnyRecord => Boolean(row))
    : [];
  const flags = Array.isArray(calibration?.flags) ? calibration.flags.map(asRecord).filter((flag): flag is AnyRecord => Boolean(flag)) : [];
  const warnings = listText(calibration?.warnings);

  return (
    <section className="panel">
      <SectionHeader
        title="Score Reliability"
        subtitle="Pattern-score calibration by realized bucket, component placeholder rate, and threshold sensitivity."
      />
      {!calibration ? (
        <p className="muted">No pattern score calibration available.</p>
      ) : (
        <>
          <div className="metric-grid diagnostics-grid">
            <MetricCard label="Scored Trades" value={`${fmtNum(valueNum(calibration, "scored_trade_count"))} / ${fmtNum(valueNum(calibration, "total_completed_trade_count"))}`} />
            <MetricCard label="Inference Strength" value={String(calibration.inference_strength ?? "Partial")} />
            <MetricCard label="Placeholder Rate" value={fmtPct(valueNum(componentAnalysis, "placeholder_component_rate"))} helper="Share of score components marked placeholder." />
            <MetricCard label="Flag Count" value={fmtNum(valueNum(calibration, "flag_count"))} />
          </div>
          {warnings.length > 0 && <p className="diagnostic-warning">{warnings.join(" / ")}</p>}
          {flags.length > 0 && (
            <div className="diagnostic-labels">
              {flags.map((flag) => (
                <span className="interpretation-pill" key={String(flag.code)}>
                  {String(flag.code)}
                </span>
              ))}
            </div>
          )}
          {buckets.length ? (
            <div className="table-wrap compact diagnostic-table">
              <table>
                <thead>
                  <tr>
                    <th>Score Bucket</th>
                    <th>Trades</th>
                    <th>Hit Rate</th>
                    <th>Avg R</th>
                    <th>Median R</th>
                    <th>Expectancy</th>
                    <th>Profit Factor</th>
                  </tr>
                </thead>
                <tbody>
                  {buckets.map((bucket) => (
                    <tr key={String(bucket.bucket)}>
                      <td>{String(bucket.bucket)}</td>
                      <td>{fmtNum(valueNum(bucket, "trade_count"))}</td>
                      <td>{fmtPct(valueNum(bucket, "hit_ratio"))}</td>
                      <td>{fmtNum(valueNum(bucket, "average_r"))}</td>
                      <td>{fmtNum(valueNum(bucket, "median_r"))}</td>
                      <td>{fmtNum(valueNum(bucket, "expectancy"))}</td>
                      <td>{bucket.profit_factor_is_infinite ? "Infinite" : fmtNum(valueNum(bucket, "profit_factor"))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="muted">No score buckets available for this run.</p>
          )}
          {thresholds.length > 0 && (
            <details className="debug-details">
              <summary>Threshold sensitivity</summary>
              <KeyValueGrid
                rows={thresholds.map((row) => ({
                  label: `Score >= ${fmtNum(valueNum(row, "minimum_pattern_score"))}`,
                  value: `${fmtNum(valueNum(row, "trade_count"))} trades / hit ${fmtPct(valueNum(row, "hit_ratio"))} / avg R ${fmtNum(valueNum(row, "average_r"))}`,
                }))}
              />
            </details>
          )}
        </>
      )}
    </section>
  );
}

function PatternGeometryPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const model = buildPatternGeometryModel(detail);

  return (
    <section className="panel">
      <SectionHeader
        title="Pattern Geometry"
        subtitle={`${model.patternType} detection fields, score components, and candidate-search diagnostics from saved metadata.`}
      />
      {!model.hasMetadata ? (
        <p className="muted">Pattern geometry and score-component metadata is not available for this run. Legacy runs should not be interpreted as having zero score or zero geometry.</p>
      ) : (
        <>
          <p className="source-note">{model.sourceTradeLabel ?? "Pattern source trade unavailable."}</p>
          <p className="diagnostic-warning">{model.scoreExplanation}</p>
          {model.candidateWarnings.map((warning) => (
            <p className="diagnostic-warning" key={warning}>{warning}</p>
          ))}
          <div className="strategy-grid">
            <div className="info-block">
              <h3>Geometry Fields</h3>
              <KeyValueGrid rows={model.geometryRows} />
            </div>
            <div className="info-block">
              <h3>Score Summary</h3>
              <KeyValueGrid rows={model.scoreRows} />
            </div>
          </div>
          <div className="score-component-grid">
            <ScoreComponentGroup components={model.observedComponents} title="Observed Components" />
            <ScoreComponentGroup components={model.placeholderComponents} title="Placeholder / Excluded Components" />
          </div>
          <details className="debug-details" open={model.candidateRows.length > 0}>
            <summary>Candidate overfit diagnostics</summary>
            <KeyValueGrid rows={model.candidateRows} />
          </details>
        </>
      )}
    </section>
  );
}

function ScoreComponentGroup({ components, title }: { components: PatternScoreComponent[]; title: string }) {
  return (
    <div className="info-block">
      <h3>{title}</h3>
      {!components.length ? (
        <p className="muted">No components available.</p>
      ) : (
        <div className="score-component-list">
          {components.map((component) => (
            <div className={`score-component ${component.isPlaceholder ? "placeholder" : "observed"}`} key={component.name}>
              <div className="score-component-heading">
                <strong>{component.name}</strong>
                <span>{component.includedInExecutableScore === null ? "Inclusion unavailable" : component.includedInExecutableScore ? "Executable score" : "Diagnostic only"}</span>
              </div>
              <KeyValueGrid
                rows={[
                  { label: "Raw Score", value: component.rawScore },
                  { label: "Weight", value: component.weight },
                  { label: "Weighted", value: component.weightedScore },
                  { label: "Source", value: component.source },
                ]}
              />
              {component.description && <p className="source-note">{component.description}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TradabilityDiagnosticsPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const attribution = asRecord(asRecord(detail.diagnostics?.summary)?.trade_attribution ?? detail.summary.metadata?.trade_attribution);
  const groups = asRecord(attribution?.attribution);
  const bySession = asRecord(groups?.by_session);
  const byLiquidity = asRecord(groups?.by_liquidity_regime);
  const bySpread = asRecord(groups?.by_spread_regime);
  const rowsFor = (record: AnyRecord | null, label: string) =>
    record
      ? Object.entries(record).map(([key, raw]) => {
          const metrics = asRecord(raw);
          return {
            label: `${label} / ${key}`,
            value: `${fmtNum(valueNum(metrics, "completed_trade_count"))} trades / expectancy ${fmtNum(valueNum(metrics, "expectancy"))} / avg R ${fmtNum(valueNum(metrics, "average_r"))}`,
          };
        })
      : [];
  const rows = [...rowsFor(bySession, "Session"), ...rowsFor(byLiquidity, "Liquidity"), ...rowsFor(bySpread, "Spread")];

  return (
    <section className="panel">
      <SectionHeader
        title="Tradability Diagnostics"
        subtitle="OHLCV-derived liquidity, range-spread, and UTC session attribution. These are proxies, not order-book spreads."
      />
      {rows.length ? (
        <div className="diagnostic-table">
          <KeyValueGrid rows={rows} />
        </div>
      ) : (
        <p className="muted">No tradability attribution is available for this run. Enable market-regime tagging on newer runs to populate liquidity, spread, and session groups.</p>
      )}
    </section>
  );
}

function FvgRetestDiagnosticsPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const model = buildFvgRetestDiagnosticsModel(detail);

  return (
    <section className="panel">
      <SectionHeader
        title="FVG Retest V2 Diagnostics"
        subtitle="Read-only trend, Fibonacci, entry-retest, liquidity-target, and stop-mode metadata from saved runs."
      />
      {!model.hasMetadata ? (
        <p className="muted">No FVG retest v2 metadata is available for this run. Baseline FVG and legacy runs remain valid with unavailable v2 fields.</p>
      ) : (
        <>
          {model.caveats.map((caveat) => (
            <p className="diagnostic-warning" key={caveat}>{caveat}</p>
          ))}
          <div className="strategy-grid">
            <div className="info-block">
              <h3>V2 Summary</h3>
              <KeyValueGrid rows={model.summaryRows} />
            </div>
            <div className="info-block">
              <h3>Trend Score</h3>
              <KeyValueGrid rows={model.trendRows} />
            </div>
            <div className="info-block">
              <h3>Fibonacci</h3>
              <KeyValueGrid rows={model.fibonacciRows} />
            </div>
            <div className="info-block">
              <h3>Liquidity Targets</h3>
              <KeyValueGrid rows={model.liquidityRows} />
            </div>
            <div className="info-block">
              <h3>Retest Entry</h3>
              <KeyValueGrid rows={model.entryRows} />
            </div>
            <div className="info-block">
              <h3>Stop Mode</h3>
              <KeyValueGrid rows={model.stopRows} />
            </div>
          </div>
          <details className="debug-details">
            <summary>Raw FVG v2 diagnostics</summary>
            <pre>{JSON.stringify(model.raw, null, 2)}</pre>
          </details>
        </>
      )}
    </section>
  );
}

function ResearchReportPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const report = asRecord(detail.research_report);
  const preview = buildResearchReportPreview(detail.research_report);
  return (
    <section className="panel">
      <SectionHeader title="Research Report" subtitle="Portable read-only JSON/markdown summary for this saved run." />
      {!preview.hasReport ? (
        <p className="muted">No research report artifact is available for this run.</p>
      ) : (
        <>
          <KeyValueGrid rows={preview.rows} />
          {preview.sections.length > 0 && (
            <div className="diagnostic-labels">
              {preview.sections.map((section) => (
                <span className="interpretation-pill neutral" key={section}>{section}</span>
              ))}
            </div>
          )}
          {preview.markdown && (
            <details className="debug-details" open>
              <summary>Markdown preview</summary>
              <pre>{preview.markdown}</pre>
            </details>
          )}
          <details className="debug-details">
            <summary>Report JSON</summary>
            <pre>{JSON.stringify(report, null, 2)}</pre>
          </details>
        </>
      )}
    </section>
  );
}

function TradeTable({ trades }: { trades: BacktestTrade[] }) {
  const [page, setPage] = useState(0);
  const [expandedTradeId, setExpandedTradeId] = useState<number | null>(null);
  const pageSize = 12;
  const pageCount = Math.max(1, Math.ceil(trades.length / pageSize));
  const pageTrades = trades.slice(page * pageSize, page * pageSize + pageSize);

  useEffect(() => {
    setPage(0);
    setExpandedTradeId(null);
  }, [trades]);

  return (
    <section className="panel">
      <div className="chart-heading">
        <SectionHeader title="Trade Review" subtitle={`${trades.length} executions`} />
        <div className="pager">
          <button className="small-button" disabled={page === 0} onClick={() => setPage((value) => Math.max(0, value - 1))} type="button">
            Prev
          </button>
          <span>
            {page + 1} / {pageCount}
          </span>
          <button
            className="small-button"
            disabled={page >= pageCount - 1}
            onClick={() => setPage((value) => Math.min(pageCount - 1, value + 1))}
            type="button"
          >
            Next
          </button>
        </div>
      </div>
      <div className="table-wrap compact">
        <table>
          <thead>
            <tr>
              <th>Seq</th>
              <th>Time</th>
              <th>Signal</th>
              <th>Exec</th>
              <th>Raw Price</th>
              <th>Effective Price</th>
              <th>Qty</th>
              <th>Total Cost</th>
              <th>Free Cash</th>
              <th>Cash Balance</th>
              <th>Equity</th>
              <th>PnL</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {pageTrades.map((trade) => {
              const signal = tradePositionSignal(trade);
              const cost = tradeCostBreakdown(trade);
              const expanded = expandedTradeId === trade.id;
              return (
                <Fragment key={trade.id}>
                  <tr>
                    <td>{trade.sequence}</td>
                    <td>{trade.candle_open_time.slice(0, 16).replace("T", " ")}</td>
                    <td>
                      <span className={signalClass(signal)}>{signal}</span>
                    </td>
                    <td>{tradeExecutionSide(trade)}</td>
                    <td>{fmtNum(tradeRawPrice(trade))}</td>
                    <td>{fmtNum(tradeEffectivePrice(trade))}</td>
                    <td>{fmtNum(trade.quantity)}</td>
                    <td>{fmtNum(tradeCost(trade, "total_cost"))}</td>
                    <td className="primary-money">{fmtNum(tradeBuyingPower(trade))}</td>
                    <td>{fmtNum(tradeCashBalance(trade))}</td>
                    <td>{fmtNum(tradeEquity(trade))}</td>
                    <td>{fmtNum(tradePnl(trade))}</td>
                    <td>
                      <button
                        className="small-button"
                        onClick={() => setExpandedTradeId(expanded ? null : trade.id)}
                        type="button"
                      >
                        {expanded ? "Hide" : "Costs"}
                      </button>
                    </td>
                  </tr>
                  {expanded && (
                    <tr className="trade-cost-row">
                      <td colSpan={13}>
                        <div className="trade-cost-detail">
                          <KeyValueGrid
                            rows={[
                              { label: "Raw Price", value: fmtNum(tradeRawPrice(trade)) },
                              { label: "Effective Price", value: fmtNum(tradeEffectivePrice(trade)) },
                              { label: "Price Semantics", value: trade.price_semantics ?? valueText(trade.metadata, "price_semantics") ?? "Unavailable" },
                              {
                                label: "Effective Price Semantics",
                                value: trade.effective_price_semantics ?? valueText(trade.metadata, "effective_price_semantics") ?? "Unavailable",
                              },
                              { label: "Fee Cost", value: fmtNum(tradeCost(trade, "fee_cost")) },
                              { label: "Spread Cost", value: fmtNum(tradeCost(trade, "spread_cost")) },
                              { label: "Slippage Cost", value: fmtNum(tradeCost(trade, "slippage_cost")) },
                              { label: "Total Cost", value: fmtNum(tradeCost(trade, "total_cost")) },
                              { label: "Fee Bps", value: fmtNum(valueNum(cost, "fee_bps")) },
                              { label: "Spread Bps", value: fmtNum(valueNum(cost, "spread_bps")) },
                              { label: "Slippage Bps", value: fmtNum(valueNum(cost, "slippage_bps")) },
                              { label: "Effective Slippage Bps", value: fmtNum(valueNum(cost, "effective_slippage_bps")) },
                              { label: "Volatility Bps", value: fmtNum(valueNum(cost, "volatility_bps")) },
                              {
                                label: "Cost Profile",
                                value:
                                  valueText(cost, "cost_profile_name")
                                  ?? valueText(cost, "profile_key")
                                  ?? valueText(cost, "profile_name")
                                  ?? valueText(cost, "name")
                                  ?? "Unavailable",
                              },
                              { label: "Currency", value: valueText(cost, "cost_currency") ?? "quote" },
                            ]}
                          />
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
      <details className="debug-details">
        <summary>Execution audit fields</summary>
        <KeyValueGrid
          rows={[
            { label: "Signal Source", value: "position_signal preferred, legacy signal fallback" },
            { label: "Cash Display", value: "free cash or buying power is primary; cash balance is audit context" },
            { label: "Execution Side", value: "BUY/SELL raw cashflow side retained separately" },
            { label: "Raw Price", value: "market-reachable fill price stored in trade.price for new runs" },
            { label: "Effective Price", value: "spread/slippage-adjusted diagnostic price; not the persisted fill price" },
          ]}
        />
      </details>
    </section>
  );
}

function ParametersPanel({ detail }: { detail: BacktestRunDetailResponse }) {
  const rows = parameterRows(detail.strategy_config.parameters).slice(0, 36);
  return (
    <section className="panel">
      <SectionHeader title="Strategy Parameters" subtitle={detail.strategy_config.version} />
      <KeyValueGrid rows={rows} />
    </section>
  );
}

function RuntimePanel({ detail, runtime }: { detail: BacktestRunDetailResponse; runtime: AnyRecord | null }) {
  const performance = asRecord(detail.summary.metadata?.performance_metrics);
  return (
    <section className="panel">
      <SectionHeader title="Run Diagnostics" subtitle={`${detail.run.engine_name} / ${detail.run.engine_version}`} />
      <div className="strategy-grid">
        <KeyValueGrid
          rows={[
            { label: "Total Runtime", value: fmtDurationMs(valueNum(runtime, "total_elapsed_ms")) },
            { label: "Load", value: fmtDurationMs(valueNum(runtime, "load_elapsed_ms")) },
            { label: "Action Build", value: fmtDurationMs(valueNum(runtime, "action_build_elapsed_ms")) },
            { label: "Engine", value: fmtDurationMs(valueNum(runtime, "engine_elapsed_ms")) },
            { label: "Persist", value: fmtDurationMs(valueNum(runtime, "persist_elapsed_ms")) },
            { label: "Interval", value: valueText(performance, "interval") ?? detail.run.market.interval },
          ]}
        />
        <KeyValueGrid
          rows={[
            { label: "Candles", value: fmtNum(detail.run.market.candle_count) },
            { label: "Source", value: detail.run.market.source },
            { label: "Actual Start", value: fmtTime(detail.run.market.actual_start_time) },
            { label: "Actual End", value: fmtTime(detail.run.market.actual_end_time) },
            { label: "Status", value: detail.run.status },
            { label: "Run ID", value: fmtNum(detail.run.id) },
          ]}
        />
      </div>
      <details className="debug-details">
        <summary>Raw metadata debug</summary>
        <pre>{JSON.stringify({ run: detail.run.metadata, result: detail.summary.metadata }, null, 2)}</pre>
      </details>
    </section>
  );
}

export default function DashboardPage() {
  const [filters, setFilters] = useState<BacktestRunListFilters>({ limit: 20 });
  const [filterDraft, setFilterDraft] = useState<RunFilterDraft>(emptyFilterDraft);
  const [runs, setRuns] = useState<BacktestRunListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<BacktestRunDetailResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    setError(null);
    setLoadingRuns(true);
    listBacktestRuns(filters)
      .then((response) => {
        setRuns(response.items);
        const selectedStillVisible = selectedId !== null && response.items.some((item) => item.id === selectedId);
        if (response.items.length > 0 && !selectedStillVisible) {
          setSelectedId(response.items[0].id);
        }
        if (response.items.length === 0) {
          setSelectedId(null);
          setDetail(null);
        }
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoadingRuns(false));
  }, [filters, selectedId]);

  useEffect(() => {
    if (selectedId === null) return;
    setError(null);
    setLoadingDetail(true);
    getBacktestRun(selectedId)
      .then(setDetail)
      .catch((err: Error) => {
        setDetail(null);
        setError(err.message);
      })
      .finally(() => setLoadingDetail(false));
  }, [selectedId]);

  const runtime = useMemo(() => getRuntimeBreakdown(detail), [detail]);
  const fvgChannelOverlays = useMemo(() => (detail ? buildFvgChannelOverlays(detail.trades, detail.graph_points) : []), [detail]);
  const startingCash = useMemo(() => (detail ? configuredStartingCash(detail) : null), [detail]);
  const allEquityZero = useMemo(
    () => Boolean(detail && detail.graph_points.length && detail.graph_points.every((point) => point.equity === 0)),
    [detail],
  );
  const chartSamplingNotice = useMemo(
    () => buildChartSamplingNotice(detail?.chart_metadata?.graph_points),
    [detail],
  );

  return (
    <main>
      <header className="app-header">
        <div>
          <p className="eyebrow">Read-only research dashboard</p>
          <h1>Backtest Analysis</h1>
        </div>
        <div className={health?.database.reachable ? "status-pill ok" : "status-pill"}>
          API {health?.status ?? "unknown"} / DB {health?.database.reachable ? "reachable" : "offline"}
        </div>
      </header>

      {error && <p className="error">API Error: {error}</p>}

      <section className="layout">
        <aside className="sidebar panel">
          <SectionHeader title="Runs" subtitle={loadingRuns ? "Loading..." : `${runs.length} loaded`} />
          <RunFilters
            draft={filterDraft}
            loading={loadingRuns}
            onApply={() => setFilters(draftToFilters(filterDraft))}
            onChange={setFilterDraft}
            onReset={() => {
              setFilterDraft(emptyFilterDraft);
              setFilters(draftToFilters(emptyFilterDraft));
            }}
          />
          <RunSelector onSelect={setSelectedId} runs={runs} selectedId={selectedId} />
        </aside>

        <div className="content">
          {loadingDetail && !detail ? (
            <section className="panel">
              <p className="muted">Loading selected run...</p>
            </section>
          ) : !detail ? (
            <section className="panel">
              <p className="muted">No run selected yet.</p>
            </section>
          ) : (
            <>
              <section className="panel">
                <SectionHeader
                  title={detail.strategy_config.name}
                  subtitle={`${detail.run.market.symbol} / ${detail.run.market.interval} / ${fmtTime(
                    detail.run.market.actual_start_time,
                  )} to ${fmtTime(detail.run.market.actual_end_time)}`}
                />
                <div className="metric-grid">
                  <MetricCard label="Final Equity" value={fmtNum(detail.summary.final_equity)} tone="neutral" />
                  <MetricCard label="Total Return" value={fmtPct(detail.summary.total_return)} tone={detail.summary.total_return >= 0 ? "good" : "bad"} />
                  <MetricCard label="Trades" value={fmtNum(detail.summary.trade_count)} />
                  <MetricCard
                    label="Starting Cash"
                    helper={hasStartingCashMismatch(detail) ? `Result summary ${fmtNum(detail.summary.starting_cash)}` : undefined}
                    value={fmtNum(startingCash)}
                  />
                  <MetricCard label="Ending Cash Balance" value={fmtNum(detail.summary.ending_cash)} />
                  <MetricCard label="Ending Position" value={fmtNum(detail.summary.ending_position)} />
                </div>
              </section>

              {detail.warnings.length > 0 && (
                <section className="panel warning">
                  <SectionHeader title="Warnings" />
                  <CompactList items={detail.warnings.map((warning) => `${warning.code}: ${warning.message}`)} />
                </section>
              )}

              {allEquityZero && <p className="error">Equity series is all zero; treat this run as placeholder-neutral.</p>}

              {chartSamplingNotice && (
                <section className="panel warning">
                  <SectionHeader title={chartSamplingNotice.title} />
                  <p className="muted">{chartSamplingNotice.detail}</p>
                  <p className={chartSamplingNotice.markerWarning ? "diagnostic-warning" : "muted"}>
                    {chartSamplingNotice.markerDetail}
                  </p>
                </section>
              )}

              <div className="chart-grid">
                <Chart
                  channelOverlays={fvgChannelOverlays}
                  color="#2563eb"
                  points={detail.graph_points}
                  title="Close Price"
                  trades={detail.trades}
                  valueKey="close_price"
                />
                <Chart
                  color="#0f766e"
                  points={detail.graph_points}
                  startingValue={startingCash ?? detail.summary.starting_cash}
                  title="Equity"
                  trades={detail.trades}
                  valueKey="equity"
                />
              </div>

              <PerformanceDiagnosticsPanel detail={detail} />
              <RunConclusionPanel detail={detail} />

              <PanelGroupDisclosure title="Run Diagnostics" subtitle="Diagnosis flags and score calibration">
                <RunDiagnosisPanel detail={detail} />
                <ScoreCalibrationPanel detail={detail} />
              </PanelGroupDisclosure>

              <PanelGroupDisclosure title="Pattern And Execution" subtitle="Pattern fields, FVG v2 metadata, and execution assumptions">
                <PatternGeometryPanel detail={detail} />
                <FvgRetestDiagnosticsPanel detail={detail} />
                <ExecutionAssumptionsPanel detail={detail} />
                <StrategyExplanation detail={detail} />
              </PanelGroupDisclosure>

              <PanelGroupDisclosure title="Timing And Risk" subtitle="Tradability, entry/exit path, and exit audit">
                <TradabilityDiagnosticsPanel detail={detail} />
                <TimingDiagnosticsPanel detail={detail} />
                <RiskAuditPanel detail={detail} />
              </PanelGroupDisclosure>

              <AccountStatePanel detail={detail} />
              <TradeTable trades={detail.trades} />
              <PanelGroupDisclosure title="Run Metadata" subtitle="Research report, parameters, and runtime">
                <ResearchReportPanel detail={detail} />
                <div className="two-column">
                  <ParametersPanel detail={detail} />
                  <RuntimePanel detail={detail} runtime={runtime} />
                </div>
              </PanelGroupDisclosure>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
