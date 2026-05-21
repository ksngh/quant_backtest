import type {
  BacktestRunDetailResponse,
  BacktestRunListFilters,
  BacktestRunsListResponse,
  HealthResponse,
} from "../types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_BACKTEST_API_BASE_URL ?? "http://localhost:8000";

function buildUrl(path: string, query?: Record<string, string | number | undefined>) {
  const base = API_BASE_URL.replace(/\/$/, "");
  const url = new URL(`${base}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>(buildUrl("/api/health"));
}

export async function listBacktestRuns(
  filters: BacktestRunListFilters = {},
): Promise<BacktestRunsListResponse> {
  return getJson<BacktestRunsListResponse>(buildUrl("/api/backtest-runs", filters));
}

export async function getBacktestRun(
  runId: number,
): Promise<BacktestRunDetailResponse> {
  return getJson<BacktestRunDetailResponse>(buildUrl(`/api/backtest-runs/${runId}`));
}
