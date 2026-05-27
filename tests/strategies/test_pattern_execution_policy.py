import inspect

import pytest

from quant_bitcoin.patterns.entry_simulation import PatternEntryMode
from quant_bitcoin.strategies.pattern_execution_policy import policy_for_pattern, validate_pattern_entry_mode


def test_policy_matrix_defines_supported_patterns() -> None:
    for pattern in (
        "FAIR_VALUE_GAP",
        "FAIR_VALUE_GAP_RETEST",
        "ORDER_BLOCK",
        "TRENDLINE_BREAK",
        "CUP_AND_HANDLE",
        "DIAMOND",
        "ADAM_AND_EVE",
    ):
        metadata = policy_for_pattern(pattern).to_metadata()
        assert metadata["pattern_key"] == pattern
        assert metadata["policy_key"]
        assert metadata["economic_rationale"]
        assert metadata["scope"] == "backtest_research_only"


def test_policy_validation_rejects_unsupported_mode() -> None:
    with pytest.raises(ValueError, match="not supported for DIAMOND"):
        validate_pattern_entry_mode("DIAMOND", PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT)


def test_policy_metadata_serializes_selected_entry_mode() -> None:
    policy = validate_pattern_entry_mode("ORDER_BLOCK", PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT)
    metadata = policy.to_metadata(selected_entry_mode=PatternEntryMode.LIMIT_AT_PATTERN_MIDPOINT)

    assert metadata["schema_version"] == "pattern_execution_policy_v1"
    assert metadata["selected_entry_mode"] == "LIMIT_AT_PATTERN_MIDPOINT"
    assert "LIMIT_AT_PATTERN_MIDPOINT" in metadata["allowed_entry_modes"]
    assert metadata["selected_entry_hypothesis"] == "RETEST_ORDER_BLOCK_MIDPOINT"


def test_fvg_and_order_block_define_canonical_experiment_modes() -> None:
    fvg = policy_for_pattern("FAIR_VALUE_GAP").to_metadata()
    order_block = policy_for_pattern("ORDER_BLOCK").to_metadata()

    assert "LIMIT_AT_PATTERN_NEAR_BOUNDARY" in fvg["allowed_entry_modes"]
    assert "LIMIT_AT_PATTERN_FAR_BOUNDARY" in fvg["allowed_entry_modes"]
    assert fvg["selected_entry_hypothesis"] == "CHASE_MOMENTUM_CONFIRMATION_CLOSE"
    assert "LIMIT_AT_ORDER_BLOCK_618_RETRACEMENT" in order_block["allowed_entry_modes"]
    assert "LIMIT_AT_CUSTOM_PRICE" in order_block["allowed_entry_modes"]


def test_fvg_retest_policy_defaults_to_midpoint_and_rejects_chase_modes() -> None:
    policy = policy_for_pattern("FAIR_VALUE_GAP_RETEST").to_metadata()

    assert policy["default_entry_mode"] == "LIMIT_AT_PATTERN_MIDPOINT"
    assert policy["selected_entry_hypothesis"] == "RETEST_GAP_MIDPOINT"
    assert "MARKET_ON_CONFIRMATION_CLOSE" not in policy["allowed_entry_modes"]
    with pytest.raises(ValueError, match="not supported for FAIR_VALUE_GAP_RETEST"):
        validate_pattern_entry_mode("FAIR_VALUE_GAP_RETEST", PatternEntryMode.MARKET_ON_CONFIRMATION_CLOSE)


def test_adam_and_eve_allows_neckline_retest_entry_mode_metadata() -> None:
    policy = validate_pattern_entry_mode("ADAM_AND_EVE", PatternEntryMode.LIMIT_AT_NECKLINE_RETEST)
    metadata = policy.to_metadata(selected_entry_mode=PatternEntryMode.LIMIT_AT_NECKLINE_RETEST)

    assert "LIMIT_AT_NECKLINE_RETEST" in metadata["allowed_entry_modes"]
    assert metadata["selected_entry_hypothesis"] == "BROKEN_NECKLINE_RETEST"


def test_policy_module_has_no_execution_client_imports() -> None:
    import quant_bitcoin.strategies.pattern_execution_policy as policy_module

    source = inspect.getsource(policy_module)
    assert "PostgresCandleDataProvider" not in source
    assert "Binance" not in source
    assert "order endpoint" not in source
