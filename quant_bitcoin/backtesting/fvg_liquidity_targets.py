"""No-lookahead FVG structural liquidity target resolver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class FvgLiquidityTargetConfig:
    require_liquidity_target: bool = False
    minimum_target_r: float = 0.0
    max_targets: int = 3

    def __post_init__(self) -> None:
        if self.minimum_target_r < 0:
            raise ValueError("minimum_target_r must be non-negative")
        if self.max_targets < 1:
            raise ValueError("max_targets must be at least 1")


@dataclass(frozen=True)
class FvgLiquidityTargetResult:
    targets: tuple[float, ...]
    metadata: dict[str, Any]


def resolve_fvg_liquidity_targets(
    event: Any,
    pivot_rows: pd.DataFrame,
    *,
    config: FvgLiquidityTargetConfig | None = None,
) -> FvgLiquidityTargetResult:
    """Resolve prior confirmed pivot liquidity targets for one FVG event."""

    cfg = config or FvgLiquidityTargetConfig()
    _validate_pivots(pivot_rows)
    entry = float(getattr(event, "entry_reference"))
    stop = float(getattr(event, "stop_reference"))
    risk = abs(entry - stop)
    direction = str(getattr(event, "direction")).upper()
    event_index = int(getattr(event, "end_index"))

    candidates: list[dict[str, Any]] = []
    visible = pivot_rows[pd.to_numeric(pivot_rows["confirmed_index"], errors="coerce") <= event_index]
    for _, row in visible.iterrows():
        pivot_type = str(row["pivot_type"]).upper()
        price = float(row["price"])
        if direction == "BULLISH" and "HIGH" not in pivot_type:
            continue
        if direction == "BEARISH" and "LOW" not in pivot_type:
            continue
        if direction == "BULLISH" and price <= entry:
            continue
        if direction == "BEARISH" and price >= entry:
            continue
        target_r = abs(price - entry) / risk if risk > 0 else None
        if target_r is None or target_r < cfg.minimum_target_r:
            continue
        candidates.append(
            {
                "price": price,
                "target_r": target_r,
                "pivot_type": pivot_type,
                "pivot_index": int(row["pivot_index"]),
                "confirmed_index": int(row["confirmed_index"]),
                "source": "confirmed_pivot",
            }
        )

    ordered = sorted(candidates, key=lambda item: abs(float(item["price"]) - entry))
    deduped: list[dict[str, Any]] = []
    seen: set[float] = set()
    for candidate in ordered:
        key = round(float(candidate["price"]), 10)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
        if len(deduped) >= cfg.max_targets:
            break

    targets = tuple(float(item["price"]) for item in deduped)
    missing_reason = None
    if not targets:
        missing_reason = "NO_ACTIONABLE_CONFIRMED_PIVOT_TARGET"
    return FvgLiquidityTargetResult(
        targets=targets,
        metadata={
            "schema_version": "fvg_liquidity_targets_v1",
            "enabled": True,
            "direction": direction,
            "entry_reference": entry,
            "stop_reference": stop,
            "risk_per_unit": risk,
            "target_count": len(targets),
            "targets": tuple(deduped),
            "missing_target_reason": missing_reason,
            "minimum_target_r": cfg.minimum_target_r,
            "require_liquidity_target": cfg.require_liquidity_target,
            "source": "confirmed_pivots",
            "caveat": "OHLCV pivot-derived structure target, not order-book liquidity.",
        },
    )


def _validate_pivots(pivot_rows: pd.DataFrame) -> None:
    if not isinstance(pivot_rows, pd.DataFrame):
        raise ValueError("pivot_rows must be a pandas DataFrame")
    missing = [
        column
        for column in ("pivot_type", "price", "pivot_index", "confirmed_index")
        if column not in pivot_rows.columns
    ]
    if missing:
        raise ValueError(f"pivot_rows missing required columns: {', '.join(missing)}")
