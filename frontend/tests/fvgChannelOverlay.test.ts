import assert from "node:assert/strict";

import {
  buildFvgChannelOverlay,
  buildFvgChannelOverlays,
  channelOverlayValues,
  projectChannelLine,
  projectChannelSegments,
} from "../src/lib/fvgChannelOverlay";
import type { BacktestGraphPoint, BacktestTrade } from "../src/types/api";

function channelGeometry(offset: number) {
  return {
    schema_version: "fvg_parallel_channel_v1",
    channel_id: `channel-${offset}`,
    window_start_index: offset,
    window_end_index: offset + 2,
    lower_anchor_1_index: offset,
    lower_anchor_2_index: offset + 2,
    upper_touch_index: offset + 1,
    lower_line: { slope: 1, intercept: 100 + offset },
    upper_line: { slope: 1, intercept: 110 + offset },
    width: 10,
  };
}

const trades: BacktestTrade[] = [
  {
    id: 1,
    sequence: 1,
    candle_open_time: "2026-05-20T00:03:00Z",
    signal: "LONG_ENTRY",
    position_signal: "LONG_ENTRY",
    position_side: "LONG",
    price: 104,
    channel_id: "channel-0",
    quantity: 1,
    cash_after: 9896,
    position_after: 1,
    metadata: {
      channel_id: "channel-0",
      channel_candidate_source: "fvg_event_expansion",
      fill_candle_index: 3,
      fill_price: 104,
      channel_geometry: channelGeometry(0),
    },
  },
  {
    id: 2,
    sequence: 2,
    candle_open_time: "2026-05-20T00:04:00Z",
    signal: "LONG_EXIT",
    position_signal: "LONG_EXIT",
    position_side: "LONG",
    price: 114,
    channel_id: "channel-0",
    quantity: 1,
    cash_after: 10010,
    position_after: 0,
    metadata: {
      channel_id: "channel-0",
      exit_candle_index: 4,
      exit_price: 114,
      channel_geometry: channelGeometry(0),
    },
  },
  {
    id: 3,
    sequence: 3,
    candle_open_time: "2026-05-20T00:08:00Z",
    signal: "LONG_ENTRY",
    position_signal: "LONG_ENTRY",
    position_side: "LONG",
    price: 216,
    channel_id: "channel-5",
    quantity: 1,
    cash_after: 9794,
    position_after: 1,
    metadata: {
      channel_id: "channel-5",
      channel_candidate_source: "standalone_visible_prefix_scan",
      fill_candle_index: 8,
      fill_price: 216,
      channel_geometry: channelGeometry(5),
    },
  },
];

const overlays = buildFvgChannelOverlays(trades);

assert.equal(overlays.length, 2);
assert.equal(overlays[0].channelId, "channel-0");
assert.equal(overlays[0].channelCandidateSource, "fvg_event_expansion");
assert.equal(overlays[0].schemaVersion, "fvg_parallel_channel_v1");
assert.equal(overlays[0].lowerLine.slope, 1);
assert.equal(overlays[0].upperLine.intercept, 110);
assert.equal(overlays[0].segmentStartIndex, 0);
assert.equal(overlays[0].segmentEndIndex, 3);
assert.equal(overlays[0].points.some((point) => point.kind === "lower-anchor" && point.index === 0), true);
assert.equal(overlays[0].points.some((point) => point.kind === "upper-touch" && point.index === 1), true);
assert.equal(overlays[0].points.some((point) => point.kind === "entry" && point.index === 3), true);
assert.equal(overlays[0].points.some((point) => point.kind === "exit" && point.index === 4), true);
assert.deepEqual(
  overlays[0].points.filter((point) => point.kind === "lower-anchor" || point.kind === "upper-touch").map((point) => point.label),
  ["L1", "H1", "L2"],
);
assert.deepEqual(
  overlays[0].points.filter((point) => point.kind === "lower-anchor" || point.kind === "upper-touch" || point.kind === "entry").map((point) => point.label),
  ["L1", "H1", "L2", "E"],
);
assert.equal(overlays[0].points.some((point) => point.label === "H"), false);
assert.equal(overlays[1].channelId, "channel-5");
assert.equal(overlays[1].channelCandidateSource, "standalone_visible_prefix_scan");

const firstOverlay = buildFvgChannelOverlay(trades);
assert.ok(firstOverlay);
assert.equal(firstOverlay.channelId, "channel-0");

const projected = projectChannelLine(overlays[0].lowerLine, 3, 4);
assert.deepEqual(projected, { x1Index: 3, y1: 103, x2Index: 4, y2: 104 });

const segments = projectChannelSegments(overlays, 0, 10);
assert.equal(segments.length, 2);
assert.equal(segments[0].lowerLine.x1Index, 0);
assert.equal(segments[0].lowerLine.x2Index, 3);

const clippedSegments = projectChannelSegments(overlays, 2, 3);
assert.equal(clippedSegments.length, 1);
assert.equal(clippedSegments[0].lowerLine.x1Index, 2);
assert.equal(clippedSegments[0].lowerLine.x2Index, 3);

assert.deepEqual(channelOverlayValues(overlays[0], 3, 4).slice(0, 4), [103, 103, 113, 113]);
assert.equal(buildFvgChannelOverlay([]), null);
assert.deepEqual(buildFvgChannelOverlays([]), []);

const missingPointMetadataTrades: BacktestTrade[] = [
  {
    id: 5,
    sequence: 5,
    candle_open_time: "2026-05-20T00:06:00Z",
    signal: "SKIP",
    price: 0,
    quantity: 0,
    cash_after: 10000,
    position_after: 0,
    metadata: {
      channel_id: "missing-points-channel",
      channel_geometry: {
        schema_version: "fvg_parallel_channel_v1",
        channel_id: "missing-points-channel",
        window_start_index: 10,
        window_end_index: 12,
        lower_line: { slope: 1, intercept: 100 },
        upper_line: { slope: 1, intercept: 110 },
        width: 10,
      },
    },
  },
];

const missingPointOverlays = buildFvgChannelOverlays(missingPointMetadataTrades);
assert.equal(missingPointOverlays.length, 1);
assert.deepEqual(missingPointOverlays[0].points, []);

const partialPointMetadataTrades: BacktestTrade[] = [
  {
    id: 6,
    sequence: 6,
    candle_open_time: "2026-05-20T00:06:00Z",
    signal: "LONG_ENTRY",
    price: 120,
    quantity: 1,
    cash_after: 9880,
    position_after: 1,
    metadata: {
      channel_id: "partial-points-channel",
      fill_candle_index: 13,
      fill_price: 120,
      channel_geometry: {
        schema_version: "fvg_parallel_channel_v1",
        channel_id: "partial-points-channel",
        window_start_index: 10,
        window_end_index: 12,
        lower_anchor_1_index: 10,
        lower_line: { slope: 1, intercept: 100 },
        upper_line: { slope: 1, intercept: 110 },
        width: 10,
      },
    },
  },
];

const partialPointOverlays = buildFvgChannelOverlays(partialPointMetadataTrades);
assert.equal(partialPointOverlays.length, 1);
assert.deepEqual(partialPointOverlays[0].points.map((point) => point.label), ["L1", "E"]);
assert.equal(partialPointOverlays[0].segmentStartIndex, 10);
assert.equal(partialPointOverlays[0].segmentEndIndex, 13);

const nestedOnlyTrades: BacktestTrade[] = [
  {
    id: 4,
    sequence: 4,
    candle_open_time: "2026-05-20T00:05:00Z",
    signal: "LONG_EXIT",
    price: 114,
    quantity: 1,
    cash_after: 10010,
    position_after: 0,
    metadata: {
      exit_metadata: {
        channel_id: "nested-channel",
        exit_candle_index: 5,
        channel_geometry: channelGeometry(0),
      },
    },
  },
];

assert.equal(buildFvgChannelOverlays(nestedOnlyTrades).length, 1);

const graphPoints: BacktestGraphPoint[] = [
  {
    id: 1,
    sequence: 1,
    candle_open_time: "2026-05-20T00:03:00Z",
    close_price: 104,
    cash: 10000,
    position: 0,
    equity: 10000,
    trade_id: null,
    signal: null,
    metadata: {
      trades: [
        {
          channel_id: "graph-channel",
          channel_geometry: channelGeometry(0),
        },
      ],
    },
  },
];

assert.equal(buildFvgChannelOverlays([], graphPoints).length, 1);
