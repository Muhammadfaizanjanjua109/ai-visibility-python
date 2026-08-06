"""Multi-dimensional GEO/AI-visibility scoring for an HTML page.

The seven dimensions and their default weights are vendored from the npm
package's published ``scoring-weights.json`` (see
:mod:`ai_visibility.scoring_weights`), so scoring here uses the same
dimension set and weighting as the JS/TypeScript version rather than an
independently invented rubric. The npm package's own docs describe this
as a heuristic rubric with no published exact formulas ("a prioritized
to-do list, not a pass/fail grade"), so the *per-dimension arithmetic*
below is an original Python implementation written to match each
dimension's published description — it is not a byte-for-byte port of
unpublished TypeScript internals.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser

from ai_visibility.scoring_weights import get_default_weights
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
_HEADING_RE = re.compile(r"^h([1-6])$")
_FACT_TOKEN_RE = re.compile(r"\b\d[\d,.:%]*\b")
_ROBOTS_BLOCK_TOKENS = {"noindex", "none"}

_MIN_SECTION_WORDS = 20
_STRONG_ANSWER_WORDS = 40
_WEAK_ANSWER_WORDS = 20


class _SignalCollector(HTMLParser):
    """Single-pass extraction of the signals the scoring dimensions need."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[tuple[int, str]] = []
        self.jsonld_blocks: list[str] = []
        self.meta_author: str | None = None
        self.meta_robots: str | None = None
        self.has_contact_link = False
        self.section_word_counts: list[int] = []
        self.first_paragraph_word_count = 0
        self.total_word_count = 0
        self.fact_token_count = 0

        self._open_stack: list[str] = []
        self._non_text_depth_marker: int | None = None
        self._current_heading_level: int | None = None
        self._current_heading_buffer: list[str] = []
        self._in_ld_json = False
        self._ld_buffer: list[str] = []
        self._active_section_idx: int | None = None
        self._capturing_first_paragraph = False
        self._first_paragraph_done = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs, self_closing=tag in _VOID_ELEMENTS)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._open(tag, attrs, self_closing=True)

    def _open(self, tag: str, attrs: list[tuple[str, str | None]], self_closing: bool) -> None:
        attrs_dict = dict(attrs)

        if tag == "meta":
            name = (attrs_dict.get("name") or "").lower()
            content = attrs_dict.get("content")
            if name == "author" and content:
                self.meta_author = content
            if name == "robots" and content:
                self.meta_robots = content

        if tag == "a":
            href = (attrs_dict.get("href") or "").strip().lower()
            if href.startswith(("mailto:", "tel:")):
                self.has_contact_link = True

        if tag == "p" and not self_closing and not self._first_paragraph_done:
            self._capturing_first_paragraph = True

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

        if tag == "p" and self._capturing_first_paragraph:
            self._capturing_first_paragraph = False
            self._first_paragraph_done = True

        if _HEADING_RE.match(tag) and self._current_heading_level is not None:
            self.headings.append(
                (self._current_heading_level, "".join(self._current_heading_buffer).strip())
            )
            self.section_word_counts.append(0)
            self._active_section_idx = len(self.headings) - 1
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

        if self._current_heading_level is not None:
            self._current_heading_buffer.append(data)
        else:
            if self._active_section_idx is not None:
                self.section_word_counts[self._active_section_idx] += len(data.split())
            if self._capturing_first_paragraph:
                self.first_paragraph_word_count += len(data.split())

        self.total_word_count += len(data.split())
        self.fact_token_count += len(_FACT_TOKEN_RE.findall(data))


def _score_schema_coverage(collector: _SignalCollector, findings: list[Finding]) -> int:
    if not collector.jsonld_blocks:
        findings.append(
            Finding(
                severity=Severity.CRITICAL,
                message="No JSON-LD structured data found on the page.",
                fix="Add JSON-LD schema markup, e.g. via ai_visibility.schema.article_schema().",
                dimension="schema_coverage",
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
                dimension="schema_coverage",
            )
        )
        return 40

    return 100


def _score_heading_structure(collector: _SignalCollector, findings: list[Finding]) -> int:
    headings = collector.headings
    if not headings:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="No headings found on the page.",
                fix="Add a single <h1> and a logical heading hierarchy (h2, h3, ...).",
                dimension="heading_structure",
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
                dimension="heading_structure",
            )
        )
    else:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message=f"Found {h1_count} <h1> elements; expected exactly one.",
                fix="Use a single <h1> per page for a clear primary topic.",
                dimension="heading_structure",
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
                dimension="heading_structure",
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
                dimension="heading_structure",
            )
        )

    return score


def _score_crawler_accessibility(
    collector: _SignalCollector,
    has_llms_txt: bool | None,
    has_ai_txt: bool | None,
    findings: list[Finding],
) -> tuple[int, bool]:
    """Score crawler accessibility. Returns ``(score, hard_block)``.

    A hard meta-robots block is a gate, not just a differentiator: per the
    vendored dimension description, it "zeroes out every other dimension's
    value", so callers must zero the overall score when ``hard_block`` is
    ``True``.
    """
    robots_tokens = {token.strip() for token in (collector.meta_robots or "").lower().split(",")}
    if robots_tokens & _ROBOTS_BLOCK_TOKENS:
        findings.append(
            Finding(
                severity=Severity.CRITICAL,
                message="Meta robots tag blocks indexing (noindex/none); "
                "no AI crawler can be shown this page.",
                fix="Remove the noindex/none directive from the robots meta tag "
                "if this page should be discoverable.",
                dimension="crawler_accessibility",
            )
        )
        return 0, True

    if has_llms_txt is None and has_ai_txt is None:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="llms.txt / ai.txt presence was not checked.",
                fix="Pass has_llms_txt/has_ai_txt to score_page(), "
                "or use `ai-visibility audit <url>`.",
                dimension="crawler_accessibility",
            )
        )
        return 50, False

    score = 40
    if has_llms_txt:
        score += 30
    elif has_llms_txt is False:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="No llms.txt found.",
                fix="Generate one with ai_visibility.generators.generate_llms_txt().",
                dimension="crawler_accessibility",
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
                dimension="crawler_accessibility",
            )
        )

    return min(score, 100), False


def _score_eeat_signals(collector: _SignalCollector, findings: list[Finding]) -> int:
    score = 0
    missing = []

    if collector.meta_author:
        score += 30
    else:
        missing.append("an author meta tag")

    has_jsonld_authority = False
    for block in collector.jsonld_blocks:
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and ("author" in parsed or "publisher" in parsed):
            has_jsonld_authority = True
            break
    if has_jsonld_authority:
        score += 40
    else:
        missing.append("author/publisher in JSON-LD")

    if collector.has_contact_link:
        score += 30
    else:
        missing.append("a contact link (mailto:/tel:)")

    if missing:
        findings.append(
            Finding(
                severity=Severity.WARNING if score == 0 else Severity.INFO,
                message=f"Missing authority/trust signals: {', '.join(missing)}.",
                fix="Add an author meta tag, author/publisher JSON-LD, and a "
                "contact link to establish E-E-A-T signals.",
                dimension="eeat_signals",
            )
        )

    return score


def _score_fact_density(collector: _SignalCollector, findings: list[Finding]) -> int:
    if collector.total_word_count == 0:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="No visible text content to evaluate factual density against.",
                fix="Add substantive written content to the page.",
                dimension="fact_density",
            )
        )
        return 0

    density = collector.fact_token_count / collector.total_word_count * 100

    if density >= 3:
        return 100
    if density >= 1.5:
        return 70
    if density >= 0.5:
        return 40

    findings.append(
        Finding(
            severity=Severity.INFO,
            message=f"Low factual density ({density:.1f} concrete numbers/stats per 100 words).",
            fix="Include more concrete numbers, dates, and statistics "
            "to make content easier to cite.",
            dimension="fact_density",
        )
    )
    return 10


def _score_snippability(collector: _SignalCollector, findings: list[Finding]) -> int:
    if not collector.headings:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="No headings to evaluate section snippability against.",
                fix="Break content into headed sections so each can be excerpted independently.",
                dimension="snippability",
            )
        )
        return 0

    well_formed = sum(1 for count in collector.section_word_counts if count >= _MIN_SECTION_WORDS)
    score = round(100 * well_formed / len(collector.headings))

    if score < 100:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="Some sections have too little content under their heading "
                "to stand alone as an excerpt.",
                fix=f"Ensure each section has at least {_MIN_SECTION_WORDS} words "
                "of self-contained content.",
                dimension="snippability",
            )
        )

    return score


def _score_answer_front_loading(collector: _SignalCollector, findings: list[Finding]) -> int:
    if collector.headings and collector.headings[0][0] == 1:
        lead_words = collector.section_word_counts[0]
    else:
        lead_words = collector.first_paragraph_word_count

    if lead_words >= _STRONG_ANSWER_WORDS:
        return 100

    if lead_words >= _WEAK_ANSWER_WORDS:
        findings.append(
            Finding(
                severity=Severity.INFO,
                message="The opening content is brief; a fuller direct answer near "
                "the top would help AI systems extract it.",
                fix=f"Lead with at least {_STRONG_ANSWER_WORDS} words directly "
                "answering the page's main question.",
                dimension="answer_front_loading",
            )
        )
        return 60

    if lead_words > 0:
        findings.append(
            Finding(
                severity=Severity.WARNING,
                message="Very little content appears before the reader has to "
                "dig further into the page.",
                fix=f"Lead with at least {_STRONG_ANSWER_WORDS} words directly "
                "answering the page's main question.",
                dimension="answer_front_loading",
            )
        )
        return 20

    findings.append(
        Finding(
            severity=Severity.CRITICAL,
            message="No direct-answer content found near the top of the page.",
            fix="Open the page (or its main heading's section) with a direct, "
            "self-contained answer to its main question.",
            dimension="answer_front_loading",
        )
    )
    return 0


def score_page(
    html: str,
    url: str | None = None,
    config: ScoringConfig | None = None,
    has_llms_txt: bool | None = None,
    has_ai_txt: bool | None = None,
) -> ScoreResult:
    """Score an HTML page across GEO/AI-visibility dimensions.

    The dimension set and default weights are vendored from the npm
    package's ``scoring-weights.json`` (see
    :mod:`ai_visibility.scoring_weights`) so results use the same rubric
    as the JS/TypeScript version.

    Args:
        html: The page's HTML source.
        url: The page's URL, used only for context in findings (unused
            for now, reserved for future dimension-specific messages).
        config: Per-dimension weight overrides. Unset fields fall back to
            the vendored defaults.
        has_llms_txt: Whether ``llms.txt`` is known to exist for this site.
            Pass ``None`` (default) if unknown — checking requires an HTTP
            request, which the core scoring engine deliberately does not make.
        has_ai_txt: Whether ``ai.txt`` is known to exist for this site.

    Returns:
        A :class:`~ai_visibility.types.ScoreResult` with an overall score,
        per-dimension scores, and actionable findings. If the page's meta
        robots tag hard-blocks indexing, ``overall_score`` is forced to 0
        regardless of other dimensions, per the vendored crawler
        accessibility dimension's definition.
    """
    del url  # reserved for future use
    cfg = config or ScoringConfig()
    collector = _SignalCollector()
    collector.feed(html)
    collector.close()

    findings: list[Finding] = []

    crawler_accessibility_score, hard_block = _score_crawler_accessibility(
        collector, has_llms_txt, has_ai_txt, findings
    )

    dimension_scores = {
        "answer_front_loading": _score_answer_front_loading(collector, findings),
        "eeat_signals": _score_eeat_signals(collector, findings),
        "heading_structure": _score_heading_structure(collector, findings),
        "schema_coverage": _score_schema_coverage(collector, findings),
        "fact_density": _score_fact_density(collector, findings),
        "snippability": _score_snippability(collector, findings),
        "crawler_accessibility": crawler_accessibility_score,
    }

    default_weights = get_default_weights()
    overrides: dict[str, float | None] = {
        "answer_front_loading": cfg.answer_front_loading_weight,
        "eeat_signals": cfg.eeat_signals_weight,
        "heading_structure": cfg.heading_structure_weight,
        "schema_coverage": cfg.schema_coverage_weight,
        "fact_density": cfg.fact_density_weight,
        "snippability": cfg.snippability_weight,
        "crawler_accessibility": cfg.crawler_accessibility_weight,
    }
    weights: dict[str, float] = {}
    for dim in dimension_scores:
        override = overrides[dim]
        weights[dim] = override if override is not None else default_weights[dim]

    if hard_block:
        overall = 0
    else:
        overall = round(sum(dimension_scores[dim] * weights[dim] for dim in dimension_scores))

    return ScoreResult(
        overall_score=overall,
        dimension_scores=dimension_scores,
        findings=findings,
    )
