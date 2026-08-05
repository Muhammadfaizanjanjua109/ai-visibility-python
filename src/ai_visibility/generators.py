"""Generators for llms.txt, llms-full.txt, ai.txt, and AI-aware robots.txt."""

from __future__ import annotations

from ai_visibility.crawlers import get_all_crawlers
from ai_visibility.types import AiTxtConfig, LlmsFullTxtConfig, LlmsTxtConfig, RobotsTxtConfig


def generate_llms_txt(config: LlmsTxtConfig) -> str:
    """Generate an ``llms.txt`` file per the https://llmstxt.org spec.

    Args:
        config: Title, optional summary/details, and link sections.

    Returns:
        The complete ``llms.txt`` markdown content as a string.
    """
    lines = [f"# {config.title}", ""]

    if config.summary:
        lines.append(f"> {config.summary}")
        lines.append("")

    if config.details:
        lines.append(config.details)
        lines.append("")

    for section in config.sections:
        lines.append(f"## {section.name}")
        lines.append("")
        for link in section.links:
            entry = f"- [{link.title}]({link.url})"
            if link.description:
                entry += f": {link.description}"
            lines.append(entry)
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def generate_llms_full_txt(config: LlmsFullTxtConfig) -> str:
    """Generate an ``llms-full.txt`` file with full page content inlined.

    Args:
        config: Title, optional summary, and the full content of each page.

    Returns:
        The complete ``llms-full.txt`` markdown content as a string.
    """
    lines = [f"# {config.title}", ""]

    if config.summary:
        lines.append(f"> {config.summary}")
        lines.append("")

    for index, page in enumerate(config.pages):
        if index > 0:
            lines.append("---")
            lines.append("")
        lines.append(f"## {page.title}")
        lines.append(f"URL: {page.url}")
        lines.append("")
        lines.append(page.content)
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def generate_ai_txt(config: AiTxtConfig) -> str:
    """Generate an ``ai.txt`` file describing AI usage permissions.

    Args:
        config: Allow/disallow path rules plus optional contact/license info.

    Returns:
        The complete ``ai.txt`` content as a string.
    """
    lines = ["User-agent: *"]
    for path in config.allow:
        lines.append(f"Allow: {path}")
    for path in config.disallow:
        lines.append(f"Disallow: {path}")

    if config.contact or config.license:
        lines.append("")
        if config.contact:
            lines.append(f"Contact: {config.contact}")
        if config.license:
            lines.append(f"License: {config.license}")

    return "\n".join(lines) + "\n"


def generate_robots_txt(config: RobotsTxtConfig | None = None) -> str:
    """Generate an AI-aware ``robots.txt`` with per-crawler rules.

    Args:
        config: Explicit per-crawler rules, sitemap URLs, and options to
            bulk-block entire crawler categories (e.g. all training bots)
            using the shared crawler registry. Defaults to a single
            permissive ``User-agent: *`` block.

    Returns:
        The complete ``robots.txt`` content as a string.
    """
    cfg = config or RobotsTxtConfig()
    blocks: list[str] = []
    ruled_agents = {rule.user_agent.lower() for rule in cfg.rules}

    for rule in cfg.rules:
        block_lines = [f"User-agent: {rule.user_agent}"]
        for path in rule.allow:
            block_lines.append(f"Allow: {path}")
        for path in rule.disallow:
            block_lines.append(f"Disallow: {path}")
        blocks.append("\n".join(block_lines))

    categories_to_block = set(cfg.block_categories)
    if cfg.block_training_bots:
        from ai_visibility.types import CrawlerCategory

        categories_to_block.add(CrawlerCategory.TRAINING)

    if categories_to_block:
        for crawler in get_all_crawlers():
            if crawler.category in categories_to_block and crawler.name.lower() not in ruled_agents:
                blocks.append(f"User-agent: {crawler.name}\nDisallow: /")

    default_block = "User-agent: *\n" + ("Allow: /" if cfg.default_allow else "Disallow: /")
    blocks.append(default_block)

    if cfg.sitemap_urls:
        blocks.append("\n".join(f"Sitemap: {url}" for url in cfg.sitemap_urls))

    return "\n\n".join(blocks) + "\n"
