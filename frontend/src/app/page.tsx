"use client";

import { useEffect, useMemo, useState } from "react";

import { getBacktestRun, getHealth, listBacktestRuns } from "../lib/api";
import type {
  BacktestGraphPoint,
  BacktestRunDetailResponse,
  BacktestRunListFilters,
  BacktestRunListItem,
  BacktestTrade,
  HealthResponse,
} from "../types/api";

type AnyRecord = Record<string, unknown>;

type PatternKnowledge = {
  indicators: string[];
  economicMeaning: string[];
  fallback: boolean;
};

const PATTERN_KNOWLEDGE: Record<string, PatternKnowledge> = {
  FAIR_VALUE_GAP: {
    indicators: ["Displacement candle", "Volume ratio", "Three-candle imbalance", "ATR risk buffer"],
    economicMeaning: [
      "Targets price gaps created by aggressive directional order flow.",
      "The thesis is that unfilled imbalance zones can act as liquidity magnets or continuation levels.",
    ],
    fallback: true,
  },
  ORDER_BLOCK: {
    indicators: ["Source candle zone", "Displacement confirmation", "ATR risk buffer", "Volume context"],
    economicMeaning: [
      "Models a price zone where a prior opposing candle preceded a strong directional move.",
      "The thesis is that retests of that zone can reveal institutional absorption or defended inventory.",
    ],
    fallback: true,
  },
  TRENDLINE_BREAK: {
    indicators: ["Pivot highs/lows", "Trendline slope", "ATR breakout buffer", "Breakout close"],
    economicMeaning: [
      "Tracks a structural regime shift after repeated trendline interaction.",
      "The thesis is that a confirmed break can unlock stops and momentum continuation.",
    ],
    fallback: true,
  },
  CUP_AND_HANDLE: {
    indicators: ["Swing pivots", "Cup depth", "Handle pullback", "Neckline breakout"],
    economicMeaning: [
      "Models accumulation, shallow pullback, and breakout continuation.",
      "The thesis is that reduced selling pressure in the handle can precede follow-through demand.",
    ],
    fallback: true,
  },
  DIAMOND: {
    indicators: ["Expansion pivots", "Contraction pivots", "Boundary break", "Measured move height"],
    economicMeaning: [
      "Models volatility expansion followed by compression before directional resolution.",
      "The thesis is that a boundary break can release trapped positioning from the consolidation.",
    ],
    fallback: true,
  },
  ADAM_AND_EVE: {
    indicators: ["Spike low", "Rounded retest", "Neckline breakout", "Measured move depth"],
    economicMeaning: [
      "Models a sharp capitulation low followed by a slower accumulation retest.",
      "The thesis is that neckline recovery confirms demand has absorbed the prior selloff.",
    ],
    fallback: true,
  },
};

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
  return trade.mark_to_market_equity_after ?? valueNum(trade.metadata, "mark_to_market_equity_after");
}

function tradePnl(trade: BacktestTrade): number | undefined {
  return valueNum(trade.metadata, "net_pnl") ?? valueNum(trade.metadata, "gross_pnl");
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

function patternKey(detail: BacktestRunDetailResponse): string {
  const params = detail.strategy_config.parameters;
  const direct =
    (typeof params.pattern === "string" && params.pattern) ||
    (typeof params.strategy === "string" && params.strategy) ||
    detail.strategy_config.key ||
    detail.strategy_config.name;
  return String(direct).toUpperCase();
}

function explanationRecord(detail: BacktestRunDetailResponse): AnyRecord | null {
  return asRecord(detail.strategy_config.metadata?.explanation);
}

function patternKnowledge(detail: BacktestRunDetailResponse): PatternKnowledge {
  const key = patternKey(detail);
  return PATTERN_KNOWLEDGE[key] ?? {
    indicators: ["Strategy-defined indicators from persisted metadata"],
    economicMeaning: ["Economic interpretation is not available for this strategy metadata."],
    fallback: true,
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

function MetricCard({ label, value, tone }: { label: string; value: string; tone?: "good" | "bad" | "neutral" }) {
  return (
    <div className={`metric-card ${tone ?? "neutral"}`}>
      <span>{label}</span>
      <strong>{value}</strong>
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
          <span className={run.summary.total_return >= 0 ? "return good" : "return bad"}>
            {fmtPct(run.summary.total_return)}
          </span>
        </button>
      ))}
    </div>
  );
}

function Chart({
  title,
  points,
  valueKey,
  trades,
  startingValue,
  color,
}: {
  title: string;
  points: BacktestGraphPoint[];
  valueKey: "close_price" | "equity";
  trades?: BacktestTrade[];
  startingValue?: number;
  color: string;
}) {
  const [startPct, setStartPct] = useState(0);
  const [endPct, setEndPct] = useState(100);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const normalizedEnd = Math.max(endPct, startPct + 1);
  const fromIndex = Math.floor((startPct / 100) * Math.max(points.length - 1, 0));
  const toIndex = Math.max(fromIndex + 1, Math.ceil((normalizedEnd / 100) * Math.max(points.length - 1, 0)));
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
  const values = visible.map((point) => point[valueKey]);
  const referenceValues = startingValue === undefined ? values : [...values, startingValue];
  const min = Math.min(...referenceValues);
  const max = Math.max(...referenceValues);
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
  const tradesByTime = new Map<string, BacktestTrade[]>();
  trades?.forEach((trade) => {
    const bucket = tradesByTime.get(trade.candle_open_time) ?? [];
    bucket.push(trade);
    tradesByTime.set(trade.candle_open_time, bucket);
  });

  return (
    <section className="panel chart-panel">
      <div className="chart-heading">
        <SectionHeader title={title} subtitle={`${fmtNum(min)} to ${fmtNum(max)}`} />
        <button
          className="small-button"
          onClick={() => {
            setStartPct(0);
            setEndPct(100);
            setHoverIndex(null);
          }}
          type="button"
        >
          Reset Range
        </button>
      </div>
      <svg
        className="chart"
        onMouseLeave={() => setHoverIndex(null)}
        onMouseMove={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          const ratio = (event.clientX - rect.left) / Math.max(rect.width, 1);
          const idx = Math.round(ratio * (visible.length - 1));
          setHoverIndex(Math.max(0, Math.min(visible.length - 1, idx)));
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
        <path className="line" d={path} stroke={color} />
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
      <div className="range-controls">
        <label>
          From
          <input
            max={99}
            min={0}
            onChange={(event) => setStartPct(Math.min(Number(event.target.value), endPct - 1))}
            type="range"
            value={startPct}
          />
        </label>
        <label>
          To
          <input
            max={100}
            min={1}
            onChange={(event) => setEndPct(Math.max(Number(event.target.value), startPct + 1))}
            type="range"
            value={normalizedEnd}
          />
        </label>
        <span className="muted">
          {fmtTime(visible[0]?.candle_open_time ?? null)} to {fmtTime(visible[visible.length - 1]?.candle_open_time ?? null)}
        </span>
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
  const explanation = explanationRecord(detail);
  const knowledge = patternKnowledge(detail);
  const algorithmName = String(explanation?.algorithm_name ?? detail.strategy_config.name);
  const algorithmKey = String(explanation?.algorithm_key ?? patternKey(detail));
  const rules = {
    Detection: listText(explanation?.detection_rules),
    Entry: listText(explanation?.entry_rules),
    "Stop Loss": listText(explanation?.stop_loss_rules),
    "Take Profit": listText(explanation?.take_profit_rules),
    "Risk Management": [
      ...listText(explanation?.partial_exit_rules),
      ...listText(explanation?.soft_invalidation_rules),
      ...listText(explanation?.time_stop_rules),
    ],
    Limitations: listText(explanation?.known_limitations),
  };

  return (
    <section className="panel">
      <SectionHeader title="Strategy Logic" subtitle={`${algorithmName} / ${algorithmKey}`} />
      <div className="strategy-grid">
        <div className="info-block">
          <h3>Indicators</h3>
          <CompactList items={knowledge.indicators} />
        </div>
        <div className="info-block">
          <h3>Economic Meaning</h3>
          <CompactList items={knowledge.economicMeaning} />
          {knowledge.fallback && <p className="source-note">Static fallback when persisted economic metadata is missing.</p>}
        </div>
      </div>
      <div className="rules-grid">
        {Object.entries(rules).map(([title, items]) => (
          <div className="rule-card" key={title}>
            <h3>{title}</h3>
            <CompactList items={items} />
          </div>
        ))}
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

function TradeTable({ trades }: { trades: BacktestTrade[] }) {
  const [page, setPage] = useState(0);
  const pageSize = 12;
  const pageCount = Math.max(1, Math.ceil(trades.length / pageSize));
  const pageTrades = trades.slice(page * pageSize, page * pageSize + pageSize);

  useEffect(() => {
    setPage(0);
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
              <th>Price</th>
              <th>Qty</th>
              <th>Free Cash</th>
              <th>Cash Balance</th>
              <th>Equity</th>
              <th>PnL</th>
            </tr>
          </thead>
          <tbody>
            {pageTrades.map((trade) => {
              const signal = tradePositionSignal(trade);
              return (
                <tr key={trade.id}>
                  <td>{trade.sequence}</td>
                  <td>{trade.candle_open_time.slice(0, 16).replace("T", " ")}</td>
                  <td>
                    <span className={signalClass(signal)}>{signal}</span>
                  </td>
                  <td>{tradeExecutionSide(trade)}</td>
                  <td>{fmtNum(trade.price)}</td>
                  <td>{fmtNum(trade.quantity)}</td>
                  <td className="primary-money">{fmtNum(tradeBuyingPower(trade))}</td>
                  <td>{fmtNum(tradeCashBalance(trade))}</td>
                  <td>{fmtNum(tradeEquity(trade))}</td>
                  <td>{fmtNum(tradePnl(trade))}</td>
                </tr>
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
  const [runs, setRuns] = useState<BacktestRunListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<BacktestRunDetailResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    setError(null);
    listBacktestRuns(filters)
      .then((response) => {
        setRuns(response.items);
        if (response.items.length > 0 && selectedId === null) {
          setSelectedId(response.items[0].id);
        }
      })
      .catch((err: Error) => setError(err.message));
  }, [filters, selectedId]);

  useEffect(() => {
    if (selectedId === null) return;
    setError(null);
    getBacktestRun(selectedId)
      .then(setDetail)
      .catch((err: Error) => {
        setDetail(null);
        setError(err.message);
      });
  }, [selectedId]);

  const runtime = useMemo(() => getRuntimeBreakdown(detail), [detail]);
  const allEquityZero = useMemo(
    () => Boolean(detail && detail.graph_points.length && detail.graph_points.every((point) => point.equity === 0)),
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

      <section className="toolbar panel">
        <input placeholder="Symbol" onChange={(event) => setFilters((value) => ({ ...value, symbol: event.target.value || undefined }))} />
        <input placeholder="Interval" onChange={(event) => setFilters((value) => ({ ...value, interval: event.target.value || undefined }))} />
        <input placeholder="Source" onChange={(event) => setFilters((value) => ({ ...value, source: event.target.value || undefined }))} />
        <input
          defaultValue={20}
          max={100}
          min={1}
          onChange={(event) => setFilters((value) => ({ ...value, limit: Number(event.target.value) || 20 }))}
          placeholder="Limit"
          type="number"
        />
      </section>

      {error && <p className="error">API Error: {error}</p>}

      <section className="layout">
        <aside className="sidebar panel">
          <SectionHeader title="Runs" subtitle={`${runs.length} loaded`} />
          <RunSelector onSelect={setSelectedId} runs={runs} selectedId={selectedId} />
        </aside>

        <div className="content">
          {!detail ? (
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
                  <MetricCard label="Starting Cash" value={fmtNum(detail.summary.starting_cash)} />
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

              <div className="chart-grid">
                <Chart color="#2563eb" points={detail.graph_points} title="Close Price" trades={detail.trades} valueKey="close_price" />
                <Chart
                  color="#0f766e"
                  points={detail.graph_points}
                  startingValue={detail.summary.starting_cash}
                  title="Equity"
                  trades={detail.trades}
                  valueKey="equity"
                />
              </div>

              <AccountStatePanel detail={detail} />
              <TradeTable trades={detail.trades} />
              <StrategyExplanation detail={detail} />
              <div className="two-column">
                <ParametersPanel detail={detail} />
                <RuntimePanel detail={detail} runtime={runtime} />
              </div>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
