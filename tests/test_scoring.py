"""Tests for ai_visibility.scoring."""

from __future__ import annotations

from ai_visibility.scoring import score_page
from ai_visibility.types import Severity

GOOD_HTML = (
    """<!DOCTYPE html>
<html lang="en">
<head>
    <title>The Complete Guide to Widgets</title>
    <meta name="description" content="Everything you need to know about widgets, how they work, and why they matter for your business.">
    <meta property="og:title" content="The Complete Guide to Widgets">
    <meta property="og:description" content="Everything you need to know about widgets.">
    <meta property="og:image" content="https://example.com/widget.png">
    <script type="application/ld+json">{"@context": "https://schema.org", "@type": "Article", "headline": "Widgets"}</script>
</head>
<body>
    <header><nav>Home</nav></header>
    <main>
        <article>
            <h1>The Complete Guide to Widgets</h1>
            <h2>What is a Widget?</h2>
            <p>"""
    + ("A widget is a small mechanical or software component. " * 30)
    + """</p>
            <h2>Why Widgets Matter</h2>
            <p>"""
    + ("Widgets matter because they save time and money. " * 30)
    + """</p>
        </article>
    </main>
    <footer>Copyright 2026</footer>
</body>
</html>"""
)


class TestScorePageGoodDocument:
    def test_overall_score_is_high(self) -> None:
        result = score_page(GOOD_HTML, has_llms_txt=True, has_ai_txt=True)
        assert result.overall_score >= 80

    def test_dimension_scores_present(self) -> None:
        result = score_page(GOOD_HTML)
        expected_dims = {
            "structured_data",
            "semantic_html",
            "meta_tags",
            "heading_hierarchy",
            "accessibility",
            "llms_txt",
        }
        assert set(result.dimension_scores) == expected_dims
        assert result.dimension_scores["structured_data"] == 100
        assert result.dimension_scores["meta_tags"] == 100


class TestScorePageBareDocument:
    def test_bare_html_scores_low(self) -> None:
        result = score_page("<html><body><div>hi</div></body></html>")
        assert result.overall_score < 30

    def test_missing_jsonld_gives_critical_finding(self) -> None:
        result = score_page("<html><body><p>no schema here</p></body></html>")
        critical = [f for f in result.findings if f.severity == Severity.CRITICAL]
        assert any("JSON-LD" in f.message for f in critical)

    def test_missing_title_gives_critical_finding(self) -> None:
        result = score_page("<html><body><p>text</p></body></html>")
        assert any("title" in f.message.lower() for f in result.findings)

    def test_invalid_json_in_ldjson_script(self) -> None:
        html = (
            '<html><head><script type="application/ld+json">{not valid json</script></head></html>'
        )
        result = score_page(html)
        assert result.dimension_scores["structured_data"] == 40


class TestHeadingHierarchy:
    def test_multiple_h1_flagged(self) -> None:
        html = "<html><body><h1>One</h1><h1>Two</h1></body></html>"
        result = score_page(html)
        assert any("h1" in f.message.lower() for f in result.findings)

    def test_skipped_level_flagged(self) -> None:
        html = "<html><body><h1>Title</h1><h3>Sub-sub</h3></body></html>"
        result = score_page(html)
        assert any("skip" in f.message.lower() for f in result.findings)

    def test_no_headings_scores_zero(self) -> None:
        html = "<html><body><p>no headings</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["heading_hierarchy"] == 0

    def test_no_h1_but_other_headings_present(self) -> None:
        html = "<html><body><h2>Only a subheading</h2></body></html>"
        result = score_page(html)
        assert any("no <h1>" in f.message.lower() for f in result.findings)

    def test_empty_heading_text_flagged(self) -> None:
        html = "<html><body><h1>Title</h1><h2></h2></body></html>"
        result = score_page(html)
        assert any("no text content" in f.message.lower() for f in result.findings)


class TestMetaDescriptionLength:
    def test_short_description_flagged(self) -> None:
        html = '<html><head><title>T</title><meta name="description" content="Too short."></head></html>'
        result = score_page(html)
        assert any("outside the ideal" in f.message for f in result.findings)


class TestLlmsTxtDimension:
    def test_unknown_defaults_to_neutral_with_info_finding(self) -> None:
        result = score_page("<html></html>")
        assert result.dimension_scores["llms_txt"] == 50
        assert any(
            f.severity == Severity.INFO for f in result.findings if f.dimension == "llms_txt"
        )

    def test_both_present_scores_100(self) -> None:
        result = score_page("<html></html>", has_llms_txt=True, has_ai_txt=True)
        assert result.dimension_scores["llms_txt"] == 100

    def test_both_absent_scores_zero_with_findings(self) -> None:
        result = score_page("<html></html>", has_llms_txt=False, has_ai_txt=False)
        assert result.dimension_scores["llms_txt"] == 0
        messages = [f.message for f in result.findings if f.dimension == "llms_txt"]
        assert any("llms.txt" in m for m in messages)
        assert any("ai.txt" in m for m in messages)


class TestAccessibilityDimension:
    def test_thin_content_flagged(self) -> None:
        html = "<html><body>" + "<div></div>" * 200 + "<p>hi</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["accessibility"] < 100

    def test_empty_body_scores_low(self) -> None:
        result = score_page("<html><body></body></html>")
        assert result.dimension_scores["accessibility"] <= 20

    def test_medium_ratio_scores_60(self) -> None:
        pad = ('<div class="' + "x" * 40 + '"></div>') * 20
        html = f"<html><body>{pad}<p>{'A' * 120}</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["accessibility"] == 60
        assert any(
            "low" in f.message.lower() for f in result.findings if f.dimension == "accessibility"
        )

    def test_very_low_ratio_with_enough_text_scores_20(self) -> None:
        pad = ('<div class="' + "x" * 40 + '"></div>') * 40
        html = f"<html><body>{pad}<p>{'A' * 120}</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["accessibility"] == 20
        assert any(
            "very low" in f.message.lower()
            for f in result.findings
            if f.dimension == "accessibility"
        )


class TestParserEdgeCases:
    def test_self_closing_tag_does_not_break_parsing(self) -> None:
        html = "<html><body><br/><p>after</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["heading_hierarchy"] == 0

    def test_unmatched_end_tag_does_not_crash(self) -> None:
        html = "</div><html><body><h1>Title</h1></body></html>"
        result = score_page(html)
        assert result.dimension_scores["heading_hierarchy"] > 0

    def test_plain_script_text_excluded_from_visible_text(self) -> None:
        html = "<html><body><script>var x = 'not visible content at all';</script><p>hi</p></body></html>"
        result = score_page(html)
        assert result.dimension_scores["accessibility"] <= 20
