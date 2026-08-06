"""Loader for the shared GEO scoring weights (``scoring_weights.json``).

Vendored from the same ``ai-visibility`` npm package release as
``crawlers.json`` (published as ``dist/scoring-weights.json`` in
``ai-visibility@0.5.0`` on npm), so the dimension set and default weights
match the JS/TypeScript version instead of an independently reinvented
rubric that would silently drift from it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

_WEIGHTS_FILE = "scoring_weights.json"

# The vendored file uses the npm package's camelCase dimension keys; the
# Python API uses snake_case (no camelCase leaking from the JS version).
_CAMEL_TO_SNAKE = {
    "answerFrontLoading": "answer_front_loading",
    "eeatSignals": "eeat_signals",
    "headingStructure": "heading_structure",
    "schemaCoverage": "schema_coverage",
    "factDensity": "fact_density",
    "snippability": "snippability",
    "crawlerAccessibility": "crawler_accessibility",
}


@dataclass(frozen=True)
class ScoringDimension:
    """One GEO scoring dimension, as published in ``scoring_weights.json``.

    Attributes:
        key: snake_case dimension key, e.g. ``"schema_coverage"``.
        label: Short human-readable label, e.g. ``"Structured data"``.
        weight: Default weight (0-1); all dimension weights sum to 1.0.
        description: Longer explanation of what the dimension measures.
    """

    key: str
    label: str
    weight: float
    description: str


@lru_cache(maxsize=1)
def _load_dimensions() -> tuple[ScoringDimension, ...]:
    raw_text = resources.files("ai_visibility").joinpath(_WEIGHTS_FILE).read_text(encoding="utf-8")
    data = json.loads(raw_text)
    return tuple(
        ScoringDimension(
            key=_CAMEL_TO_SNAKE.get(entry["key"], entry["key"]),
            label=entry["label"],
            weight=entry["weight"],
            description=entry["description"],
        )
        for entry in data["dimensions"]
    )


def get_scoring_dimensions() -> list[ScoringDimension]:
    """Return the vendored GEO scoring dimensions, in weight order.

    Returns:
        A list of :class:`ScoringDimension`, in the order published in
        ``scoring_weights.json``.
    """
    return list(_load_dimensions())


def get_default_weights() -> dict[str, float]:
    """Return the vendored default weight for each scoring dimension.

    Returns:
        A ``{snake_case_dimension_key: weight}`` mapping.
    """
    return {dimension.key: dimension.weight for dimension in _load_dimensions()}
