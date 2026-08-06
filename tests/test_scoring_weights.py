"""Tests for ai_visibility.scoring_weights."""

from __future__ import annotations

from ai_visibility.scoring_weights import (
    ScoringDimension,
    get_default_weights,
    get_scoring_dimensions,
)


class TestGetScoringDimensions:
    def test_returns_seven_dimensions(self) -> None:
        dimensions = get_scoring_dimensions()
        assert len(dimensions) == 7
        assert all(isinstance(d, ScoringDimension) for d in dimensions)

    def test_keys_are_snake_case(self) -> None:
        keys = {d.key for d in get_scoring_dimensions()}
        assert keys == {
            "answer_front_loading",
            "eeat_signals",
            "heading_structure",
            "schema_coverage",
            "fact_density",
            "snippability",
            "crawler_accessibility",
        }

    def test_weights_sum_to_one(self) -> None:
        total = sum(d.weight for d in get_scoring_dimensions())
        assert round(total, 6) == 1.0

    def test_labels_and_descriptions_present(self) -> None:
        for dimension in get_scoring_dimensions():
            assert dimension.label
            assert dimension.description


class TestGetDefaultWeights:
    def test_matches_dimension_weights(self) -> None:
        weights = get_default_weights()
        dimensions = {d.key: d.weight for d in get_scoring_dimensions()}
        assert weights == dimensions

    def test_specific_known_weights(self) -> None:
        weights = get_default_weights()
        assert weights["answer_front_loading"] == 0.2
        assert weights["eeat_signals"] == 0.2
        assert weights["heading_structure"] == 0.15
        assert weights["schema_coverage"] == 0.15
        assert weights["fact_density"] == 0.1
        assert weights["snippability"] == 0.1
        assert weights["crawler_accessibility"] == 0.1
