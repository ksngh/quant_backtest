import type { BacktestRunDetailResponse, BacktestRunListItem } from "../types/api";

export function configuredStartingCash(detail: BacktestRunDetailResponse): number {
  return detail.run.starting_cash ?? detail.summary.starting_cash;
}

export function listItemStartingCash(run: BacktestRunListItem): number | null {
  return typeof run.summary.starting_cash === "number" ? run.summary.starting_cash : null;
}

export function hasStartingCashMismatch(detail: BacktestRunDetailResponse): boolean {
  return (
    typeof detail.run.starting_cash === "number"
    && typeof detail.summary.starting_cash === "number"
    && detail.run.starting_cash !== detail.summary.starting_cash
  );
}
