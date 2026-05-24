from pathlib import Path
import ast

import pandas as pd
import pytest

from quant_bitcoin.backtesting.intrabar_policy import IntrabarPolicyConfig, IntrabarSequencingMode
from quant_bitcoin.patterns import (
    BreakEvenSettings,
    PartialExitSettings,
    PatternExitReason,
    RiskExitConfig,
    SoftInvalidationRule,
    TimeStopSettings,
    TrailingStopSettings,
    create_risk_exit_plan,
    simulate_pattern_exit,
)
from quant_bitcoin.risk.exit_simulation import INTRABAR_PRECEDENCE_POLICY


def _candles(rows: list[dict]) -> pd.DataFrame:
    base = []
    for index, row in enumerate(rows):
        candle = {
            "timestamp": f"2026-05-18T00:{index:02d}:00Z",
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
        }
        candle.update(row)
        base.append(candle)
    return pd.DataFrame(base)


def _plan(direction: str = "LONG", **config_overrides):
    config_values = {
        "atr_buffer_multiplier": 0.0,
        "break_even": BreakEvenSettings(enabled=False),
        "trailing_stop": TrailingStopSettings(enabled=False),
        "partial_exits": (),
    }
    config_values.update(config_overrides)
    if direction == "LONG":
        return create_risk_exit_plan(
            direction="LONG",
            entry_price=100.0,
            structural_stop=95.0,
            atr=10.0,
            config=RiskExitConfig(**config_values),
        )
    return create_risk_exit_plan(
        direction="SHORT",
        entry_price=100.0,
        structural_stop=105.0,
        atr=10.0,
        config=RiskExitConfig(**config_values),
    )


def test_long_hard_stop_hit() -> None:
    result = simulate_pattern_exit(_plan(), _candles([{"low": 94.0, "close": 95.0}]))

    assert result.final_reason == PatternExitReason.HARD_STOP
    assert result.final_price == pytest.approx(95.0)
    assert result.remaining_quantity_ratio == pytest.approx(0.0)
    assert result.events[0].metadata["intrabar_precedence_policy"] == INTRABAR_PRECEDENCE_POLICY
    assert result.events[0].metadata["ambiguous_stop_target"] is False


def test_short_hard_stop_hit() -> None:
    result = simulate_pattern_exit(_plan("SHORT"), _candles([{"high": 106.0, "close": 105.0}]))

    assert result.final_reason == PatternExitReason.HARD_STOP
    assert result.final_price == pytest.approx(105.0)
    assert result.events[0].metadata["intrabar_precedence_policy"] == INTRABAR_PRECEDENCE_POLICY
    assert result.events[0].metadata["ambiguous_stop_target"] is False


def test_long_target_only_hit() -> None:
    result = simulate_pattern_exit(_plan(), _candles([{"high": 106.0, "low": 99.0, "close": 104.0}]))
    assert result.final_reason == PatternExitReason.TAKE_PROFIT


def test_short_target_only_hit() -> None:
    result = simulate_pattern_exit(_plan("SHORT"), _candles([{"high": 101.0, "low": 94.0, "close": 96.0}]))
    assert result.final_reason == PatternExitReason.TAKE_PROFIT


def test_tp1_tp2_tp3_hit_sequencing() -> None:
    result = simulate_pattern_exit(
        _plan(
            partial_exits=(
                PartialExitSettings(1.0, 0.25),
                PartialExitSettings(2.0, 0.25),
                PartialExitSettings(3.0, 0.5),
            )
        ),
        _candles([
            {"high": 105.0, "low": 100.0, "close": 104.0},
            {"high": 110.0, "low": 104.0, "close": 109.0},
            {"high": 115.0, "low": 109.0, "close": 115.0},
        ]),
    )

    assert [event.target_name for event in result.events] == ["TP1", "TP2", "TP3"]
    assert [event.quantity_ratio for event in result.events] == pytest.approx([0.25, 0.25, 0.5])
    assert result.final_reason == PatternExitReason.TAKE_PROFIT
    assert result.remaining_quantity_ratio == pytest.approx(0.0)


def test_same_candle_stop_takes_precedence_over_target() -> None:
    result = simulate_pattern_exit(
        _plan(),
        _candles([{"high": 106.0, "low": 94.0, "close": 102.0}]),
    )

    assert result.final_reason == PatternExitReason.HARD_STOP
    assert result.events[0].metadata["precedence"] == INTRABAR_PRECEDENCE_POLICY
    assert result.events[0].metadata["intrabar_precedence_policy"] == INTRABAR_PRECEDENCE_POLICY
    assert result.events[0].metadata["ambiguous_stop_target"] is True
    assert result.events[0].metadata["intrabar_policy"] == "CONSERVATIVE"
    assert result.events[0].metadata["decision_outcome"] == "STOP"


def test_same_candle_target_first_policy_exits_at_target() -> None:
    result = simulate_pattern_exit(
        _plan(),
        _candles([{"high": 106.0, "low": 94.0, "close": 102.0}]),
        intrabar_policy_config=IntrabarPolicyConfig(mode=IntrabarSequencingMode.TARGET_FIRST),
    )

    assert result.final_reason == PatternExitReason.TAKE_PROFIT
    assert result.final_price == pytest.approx(105.0)
    assert result.events[0].metadata["intrabar_policy"] == "TARGET_FIRST"
    assert result.events[0].metadata["decision_outcome"] == "TARGET"


def test_same_candle_skip_ambiguous_policy_creates_no_exit() -> None:
    result = simulate_pattern_exit(
        _plan(),
        _candles([{"high": 106.0, "low": 94.0, "close": 102.0}]),
        intrabar_policy_config=IntrabarPolicyConfig(mode=IntrabarSequencingMode.SKIP_AMBIGUOUS),
    )

    assert result.events == ()
    assert result.final_reason == PatternExitReason.NO_EXIT


def test_short_same_candle_stop_takes_precedence_over_target() -> None:
    result = simulate_pattern_exit(
        _plan("SHORT"),
        _candles([{"high": 106.0, "low": 94.0, "close": 98.0}]),
    )
    assert result.final_reason == PatternExitReason.HARD_STOP
    assert result.events[0].metadata["precedence"] == INTRABAR_PRECEDENCE_POLICY
    assert result.events[0].metadata["ambiguous_stop_target"] is True


def test_time_stop_before_later_target() -> None:
    result = simulate_pattern_exit(
        _plan(time_stop=TimeStopSettings(max_bars_in_trade=1, required_r_multiple=1.0)),
        _candles([
            {"high": 102.0, "low": 99.0, "close": 101.0},
            {"high": 110.0, "low": 101.0, "close": 109.0},
        ]),
    )

    assert result.final_reason == PatternExitReason.TIME_STOP
    assert result.bars_evaluated == 1


def test_soft_invalidation_exit() -> None:
    result = simulate_pattern_exit(
        _plan(),
        _candles([{"high": 102.0, "low": 96.0, "close": 98.0}]),
        soft_invalidation=SoftInvalidationRule("close < neckline", reference_price=99.0),
    )

    assert result.final_reason == PatternExitReason.SOFT_INVALIDATION
    assert result.final_price == pytest.approx(98.0)


def test_break_even_stop_movement() -> None:
    result = simulate_pattern_exit(
        _plan(break_even=BreakEvenSettings(enabled=True, trigger_r_multiple=1.0)),
        _candles([{"high": 106.0, "low": 99.0, "close": 101.0}]),
    )

    assert result.final_reason == PatternExitReason.HARD_STOP
    assert result.final_price == pytest.approx(100.0)
    assert result.events[0].metadata["be_trailing_sequence"] == "favorable-extreme updates are applied before stop/target checks"


def test_trailing_stop_movement() -> None:
    result = simulate_pattern_exit(
        _plan(trailing_stop=TrailingStopSettings(enabled=True, activation_r_multiple=1.0, trail_atr_multiplier=0.2)),
        _candles([{"high": 106.0, "low": 103.0, "close": 104.0}]),
    )

    assert result.final_reason == PatternExitReason.HARD_STOP
    assert result.final_price == pytest.approx(104.0)


def test_partial_exit_recording() -> None:
    result = simulate_pattern_exit(
        _plan(partial_exits=(PartialExitSettings(1.0, 0.5), PartialExitSettings(2.0, 0.5))),
        _candles([
            {"high": 105.0, "low": 100.0, "close": 105.0},
            {"high": 110.0, "low": 105.0, "close": 110.0},
        ]),
    )

    assert [event.quantity_ratio for event in result.events] == pytest.approx([0.5, 0.5])
    assert [event.remaining_quantity_ratio for event in result.events] == pytest.approx([0.5, 0.0])


def test_simulation_does_not_mutate_caller_candles() -> None:
    candles = _candles([{"high": 102.0}])
    original = candles.copy(deep=True)

    simulate_pattern_exit(_plan(), candles)

    pd.testing.assert_frame_equal(candles, original)


def test_exit_simulation_module_does_not_import_exchange_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/patterns/exit_simulation.py")
    tree = ast.parse(source_path.read_text())
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)

    assert not any(module.startswith("quant_bitcoin.market_data") for module in imported_modules)
    assert not any(module.startswith("quant_bitcoin.execution") for module in imported_modules)
    assert not any("binance" in module.lower() for module in imported_modules)
