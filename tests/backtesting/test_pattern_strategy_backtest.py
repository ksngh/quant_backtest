from pathlib import Path
import ast

import pandas as pd
import pytest

from quant_bitcoin.backtesting import (
    DEFAULT_PATTERN,
    SUPPORTED_PATTERNS,
    PatternStrategyBacktestConfig,
    run_pattern_strategy_backtest,
    strategy_name_for_patterns,
    validate_pattern_selection,
)
from quant_bitcoin.backtesting.pattern_strategy import PATTERN_REGISTRY
from quant_bitcoin.indicators import AtrConfig, VolumeRatioConfig
from quant_bitcoin.patterns import (
    FairValueGapConfig,
    FairValueGapRiskExitConfig,
    PatternExitReason,
    RiskExitPlanStatus,
)


def _config(*, reaction_failure_bars: int = 20) -> PatternStrategyBacktestConfig:
    return PatternStrategyBacktestConfig(
        symbol="BTCUSDT",
        timeframe="1m",
        fair_value_gap=FairValueGapConfig(
            require_displacement_candle=False,
            minimum_volume_ratio=0.0,
            strong_volume_ratio=0.0,
            minimum_pattern_score=0.0,
            atr_config=AtrConfig(period=1),
            volume_ratio_config=VolumeRatioConfig(window=1),
        ),
        fair_value_gap_risk_exit=FairValueGapRiskExitConfig(
            reaction_failure_bars=reaction_failure_bars,
            partial_exits=(),
        ),
    )


def _candles(rows: list[tuple[str, float, float, float, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )


def _bullish_fvg_base() -> list[tuple[str, float, float, float, float, float]]:
    return [
        ("2026-05-18 00:00:00", 97.0, 100.0, 95.0, 98.0, 10.0),
        ("2026-05-18 00:01:00", 100.0, 112.0, 99.0, 111.0, 10.0),
        ("2026-05-18 00:02:00", 106.0, 110.0, 105.0, 108.0, 10.0),
    ]


def test_pattern_strategy_default_selection_is_fair_value_gap() -> None:
    config = PatternStrategyBacktestConfig()

    assert DEFAULT_PATTERN == "FAIR_VALUE_GAP"
    assert SUPPORTED_PATTERNS == (
        "FAIR_VALUE_GAP",
        "TRENDLINE_BREAK",
        "ORDER_BLOCK",
        "CUP_AND_HANDLE",
        "DIAMOND",
        "ADAM_AND_EVE",
    )
    assert config.patterns == ("FAIR_VALUE_GAP",)


def test_pattern_selection_validation_accepts_supported_patterns() -> None:
    for pattern in SUPPORTED_PATTERNS:
        assert validate_pattern_selection((pattern,)) == (pattern,)
        assert strategy_name_for_patterns((pattern,)) == f"{pattern}_PATTERN_STRATEGY"


def test_supported_pattern_registry_includes_every_wireable_pattern() -> None:
    assert tuple(PATTERN_REGISTRY) == SUPPORTED_PATTERNS
    for pattern in SUPPORTED_PATTERNS:
        entry = PATTERN_REGISTRY[pattern]
        assert callable(entry.detector)
        assert callable(entry.planner)
        assert entry.event_pattern_type


def test_pattern_selection_validation_rejects_unsupported_patterns() -> None:
    with pytest.raises(ValueError, match="unsupported pattern selection: NOT_A_PATTERN"):
        validate_pattern_selection(("NOT_A_PATTERN",))

    with pytest.raises(ValueError, match="unsupported pattern selection: NOT_A_PATTERN"):
        PatternStrategyBacktestConfig(patterns=("NOT_A_PATTERN",))


def test_pattern_selection_validation_rejects_multiple_patterns() -> None:
    with pytest.raises(ValueError, match="multiple pattern selections are not supported"):
        validate_pattern_selection(("FAIR_VALUE_GAP", "ORDER_BLOCK"))


def test_no_trade_when_no_configured_pattern_is_detected() -> None:
    candles = _candles(
        [
            ("2026-05-18 00:00:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:01:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:02:00", 100.0, 101.0, 99.0, 100.0, 1.0),
        ]
    )

    result = run_pattern_strategy_backtest(candles, config=_config())

    assert result.trades == ()
    assert result.evaluated_candle_count == 3


def test_valid_configured_pattern_opens_one_simulated_position() -> None:
    candles = _candles(_bullish_fvg_base() + [("2026-05-18 00:03:00", 106.0, 107.0, 103.0, 106.0, 10.0)])

    result = run_pattern_strategy_backtest(candles, config=_config())

    assert result.trade_count == 1
    trade = result.trades[0]
    assert trade.pattern_type == "FAIR_VALUE_GAP"
    assert trade.entry_candle_index == 2
    assert trade.entry_price == pytest.approx(102.5)
    assert trade.risk_plan.status == RiskExitPlanStatus.VALID


def test_duplicate_stable_pattern_event_does_not_create_duplicate_entries() -> None:
    candles = _candles(
        _bullish_fvg_base()
        + [
            ("2026-05-18 00:03:00", 108.0, 106.0, 102.0, 104.0, 10.0),
            ("2026-05-18 00:04:00", 104.0, 106.0, 102.0, 104.0, 10.0),
        ]
    )

    result = run_pattern_strategy_backtest(candles, config=_config(reaction_failure_bars=10))

    assert result.trade_count == 1
    assert len(result.seen_event_ids) == 1


def test_stop_loss_exit_is_recorded_through_exit_simulator() -> None:
    candles = _candles(_bullish_fvg_base() + [("2026-05-18 00:03:00", 102.0, 103.0, 98.0, 99.0, 10.0)])

    result = run_pattern_strategy_backtest(candles, config=_config())

    trade = result.trades[0]
    assert trade.exit_reason == PatternExitReason.HARD_STOP
    assert trade.exit_candle_index == 3
    assert trade.exit_price == pytest.approx(98.8)
    assert trade.remaining_quantity_ratio == 0.0
    assert trade.realized_r_multiple == pytest.approx(-1.0)


def test_take_profit_exit_is_recorded_through_exit_simulator() -> None:
    candles = _candles(_bullish_fvg_base() + [("2026-05-18 00:03:00", 106.0, 107.0, 103.0, 106.0, 10.0)])

    result = run_pattern_strategy_backtest(candles, config=_config())

    trade = result.trades[0]
    assert trade.exit_reason == PatternExitReason.TAKE_PROFIT
    assert trade.exit_candle_index == 3
    assert trade.exit_price == pytest.approx(106.2)
    assert trade.remaining_quantity_ratio == 0.0
    assert trade.realized_r_multiple == pytest.approx(1.0)


def test_indicator_warmup_insufficient_history_has_deterministic_no_trade_behavior() -> None:
    candles = _candles(_bullish_fvg_base())
    config = PatternStrategyBacktestConfig(
        fair_value_gap=FairValueGapConfig(
            require_displacement_candle=False,
            minimum_pattern_score=0.0,
            atr_config=AtrConfig(period=4),
            volume_ratio_config=VolumeRatioConfig(window=1),
        ),
        fair_value_gap_risk_exit=FairValueGapRiskExitConfig(partial_exits=()),
    )

    result = run_pattern_strategy_backtest(candles, config=config)

    assert result.trades == ()


@pytest.mark.parametrize("pattern", SUPPORTED_PATTERNS)
def test_caller_provided_candle_data_is_not_mutated_for_supported_patterns(pattern: str) -> None:
    candles = _candles(_bullish_fvg_base())
    original = candles.copy(deep=True)

    run_pattern_strategy_backtest(
        candles,
        config=PatternStrategyBacktestConfig(patterns=(pattern,)),
    )

    pd.testing.assert_frame_equal(candles, original)


@pytest.mark.parametrize("pattern", SUPPORTED_PATTERNS[1:])
def test_supported_non_fvg_patterns_have_deterministic_no_trade_selection(pattern: str) -> None:
    # Building compact synthetic entries for these multi-pivot/displacement patterns
    # is intentionally left to detector-specific tests; this backtest integration
    # test proves safe selection, schema validation, and no contract mutation.
    candles = _candles(
        [
            ("2026-05-18 00:00:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:01:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:02:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:03:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:04:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:05:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:06:00", 100.0, 101.0, 99.0, 100.0, 1.0),
            ("2026-05-18 00:07:00", 100.0, 101.0, 99.0, 100.0, 1.0),
        ]
    )

    result = run_pattern_strategy_backtest(
        candles,
        config=PatternStrategyBacktestConfig(patterns=(pattern,)),
    )

    assert result.trade_count == 0
    assert result.evaluated_candle_count == len(candles)


def test_same_candle_multiple_pattern_rule_is_documented_on_trade_metadata() -> None:
    candles = _candles(_bullish_fvg_base() + [("2026-05-18 00:03:00", 106.0, 107.0, 103.0, 106.0, 10.0)])

    result = run_pattern_strategy_backtest(candles, config=_config())

    assert result.trades[0].metadata["same_candle_entry_rule"] == "pattern_type_direction_event_id_order_first_valid_plan"
    assert result.trades[0].metadata["exit_evaluation"] == "starts_on_candle_after_entry"


def test_pattern_strategy_backtest_requires_standard_candle_schema() -> None:
    candles = _candles(_bullish_fvg_base()).drop(columns=["volume"])

    with pytest.raises(ValueError, match="missing required candle columns: volume"):
        run_pattern_strategy_backtest(candles, config=_config())


def test_pattern_strategy_backtest_rejects_unsorted_candles() -> None:
    candles = _candles(_bullish_fvg_base()).iloc[[1, 0, 2]].reset_index(drop=True)

    with pytest.raises(ValueError, match="sorted ascending by timestamp"):
        run_pattern_strategy_backtest(candles, config=_config())


def test_pattern_strategy_backtest_does_not_import_exchange_or_execution_dependencies() -> None:
    source_path = Path("quant_bitcoin/backtesting/pattern_strategy.py")
    tree = ast.parse(source_path.read_text())
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)

    assert not any(module.startswith("quant_bitcoin.market_data") for module in imported_modules)
    assert not any(module.startswith("quant_bitcoin.execution") for module in imported_modules)
    assert not any("binance" in module.lower() for module in imported_modules)


def test_pattern_strategy_backtest_does_not_read_api_keys_env_or_place_orders() -> None:
    source = Path("quant_bitcoin/backtesting/pattern_strategy.py").read_text().lower()

    assert "api_key" not in source
    assert ".env" not in source
    assert "create_order(" not in source
    assert "place_order(" not in source
    assert "enable_live_trading" not in source
