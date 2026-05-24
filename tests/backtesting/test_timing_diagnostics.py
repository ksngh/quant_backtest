import inspect

import pytest

from quant_bitcoin.backtesting.timing_diagnostics import calculate_trade_timing_diagnostics


def _execution(timestamp, action_type, price, *, quantity=1.0, side="LONG", metadata=None):
    return {
        "timestamp": timestamp,
        "action_type": action_type,
        "price": price,
        "effective_price": price,
        "quantity": quantity,
        "position_after": 0.0 if action_type.startswith("EXIT") else (quantity if side == "LONG" else -quantity),
        "position_side": side,
        "metadata": metadata or {},
    }


def test_long_trade_reports_positive_mfe_and_mae_from_ohlc_path() -> None:
    diagnostics = calculate_trade_timing_diagnostics(
        (
            _execution("t0", "ENTER_LONG", 100.0, metadata={"risk_per_unit": 5.0, "entry_reference": 100.0}),
            _execution("t2", "EXIT_LONG", 105.0, metadata={"realized_r_multiple": 1.0, "exit_reason": "TIME_STOP"}),
        ),
        (
            {"timestamp": "t0", "high": 100.0, "low": 100.0, "close": 100.0},
            {"timestamp": "t1", "high": 112.0, "low": 99.0, "close": 108.0},
            {"timestamp": "t2", "high": 106.0, "low": 98.0, "close": 105.0},
        ),
    )

    trade = diagnostics["trades"][0]
    assert trade["mfe_price"] == pytest.approx(12.0)
    assert trade["mae_price"] == pytest.approx(2.0)
    assert trade["mfe_r"] == pytest.approx(2.4)
    assert trade["mae_r"] == pytest.approx(0.4)
    assert trade["bars_to_mfe"] == 1
    assert trade["bars_to_mae"] == 2
    assert trade["bars_to_time_stop"] == 2


def test_timing_diagnostics_carries_exit_attribution_metadata() -> None:
    diagnostics = calculate_trade_timing_diagnostics(
        (
            _execution(
                "t0",
                "ENTER_LONG",
                100.0,
                metadata={
                    "risk_per_unit": 5.0,
                    "pattern_type": "CUP_AND_HANDLE",
                    "pattern_direction": "BULLISH",
                    "entry_mode": "MARKET_ON_CONFIRMATION_CLOSE",
                },
            ),
            _execution(
                "t1",
                "EXIT_LONG",
                105.0,
                metadata={
                    "realized_r_multiple": 1.0,
                    "exit_reason": "TAKE_PROFIT",
                    "target_source": "MEASURED",
                    "exit_metadata": {
                        "target_source": "MEASURED",
                        "intrabar_policy": "TARGET_FIRST",
                        "ambiguous_stop_target": True,
                        "stop_moved_by_break_even_or_trailing": True,
                    },
                },
            ),
        ),
        (
            {"timestamp": "t0", "high": 100.0, "low": 100.0, "close": 100.0},
            {"timestamp": "t1", "high": 106.0, "low": 99.0, "close": 105.0},
        ),
    )

    trade = diagnostics["trades"][0]
    assert trade["pattern_type"] == "CUP_AND_HANDLE"
    assert trade["entry_mode"] == "MARKET_ON_CONFIRMATION_CLOSE"
    assert trade["target_source"] == "MEASURED"
    assert trade["intrabar_policy"] == "TARGET_FIRST"
    assert trade["ambiguous_stop_target"] is True
    assert trade["stop_moved_by_break_even_or_trailing"] is True


def test_short_trade_reports_positive_mfe_when_low_prints_after_entry() -> None:
    diagnostics = calculate_trade_timing_diagnostics(
        (
            _execution("t0", "ENTER_SHORT", 100.0, side="SHORT", metadata={"risk_per_unit": 5.0}),
            _execution("t2", "EXIT_SHORT", 95.0, side="SHORT", metadata={"realized_r_multiple": 1.0}),
        ),
        (
            {"timestamp": "t0", "high": 100.0, "low": 100.0, "close": 100.0},
            {"timestamp": "t1", "high": 103.0, "low": 88.0, "close": 90.0},
            {"timestamp": "t2", "high": 98.0, "low": 94.0, "close": 95.0},
        ),
    )

    trade = diagnostics["trades"][0]
    assert trade["mfe_price"] == pytest.approx(12.0)
    assert trade["mae_price"] == pytest.approx(3.0)
    assert trade["mfe_r"] == pytest.approx(2.4)
    assert trade["mae_r"] == pytest.approx(0.6)


def test_fill_reference_divergence_flags_late_chasing_entry() -> None:
    diagnostics = calculate_trade_timing_diagnostics(
        (
            _execution("t0", "ENTER_LONG", 106.0, metadata={"risk_per_unit": 10.0, "entry_reference": 100.0, "zone_mid": 100.0}),
            _execution("t1", "EXIT_LONG", 107.0, metadata={"realized_r_multiple": 0.1}),
        ),
        (
            {"timestamp": "t0", "high": 106.0, "low": 105.0, "close": 106.0},
            {"timestamp": "t1", "high": 109.0, "low": 104.0, "close": 107.0},
        ),
    )

    codes = {flag["code"] for flag in diagnostics["flags"]}
    assert "ENTRY_WAS_LATE_CHASING" in codes
    assert diagnostics["trades"][0]["entry_fill_zone_midpoint_distance"] == pytest.approx(6.0)


def test_missing_candle_matching_produces_warning_not_exception() -> None:
    diagnostics = calculate_trade_timing_diagnostics(
        (
            _execution("entry", "ENTER_LONG", 100.0, metadata={"risk_per_unit": 10.0}),
            _execution("exit", "EXIT_LONG", 101.0, metadata={"realized_r_multiple": 0.1}),
        ),
        ({"timestamp": "other", "close": 100.0},),
    )

    assert diagnostics["trades"] == ()
    assert "trade could not be matched to price path" in diagnostics["warnings"]
    assert "high/low path unavailable; MFE/MAE uses close-only approximation" in diagnostics["warnings"]


def test_timing_diagnostics_module_has_no_exchange_or_live_order_imports() -> None:
    import quant_bitcoin.backtesting.timing_diagnostics as timing_diagnostics

    source = inspect.getsource(timing_diagnostics)
    assert "binance" not in source.lower()
    assert "exchange" not in source.lower()
    assert "order endpoint" not in source.lower()
