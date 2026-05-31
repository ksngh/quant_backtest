import assert from "node:assert/strict";

import { configuredStartingCash, hasStartingCashMismatch, listItemStartingCash } from "../src/lib/runDisplay";
import type { BacktestRunDetailResponse, BacktestRunListItem } from "../src/types/api";

const detail = {
  run: {
    id: 9,
    run_key: "run-key",
    engine_name: "BasicBacktester",
    engine_version: "basic_backtester_v1",
    status: "completed",
    market: {
      source: "binance_spot",
      symbol: "BTCUSDT",
      interval: "1m",
      requested_start_time: "2026-05-20T00:00:00Z",
      requested_end_time: null,
      actual_start_time: "2026-05-20T00:00:00Z",
      actual_end_time: "2026-05-20T00:10:00Z",
      candle_count: 10,
    },
    starting_cash: 1_000_000,
    trade_quantity: 1,
    created_at: "2026-05-28T00:00:00Z",
    completed_at: "2026-05-28T00:00:01Z",
    metadata: null,
  },
  strategy_config: {
    id: 1,
    key: "fair_value_gap",
    name: "FAIR_VALUE_GAP_PATTERN_STRATEGY",
    version: "strategy_engine_v1",
    parameters: {},
    parameters_hash: "hash",
    metadata: null,
  },
  summary: {
    starting_cash: 10_000,
    ending_cash: 1_000_100,
    ending_position: 0,
    final_price: 100,
    final_equity: 1_000_100,
    total_return: 0.0001,
    trade_count: 2,
    buy_count: 1,
    sell_count: 1,
    metadata: null,
    created_at: "2026-05-28T00:00:01Z",
  },
  trades: [],
  graph_points: [],
  warnings: [],
} satisfies BacktestRunDetailResponse;

assert.equal(configuredStartingCash(detail), 1_000_000);
assert.equal(hasStartingCashMismatch(detail), true);

const listItem = {
  id: 9,
  run_key: "run-key",
  strategy: {
    config_id: 1,
    key: "fair_value_gap",
    name: "FAIR_VALUE_GAP_PATTERN_STRATEGY",
    version: "strategy_engine_v1",
    parameters: {},
    parameters_hash: "hash",
  },
  market: {
    source: "binance_spot",
    symbol: "BTCUSDT",
    interval: "1m",
    actual_start_time: "2026-05-20T00:00:00Z",
    actual_end_time: "2026-05-20T00:10:00Z",
    candle_count: 10,
  },
  summary: {
    starting_cash: 1_000_000,
    final_equity: 1_000_100,
    total_return: 0.0001,
    trade_count: 2,
  },
  created_at: "2026-05-28T00:00:00Z",
  completed_at: "2026-05-28T00:00:01Z",
} satisfies BacktestRunListItem;

assert.equal(listItemStartingCash(listItem), 1_000_000);
