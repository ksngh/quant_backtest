from __future__ import annotations

import pytest

from quant_bitcoin.patterns.score_metadata import build_score_metadata


def test_placeholder_only_components_do_not_raise_executable_score() -> None:
    metadata = build_score_metadata(
        "TEST_PATTERN",
        [
            {
                "name": "placeholder_prior",
                "raw_score": 1.0,
                "weight": 0.4,
                "is_placeholder": True,
                "source": "placeholder_constant",
            }
        ],
    )

    assert metadata["pattern_score"] == 0.0
    assert metadata["executable_pattern_score"] == 0.0
    assert metadata["diagnostic_pattern_score"] == pytest.approx(0.4)
    assert metadata["score_components"]["placeholder_prior"]["included_in_executable_score"] is False
    assert metadata["score_components"]["placeholder_prior"]["executable_weighted_score"] == 0.0


def test_observed_components_still_contribute_to_executable_score() -> None:
    metadata = build_score_metadata(
        "TEST_PATTERN",
        [
            {
                "name": "observed_feature",
                "raw_score": 0.5,
                "weight": 0.6,
                "source": "observed_feature",
            },
            {
                "name": "placeholder_prior",
                "raw_score": 1.0,
                "weight": 0.4,
                "is_placeholder": True,
                "source": "placeholder_constant",
            },
        ],
    )

    assert metadata["executable_pattern_score"] == pytest.approx(0.3)
    assert metadata["diagnostic_pattern_score"] == pytest.approx(0.7)
    assert metadata["score_components"]["observed_feature"]["included_in_executable_score"] is True
