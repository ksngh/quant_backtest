import pandas as pd
import pytest

from quant_bitcoin.indicators.support_resistance_zone import (
    SupportResistanceZoneConfig,
    ZoneStatus,
    ZoneType,
    detect_support_resistance_zones,
    support_resistance_proximity_feature,
)


def _pivots(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "BTCUSDT",
                "pivot_timestamp": f"2026-05-16T0{i}:00:00Z",
                "confirmed_timestamp": f"2026-05-16T0{i}:05:00Z",
                "pivot_index": i,
                "pivot_type": pivot_type,
                "price": price,
                "is_confirmed": is_confirmed,
            }
            for i, (pivot_type, price, is_confirmed) in enumerate(rows)
        ]
    )


def test_detects_support_zone_from_repeated_confirmed_lows() -> None:
    pivots = _pivots(
        [
            ("PIVOT_LOW", 1000.0, True),
            ("PIVOT_HIGH", 1300.0, True),
            ("PIVOT_LOW", 1004.0, True),
            ("PIVOT_HIGH", 1500.0, True),
        ]
    )

    zones = detect_support_resistance_zones(
        pivots,
        current_close=1015.0,
        atr=10.0,
        timestamp="2026-05-16T10:00:00Z",
        config=SupportResistanceZoneConfig(merge_overlapping_zones=False),
    )

    assert len(zones) == 2
    zone = zones.iloc[0]
    assert zone["zone_type"] == ZoneType.SUPPORT.value
    assert zone["zone_status"] == ZoneStatus.WEAK.value
    assert zone["center_price"] == pytest.approx(1002.0)
    assert zone["zone_low"] == pytest.approx(997.0)
    assert zone["zone_high"] == pytest.approx(1007.0)
    assert zone["touch_count"] == 2
    assert zone["pivot_indices"] == [0, 2]
    assert zone["zone_width"] == pytest.approx(5.0)
    assert zone["atr"] == pytest.approx(10.0)
    assert zone["is_broken"] == False
    assert zone["is_valid"] == True


def test_detects_broken_strong_resistance_zone_from_repeated_highs() -> None:
    pivots = _pivots(
        [
            ("PIVOT_HIGH", 1980.0, True),
            ("PIVOT_LOW", 1600.0, True),
            ("PIVOT_HIGH", 2010.0, True),
            ("PIVOT_LOW", 1550.0, True),
            ("PIVOT_HIGH", 2020.0, True),
        ]
    )

    zones = detect_support_resistance_zones(
        pivots,
        current_close=2100.0,
        atr=80.0,
        config=SupportResistanceZoneConfig(merge_overlapping_zones=False),
    )

    assert len(zones) == 3
    for _, zone in zones.iterrows():
        assert zone["zone_type"] == ZoneType.RESISTANCE.value
        assert zone["zone_status"] == ZoneStatus.BROKEN.value
        assert zone["touch_count"] == 3
        assert zone["is_broken"] == True
        assert zone["is_valid"] == True


def test_merges_overlapping_same_type_zones_when_enabled() -> None:
    pivots = _pivots(
        [
            ("PIVOT_LOW", 100.0, True),
            ("PIVOT_LOW", 101.0, True),
            ("PIVOT_LOW", 102.0, True),
        ]
    )

    zones = detect_support_resistance_zones(
        pivots,
        atr=4.0,
        config=SupportResistanceZoneConfig(merge_overlapping_zones=True),
    )

    assert len(zones) == 1
    zone = zones.iloc[0]
    assert zone["zone_type"] == ZoneType.SUPPORT.value
    assert zone["zone_status"] == ZoneStatus.STRONG.value
    assert zone["touch_count"] == 9
    assert zone["pivot_indices"] == [0, 1, 2]


def test_creates_mixed_zone_when_support_and_resistance_overlap() -> None:
    pivots = _pivots(
        [
            ("PIVOT_LOW", 1000.0, True),
            ("PIVOT_LOW", 1001.0, True),
            ("PIVOT_HIGH", 1002.0, True),
            ("PIVOT_HIGH", 1003.0, True),
        ]
    )

    zones = detect_support_resistance_zones(
        pivots,
        atr=6.0,
        config=SupportResistanceZoneConfig(merge_overlapping_zones=True),
    )

    assert len(zones) == 1
    zone = zones.iloc[0]
    assert zone["zone_type"] == ZoneType.MIXED.value
    assert zone["zone_status"] == ZoneStatus.STRONG.value
    assert zone["pivot_indices"] == [0, 1, 2, 3]
    assert zone["is_broken"] == False


def test_uses_percentage_fallback_when_atr_is_missing() -> None:
    pivots = _pivots(
        [
            ("PIVOT_LOW", 65000.0, True),
            ("PIVOT_LOW", 65100.0, True),
        ]
    )

    zones = detect_support_resistance_zones(pivots, atr=None)

    assert len(zones) == 1
    assert zones.iloc[0]["zone_width"] == pytest.approx(195.3)
    assert zones.iloc[0]["atr"] is None


def test_filters_unconfirmed_pivots_when_confirmation_is_required() -> None:
    pivots = _pivots(
        [
            ("PIVOT_LOW", 100.0, True),
            ("PIVOT_LOW", 101.0, False),
        ]
    )

    zones = detect_support_resistance_zones(pivots, atr=4.0)

    assert zones.empty


def test_respects_lookback_pivot_count() -> None:
    pivots = _pivots(
        [
            ("PIVOT_LOW", 100.0, True),
            ("PIVOT_LOW", 101.0, True),
            ("PIVOT_LOW", 150.0, True),
        ]
    )

    zones = detect_support_resistance_zones(
        pivots,
        atr=4.0,
        config=SupportResistanceZoneConfig(lookback_pivot_count=1),
    )

    assert zones.empty


def test_marks_very_wide_zone_invalid() -> None:
    pivots = _pivots(
        [
            ("PIVOT_LOW", 100.0, True),
            ("PIVOT_LOW", 101.0, True),
        ]
    )

    zones = detect_support_resistance_zones(pivots, atr=10.0)

    assert len(zones) == 1
    assert zones.iloc[0]["zone_status"] == ZoneStatus.INVALID.value
    assert zones.iloc[0]["is_valid"] == False


def test_returns_empty_zone_list_when_no_pivots_exist() -> None:
    zones = detect_support_resistance_zones(pd.DataFrame())

    assert zones.empty
    assert list(zones.columns)


def test_rejects_malformed_pivot_input_and_invalid_config() -> None:
    with pytest.raises(ValueError, match="missing required columns: price"):
        detect_support_resistance_zones(
            _pivots([("PIVOT_LOW", 100.0, True)]).drop(columns=["price"])
        )

    bad_type = _pivots([("BOTH", 100.0, True)])
    with pytest.raises(ValueError, match="unsupported pivot_type"):
        detect_support_resistance_zones(bad_type)

    with pytest.raises(ValueError, match="minimum_touch_count"):
        SupportResistanceZoneConfig(minimum_touch_count=0)


def test_support_proximity_uses_only_zones_confirmed_before_event_index() -> None:
    pivots = _pivots(
        [
            ("PIVOT_LOW", 100.0, True),
            ("PIVOT_HIGH", 130.0, True),
            ("PIVOT_LOW", 101.0, True),
            ("PIVOT_HIGH", 140.0, True),
            ("PIVOT_LOW", 80.0, True),
            ("PIVOT_LOW", 80.5, True),
        ]
    )
    pivots["confirmed_index"] = [1, 2, 3, 4, 8, 9]

    feature = support_resistance_proximity_feature(
        pivots,
        current_index=5,
        price=101.0,
        direction="BULLISH",
        atr=4.0,
        config=SupportResistanceZoneConfig(merge_overlapping_zones=False),
    )

    assert feature["source"] == "observed_support_resistance_proximity"
    assert feature["context"] == "NEAR_SUPPORT"
    assert feature["pivot_indices"] == (0, 2)
    assert feature["latest_confirmed_index"] == 4
    assert feature["confirmation_delay_bars"] == 1
