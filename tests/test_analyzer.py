"""Tests for ai_visibility.analyzer."""

from __future__ import annotations

from ai_visibility.analyzer import analyze_content
from ai_visibility.types import Severity


class TestAnalyzeContent:
    def test_poor_page_summary_mentions_poor(self) -> None:
        result = analyze_content("<html><body><div>hi</div></body></html>")
        assert "poor" in result.summary.lower() or "needs improvement" in result.summary.lower()
        assert str(result.score.overall_score) in result.summary

    def test_recommendations_sorted_critical_first(self) -> None:
        result = analyze_content("<html><body><div>hi</div></body></html>")
        severities = [r.severity for r in result.recommendations]
        # Once we hit a non-critical severity, no critical should follow.
        seen_non_critical = False
        for severity in severities:
            if severity != Severity.CRITICAL:
                seen_non_critical = True
            elif seen_non_critical:
                raise AssertionError("critical finding appeared after a non-critical one")

    def test_recommendations_match_score_findings(self) -> None:
        result = analyze_content("<html><body><div>hi</div></body></html>")
        assert len(result.recommendations) == len(result.score.findings)

    def test_summary_mentions_weakest_area(self) -> None:
        result = analyze_content("<html><body><div>hi</div></body></html>")
        weakest = min(result.score.dimension_scores, key=lambda d: result.score.dimension_scores[d])
        assert weakest.replace("_", " ") in result.summary


_EXCELLENT_HTML = (
    """<!DOCTYPE html>
<html><head>
<title>The Complete Guide to Widgets</title>
<meta name="author" content="Jane Doe">
<script type="application/ld+json">{"@context": "https://schema.org", "@type": "Article", "headline": "Widgets", "author": {"@type": "Person", "name": "Jane Doe"}, "publisher": {"@type": "Organization", "name": "Acme"}}</script>
</head><body>
<h1>The Complete Guide to Widgets</h1>
<p>"""
    + (
        "Widgets are small mechanical devices used across 50 industries since 1990, "
        "with 3 main types and 12 documented subtypes. " * 3
    )
    + """</p>
<h2>History</h2>
<p>"""
    + (
        "In 1990 the first widget factory opened, producing 500 units per day "
        "with 42 employees across 5 departments. " * 3
    )
    + """</p>
<h2>Contact</h2>
<p>Reach the author, who has over 10 years of documented widget industry
expertise, at <a href="mailto:jane@acme.example">jane@acme.example</a> with
any questions about this guide or its 2 main sections.</p>
</body></html>"""
)


_GOOD_HTML = (
    """<html><head>
<title>The Complete Guide to Widgets</title>
<script type="application/ld+json">{"@context": "https://schema.org", "@type": "Article", "headline": "Widgets"}</script>
</head><body>
<h1>The Complete Guide to Widgets</h1>
<p>"""
    + (
        "Widgets are small mechanical devices used across 50 industries since 1990, "
        "with 3 main types and 12 documented subtypes. " * 3
    )
    + """</p>
<h2>History</h2>
<p>"""
    + ("In 1990 the first widget factory opened, producing 500 units per day. " * 3)
    + """</p>
</body></html>"""
)


class TestAnalyzeContentTiers:
    def test_excellent_tier(self) -> None:
        result = analyze_content(_EXCELLENT_HTML, has_llms_txt=True, has_ai_txt=True)
        assert "excellent" in result.summary.lower()

    def test_good_tier(self) -> None:
        result = analyze_content(_GOOD_HTML, has_llms_txt=True, has_ai_txt=False)
        assert "good" in result.summary.lower()
        assert 65 <= result.score.overall_score < 85

    def test_needs_improvement_tier(self) -> None:
        html = (
            "<html><head><title>A page with a decent title here</title>"
            '<meta name="description" content="A reasonably sized description that meets the ideal length range for meta descriptions.">'
            "</head><body><main><h1>Title</h1><p>"
            + ("Some reasonable content that is long enough to not be flagged as thin. " * 10)
            + "</p></main></body></html>"
        )
        result = analyze_content(html, has_llms_txt=False, has_ai_txt=False)
        assert "needs improvement" in result.summary.lower()
