export type HealthResponse = {
  status: string;
  service: string;
  database: {
    configured: boolean;
    reachable: boolean;
  };
};

export type BacktestRunListFilters = {
  source?: string;
  symbol?: string;
  interval?: string;
  actual_start_time?: string;
  actual_end_time?: string;
  limit?: number;
};

export type BacktestRuntimeSummary = {
  total_elapsed_ms?: number;
  action_build_elapsed_ms?: number;
  engine_elapsed_ms?: number;
};

export type BacktestRuntimeBreakdown = BacktestRuntimeSummary & {
  load_elapsed_ms?: number;
  persist_elapsed_ms?: number;
  json_elapsed_ms?: number;
};

export type BacktestRunListItem = {
  id: number;
  run_key: string;
  strategy: {
    config_id: number;
    key: string;
    name: string;
    version: string;
    parameters: Record<string, unknown>;
    parameters_hash: string;
  };
  market: {
    source: string;
    symbol: string;
    interval: string;
    actual_start_time: string | null;
    actual_end_time: string | null;
    candle_count: number;
  };
  summary: {
    final_equity: number;
    total_return: number;
    trade_count: number;
  };
  runtime?: BacktestRuntimeSummary | null;
  created_at: string;
  completed_at: string | null;
};

export type BacktestRunsListResponse = {
  items: BacktestRunListItem[];
  limit: number;
};

export type WarningMessage = { code: string; message: string };

export type BacktestResearchDiagnostics = {
  schema_version: string;
  available_sections: string[];
  run?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  trade_metadata_keys?: string[];
  graph_metadata_keys?: string[];
};

export type BacktestTrade = {
  id: number;
  sequence: number;
  candle_open_time: string;
  signal: string;
  position_signal?: string | null;
  side?: string | null;
  execution_side?: string | null;
  position_side?: string | null;
  price: number;
  quantity: number;
  cash_after: number;
  cash_balance_after?: number | null;
  execution_equity_after?: number | null;
  mark_to_market_equity_after?: number | null;
  free_cash_after?: number | null;
  margin_used_after?: number | null;
  short_proceeds_locked_after?: number | null;
  short_collateral_locked_after?: number | null;
  available_buying_power_after?: number | null;
  cash_after_semantics?: string | null;
  position_after: number;
  metadata: Record<string, unknown> | null;
};

export type BacktestGraphPoint = {
  id: number;
  sequence: number;
  candle_open_time: string;
  close_price: number;
  cash: number;
  free_cash?: number | null;
  margin_used?: number | null;
  short_proceeds_locked?: number | null;
  short_collateral_locked?: number | null;
  available_buying_power?: number | null;
  cash_semantics?: string | null;
  equity_semantics?: string | null;
  position_signal?: string | null;
  execution_side?: string | null;
  position: number;
  equity: number;
  trade_id: number | null;
  signal: string | null;
  metadata: Record<string, unknown> | null;
};

export type BacktestRunDetailResponse = {
  run: {
    id: number;
    run_key: string;
    engine_name: string;
    engine_version: string;
    status: string;
    market: {
      source: string;
      symbol: string;
      interval: string;
      requested_start_time: string | null;
      requested_end_time: string | null;
      actual_start_time: string | null;
      actual_end_time: string | null;
      candle_count: number;
    };
    starting_cash: number;
    trade_quantity: number;
    created_at: string;
    completed_at: string | null;
    metadata: {
      runtime?: BacktestRuntimeBreakdown;
      [key: string]: unknown;
    } | null;
  };
  strategy_config: {
    id: number;
    key: string;
    name: string;
    version: string;
    parameters: Record<string, unknown>;
    parameters_hash: string;
    metadata: Record<string, unknown> | null;
  };
  summary: {
    starting_cash: number;
    ending_cash: number;
    ending_position: number;
    final_price: number | null;
    final_equity: number;
    total_return: number;
    trade_count: number;
    buy_count: number;
    sell_count: number;
    metadata: Record<string, unknown> | null;
    created_at: string;
  };
  trades: BacktestTrade[];
  graph_points: BacktestGraphPoint[];
  diagnostics?: BacktestResearchDiagnostics | null;
  research_report?: Record<string, unknown> | null;
  warnings: WarningMessage[];
};
