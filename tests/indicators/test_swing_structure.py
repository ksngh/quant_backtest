import pandas as pd
import pytest

from quant_bitcoin.indicators.pivots import PivotType
from quant_bitcoin.indicators.swing_structure import (
    MarketStructureStatus,
    SwingLabel,
    SwingStructureConfig,
    classify_high,
    classify_low,
    classify_market_status,
    classify_swing_structure,
    swing_structure_alignment_feature,
)


def _pivots(rows: list[dict[str, object]]) -> pd.DataFrame:
    base_time = pd.Timestamp("2026-05-16T00:00:00Z")
    normalized = []
    for index, row in enumerate(rows):
        normalized.append(
            {
                "symbol": row.get("symbol", "BTCUSDT"),
                "pivot_timestamp": row.get(
                    "pivot_timestamp", base_time + pd.Timedelta(minutes=5 * index)
                ),
                "confirmed_timestamp": row.get(
                    "confirmed_timestamp", base_time + pd.Timedelta(minutes=5 * index + 5)
                ),
                "pivot_index": row.get("pivot_index", index),
                "confirmed_index": row.get("confirmed_index", index + 1),
                "pivot_type": row["pivot_type"],
                "price": row.get("price"),
                "is_confirmed": row.get("is_confirmed", True),
                **({"atr": row["atr"]} if "atr" in row else {}),
            }
        )
    return pd.DataFrame(normalized)


def test_classifies_higher_highs_and_higher_lows_as_uptrend() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 80.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 110.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 90.0},
        ]
    )

    structures = classify_swing_structure(pivots)

    assert list(structures["swing_label"]) == [
        SwingLabel.UNKNOWN.value,
        SwingLabel.UNKNOWN.value,
        SwingLabel.HH.value,
        SwingLabel.HL.value,
    ]
    assert structures.iloc[-1]["market_structure_status"] == (
        MarketStructureStatus.UPTREND.value
    )
    assert structures.iloc[2]["previous_same_type_pivot_price"] == 100.0
    assert structures.iloc[2]["change_rate"] == pytest.approx(0.10)


def test_classifies_lower_highs_and_lower_lows_as_downtrend() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 110.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 90.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 80.0},
        ]
    )

    structures = classify_swing_structure(pivots)

    assert list(structures["swing_label"]) == [
        SwingLabel.UNKNOWN.value,
        SwingLabel.UNKNOWN.value,
        SwingLabel.LH.value,
        SwingLabel.LL.value,
    ]
    assert structures.iloc[-1]["market_structure_status"] == (
        MarketStructureStatus.DOWNTREND.value
    )


def test_returns_range_for_mixed_structure() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 80.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 110.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 70.0},
        ]
    )

    structures = classify_swing_structure(pivots)

    assert list(structures["swing_label"]) == [
        SwingLabel.UNKNOWN.value,
        SwingLabel.UNKNOWN.value,
        SwingLabel.HH.value,
        SwingLabel.LL.value,
    ]
    assert structures.iloc[-1]["market_structure_status"] == (
        MarketStructureStatus.RANGE.value
    )


def test_returns_transition_when_uptrend_breaks_with_lower_low() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 80.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 110.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 90.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 70.0},
        ]
    )

    structures = classify_swing_structure(pivots)

    assert structures.iloc[3]["market_structure_status"] == (
        MarketStructureStatus.UPTREND.value
    )
    assert structures.iloc[-1]["swing_label"] == SwingLabel.LL.value
    assert structures.iloc[-1]["market_structure_status"] == (
        MarketStructureStatus.TRANSITION.value
    )


def test_returns_transition_when_downtrend_breaks_with_higher_high() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 110.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 90.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 80.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 120.0},
        ]
    )

    structures = classify_swing_structure(pivots)

    assert structures.iloc[3]["market_structure_status"] == (
        MarketStructureStatus.DOWNTREND.value
    )
    assert structures.iloc[-1]["swing_label"] == SwingLabel.HH.value
    assert structures.iloc[-1]["market_structure_status"] == (
        MarketStructureStatus.TRANSITION.value
    )


def test_ignores_unconfirmed_and_unsupported_pivots() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {
                "pivot_type": PivotType.PIVOT_HIGH.value,
                "price": 120.0,
                "is_confirmed": False,
            },
            {"pivot_type": PivotType.BOTH.value, "price": 90.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 110.0},
        ]
    )

    structures = classify_swing_structure(pivots)

    assert len(structures) == 2
    assert list(structures["swing_label"]) == [
        SwingLabel.UNKNOWN.value,
        SwingLabel.HH.value,
    ]


def test_handles_equal_high_and_low_default_as_noise() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 80.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_LOW.value, "price": 80.0},
        ]
    )

    structures = classify_swing_structure(pivots)

    assert list(structures["swing_label"])[-2:] == [
        SwingLabel.EQUAL_OR_NOISE.value,
        SwingLabel.EQUAL_OR_NOISE.value,
    ]
    assert structures.iloc[-1]["market_structure_status"] == (
        MarketStructureStatus.RANGE.value
    )


def test_can_label_equal_high_and_low_when_equal_prices_are_not_ignored() -> None:
    config = SwingStructureConfig(ignore_equal_price=False)
    high_label, high_change_rate = classify_high(100.0, 100.0, None, config)
    low_label, low_change_rate = classify_low(80.0, 80.0, None, config)

    assert high_label == SwingLabel.EQUAL_HIGH.value
    assert high_change_rate == 0.0
    assert low_label == SwingLabel.EQUAL_LOW.value
    assert low_change_rate == 0.0


def test_percentage_threshold_labels_small_changes_as_noise() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.05},
        ]
    )

    structures = classify_swing_structure(
        pivots,
        SwingStructureConfig(minimum_price_change_rate=0.001),
    )

    assert structures.iloc[-1]["swing_label"] == SwingLabel.EQUAL_OR_NOISE.value
    assert structures.iloc[-1]["change_rate"] == pytest.approx(0.0005)


def test_atr_threshold_labels_small_absolute_changes_as_noise() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0, "atr": 10.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 104.0, "atr": 10.0},
        ]
    )

    structures = classify_swing_structure(
        pivots,
        SwingStructureConfig(
            use_atr_threshold=True,
            minimum_price_change_atr_multiplier=0.5,
        ),
    )

    assert structures.iloc[-1]["swing_label"] == SwingLabel.EQUAL_OR_NOISE.value


def test_atr_threshold_returns_unknown_when_atr_is_missing() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0},
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": 110.0},
        ]
    )

    structures = classify_swing_structure(
        pivots,
        SwingStructureConfig(
            use_atr_threshold=True,
            minimum_price_change_atr_multiplier=0.5,
        ),
    )

    assert structures.iloc[-1]["swing_label"] == SwingLabel.UNKNOWN.value
    assert structures.iloc[-1]["change_rate"] == pytest.approx(0.10)


def test_missing_current_pivot_price_returns_unknown_status() -> None:
    pivots = _pivots(
        [
            {"pivot_type": PivotType.PIVOT_HIGH.value, "price": None},
        ]
    )

    structures = classify_swing_structure(pivots)

    assert len(structures) == 1
    assert structures.iloc[0]["pivot_price"] is None
    assert structures.iloc[0]["swing_label"] == SwingLabel.UNKNOWN.value
    assert structures.iloc[0]["market_structure_status"] == (
        MarketStructureStatus.UNKNOWN.value
    )


def test_rejects_missing_required_pivot_columns() -> None:
    pivots = _pivots(
        [{"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0}]
    ).drop(columns=["symbol"])

    with pytest.raises(ValueError, match="missing required columns: symbol"):
        classify_swing_structure(pivots)


def test_rejects_non_positive_prices() -> None:
    pivots = _pivots(
        [{"pivot_type": PivotType.PIVOT_HIGH.value, "price": 0.0}]
    )

    with pytest.raises(ValueError, match="non-positive price"):
        classify_swing_structure(pivots)


@pytest.mark.parametrize(
    "config_kwargs, error",
    [
        (
            {"minimum_price_change_rate": -0.1},
            "minimum_price_change_rate must be non-negative",
        ),
        ({"structure_window": 0}, "structure_window must be at least 1"),
        (
            {"minimum_price_change_atr_multiplier": -0.1},
            "minimum_price_change_atr_multiplier must be non-negative",
        ),
        (
            {"use_atr_threshold": True},
            "minimum_price_change_atr_multiplier is required",
        ),
    ],
)
def test_rejects_invalid_config_parameters(
    config_kwargs: dict[str, object], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        SwingStructureConfig(**config_kwargs)


def test_contract_output_columns_and_market_status_helper_are_stable() -> None:
    pivots = _pivots(
        [{"pivot_type": PivotType.PIVOT_HIGH.value, "price": 100.0}]
    )

    structures = classify_swing_structure(pivots)

    assert list(structures.columns) == [
        "symbol",
        "timestamp",
        "pivot_timestamp",
        "pivot_type",
        "pivot_price",
        "previous_same_type_pivot_price",
        "swing_label",
        "change_rate",
        "market_structure_status",
    ]
    assert classify_market_status(
        [SwingLabel.HH.value],
        [SwingLabel.HL.value],
        MarketStructureStatus.UNKNOWN.value,
    ) == MarketStructureStatus.UPTREND.value


def test_swing_alignment_uses_only_pivots_confirmed_before_event_index() -> None:
    pivots = _pivots(
        [
            {
                "pivot_type": PivotType.PIVOT_HIGH.value,
                "price": 100.0,
                "pivot_index": 0,
                "confirmed_index": 1,
            },
            {
                "pivot_type": PivotType.PIVOT_LOW.value,
                "price": 80.0,
                "pivot_index": 1,
                "confirmed_index": 2,
            },
            {
                "pivot_type": PivotType.PIVOT_HIGH.value,
                "price": 110.0,
                "pivot_index": 2,
                "confirmed_index": 3,
            },
            {
                "pivot_type": PivotType.PIVOT_LOW.value,
                "price": 90.0,
                "pivot_index": 3,
                "confirmed_index": 4,
            },
            {
                "pivot_type": PivotType.PIVOT_HIGH.value,
                "price": 70.0,
                "pivot_index": 6,
                "confirmed_index": 8,
            },
            {
                "pivot_type": PivotType.PIVOT_LOW.value,
                "price": 60.0,
                "pivot_index": 7,
                "confirmed_index": 9,
            },
        ]
    )

    feature = swing_structure_alignment_feature(
        pivots,
        current_index=5,
        direction="BULLISH",
    )

    assert feature["source"] == "observed_swing_structure_alignment"
    assert feature["context"] == "BULLISH_STRUCTURE_ALIGNED"
    assert feature["market_structure_status"] == MarketStructureStatus.UPTREND.value
    assert feature["feature_window_pivots"] == 4
