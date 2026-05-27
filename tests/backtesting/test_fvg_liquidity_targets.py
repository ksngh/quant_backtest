from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from quant_bitcoin.backtesting.fvg_liquidity_targets import (
    FvgLiquidityTargetConfig,
    resolve_fvg_liquidity_targets,
)


def _event(direction: str = "BULLISH", entry: float = 105.0, stop: float = 100.0):
    return SimpleNamespace(direction=direction, entry_reference=entry, stop_reference=stop, end_index=5)


def _pivots(rows: list[dict]) -> pd.DataFrame:
    base = []
    for index, row in enumerate(rows):
        item = {
            "pivot_type": "PIVOT_HIGH",
            "price": 110.0 + index,
            "pivot_index": index,
            "confirmed_index": index + 1,
        }
        item.update(row)
        base.append(item)
    return pd.DataFrame(base)


def test_bullish_resolves_prior_pivot_highs_above_entry() -> None:
    result = resolve_fvg_liquidity_targets(
        _event("BULLISH"),
        _pivots([
            {"pivot_type": "PIVOT_HIGH", "price": 112.0, "confirmed_index": 2},
            {"pivot_type": "PIVOT_LOW", "price": 98.0, "confirmed_index": 2},
        ]),
    )

    assert result.targets == pytest.approx((112.0,))
    assert result.metadata["targets"][0]["target_r"] == pytest.approx(1.4)
    assert result.metadata["missing_target_reason"] is None


def test_bearish_resolves_prior_pivot_lows_below_entry() -> None:
    result = resolve_fvg_liquidity_targets(
        _event("BEARISH", entry=105.0, stop=110.0),
        _pivots([
            {"pivot_type": "PIVOT_LOW", "price": 99.0, "confirmed_index": 2},
            {"pivot_type": "PIVOT_HIGH", "price": 112.0, "confirmed_index": 2},
        ]),
    )

    assert result.targets == pytest.approx((99.0,))
    assert result.metadata["targets"][0]["target_r"] == pytest.approx(1.2)


def test_wrong_side_and_unconfirmed_targets_are_excluded() -> None:
    result = resolve_fvg_liquidity_targets(
        _event("BULLISH"),
        _pivots([
            {"pivot_type": "PIVOT_HIGH", "price": 104.0, "confirmed_index": 2},
            {"pivot_type": "PIVOT_HIGH", "price": 112.0, "confirmed_index": 9},
        ]),
    )

    assert result.targets == ()
    assert result.metadata["missing_target_reason"] == "NO_ACTIONABLE_CONFIRMED_PIVOT_TARGET"


def test_duplicate_targets_are_deduped_by_price() -> None:
    result = resolve_fvg_liquidity_targets(
        _event("BULLISH"),
        _pivots([
            {"pivot_type": "PIVOT_HIGH", "price": 112.0, "confirmed_index": 2},
            {"pivot_type": "PIVOT_HIGH", "price": 112.0, "confirmed_index": 3},
            {"pivot_type": "PIVOT_HIGH", "price": 118.0, "confirmed_index": 4},
        ]),
    )

    assert result.targets == pytest.approx((112.0, 118.0))


def test_minimum_r_filter_excludes_close_targets() -> None:
    result = resolve_fvg_liquidity_targets(
        _event("BULLISH"),
        _pivots([
            {"pivot_type": "PIVOT_HIGH", "price": 107.0, "confirmed_index": 2},
            {"pivot_type": "PIVOT_HIGH", "price": 112.0, "confirmed_index": 3},
        ]),
        config=FvgLiquidityTargetConfig(minimum_target_r=1.0),
    )

    assert result.targets == pytest.approx((112.0,))


def test_resolver_rejects_missing_pivot_columns() -> None:
    with pytest.raises(ValueError, match="pivot_rows missing required columns"):
        resolve_fvg_liquidity_targets(_event("BULLISH"), pd.DataFrame([{"price": 1}]))
