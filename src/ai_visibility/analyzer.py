"""Human-readable AI-readability analysis, built on top of scoring."""

from __future__ import annotations

from ai_visibility.scoring import score_page
from ai_visibility.types import AnalysisResult, Finding, ScoreResult, ScoringConfig, Severity

_SEVERITY_ORDER = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}


def _build_summary(score: ScoreResult) -> str:
    overall = score.overall_score
    if overall >= 85:
        tier = "excellent"
    elif overall >= 65:
        tier = "good"
    elif overall >= 40:
        tier = "needs improvement"
    else:
        tier = "poor"

    critical_count = sum(1 for f in score.findings if f.severity == Severity.CRITICAL)
    warning_count = sum(1 for f in score.findings if f.severity == Severity.WARNING)

    parts = [f"AI-visibility is {tier} ({overall}/100)."]
    if critical_count:
        plural = "s" if critical_count != 1 else ""
        parts.append(
            f"{critical_count} critical issue{plural} likely block AI crawlers "
            "from understanding this page well."
        )
    if warning_count:
        plural = "s" if warning_count != 1 else ""
        parts.append(f"{warning_count} warning{plural} should be addressed.")

    weakest_dim = min(score.dimension_scores, key=lambda d: score.dimension_scores[d])
    weakest_score = score.dimension_scores[weakest_dim]
    parts.append(f"Weakest area: {weakest_dim.replace('_', ' ')} ({weakest_score}/100).")
    return " ".join(parts)


def analyze_content(
    html: str,
    url: str | None = None,
    config: ScoringConfig | None = None,
    has_llms_txt: bool | None = None,
    has_ai_txt: bool | None = None,
) -> AnalysisResult:
    """Produce a human-readable AI-visibility report for an HTML page.

    This wraps :func:`ai_visibility.scoring.score_page` with a plain-English
    summary and a priority-ordered list of recommendations (critical issues
    first).

    Args:
        html: The page's HTML source.
        url: The page's URL, passed through to the scorer for context.
        config: Per-dimension scoring weights.
        has_llms_txt: Whether ``llms.txt`` is known to exist for this site.
        has_ai_txt: Whether ``ai.txt`` is known to exist for this site.

    Returns:
        An :class:`~ai_visibility.types.AnalysisResult` with the underlying
        score, a summary string, and ranked recommendations.
    """
    score = score_page(
        html, url=url, config=config, has_llms_txt=has_llms_txt, has_ai_txt=has_ai_txt
    )
    recommendations: list[Finding] = sorted(
        score.findings, key=lambda finding: _SEVERITY_ORDER[finding.severity]
    )
    return AnalysisResult(
        score=score,
        summary=_build_summary(score),
        recommendations=recommendations,
    )
