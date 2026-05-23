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

function fmtNum(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  return value.toLocaleString(undefined, { maximumFractionDigits: 6 });
}

function fmtPct(value: number): string {
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

function getRuntimeBreakdown(detail: BacktestRunDetailResponse | null) {
  const runtime = detail?.run.metadata?.runtime;
  if (!runtime || typeof runtime !== "object") return null;
  return runtime;
}

function metaNum(record: Record<string, unknown> | null | undefined, key: string): number | undefined {
  const value = record?.[key];
  return typeof value === "number" ? value : undefined;
}

function metaText(record: Record<string, unknown> | null | undefined, key: string): string | undefined {
  const value = record?.[key];
  return typeof value === "string" ? value : undefined;
}

function tradeFreeCash(trade: BacktestTrade): number | undefined {
  return trade.free_cash_after ?? metaNum(trade.metadata, "free_cash_after");
}

function tradeCashSemantics(trade: BacktestTrade): string | undefined {
  return trade.cash_after_semantics ?? metaText(trade.metadata, "cash_after_semantics");
}

function accountState(summaryMetadata: Record<string, unknown> | null | undefined) {
  const state = summaryMetadata?.account_state;
  return state && typeof state === "object" ? (state as Record<string, unknown>) : null;
}


function ExplanationCard({ title, items }: { title: string; items: unknown }) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) return null;
  return (
    <section className="card">
      <h3>{title}</h3>
      <ul>{list.map((v, i) => <li key={`${title}-${i}`}>{String(v)}</li>)}</ul>
    </section>
  );
}

function JsonPanel({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="card">
      <h3>{title}</h3>
      <pre>{JSON.stringify(value ?? {}, null, 2)}</pre>
    </section>
  );
}

function LineChart({
  title,
  points,
  valueKey,
  markerTrades,
}: {
  title: string;
  points: BacktestGraphPoint[];
  valueKey: "close_price" | "equity";
  markerTrades?: BacktestTrade[];
}) {
  if (!points.length) {
    return (
      <section className="card">
        <h3>{title}</h3>
        <p>No points available.</p>
      </section>
    );
  }

  const width = 900;
  const height = 240;
  const pad = 24;
  const values = points.map((point) => point[valueKey]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const toX = (idx: number): number =>
    pad + (idx / Math.max(points.length - 1, 1)) * (width - pad * 2);
  const toY = (value: number): number =>
    height - pad - ((value - min) / range) * (height - pad * 2);

  const path = points
    .map((point, idx) => `${idx === 0 ? "M" : "L"} ${toX(idx)} ${toY(point[valueKey])}`)
    .join(" ");

  const tradesBySequence = new Map<number, BacktestTrade>();
  markerTrades?.forEach((trade) => tradesBySequence.set(trade.sequence, trade));

  return (
    <section className="card">
      <h3>{title}</h3>
      <svg viewBox={`0 0 ${width} ${height}`} className="chart">
        <path d={path} className="line" />
        {markerTrades &&
          points.map((point, idx) => {
            if (!point.signal) return null;
            const trade = tradesBySequence.get(point.sequence);
            const color = point.signal === "BUY" ? "#16a34a" : "#dc2626";
            return (
              <g key={`${point.id}-${point.sequence}`}>
                <circle cx={toX(idx)} cy={toY(point[valueKey])} r={4} fill={color}>
                  <title>{`time: ${point.candle_open_time}\nsignal: ${point.signal}\nprice: ${fmtNum(
                    point.close_price,
                  )}\nquantity: ${fmtNum(trade?.quantity)}\ncash_balance_after: ${fmtNum(
                    trade?.cash_after,
                  )}\nfree_cash_after: ${fmtNum(
                    trade ? tradeFreeCash(trade) : undefined,
                  )}\nposition_after: ${fmtNum(trade?.position_after)}\ncash_semantics: ${
                    trade ? tradeCashSemantics(trade) ?? "-" : "-"
                  }\nmetadata: ${JSON.stringify(
                    trade?.metadata ?? point.metadata ?? {},
                  )}`}</title>
                </circle>
              </g>
            );
          })}
      </svg>
      <p className="muted">min: {fmtNum(min)} / max: {fmtNum(max)}</p>
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
  const finalAccountState = useMemo(() => accountState(detail?.summary.metadata), [detail]);

  const allEquityZero = useMemo(
    () => Boolean(detail && detail.graph_points.length && detail.graph_points.every((p) => p.equity === 0)),
    [detail],
  );

  return (
    <main>
      <h1>Quant Backtest Dashboard</h1>

      <section className="card">
        <h2>API Connectivity</h2>
        <p>
          Status: {health?.status ?? "unknown"} / DB configured: {String(health?.database.configured ?? false)} /
          reachable: {String(health?.database.reachable ?? false)}
        </p>
      </section>

      <section className="card">
        <h2>Run Filters</h2>
        <div className="filters">
          <input placeholder="symbol" onChange={(e) => setFilters((f) => ({ ...f, symbol: e.target.value || undefined }))} />
          <input placeholder="interval" onChange={(e) => setFilters((f) => ({ ...f, interval: e.target.value || undefined }))} />
          <input placeholder="source" onChange={(e) => setFilters((f) => ({ ...f, source: e.target.value || undefined }))} />
          <input
            placeholder="limit"
            type="number"
            defaultValue={20}
            min={1}
            max={100}
            onChange={(e) => setFilters((f) => ({ ...f, limit: Number(e.target.value) || 20 }))}
          />
        </div>
      </section>

      {error && <p className="error">API Error: {error}</p>}

      <section className="card">
        <h2>Backtest Runs</h2>
        {!runs.length ? (
          <p>No completed runs found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Run ID</th><th>Strategy</th><th>Version</th><th>Symbol</th><th>Interval</th><th>Actual Range</th><th>Candles</th><th>Runtime</th><th>Final Equity</th><th>Total Return</th><th>Trades</th><th>Completed</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} onClick={() => setSelectedId(run.id)} className={selectedId === run.id ? "selected" : ""}>
                  <td>{run.id}</td><td>{run.strategy.name}</td><td>{run.strategy.version}</td><td>{run.market.symbol}</td><td>{run.market.interval}</td>
                  <td>{fmtTime(run.market.actual_start_time)} → {fmtTime(run.market.actual_end_time)}</td><td>{run.market.candle_count}</td><td>{fmtDurationMs(run.runtime?.total_elapsed_ms)}</td><td>{fmtNum(run.summary.final_equity)}</td>
                  <td>{fmtPct(run.summary.total_return)}</td><td>{run.summary.trade_count}</td><td>{fmtTime(run.completed_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2>Selected Run Summary</h2>
        {!detail ? (
          <p>No run selected yet.</p>
        ) : (
          <div className="summary-grid">
            <div><strong>Strategy:</strong> {detail.strategy_config.name} ({detail.strategy_config.version})</div>
            <div><strong>Symbol/Interval:</strong> {detail.run.market.symbol} / {detail.run.market.interval}</div>
            <div><strong>Candle Range:</strong> {fmtTime(detail.run.market.actual_start_time)} → {fmtTime(detail.run.market.actual_end_time)}</div>
            <div><strong>Starting Cash:</strong> {fmtNum(detail.summary.starting_cash)}</div>
            <div><strong>Ending Cash Balance:</strong> {fmtNum(detail.summary.ending_cash)}</div>
            <div><strong>Free Cash:</strong> {fmtNum(metaNum(finalAccountState, "free_cash_after"))}</div>
            <div><strong>Final Equity:</strong> {fmtNum(detail.summary.final_equity)}</div>
            <div><strong>Total Return:</strong> {fmtPct(detail.summary.total_return)}</div>
            <div><strong>Trade Count:</strong> {detail.summary.trade_count}</div>
            <div><strong>Buy/Sell:</strong> {detail.summary.buy_count}/{detail.summary.sell_count}</div>
            <div><strong>Total Runtime:</strong> {fmtDurationMs(runtime?.total_elapsed_ms)}</div>
            <div><strong>Load Time:</strong> {fmtDurationMs(runtime?.load_elapsed_ms)}</div>
            <div><strong>Action Build Time:</strong> {fmtDurationMs(runtime?.action_build_elapsed_ms)}</div>
            <div><strong>Engine Time:</strong> {fmtDurationMs(runtime?.engine_elapsed_ms)}</div>
            <div><strong>Persist Time:</strong> {fmtDurationMs(runtime?.persist_elapsed_ms)}</div>
          </div>
        )}
      </section>

      {detail && detail.warnings.length > 0 && (
        <section className="card warning">
          <h3>Warnings</h3>
          <ul>
            {detail.warnings.map((warning, idx) => (
              <li key={`${warning.code}-${idx}`}>{warning.code}: {warning.message}</li>
            ))}
          </ul>
        </section>
      )}

      {detail && (
        <>
          <section className="card">
            <h3>Runtime Breakdown</h3>
            <div className="summary-grid">
              <div><strong>Total:</strong> {fmtDurationMs(runtime?.total_elapsed_ms)}</div>
              <div><strong>Load:</strong> {fmtDurationMs(runtime?.load_elapsed_ms)}</div>
              <div><strong>Action Build:</strong> {fmtDurationMs(runtime?.action_build_elapsed_ms)}</div>
              <div><strong>Engine:</strong> {fmtDurationMs(runtime?.engine_elapsed_ms)}</div>
              <div><strong>Persist:</strong> {fmtDurationMs(runtime?.persist_elapsed_ms)}</div>
              <div><strong>JSON:</strong> {fmtDurationMs(runtime?.json_elapsed_ms)}</div>
            </div>
          </section>
          {(() => {
            const explanation = (detail.strategy_config.metadata as Record<string, unknown> | null)?.explanation as Record<string, unknown> | undefined;
            if (!explanation) return null;
            return (<>
              <section className="card"><h3>Algorithm Summary</h3><p><strong>{String(explanation.algorithm_name ?? "-")}</strong> ({String(explanation.algorithm_key ?? "-")})</p></section>
              <ExplanationCard title="Entry Rules" items={explanation.entry_rules} />
              <ExplanationCard title="Stop-Loss Rules" items={explanation.stop_loss_rules} />
              <ExplanationCard title="Take-Profit Rules" items={explanation.take_profit_rules} />
              <ExplanationCard title="Risk/Exit Management" items={[...(Array.isArray(explanation.partial_exit_rules) ? explanation.partial_exit_rules : []), ...(Array.isArray(explanation.soft_invalidation_rules) ? explanation.soft_invalidation_rules : []), ...(Array.isArray(explanation.time_stop_rules) ? explanation.time_stop_rules : [])]} />
              <ExplanationCard title="Design Rationale" items={explanation.design_rationale} />
              <ExplanationCard title="Limitations" items={explanation.known_limitations} />
            </>);
          })()}
          <LineChart title="Close Price" points={detail.graph_points} valueKey="close_price" markerTrades={detail.trades} />
          <LineChart title="Equity" points={detail.graph_points} valueKey="equity" />
          {allEquityZero && <p className="error">Equity series is all zero; treat as placeholder-neutral and not real performance.</p>}

          <section className="card">
            <h3>Trades</h3>
            <table>
              <thead>
                <tr>
                  <th>Seq</th><th>Timestamp</th><th>Signal</th><th>Price</th><th>Qty</th><th>Cash Balance / Free Cash</th><th>Position After</th><th>Metadata</th>
                </tr>
              </thead>
              <tbody>
                {detail.trades.map((trade) => (
                  <tr key={trade.id}>
                    <td>{trade.sequence}</td><td>{trade.candle_open_time}</td><td>{trade.signal}</td><td>{fmtNum(trade.price)}</td>
                    <td>{fmtNum(trade.quantity)}</td><td>{fmtNum(trade.cash_after)} / {fmtNum(tradeFreeCash(trade))}</td><td>{fmtNum(trade.position_after)}</td>
                    <td>{JSON.stringify({
                      event_id: trade.metadata?.event_id,
                      pattern_type: trade.metadata?.pattern_type,
                      pattern_direction: trade.metadata?.pattern_direction,
                      exit_reason: trade.metadata?.exit_reason,
                      cash_after_semantics: tradeCashSemantics(trade),
                      short_proceeds_locked_after: trade.metadata?.short_proceeds_locked_after,
                      margin_used_after: trade.metadata?.margin_used_after,
                      exit_timestamp: trade.metadata?.exit_timestamp,
                      exit_price: trade.metadata?.exit_price,
                      realized_pnl_per_unit: trade.metadata?.realized_pnl_per_unit,
                      realized_r_multiple: trade.metadata?.realized_r_multiple,
                    })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <JsonPanel title="Strategy Parameters" value={detail.strategy_config.parameters} />
          <JsonPanel title="Run Metadata" value={detail.run.metadata} />
          <JsonPanel title="Result Metadata" value={detail.summary.metadata} />
        </>
      )}
    </main>
  );
}
