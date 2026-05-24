import inspect

import pytest

from quant_bitcoin.patterns.entry_simulation import PatternEntryMode
from quant_bitcoin.strategies.pattern_execution_policy import policy_for_pattern, validate_pattern_entry_mode


def test_policy_matrix_defines_supported_patterns() -> None:
    for pattern in (
        "FAIR_VALUE_GAP",
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


def test_policy_module_has_no_execution_client_imports() -> None:
    import quant_bitcoin.strategies.pattern_execution_policy as policy_module

    source = inspect.getsource(policy_module)
    assert "PostgresCandleDataProvider" not in source
    assert "Binance" not in source
    assert "order endpoint" not in source
