"""AI crawler detection via User-Agent matching."""

from __future__ import annotations

from ai_visibility.crawlers import get_all_crawlers
from ai_visibility.types import CrawlerInfo


def detect_crawler(user_agent: str | None) -> CrawlerInfo | None:
    """Identify which known AI crawler sent a request, if any.

    Matching is a case-insensitive substring check of each registry
    entry's ``user_agent_pattern`` against ``user_agent`` — the same
    cheap, regex-free approach used by the npm package, safe to call on
    every request.

    Args:
        user_agent: The raw ``User-Agent`` header value.

    Returns:
        The matching :class:`~ai_visibility.types.CrawlerInfo`, or ``None``
        if the user agent is empty or unrecognized.
    """
    if not user_agent or not user_agent.strip():
        return None

    lowered = user_agent.lower()
    for crawler in get_all_crawlers():
        if crawler.user_agent_pattern in lowered:
            return crawler
    return None


def is_ai_crawler(user_agent: str | None) -> bool:
    """Return whether ``user_agent`` matches a known AI crawler.

    Args:
        user_agent: The raw ``User-Agent`` header value.

    Returns:
        ``True`` if the user agent matches an entry in the registry.
    """
    return detect_crawler(user_agent) is not None
