"""Tests for ai_visibility.scoring."""

from __future__ import annotations

from ai_visibility.scoring import score_page
from ai_visibility.scoring_weights import get_default_weights
from ai_visibility.types import ScoringConfig, Severity


def _words(n: int) -> str:
    return " ".join(["word"] * n)


class TestScorePageDimensionKeys:
    def test_all_seven_dimensions_present(self) -> None:
        result = score_page("<html><body><p>hi</p></body></html>")
        assert set(result.dimension_scores) == set(get_default_weights())


class TestSchemaCoverage:
    def test_no_jsonld_is_critical(self) -> None:
        result = score_page("<html><body><p>no schema here</p></body></html>")
        assert result.dimension_scores["schema_coverage"] == 0
        critical = [f for f in result.findings if f.severity == Severity.CRITICAL]
        assert any("JSON-LD" in f.message for f in critical)

    def test_invalid_json_scores_40(self) -> None:
        html = '<html><head><script type="application/ld+json">{not valid</script></head></html>'
        result = score_page(html)
        assert result.dimension_scores["schema_coverage"] == 40
        assert any(
            "none parsed as valid" in f.message
            for f in result.findings
            if f.dimension == "schema_coverage"
        )

    def test_valid_json_without_type_scores_40(self) -> None:
        html = '<html><head><script type="application/ld+json">{"foo": 1}</script></head></html>'
        result = score_page(html)
        assert result.dimension_scores["schema_coverage"] == 40

    def test_valid_schema_scores_100(self) -> None:
        html = (
            '<html><head><script type="application/ld+json">'
            '{"@context": "https://schema.org", "@type": "Article"}'
            "</script></head></html>"
        )
        result = score_page(html)
        assert result.dimension_scores["schema_coverage"] == 100


class TestHeadingStructure:
    def test_no_headings_scores_zero(self) -> None:
        result = score_page("<html><body><p>no headings</p></body></html>")
        assert result.dimension_scores["heading_structure"] == 0
        assert any("No headings found" in f.message for f in result.findings)

    def test_single_h1_no_skip_all_text_scores_100(self) -> None:
        html = "<html><body><h1>Title</h1><h2>Sub</h2></body></html>"
        result = score_page(html)
        assert result.dimension_scores["heading_structure"] == 100

    def test_no_h1_with_other_headings(self) -> None:
        html = "<html><body><h2>Only a subheading</h2></body></html>"
        result = score_page(html)
        assert any("No <h1> found" in f.message for f in result.findings)

    def test_multiple_h1_flagged(self) -> None:
        html = "<html><body><h1>One</h1><h1>Two</h1></body></html>"
        result = score_page(html)
        assert any("expected exactly one" in f.message for f in result.findings)

    def test_skipped_level_flagged(self) -> None:
        html = "<html><body><h1>Title</h1><h3>Sub-sub</h3></body></html>"
        result = score_page(html)
        assert any("skip a level" in f.message for f in result.findings)

    def test_empty_heading_text_flagged(self) -> None:
        html = "<html><body><h1>Title</h1><h2></h2></body></html>"
        result = score_page(html)
        assert any("no text content" in f.message for f in result.findings)


class TestCrawlerAccessibility:
    def test_hard_block_zeroes_overall_score(self) -> None:
        html = (
            '<html><head><meta name="robots" content="noindex, nofollow"></head>'
            "<body><h1>T</h1></body></html>"
        )
        result = score_page(html, has_llms_txt=True, has_ai_txt=True)
        assert result.dimension_scores["crawler_accessibility"] == 0
        assert result.overall_score == 0
        assert any(
            f.severity == Severity.CRITICAL and "blocks indexing" in f.message
            for f in result.findings
        )

    def test_meta_robots_allow_is_not_a_block(self) -> None:
        html = '<html><head><meta name="robots" content="index, follow"></head></html>'
        result = score_page(html, has_llms_txt=True, has_ai_txt=True)
        assert result.dimension_scores["crawler_accessibility"] == 100

    def test_both_flags_none_is_neutral(self) -> None:
        result = score_page("<html></html>")
        assert result.dimension_scores["crawler_accessibility"] == 50
        assert any(
            f.severity == Severity.INFO and "not checked" in f.message
            for f in result.findings
            if f.dimension == "crawler_accessibility"
        )

    def test_both_true_scores_100(self) -> None:
        result = score_page("<html></html>", has_llms_txt=True, has_ai_txt=True)
        assert result.dimension_scores["crawler_accessibility"] == 100

    def test_llms_txt_false_warns_and_withholds_points(self) -> None:
        result = score_page("<html></html>", has_llms_txt=False, has_ai_txt=None)
        assert result.dimension_scores["crawler_accessibility"] == 40
        assert any(
            f.severity == Severity.WARNING and "No llms.txt" in f.message for f in result.findings
        )

    def test_ai_txt_false_informs_and_withholds_points(self) -> None:
        result = score_page("<html></html>", has_llms_txt=None, has_ai_txt=False)
        assert result.dimension_scores["crawler_accessibility"] == 40
        assert any(
            f.severity == Severity.INFO and "No ai.txt" in f.message for f in result.findings
        )


class TestEeatSignals:
    def test_nothing_present_scores_zero(self) -> None:
        result = score_page("<html><body><p>hi</p></body></html>")
        assert result.dimension_scores["eeat_signals"] == 0
        assert any(
            f.severity == Severity.WARNING and "Missing authority/trust signals" in f.message
            for f in result.findings
        )

    def test_meta_author_only_scores_30(self) -> None:
        html = '<html><head><meta name="author" content="Jane Doe"></head></html>'
        result = score_page(html)
        assert result.dimension_scores["eeat_signals"] == 30
        assert any(
            f.severity == Severity.INFO and "Missing authority/trust signals" in f.message
            for f in result.findings
        )

    def test_jsonld_author_only_scores_40(self) -> None:
        html = (
            '<html><head><script type="application/ld+json">'
            '{"@type": "Article", "author": {"name": "Jane"}}'
            "</script></head></html>"
        )
        result = score_page(html)
        assert result.dimension_scores["eeat_signals"] == 40

    def test_jsonld_publisher_only_scores_40(self) -> None:
        html = (
            '<html><head><script type="application/ld+json">'
            '{"@type": "Article", "publisher": {"name": "Acme"}}'
            "</script></head></html>"
        )
        result = score_page(html)
        assert result.dimension_scores["eeat_signals"] == 40

    def test_invalid_jsonld_block_is_skipped_not_counted(self) -> None:
        html = '<html><head><script type="application/ld+json">{not valid</script></head></html>'
        result = score_page(html)
        assert result.dimension_scores["eeat_signals"] == 0

    def test_contact_link_only_scores_30(self) -> None:
        html = '<html><body><a href="mailto:hi@acme.example">Email</a></body></html>'
        result = score_page(html)
        assert result.dimension_scores["eeat_signals"] == 30

    def test_tel_link_counts_as_contact(self) -> None:
        html = '<html><body><a href="tel:+15551234567">Call</a></body></html>'
        result = score_page(html)
        assert result.dimension_scores["eeat_signals"] == 30

    def test_all_present_scores_100_with_no_finding(self) -> None:
        html = (
            '<html><head><meta name="author" content="Jane Doe">'
            '<script type="application/ld+json">'
            '{"@type": "Article", "author": {"name": "Jane"}}</script></head>'
            '<body><a href="mailto:hi@acme.example">Email</a></body></html>'
        )
        result = score_page(html)
        assert result.dimension_scores["eeat_signals"] == 100
        assert not any(f.dimension == "eeat_signals" for f in result.findings)


class TestFactDensity:
    def test_no_text_scores_zero(self) -> None:
        result = score_page("<html><body></body></html>")
        assert result.dimension_scores["fact_density"] == 0
        assert any(
            "No visible text content" in f.message
            for f in result.findings
            if f.dimension == "fact_density"
        )

    def test_high_density_scores_100(self) -> None:
        html = f"<html><body><p>{'1 2 3 4 5 6 7 8 9 10'}</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["fact_density"] == 100

    def test_density_around_2_scores_70(self) -> None:
        html = f"<html><body><p>{_words(98)} 5 6</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["fact_density"] == 70

    def test_density_around_half_scores_40(self) -> None:
        html = f"<html><body><p>{_words(149)} 5</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["fact_density"] == 40

    def test_low_density_scores_10_with_finding(self) -> None:
        html = f"<html><body><p>{_words(299)} 5</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["fact_density"] == 10
        assert any(
            "Low factual density" in f.message
            for f in result.findings
            if f.dimension == "fact_density"
        )


class TestSnippability:
    def test_no_headings_scores_zero(self) -> None:
        result = score_page("<html><body><p>text</p></body></html>")
        assert result.dimension_scores["snippability"] == 0
        assert any(
            "No headings to evaluate" in f.message
            for f in result.findings
            if f.dimension == "snippability"
        )

    def test_all_sections_well_formed_scores_100(self) -> None:
        html = f"<html><body><h2>A</h2><p>{_words(25)}</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["snippability"] == 100
        assert not any(f.dimension == "snippability" for f in result.findings)

    def test_partial_sections_well_formed(self) -> None:
        html = (
            f"<html><body><h2>A</h2><p>{_words(25)}</p><h2>B</h2><p>{_words(5)}</p></body></html>"
        )
        result = score_page(html)
        assert result.dimension_scores["snippability"] == 50
        assert any(
            "too little content" in f.message
            for f in result.findings
            if f.dimension == "snippability"
        )


class TestAnswerFrontLoading:
    def test_h1_with_40_plus_words_scores_100(self) -> None:
        html = f"<html><body><h1>Title</h1><p>{_words(40)}</p><h2>Next</h2></body></html>"
        result = score_page(html)
        assert result.dimension_scores["answer_front_loading"] == 100

    def test_h1_with_20_to_39_words_scores_60(self) -> None:
        html = f"<html><body><h1>Title</h1><p>{_words(20)}</p><h2>Next</h2></body></html>"
        result = score_page(html)
        assert result.dimension_scores["answer_front_loading"] == 60
        assert any(
            f.severity == Severity.INFO
            for f in result.findings
            if f.dimension == "answer_front_loading"
        )

    def test_h1_with_few_words_scores_20(self) -> None:
        html = f"<html><body><h1>Title</h1><p>{_words(5)}</p><h2>Next</h2></body></html>"
        result = score_page(html)
        assert result.dimension_scores["answer_front_loading"] == 20
        assert any(
            f.severity == Severity.WARNING
            for f in result.findings
            if f.dimension == "answer_front_loading"
        )

    def test_h1_with_no_content_scores_zero_critical(self) -> None:
        html = "<html><body><h1>Title</h1><h2>Next</h2></body></html>"
        result = score_page(html)
        assert result.dimension_scores["answer_front_loading"] == 0
        assert any(
            f.severity == Severity.CRITICAL
            for f in result.findings
            if f.dimension == "answer_front_loading"
        )

    def test_falls_back_to_first_paragraph_when_no_leading_h1(self) -> None:
        html = f"<html><body><p>{_words(45)}</p><h2>Sub</h2></body></html>"
        result = score_page(html)
        assert result.dimension_scores["answer_front_loading"] == 100

    def test_self_closed_p_is_not_counted_as_first_paragraph(self) -> None:
        html = f"<html><body><p/><p>{_words(45)}</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["answer_front_loading"] == 100


class TestOverallScoreAndConfig:
    def test_hard_block_overrides_otherwise_high_score(self) -> None:
        html = (
            '<html><head><meta name="robots" content="none">'
            '<script type="application/ld+json">{"@type": "Article"}</script>'
            '<meta name="author" content="Jane"></head>'
            f"<body><h1>Title</h1><p>{_words(50)}</p></body></html>"
        )
        result = score_page(html, has_llms_txt=True, has_ai_txt=True)
        assert result.overall_score == 0

    def test_config_weight_override_changes_overall_score(self) -> None:
        html = (
            '<html><head><script type="application/ld+json">'
            '{"@context": "https://schema.org", "@type": "Article"}'
            "</script></head><body><p>no other signals</p></body></html>"
        )
        default_result = score_page(html)
        heavy_schema_result = score_page(html, config=ScoringConfig(schema_coverage_weight=0.9))
        assert heavy_schema_result.overall_score > default_result.overall_score

    def test_unset_config_fields_fall_back_to_vendored_defaults(self) -> None:
        html = "<html><body><p>hi</p></body></html>"
        default_result = score_page(html)
        explicit_result = score_page(html, config=ScoringConfig())
        assert default_result.overall_score == explicit_result.overall_score


class TestParserEdgeCases:
    def test_self_closing_void_tag_does_not_break_parsing(self) -> None:
        html = "<html><body><br/><h1>Title</h1></body></html>"
        result = score_page(html)
        assert result.dimension_scores["heading_structure"] == 100

    def test_unmatched_end_tag_does_not_crash(self) -> None:
        html = "</div><html><body><h1>Title</h1></body></html>"
        result = score_page(html)
        assert result.dimension_scores["heading_structure"] == 100

    def test_script_text_excluded_from_fact_density(self) -> None:
        html = "<html><body><script>1 2 3 4 5 6 7 8 9 10</script><p>hi</p></body></html>"
        result = score_page(html)
        # The numeric tokens live only inside <script>, which is excluded from
        # word/fact counting — only "hi" (1 word, 0 fact tokens) should count.
        assert result.dimension_scores["fact_density"] == 10
