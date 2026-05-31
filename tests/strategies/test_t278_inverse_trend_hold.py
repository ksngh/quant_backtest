import pandas as pd
import pytest

from quant_bitcoin.strategies.actions import StrategyActionType, StrategyQuantityMode
from quant_bitcoin.strategies.t278_inverse_trend_hold import build_inverse_trend_hold_actions


def test_build_inverse_trend_hold_actions_enters_short_and_exits_final_candle() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-05-20T00:00:00Z"), "close": 100.0},
            {"timestamp": pd.Timestamp("2026-05-20T00:01:00Z"), "close": 99.0},
        ]
    )

    actions = build_inverse_trend_hold_actions(candles, variant_id="T278_TEST")

    assert [action.action_type for action in actions] == [
        StrategyActionType.ENTER_SHORT,
        StrategyActionType.EXIT_SHORT,
    ]
    assert actions[0].requested_price == 100.0
    assert actions[1].requested_price == 99.0
    assert actions[1].quantity == 1.0
    assert actions[1].quantity_mode == StrategyQuantityMode.POSITION_RATIO
    assert actions[0].metadata["variant_id"] == "T278_TEST"


def test_build_inverse_trend_hold_actions_rejects_unsorted_candles() -> None:
    candles = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-05-20T00:01:00Z"), "close": 99.0},
            {"timestamp": pd.Timestamp("2026-05-20T00:00:00Z"), "close": 100.0},
        ]
    )

    with pytest.raises(ValueError, match="sorted ascending"):
        build_inverse_trend_hold_actions(candles, variant_id="T278_TEST")
