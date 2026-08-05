"""Multi-dimensional GEO/AI-visibility scoring for an HTML page."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Optional

from ai_visibility.types import Finding, ScoreResult, ScoringConfig, Severity

_VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

_NON_TEXT_TAGS = {"script", "style", "noscript"}
_SEMANTIC_TAGS = {"main", "article", "nav", "header", "footer", "section", "aside", "figure"}
_HEADING_RE = re.compile(r"^h([1-6])$")


class _SignalCollector(HTMLParser):
    """Single-pass extraction of the signals scoring dimensions need."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags_seen: set[str] = set()
        self.meta_description: Optional[str] = None
        self.og_tags: dict[str, str] = {}
        self.title_text = ""
        self.headings: list[tuple[int, str]] = []
        self.jsonld_blocks: list[str] = []
        self.text_chars = 0

        self._open_stack: list[str] = []
        self._non_text_depth_marker: Optional[int] = None
        self._in_title = False
        self._current_heading_level: Optional[int] = None
        self._current_heading_buffer: list[str] = []
        self._in_ld_json = False
        self._ld_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs, self_closing=tag in _VOID_ELEMENTS)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs, self_closing=True)

    def _open(self, tag: str, attrs: list[tuple[str, str | None]], self_closing: bool) -> None:
        attrs_dict = dict(attrs)

        if tag in _SEMANTIC_TAGS:
            self.tags_seen.add(tag)
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = (attrs_dict.get("name") or "").lower()
            property_ = (attrs_dict.get("property") or "").lower()
            content = attrs_dict.get("content")
            if name == "description" and content:
                self.meta_description = content
            if property_.startswith("og:") and content is not None:
                self.og_tags[property_] = content

        heading_match = _HEADING_RE.match(tag)
        if heading_match:
            self._current_heading_level = int(heading_match.group(1))
            self._current_heading_buffer = []

        if tag == "script" and (attrs_dict.get("type") or "").lower() == "application/ld+json":
            self._in_ld_json = True
            self._ld_buffer = []

        if not self_closing:
            self._open_stack.append(tag)
            if tag in _NON_TEXT_TAGS and self._non_text_depth_marker is None:
                self._non_text_depth_marker = len(self._open_stack)

    def handle_endtag(self, tag: str) -> None:
        if not self._open_stack:
            return
        depth_before_pop = len(self._open_stack)
        self._open_stack.pop()

        if tag == "title":
            self._in_title = False
        if _HEADING_RE.match(tag) and self._current_heading_level is not None:
            self.headings.append(
                (self._current_heading_level, "".join(self._current_heading_buffer).strip())
            )
            self._current_heading_level = None
        if tag == "script" and self._in_ld_json:
            self.jsonld_blocks.append("".join(self._ld_buffer))
            self._in_ld_json = False

        if (
            self._non_text_depth_marker is not None
            and depth_before_pop == self._non_text_depth_marker
        ):
            self._non_text_depth_marker = None

    def handle_data(self, data: str) -> None:
        if self._in_ld_json:
            self._ld_buffer.append(data)
            return
        if self._non_text_depth_marker is not None:
            return
        if self._in_title:
            self.title_text += data
        if self._current_heading_level is not None:
            self._current_heading_buffer.append(data)
        self.text_chars += len(data.strip())


def _score_structured_data(collector: _SignalCollector, findings: list[Finding]) -> int:
    if not collector.jsonld_blocks:
        findings.append(
            Finding(
                severity=Severity.CRITICAL,
                message="No JSON-LD structured data found on the page.",
                fix="Add JSON-LD schema markup, e.g. via ai_visibility.schema.article_schema().",
                dimension="structured_data",
            )
        )
        return 0

    valid_count = 0
    for block in collector.jsonld_blocks:
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and ("@type" in parsed or "@graph" in parsed):
            valid_count += 1

    if valid_count == 0:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="JSON-LD script tag(s) found but none parsed as valid schema.org markup.",
                fix="Validate JSON-LD content and ensure it includes '@type'.",
                dimension="structured_data",
            )
        )
        return 40

    return 100


def _score_semantic_html(collector: _SignalCollector, findings: list[Finding]) -> int:
    important = {"main", "article", "header", "footer", "nav"}
    found_important = collector.tags_seen & important
    score = round(100 * len(collector.tags_seen) / len(_SEMANTIC_TAGS))

    if "main" not in collector.tags_seen and "article" not in collector.tags_seen:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="No <main> or <article> landmark found.",
                fix="Wrap primary content in a <main> or <article> element "
                "so crawlers can locate it.",
                dimension="semantic_html",
            )
        )
    missing_important = important - found_important
    if missing_important and missing_important != {"main", "article"}:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message=f"Missing semantic landmark(s): {', '.join(sorted(missing_important))}.",
                fix="Use semantic HTML5 elements (header, nav, main, article, footer) "
                "over generic <div>s.",
                dimension="semantic_html",
            )
        )
    return min(score, 100)


def _score_meta_tags(collector: _SignalCollector, findings: list[Finding]) -> int:
    score = 0
    title = collector.title_text.strip()
    if title:
        score += 30
    else:
        findings.append(
            Finding(
                severity=Severity.CRITICAL,
                message="Missing or empty <title> tag.",
                fix="Add a descriptive <title> tag summarizing the page.",
                dimension="meta_tags",
            )
        )

    description = (collector.meta_description or "").strip()
    if description:
        score += 30
        if not (50 <= len(description) <= 160):
            findings.append(
                Finding(
                    severity=Severity.INFO,
                    message=f"Meta description length ({len(description)} chars) is outside "
                    "the ideal 50-160 range.",
                    fix="Rewrite the meta description to be 50-160 characters.",
                    dimension="meta_tags",
                )
            )
    else:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="Missing meta description.",
                fix='Add <meta name="description" content="..."> summarizing the page.',
                dimension="meta_tags",
            )
        )

    if collector.og_tags.get("og:title"):
        score += 15
    else:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="Missing og:title meta tag.",
                fix='Add <meta property="og:title" content="...">.',
                dimension="meta_tags",
            )
        )

    if collector.og_tags.get("og:description"):
        score += 15
    else:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="Missing og:description meta tag.",
                fix='Add <meta property="og:description" content="...">.',
                dimension="meta_tags",
            )
        )

    if collector.og_tags.get("og:image"):
        score += 10
    else:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="Missing og:image meta tag.",
                fix='Add <meta property="og:image" content="...">.',
                dimension="meta_tags",
            )
        )

    return score


def _score_heading_hierarchy(collector: _SignalCollector, findings: list[Finding]) -> int:
    headings = collector.headings
    if not headings:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="No headings found on the page.",
                fix="Add a single <h1> and a logical heading hierarchy (h2, h3, ...).",
                dimension="heading_hierarchy",
            )
        )
        return 0

    score = 0
    h1_count = sum(1 for level, _ in headings if level == 1)
    if h1_count == 1:
        score += 40
    elif h1_count == 0:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="No <h1> found on the page.",
                fix="Add exactly one <h1> describing the page's main topic.",
                dimension="heading_hierarchy",
            )
        )
    else:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message=f"Found {h1_count} <h1> elements; expected exactly one.",
                fix="Use a single <h1> per page for a clear primary topic.",
                dimension="heading_hierarchy",
            )
        )

    max_seen = 0
    has_skip = False
    for level, _ in headings:
        if level > max_seen + 1:
            has_skip = True
        max_seen = max(max_seen, level)
    if not has_skip:
        score += 40
    else:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="Heading levels skip a level (e.g. h2 to h4 with no h3).",
                fix="Keep heading levels sequential without skipping.",
                dimension="heading_hierarchy",
            )
        )

    if all(text for _, text in headings):
        score += 20
    else:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="One or more headings have no text content.",
                fix="Ensure every heading element contains descriptive text.",
                dimension="heading_hierarchy",
            )
        )

    return score


def _score_accessibility(collector: _SignalCollector, html: str, findings: list[Finding]) -> int:
    total_length = max(len(html), 1)
    ratio = collector.text_chars / total_length

    if collector.text_chars < 100:
        findings.append(
            Finding(
                severity=Severity.CRITICAL,
                message=f"Very little visible text content ({collector.text_chars} chars).",
                fix="Ensure meaningful content is present in the initial HTML response, "
                "not injected by client-side JS.",
                dimension="accessibility",
            )
        )
        return 10

    if ratio >= 0.15:
        return 100
    if ratio >= 0.05:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message=f"Text-to-markup ratio is low ({ratio:.0%}).",
                fix="Reduce markup/script overhead relative to visible text, "
                "or server-render more content.",
                dimension="accessibility",
            )
        )
        return 60

    findings.append(
        Finding(
            severity=Severity.WARNING,
            message=f"Text-to-markup ratio is very low ({ratio:.0%}); "
            "content may rely on client-side rendering.",
            fix="Serve a server-rendered HTML snapshot to AI crawlers "
            "(see ai_visibility.optimizer).",
            dimension="accessibility",
        )
    )
    return 20


def _score_llms_txt(
    has_llms_txt: Optional[bool], has_ai_txt: Optional[bool], findings: list[Finding]
) -> int:
    if has_llms_txt is None and has_ai_txt is None:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="llms.txt / ai.txt presence was not checked.",
                fix="Pass has_llms_txt/has_ai_txt to score_page(), "
                "or use `ai-visibility audit <url>`.",
                dimension="llms_txt",
            )
        )
        return 50

    score = 0
    if has_llms_txt:
        score += 70
    elif has_llms_txt is False:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="No llms.txt found.",
                fix="Generate one with ai_visibility.generators.generate_llms_txt().",
                dimension="llms_txt",
            )
        )

    if has_ai_txt:
        score += 30
    elif has_ai_txt is False:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="No ai.txt found.",
                fix="Generate one with ai_visibility.generators.generate_ai_txt().",
                dimension="llms_txt",
            )
        )

    return score


def score_page(
    html: str,
    url: Optional[str] = None,
    config: Optional[ScoringConfig] = None,
    has_llms_txt: Optional[bool] = None,
    has_ai_txt: Optional[bool] = None,
) -> ScoreResult:
    """Score an HTML page across GEO/AI-visibility dimensions.

    Args:
        html: The page's HTML source.
        url: The page's URL, used only for context in findings (unused
            for now, reserved for future dimension-specific messages).
        config: Per-dimension weights. Defaults to :class:`ScoringConfig`'s
            built-in weights.
        has_llms_txt: Whether ``llms.txt`` is known to exist for this site.
            Pass ``None`` (default) if unknown — checking requires an HTTP
            request, which the core scoring engine deliberately does not make.
        has_ai_txt: Whether ``ai.txt`` is known to exist for this site.

    Returns:
        A :class:`~ai_visibility.types.ScoreResult` with an overall score,
        per-dimension scores, and actionable findings.
    """
    del url  # reserved for future use
    cfg = config or ScoringConfig()
    collector = _SignalCollector()
    collector.feed(html)
    collector.close()

    findings: list[Finding] = []
    dimension_scores = {
        "structured_data": _score_structured_data(collector, findings),
        "semantic_html": _score_semantic_html(collector, findings),
        "meta_tags": _score_meta_tags(collector, findings),
        "heading_hierarchy": _score_heading_hierarchy(collector, findings),
        "accessibility": _score_accessibility(collector, html, findings),
        "llms_txt": _score_llms_txt(has_llms_txt, has_ai_txt, findings),
    }

    weights = {
        "structured_data": cfg.structured_data_weight,
        "semantic_html": cfg.semantic_html_weight,
        "meta_tags": cfg.meta_tags_weight,
        "heading_hierarchy": cfg.heading_hierarchy_weight,
        "accessibility": cfg.accessibility_weight,
        "llms_txt": cfg.llms_txt_weight,
    }

    overall = round(sum(dimension_scores[dim] * weights[dim] for dim in dimension_scores))

    return ScoreResult(
        overall_score=overall,
        dimension_scores=dimension_scores,
        findings=findings,
    )
