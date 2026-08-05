"""Loader for the shared AI crawler registry (``crawlers.json``).

This is the same source-of-truth data used by the ``ai-visibility`` npm
package, so a page classified as visible to ``GPTBot`` here will be
classified the same way in the JavaScript/TypeScript version.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from ai_visibility.types import CrawlerCategory, CrawlerInfo

_REGISTRY_FILE = "crawlers.json"


def _parse_crawler(raw: dict[str, object]) -> CrawlerInfo:
    return CrawlerInfo(
        name=str(raw["name"]),
        company=str(raw["company"]),
        user_agent_pattern=str(raw["userAgentPattern"]),
        category=CrawlerCategory(raw["category"]),
        verified=bool(raw.get("verified", False)),
        source_url=raw.get("sourceUrl") or None,  # type: ignore[arg-type]
        last_checked=raw.get("lastChecked") or None,  # type: ignore[arg-type]
    )


@lru_cache(maxsize=1)
def _load_registry() -> tuple[CrawlerInfo, ...]:
    raw_text = resources.files("ai_visibility").joinpath(_REGISTRY_FILE).read_text(encoding="utf-8")
    data = json.loads(raw_text)
    return tuple(_parse_crawler(entry) for entry in data["crawlers"])


def get_all_crawlers() -> list[CrawlerInfo]:
    """Return every known crawler in the registry.

    Returns:
        A list of :class:`~ai_visibility.types.CrawlerInfo`, in registry order.
    """
    return list(_load_registry())


def get_crawlers_by_category(category: CrawlerCategory | str) -> list[CrawlerInfo]:
    """Return crawlers matching the given category.

    Args:
        category: A :class:`~ai_visibility.types.CrawlerCategory` or its
            string value (``"training"``, ``"search"``, ``"indexing"``).

    Returns:
        Matching crawlers, in registry order.
    """
    wanted = CrawlerCategory(category)
    return [c for c in _load_registry() if c.category == wanted]


def get_crawler_by_name(name: str) -> CrawlerInfo | None:
    """Look up a single crawler by its exact, case-insensitive name.

    Args:
        name: Crawler name, e.g. ``"GPTBot"``.

    Returns:
        The matching :class:`~ai_visibility.types.CrawlerInfo`, or ``None``.
    """
    lowered = name.lower()
    for crawler in _load_registry():
        if crawler.name.lower() == lowered:
            return crawler
    return None
