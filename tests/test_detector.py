"""Tests for ai_visibility.detector and ai_visibility.crawlers."""

from __future__ import annotations

import pytest

from ai_visibility.crawlers import (
    get_all_crawlers,
    get_crawler_by_name,
    get_crawlers_by_category,
)
from ai_visibility.detector import detect_crawler, is_ai_crawler
from ai_visibility.types import CrawlerCategory


class TestRegistry:
    def test_get_all_crawlers_nonempty(self) -> None:
        crawlers = get_all_crawlers()
        assert len(crawlers) > 10
        names = {c.name for c in crawlers}
        assert "GPTBot" in names
        assert "ClaudeBot" in names

    def test_get_crawlers_by_category(self) -> None:
        training = get_crawlers_by_category(CrawlerCategory.TRAINING)
        assert all(c.category == CrawlerCategory.TRAINING for c in training)
        assert any(c.name == "GPTBot" for c in training)

    def test_get_crawlers_by_category_string(self) -> None:
        search = get_crawlers_by_category("search")
        assert all(c.category == CrawlerCategory.SEARCH for c in search)

    def test_get_crawler_by_name_case_insensitive(self) -> None:
        crawler = get_crawler_by_name("gptbot")
        assert crawler is not None
        assert crawler.name == "GPTBot"
        assert crawler.company == "OpenAI"

    def test_get_crawler_by_name_missing(self) -> None:
        assert get_crawler_by_name("NotARealBot") is None


class TestDetectCrawler:
    @pytest.mark.parametrize(
        "user_agent,expected_name",
        [
            ("Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)", "GPTBot"),
            ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) ClaudeBot/1.0", "ClaudeBot"),
            ("Mozilla/5.0 (compatible; PerplexityBot/1.0)", "PerplexityBot"),
            ("Bytespider", "Bytespider"),
        ],
    )
    def test_detects_known_crawlers(self, user_agent: str, expected_name: str) -> None:
        result = detect_crawler(user_agent)
        assert result is not None
        assert result.name == expected_name

    def test_returns_none_for_regular_browser(self) -> None:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        assert detect_crawler(ua) is None

    def test_returns_none_for_empty_or_none(self) -> None:
        assert detect_crawler("") is None
        assert detect_crawler(None) is None
        assert detect_crawler("   ") is None

    def test_is_case_insensitive(self) -> None:
        assert detect_crawler("MOZILLA GPTBOT/1.0") is not None


class TestIsAiCrawler:
    def test_true_for_known_crawler(self) -> None:
        assert is_ai_crawler("ClaudeBot/1.0") is True

    def test_false_for_browser(self) -> None:
        assert is_ai_crawler("Mozilla/5.0 Chrome/120.0") is False
