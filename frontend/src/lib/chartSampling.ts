import type { ChartGraphSamplingMetadata } from "../types/api";

export type ChartSamplingNotice = {
  title: string;
  detail: string;
  markerDetail: string;
  markerWarning: boolean;
};

function countText(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
}

export function buildChartSamplingNotice(
  metadata: ChartGraphSamplingMetadata | null | undefined,
): ChartSamplingNotice | null {
  if (!metadata?.sampled) return null;

  const maxText = metadata.max_points === null
    ? "no explicit max"
    : `max ${countText(metadata.max_points)}`;
  const markerDetail = metadata.marker_points_preserved
    ? `All ${countText(metadata.marker_point_count)} marker points were preserved.`
    : `${countText(metadata.preserved_marker_point_count)} of ${countText(metadata.marker_point_count)} marker points fit inside the chart budget.`;

  return {
    title: "Chart Data Sampled",
    detail: `Showing ${countText(metadata.returned_point_count)} of ${countText(metadata.original_point_count)} saved graph points (${metadata.sampling_mode}, ${maxText}).`,
    markerDetail,
    markerWarning: !metadata.marker_points_preserved,
  };
}
