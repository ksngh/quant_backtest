"""Pattern score transparency helpers.

Pattern scores in this project are deterministic heuristic quality scores, not
calibrated probabilities of profit. This module standardizes component metadata
so downstream research can audit which inputs were measured and which were
placeholder priors.
"""

from __future__ import annotations

from typing import Any


def build_score_metadata(
    pattern_type: str,
    components: list[dict[str, Any]],
) -> dict[str, Any]:
    score_components: dict[str, dict[str, Any]] = {}
    score_component_sources: dict[str, str] = {}
    limitations: list[str] = [
        "pattern_score is a deterministic heuristic quality score, not a calibrated alpha probability.",
        "score thresholds are heuristic filters until validated against out-of-sample outcomes.",
    ]
    total = 0.0

    for component in components:
        name = str(component["name"])
        raw_score = _bounded(component["raw_score"])
        weight = float(component["weight"])
        weighted_score = raw_score * weight
        source = str(component.get("source", "observed_feature"))
        is_placeholder = bool(component.get("is_placeholder", False))
        score_components[name] = {
            "raw_score": raw_score,
            "weight": weight,
            "weighted_score": weighted_score,
            "source": source,
            "is_placeholder": is_placeholder,
            "description": component.get("description"),
        }
        score_component_sources[name] = source
        if is_placeholder:
            limitations.append(f"{name} uses placeholder context and should not be read as validated evidence.")
        total += weighted_score

    score = round(max(0.0, min(total, 1.0)), 6)
    return {
        "pattern_type": pattern_type,
        "pattern_score": score,
        "score_components": score_components,
        "score_component_sources": score_component_sources,
        "score_limitations": tuple(dict.fromkeys(limitations)),
        "score_calibration": {
            "score_type": "heuristic_quality_score",
            "is_calibrated_probability": False,
            "score_bucket": score_bucket(score),
        },
    }


def score_bucket(score: float) -> str:
    value = _bounded(score)
    if value >= 0.8:
        return "HIGH"
    if value >= 0.6:
        return "MEDIUM"
    if value > 0:
        return "LOW"
    return "NONE"


def _bounded(value: Any) -> float:
    numeric = float(value)
    return max(0.0, min(numeric, 1.0))
