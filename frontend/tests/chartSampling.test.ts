import assert from "node:assert/strict";

import { buildChartSamplingNotice } from "../src/lib/chartSampling";
import type { ChartGraphSamplingMetadata } from "../src/types/api";

const sampledMetadata = {
  schema_version: "graph_sampling_v1",
  sampled: true,
  original_point_count: 120000,
  returned_point_count: 3000,
  max_points: 3000,
  sampling_mode: "preserve_markers",
  marker_point_count: 8,
  preserved_marker_point_count: 8,
  marker_points_preserved: true,
} satisfies ChartGraphSamplingMetadata;

const notice = buildChartSamplingNotice(sampledMetadata);

assert.equal(notice?.title, "Chart Data Sampled");
assert.ok(notice?.detail.includes("120,000"));
assert.ok(notice?.detail.includes("3,000"));
assert.equal(notice?.markerWarning, false);
assert.equal(notice?.markerDetail, "All 8 marker points were preserved.");

assert.equal(buildChartSamplingNotice({ ...sampledMetadata, sampled: false }), null);
assert.equal(buildChartSamplingNotice(null), null);

const limitedMarkers = buildChartSamplingNotice({
  ...sampledMetadata,
  marker_point_count: 120,
  preserved_marker_point_count: 100,
  marker_points_preserved: false,
});

assert.equal(limitedMarkers?.markerWarning, true);
assert.equal(limitedMarkers?.markerDetail, "100 of 120 marker points fit inside the chart budget.");
