"""HTML optimization: strip scripts/styles/tracking, keep AI-crawler-relevant content.

Implemented entirely on top of :mod:`html.parser` from the standard library
— no BeautifulSoup or lxml dependency.
"""

from __future__ import annotations

import json
import re
from html import escape
from html.parser import HTMLParser
from typing import Any

from ai_visibility.types import OptimizeOptions

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

_RAW_TEXT_TAGS = {"script", "style"}

_TRACKING_SRC_PATTERNS = (
    "pixel",
    "beacon",
    "track",
    "analytics",
    "doubleclick",
    "facebook.com/tr",
    "google-analytics",
    "googletagmanager",
    "/collect?",
)

_AD_SUBSTRING_PATTERNS = (
    "adsbygoogle",
    "advertisement",
    "ad-container",
    "ad-banner",
    "google_ads",
    "doubleclick",
    "googlesyndication",
    "taboola",
    "outbrain",
)

_AD_CLASS_TOKENS = {"ad", "ads", "advert", "advertisement", "sponsor", "sponsored"}

_AD_ELIGIBLE_TAGS = {"div", "ins", "iframe", "aside", "section"}


def _is_tracking_img(attrs: dict[str, str | None]) -> bool:
    width = attrs.get("width")
    height = attrs.get("height")
    if width in ("0", "1") and height in ("0", "1"):
        return True
    src = (attrs.get("src") or "").lower()
    return any(pattern in src for pattern in _TRACKING_SRC_PATTERNS)


def _is_ad_element(tag: str, attrs: dict[str, str | None]) -> bool:
    if tag not in _AD_ELIGIBLE_TAGS:
        return False
    class_attr = (attrs.get("class") or "").lower()
    id_attr = (attrs.get("id") or "").lower()
    src_attr = (attrs.get("src") or "").lower()

    combined = f"{class_attr} {id_attr} {src_attr}"
    if any(pattern in combined for pattern in _AD_SUBSTRING_PATTERNS):
        return True

    tokens = set(class_attr.split()) | set(id_attr.split("-"))
    return bool(tokens & _AD_CLASS_TOKENS)


def _is_ld_json_script(attrs: dict[str, str | None]) -> bool:
    return (attrs.get("type") or "").lower() == "application/ld+json"


def _serialize_starttag(
    tag: str, attrs: list[tuple[str, str | None]], self_close: bool = False
) -> str:
    parts = [f"<{tag}"]
    for name, value in attrs:
        if value is None:
            parts.append(f" {name}")
        else:
            parts.append(f' {name}="{escape(value, quote=True)}"')
    parts.append(" />" if self_close else ">")
    return "".join(parts)


class _OptimizingParser(HTMLParser):
    """Streams HTML through, dropping elements the given options exclude."""

    def __init__(self, options: OptimizeOptions) -> None:
        super().__init__(convert_charrefs=True)
        self.options = options
        self.output: list[str] = []
        self._open_stack: list[str] = []
        self._skip_from_depth: int | None = None
        self._raw_text_tag: str | None = None

    @property
    def _skipping(self) -> bool:
        return self._skip_from_depth is not None

    def _should_skip_element(self, tag: str, attrs: dict[str, str | None]) -> bool:
        opts = self.options
        if tag == "script":
            if _is_ld_json_script(attrs):
                return False
            return opts.strip_scripts
        if tag == "style":
            return opts.strip_styles
        if tag == "noscript":
            return opts.strip_noscript
        if opts.strip_tracking:
            if tag == "img" and _is_tracking_img(attrs):
                return True
            if _is_ad_element(tag, attrs):
                return True
        return False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_open(tag, attrs, self_closing=tag in _VOID_ELEMENTS)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle_open(tag, attrs, self_closing=True)

    def _handle_open(
        self, tag: str, attrs: list[tuple[str, str | None]], self_closing: bool
    ) -> None:
        attrs_dict = dict(attrs)

        if self._skipping:
            if not self_closing:
                self._open_stack.append(tag)
            return

        if self._should_skip_element(tag, attrs_dict):
            if self_closing:
                return
            self._open_stack.append(tag)
            self._skip_from_depth = len(self._open_stack)
            return

        filtered_attrs = self._filter_attrs(attrs)
        self.output.append(_serialize_starttag(tag, filtered_attrs, self_closing))

        if not self_closing:
            self._open_stack.append(tag)
            if tag in _RAW_TEXT_TAGS:
                self._raw_text_tag = tag

    def _filter_attrs(self, attrs: list[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
        opts = self.options
        filtered = []
        for name, value in attrs:
            lname = name.lower()
            if opts.strip_event_handlers and lname.startswith("on"):
                continue
            if opts.strip_styles and lname == "style":
                continue
            filtered.append((name, value))
        return filtered

    def handle_endtag(self, tag: str) -> None:
        if not self._open_stack:
            return
        depth_before_pop = len(self._open_stack)
        self._open_stack.pop()

        if self._skipping:
            if depth_before_pop == self._skip_from_depth:
                self._skip_from_depth = None
            return

        if tag == self._raw_text_tag:
            self._raw_text_tag = None

        self.output.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._skipping:
            return
        if self._raw_text_tag is not None:
            self.output.append(data)
        else:
            self.output.append(escape(data, quote=False))

    def handle_comment(self, data: str) -> None:
        if self._skipping:
            return
        self.output.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        if self._skipping:
            return
        self.output.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        if self._skipping:
            return
        self.output.append(f"<?{data}>")


_HEAD_CLOSE_RE = re.compile(r"</head\s*>", re.IGNORECASE)


def _render_ld_json(schema: dict[str, Any]) -> str:
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'


def inject_schemas(html: str, schemas: list[dict[str, Any]]) -> str:
    """Insert JSON-LD ``<script>`` tags into an HTML document's ``<head>``.

    Args:
        html: The source HTML document.
        schemas: JSON-LD schema dicts to inject, e.g. from
            :mod:`ai_visibility.schema` builders.

    Returns:
        The HTML with schemas inserted just before ``</head>``, or appended
        to the end of the document if no ``<head>`` closing tag is found.
    """
    if not schemas:
        return html
    markup = "".join(_render_ld_json(schema) for schema in schemas)
    match = _HEAD_CLOSE_RE.search(html)
    if match:
        return html[: match.start()] + markup + html[match.start() :]
    return html + markup


def optimize_html(html: str, options: OptimizeOptions | None = None) -> str:
    """Strip clutter from an HTML document while preserving AI-relevant content.

    Removes ``<script>`` (except JSON-LD), ``<style>``, ``<noscript>``,
    inline event handlers, and tracking/ad elements, while preserving
    semantic HTML structure, ``<meta>`` tags, JSON-LD, Open Graph tags,
    headings, and landmark elements.

    Args:
        html: The source HTML document as a string.
        options: Controls which categories of content are stripped, and
            any extra JSON-LD schemas to inject. Defaults to stripping
            everything the options support.

    Returns:
        The optimized HTML as a string.
    """
    opts = options or OptimizeOptions()
    parser = _OptimizingParser(opts)
    parser.feed(html)
    parser.close()
    result = "".join(parser.output)
    return inject_schemas(result, opts.inject_schemas)
