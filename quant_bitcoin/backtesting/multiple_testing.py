"""Deterministic helpers for multiple-testing protocol enforcement.

These utilities are pure and side-effect free. They provide reusable
significance-threshold helpers and declared variant counting for research
scripts/reports without any market/exchange dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
import math


def bonferroni_threshold(alpha: float, tested_variants: int) -> float:
    """Return Bonferroni family-wise threshold ``alpha / tested_variants``."""

    validated_alpha = _validate_alpha(alpha)
    validated_variants = _validate_tested_variants(tested_variants)
    return validated_alpha / validated_variants


def benjamini_hochberg_thresholds(alpha: float, tested_variants: int) -> list[float]:
    """Return BH critical values for ranks 1..m as ``(i / m) * alpha``."""

    validated_alpha = _validate_alpha(alpha)
    validated_variants = _validate_tested_variants(tested_variants)

    return [
        (rank / validated_variants) * validated_alpha
        for rank in range(1, validated_variants + 1)
    ]


def count_strategy_variants(
    search_space: Mapping[str, Sequence | Set | tuple | list | range | int],
) -> int:
    """Count total declared strategy variants from a pre-declared search-space.

    Rules:
    - Mapping must be non-empty.
    - Sequence/set-like dimensions count unique candidates.
    - Integer dimensions are treated as explicit cardinalities and must be
      positive finite integers.
    """

    if not isinstance(search_space, Mapping):
        raise ValueError("search_space must be a mapping")
    if not search_space:
        raise ValueError("search_space must not be empty")

    total = 1
    for key, value in search_space.items():
        cardinality = _dimension_cardinality(value)
        if cardinality <= 0:
            raise ValueError(f"dimension '{key}' must have positive cardinality")
        total *= cardinality

    return int(total)


def _validate_alpha(alpha: float) -> float:
    if not isinstance(alpha, (int, float)) or not math.isfinite(float(alpha)):
        raise ValueError("alpha must be a finite number")
    value = float(alpha)
    if value <= 0 or value > 1:
        raise ValueError("alpha must be in (0, 1]")
    return value


def _validate_tested_variants(tested_variants: int) -> int:
    if not isinstance(tested_variants, int):
        raise ValueError("tested_variants must be an integer")
    if tested_variants <= 0:
        raise ValueError("tested_variants must be positive")
    return tested_variants


def _dimension_cardinality(value: Sequence | Set | tuple | list | range | int) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean cardinality is not supported")

    if isinstance(value, int):
        if value <= 0:
            raise ValueError("integer cardinality must be positive")
        return value

    if isinstance(value, (str, bytes)):
        raise ValueError("string-like dimensions are not supported")

    if isinstance(value, (Sequence, Set, range, tuple, list)):
        unique_values = set(value)
        if not unique_values:
            raise ValueError("dimension candidate set must not be empty")
        return len(unique_values)

    raise ValueError("unsupported search-space dimension type")
