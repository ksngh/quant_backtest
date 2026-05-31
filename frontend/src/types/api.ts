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
  strategy_key?: string;
  actual_start_time?: string;
  actual_end_time?: string;
  created_start_time?: string;
  created_end_time?: string;
  min_total_return?: number;
  max_total_return?: number;
  cost_profile?: string;
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
    starting_cash?: number;
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

export type FvgRetestV2TrendScoreSettings = {
  enabled?: boolean;
  fast_period?: number;
  slow_period?: number;
  weights?: Record<string, number>;
  minimum_bullish_trend_score?: number;
};

export type FvgRetestV2Settings = {
  schema_version?: "fvg_retest_v2_settings_v1" | string;
  enabled?: boolean;
  experimental_scope?: string;
  trend_score?: FvgRetestV2TrendScoreSettings;
  fibonacci_confluence?: {
    enabled?: boolean;
  };
  liquidity_targets?: {
    require_liquidity_target?: boolean;
  };
  stop_mode?: string;
  entry_trigger?: string;
  parallel_channel?: Record<string, unknown> | null;
  default_behavior_preserved?: boolean;
};

export type FvgRetestV2Diagnostics = {
  schema_version?: "fvg_retest_v2_diagnostics_v1" | string;
  settings?: FvgRetestV2Settings;
  entry_trigger?: string;
  stop_mode?: string;
  experimental_scope?: string;
  counts?: {
    filled_entry_count?: number | null;
    skipped_entry_count?: number | null;
  };
};

export type BacktestResearchDiagnostics = {
  schema_version: string;
  available_sections: string[];
  run?: Record<string, unknown>;
  summary?: Record<string, unknown> & {
    fvg_retest_v2?: FvgRetestV2Diagnostics;
  };
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
  raw_price?: number | null;
  effective_price?: number | null;
  price_semantics?: string | null;
  effective_price_semantics?: string | null;
  channel_mode?: string | null;
  channel_id?: string | null;
  channel_candidate_source?: string | null;
  channel_scan_source?: string | null;
  channel_trend_direction?: string | null;
  channel_direction_rule?: string | null;
  channel_boundary_direction_mode?: string | null;
  channel_identity?: Record<string, unknown> | null;
  channel_geometry?: Record<string, unknown> | null;
  fvg_channel?: Record<string, unknown> | null;
  entry_boundary?: string | null;
  original_channel_entry_side?: string | null;
  effective_channel_entry_side?: string | null;
  stop_boundary?: string | null;
  target_boundary?: string | null;
  stop_source?: string | null;
  retest_structure_low?: number | null;
  channel_lower_line_price_at_entry?: number | null;
  channel_upper_line_price_at_entry?: number | null;
  channel_width_at_entry?: number | null;
  target_price_source?: string | null;
  target_source?: string | null;
  channel_target_policy?: string | null;
  projected_channel_width_target?: number | null;
  opposite_boundary_target_price?: number | null;
  line_stop_price?: number | null;
  line_target_price?: number | null;
  same_candle_entry_exit_ambiguity?: boolean | null;
  cost_aware_entry_filter?: Record<string, unknown> | null;
  cost_breakdown?: {
    fee_cost?: number | null;
    spread_cost?: number | null;
    slippage_cost?: number | null;
    total_cost?: number | null;
    fee_bps?: number | null;
    spread_bps?: number | null;
    slippage_bps?: number | null;
    effective_slippage_bps?: number | null;
    volatility_bps?: number | null;
    cost_profile_name?: string | null;
    cost_currency?: string | null;
  } | null;
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
