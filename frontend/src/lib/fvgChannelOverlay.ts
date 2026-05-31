import type { BacktestGraphPoint, BacktestTrade } from "../types/api";

type AnyRecord = Record<string, unknown>;

export type ChannelLineModel = {
  slope: number;
  intercept: number;
};

export type ChannelPointModel = {
  index: number;
  price: number;
  label: string;
  kind: "lower-anchor" | "upper-touch" | "entry" | "exit";
};

export type FvgChannelOverlayModel = {
  schemaVersion: string;
  channelId: string | null;
  channelCandidateSource: string | null;
  lowerLine: ChannelLineModel;
  upperLine: ChannelLineModel;
  windowStartIndex: number;
  windowEndIndex: number;
  segmentStartIndex: number;
  segmentEndIndex: number;
  width: number;
  points: ChannelPointModel[];
};

export type ProjectedLine = {
  x1Index: number;
  y1: number;
  x2Index: number;
  y2: number;
};

export type ProjectedChannelSegment = {
  overlay: FvgChannelOverlayModel;
  lowerLine: ProjectedLine;
  upperLine: ProjectedLine;
  points: ChannelPointModel[];
};

function asRecord(value: unknown): AnyRecord | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as AnyRecord) : null;
}

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}

function lineValue(line: ChannelLineModel, index: number): number {
  return line.slope * index + line.intercept;
}

export function buildFvgChannelOverlays(
  trades: BacktestTrade[],
  graphPoints: BacktestGraphPoint[] = [],
): FvgChannelOverlayModel[] {
  const candidates = [...trades, ...channelRowsFromGraphPoints(graphPoints)];
  const overlays = new Map<string, FvgChannelOverlayModel>();

  for (const candidate of candidates) {
    const record = candidate as unknown as AnyRecord;
    const geometry = channelGeometryFromRecord(record);
    if (!geometry) continue;
    const lowerLine = parseLine(asRecord(geometry.lower_line));
    const upperLine = parseLine(asRecord(geometry.upper_line));
    const windowStartIndex = num(geometry.window_start_index);
    const windowEndIndex = num(geometry.window_end_index);
    const width = num(geometry.width);
    if (!lowerLine || !upperLine || windowStartIndex === null || windowEndIndex === null || width === null) {
      continue;
    }

    const channelId = channelIdFromRecord(record, geometry);
    const key = channelId ?? geometryKey(geometry);
    if (overlays.has(key)) continue;

    const relatedTrades = trades.filter((trade) => tradeBelongsToChannel(trade, channelId, geometry));
    const tradePointIndex = (
      tradeEntryIndex(record)
      ?? relatedTrades.map((trade) => tradeEntryIndex(trade as unknown as AnyRecord)).find((value) => value !== null)
      ?? tradePrimaryIndex(record)
      ?? relatedTrades.map((trade) => tradePrimaryIndex(trade as unknown as AnyRecord)).find((value) => value !== null)
      ?? windowEndIndex
    );
    const segmentStartIndex = firstConstructionIndex(geometry, windowStartIndex);
    const points = channelPointsFromGeometry(geometry, lowerLine, upperLine);
    collectTradeMarkers(relatedTrades, points);

    overlays.set(key, {
      schemaVersion: String(geometry.schema_version ?? "fvg_parallel_channel_v1"),
      channelId,
      channelCandidateSource: channelCandidateSourceFromRecord(record),
      lowerLine,
      upperLine,
      windowStartIndex,
      windowEndIndex,
      segmentStartIndex,
      segmentEndIndex: Math.max(segmentStartIndex, tradePointIndex),
      width,
      points,
    });
  }

  return Array.from(overlays.values()).sort((left, right) => left.segmentStartIndex - right.segmentStartIndex);
}

export function buildFvgChannelOverlay(
  trades: BacktestTrade[],
  graphPoints: BacktestGraphPoint[] = [],
): FvgChannelOverlayModel | null {
  return buildFvgChannelOverlays(trades, graphPoints)[0] ?? null;
}

export function projectChannelLine(
  line: ChannelLineModel,
  fromIndex: number,
  toIndex: number,
): ProjectedLine {
  return {
    x1Index: fromIndex,
    y1: lineValue(line, fromIndex),
    x2Index: toIndex,
    y2: lineValue(line, toIndex),
  };
}

export function projectChannelSegments(
  overlays: FvgChannelOverlayModel[] | null,
  fromIndex: number,
  toIndex: number,
): ProjectedChannelSegment[] {
  if (!overlays?.length) return [];
  return overlays.flatMap((overlay) => {
    const segmentStart = Math.max(fromIndex, overlay.segmentStartIndex);
    const segmentEnd = Math.min(toIndex, overlay.segmentEndIndex);
    if (segmentEnd < segmentStart) return [];
    return [{
      overlay,
      lowerLine: projectChannelLine(overlay.lowerLine, segmentStart, segmentEnd),
      upperLine: projectChannelLine(overlay.upperLine, segmentStart, segmentEnd),
      points: overlay.points.filter((point) => point.index >= fromIndex && point.index <= toIndex),
    }];
  });
}

export function channelOverlayValues(
  overlays: FvgChannelOverlayModel[] | FvgChannelOverlayModel | null,
  fromIndex: number,
  toIndex: number,
): number[] {
  if (!overlays) return [];
  const overlayList = Array.isArray(overlays) ? overlays : [overlays];
  return projectChannelSegments(overlayList, fromIndex, toIndex).flatMap((segment) => [
    segment.lowerLine.y1,
    segment.lowerLine.y2,
    segment.upperLine.y1,
    segment.upperLine.y2,
    ...segment.points.map((point) => point.price),
  ]);
}

function parseLine(value: AnyRecord | null): ChannelLineModel | null {
  const slope = num(value?.slope);
  const intercept = num(value?.intercept);
  return slope === null || intercept === null ? null : { slope, intercept };
}

function channelGeometryFromRecord(row: AnyRecord): AnyRecord | null {
  const metadata = asRecord(row.metadata);
  const exitMetadata = asRecord(metadata?.exit_metadata);
  return (
    asRecord(row.channel_geometry)
    ?? asRecord(row.fvg_channel)
    ?? asRecord(metadata?.channel_geometry)
    ?? asRecord(metadata?.fvg_channel)
    ?? asRecord(exitMetadata?.channel_geometry)
    ?? asRecord(exitMetadata?.fvg_channel)
  );
}

function channelIdFromRecord(row: AnyRecord, geometry: AnyRecord): string | null {
  const metadata = asRecord(row.metadata);
  const exitMetadata = asRecord(metadata?.exit_metadata);
  return (
    text(row.channel_id)
    ?? text(metadata?.channel_id)
    ?? text(exitMetadata?.channel_id)
    ?? text(geometry.channel_id)
  );
}

function channelCandidateSourceFromRecord(row: AnyRecord): string | null {
  const metadata = asRecord(row.metadata);
  const exitMetadata = asRecord(metadata?.exit_metadata);
  return (
    text(row.channel_candidate_source)
    ?? text(metadata?.channel_candidate_source)
    ?? text(exitMetadata?.channel_candidate_source)
    ?? text(row.channel_scan_source)
    ?? text(metadata?.channel_scan_source)
    ?? text(exitMetadata?.channel_scan_source)
  );
}

function channelRowsFromGraphPoints(points: BacktestGraphPoint[]): AnyRecord[] {
  const rows: AnyRecord[] = [];
  for (const point of points) {
    const metadata = asRecord(point.metadata);
    if (!metadata) continue;
    if (channelGeometryFromRecord(metadata)) rows.push(metadata);
    const trades = Array.isArray(metadata.trades) ? metadata.trades : [];
    for (const trade of trades) {
      const record = asRecord(trade);
      if (record) rows.push(record);
    }
  }
  return rows;
}

function channelPointsFromGeometry(
  geometry: AnyRecord,
  lowerLine: ChannelLineModel,
  upperLine: ChannelLineModel,
): ChannelPointModel[] {
  const lowerAnchor1Index = num(geometry.lower_anchor_1_index);
  const lowerAnchor2Index = num(geometry.lower_anchor_2_index);
  const upperTouchIndex = num(geometry.upper_touch_index);
  const points: ChannelPointModel[] = [];
  if (lowerAnchor1Index !== null) {
    points.push({ index: lowerAnchor1Index, price: lineValue(lowerLine, lowerAnchor1Index), label: "L1", kind: "lower-anchor" });
  }
  if (upperTouchIndex !== null) {
    points.push({ index: upperTouchIndex, price: lineValue(upperLine, upperTouchIndex), label: "H1", kind: "upper-touch" });
  }
  if (lowerAnchor2Index !== null) {
    points.push({ index: lowerAnchor2Index, price: lineValue(lowerLine, lowerAnchor2Index), label: "L2", kind: "lower-anchor" });
  }
  return points;
}

function collectTradeMarkers(trades: BacktestTrade[], points: ChannelPointModel[]): void {
  for (const trade of trades) {
    const metadata = asRecord(trade.metadata);
    const fillIndex = num(metadata?.fill_candle_index);
    const exitIndex = num(metadata?.exit_candle_index ?? asRecord(metadata?.exit_metadata)?.exit_candle_index);
    const fillPrice = num(metadata?.fill_price);
    const exitPrice = num(metadata?.exit_price);
    if (fillIndex !== null && fillPrice !== null) {
      points.push({ index: fillIndex, price: fillPrice, label: "E", kind: "entry" });
    }
    if (exitIndex !== null && exitPrice !== null) {
      points.push({ index: exitIndex, price: exitPrice, label: "X", kind: "exit" });
    }
  }
}

function tradeBelongsToChannel(trade: BacktestTrade, channelId: string | null, geometry: AnyRecord): boolean {
  const record = trade as unknown as AnyRecord;
  const tradeGeometry = channelGeometryFromRecord(record);
  if (!tradeGeometry) return false;
  if (channelId) return channelIdFromRecord(record, tradeGeometry) === channelId;
  return geometryKey(tradeGeometry) === geometryKey(geometry);
}

function tradeBoundaryIndexes(trades: BacktestTrade[]): number[] {
  return Array.from(
    new Set(
      trades.flatMap((trade) => {
        const metadata = asRecord(trade.metadata);
        return [
          num(metadata?.fill_candle_index),
          num(metadata?.exit_candle_index ?? asRecord(metadata?.exit_metadata)?.exit_candle_index),
        ].filter((value): value is number => value !== null);
      }),
    ),
  ).sort((left, right) => left - right);
}

function tradePrimaryIndex(row: AnyRecord): number | null {
  const metadata = asRecord(row.metadata) ?? row;
  return num(metadata.fill_candle_index) ?? num(metadata.exit_candle_index ?? asRecord(metadata.exit_metadata)?.exit_candle_index);
}

function tradeEntryIndex(row: AnyRecord): number | null {
  const metadata = asRecord(row.metadata) ?? row;
  return num(metadata.fill_candle_index);
}

function firstConstructionIndex(geometry: AnyRecord, fallback: number): number {
  const indexes = [
    num(geometry.lower_anchor_1_index),
    num(geometry.upper_touch_index),
    num(geometry.lower_anchor_2_index),
    num(geometry.upper_anchor_1_index),
    num(geometry.lower_touch_index),
    num(geometry.upper_anchor_2_index),
  ].filter((value): value is number => value !== null);
  return indexes.length ? Math.min(...indexes) : fallback;
}

function geometryKey(geometry: AnyRecord): string {
  const identity = asRecord(geometry.channel_identity);
  if (identity) return JSON.stringify(identity);
  return JSON.stringify({
    window_start_index: geometry.window_start_index,
    window_end_index: geometry.window_end_index,
    lower_anchor_1_index: geometry.lower_anchor_1_index,
    lower_anchor_2_index: geometry.lower_anchor_2_index,
    upper_touch_index: geometry.upper_touch_index,
    lower_line: geometry.lower_line,
    upper_line: geometry.upper_line,
    width: geometry.width,
  });
}
