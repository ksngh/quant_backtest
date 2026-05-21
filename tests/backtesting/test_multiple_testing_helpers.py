import pytest

from quant_bitcoin.backtesting.multiple_testing import (
    benjamini_hochberg_thresholds,
    bonferroni_threshold,
    count_strategy_variants,
)


def test_bonferroni_threshold_nominal() -> None:
    assert bonferroni_threshold(alpha=0.05, tested_variants=10) == pytest.approx(0.005)


@pytest.mark.parametrize("alpha", [0.0, -0.1, 1.1])
def test_bonferroni_threshold_rejects_invalid_alpha(alpha: float) -> None:
    with pytest.raises(ValueError):
        bonferroni_threshold(alpha=alpha, tested_variants=2)


@pytest.mark.parametrize("tested_variants", [0, -1])
def test_bonferroni_threshold_rejects_invalid_tested_variants(tested_variants: int) -> None:
    with pytest.raises(ValueError):
        bonferroni_threshold(alpha=0.05, tested_variants=tested_variants)


def test_bh_thresholds_nominal_monotonic_and_length() -> None:
    thresholds = benjamini_hochberg_thresholds(alpha=0.1, tested_variants=5)

    assert thresholds == pytest.approx([0.02, 0.04, 0.06, 0.08, 0.1])
    assert len(thresholds) == 5
    assert thresholds == sorted(thresholds)


@pytest.mark.parametrize("alpha", [0.0, -0.1, 1.01])
def test_bh_thresholds_reject_invalid_alpha(alpha: float) -> None:
    with pytest.raises(ValueError):
        benjamini_hochberg_thresholds(alpha=alpha, tested_variants=3)


@pytest.mark.parametrize("tested_variants", [0, -2])
def test_bh_thresholds_reject_invalid_tested_variants(tested_variants: int) -> None:
    with pytest.raises(ValueError):
        benjamini_hochberg_thresholds(alpha=0.05, tested_variants=tested_variants)


def test_count_strategy_variants_nominal_deduplicates_sequence_values() -> None:
    search_space = {
        "lookback": [14, 14, 21],
        "entry_threshold": (30, 35),
        "exit_threshold": {60, 65, 70},
    }

    result = count_strategy_variants(search_space)

    assert result == 2 * 2 * 3
    assert isinstance(result, int)


def test_count_strategy_variants_accepts_integer_cardinality() -> None:
    search_space = {
        "preset_id": 4,
        "holding_period": range(1, 4),
    }

    assert count_strategy_variants(search_space) == 12


@pytest.mark.parametrize(
    "search_space",
    [
        {},
        {"x": []},
        {"x": 0},
        {"x": -1},
        {"x": "abc"},
        {"x": True},
        {"x": 1.5},
    ],
)
def test_count_strategy_variants_rejects_invalid_search_space(search_space: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        count_strategy_variants(search_space)
