from quant_bitcoin.strategies.pattern_explanations import build_pattern_strategy_explanation


PATTERNS = [
    "FAIR_VALUE_GAP",
    "ORDER_BLOCK",
    "TRENDLINE_BREAK",
    "CUP_AND_HANDLE",
    "DIAMOND",
    "ADAM_AND_EVE",
]


def test_supported_patterns_have_required_keys_and_are_serializable():
    for pattern in PATTERNS:
        payload = build_pattern_strategy_explanation(pattern)
        for key in (
            "algorithm_key","algorithm_name","direction_support","detection_rules","entry_rules","stop_loss_rules",
            "take_profit_rules","partial_exit_rules","soft_invalidation_rules","time_stop_rules","design_rationale","known_limitations",
        ):
            assert key in payload


def test_unsupported_pattern_raises_clear_error():
    try:
        build_pattern_strategy_explanation("UNKNOWN")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "unsupported pattern" in str(exc)
