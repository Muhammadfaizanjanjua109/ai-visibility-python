"""Tests for ai_visibility.analytics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ai_visibility.analytics import CrawlerAnalytics, InMemoryAnalyticsStore
from ai_visibility.crawlers import get_crawler_by_name
from ai_visibility.types import AnalyticsStore, CrawlerVisit


def _gptbot():
    crawler = get_crawler_by_name("GPTBot")
    assert crawler is not None
    return crawler


def _claudebot():
    crawler = get_crawler_by_name("ClaudeBot")
    assert crawler is not None
    return crawler


class TestLogAndGetVisits:
    def test_log_visit_and_retrieve(self) -> None:
        analytics = CrawlerAnalytics()
        analytics.log_visit(_gptbot(), "/blog/post-1")
        visits = analytics.get_visits()
        assert len(visits) == 1
        assert visits[0].crawler_name == "GPTBot"
        assert visits[0].path == "/blog/post-1"

    def test_filter_by_crawler_name(self) -> None:
        analytics = CrawlerAnalytics()
        analytics.log_visit(_gptbot(), "/a")
        analytics.log_visit(_claudebot(), "/b")
        visits = analytics.get_visits(crawler_name="claudebot")
        assert len(visits) == 1
        assert visits[0].crawler_name == "ClaudeBot"

    def test_filter_by_since(self) -> None:
        analytics = CrawlerAnalytics()
        old_time = datetime.now(timezone.utc) - timedelta(days=2)
        analytics.log_visit(_gptbot(), "/old", timestamp=old_time)
        analytics.log_visit(_gptbot(), "/new")
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        visits = analytics.get_visits(since=cutoff)
        assert len(visits) == 1
        assert visits[0].path == "/new"

    def test_timestamp_defaults_to_now(self) -> None:
        analytics = CrawlerAnalytics()
        before = datetime.now(timezone.utc)
        analytics.log_visit(_gptbot(), "/a")
        after = datetime.now(timezone.utc)
        visit = analytics.get_visits()[0]
        assert before <= visit.timestamp <= after


class TestGetSummary:
    def test_empty_summary(self) -> None:
        analytics = CrawlerAnalytics()
        summary = analytics.get_summary()
        assert summary.total_visits == 0
        assert summary.visits_by_crawler == {}
        assert summary.first_visit is None

    def test_aggregates_by_crawler_and_path(self) -> None:
        analytics = CrawlerAnalytics()
        analytics.log_visit(_gptbot(), "/a")
        analytics.log_visit(_gptbot(), "/a")
        analytics.log_visit(_claudebot(), "/b")
        summary = analytics.get_summary()
        assert summary.total_visits == 3
        assert summary.visits_by_crawler["GPTBot"] == 2
        assert summary.visits_by_crawler["ClaudeBot"] == 1
        assert summary.visits_by_path["/a"] == 2

    def test_first_and_last_visit(self) -> None:
        analytics = CrawlerAnalytics()
        t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 6, 1, tzinfo=timezone.utc)
        analytics.log_visit(_gptbot(), "/a", timestamp=t2)
        analytics.log_visit(_gptbot(), "/b", timestamp=t1)
        summary = analytics.get_summary()
        assert summary.first_visit == t1
        assert summary.last_visit == t2


class TestCustomStore:
    def test_custom_store_receives_visits(self) -> None:
        class ListStore:
            def __init__(self) -> None:
                self.visits: list[CrawlerVisit] = []

            def add(self, visit: CrawlerVisit) -> None:
                self.visits.append(visit)

            def query(self, since=None, crawler_name=None) -> list[CrawlerVisit]:
                return list(self.visits)

        store = ListStore()
        assert isinstance(store, AnalyticsStore)
        analytics = CrawlerAnalytics(store=store)
        analytics.log_visit(_gptbot(), "/custom")
        assert len(store.visits) == 1

    def test_in_memory_store_is_analytics_store(self) -> None:
        assert isinstance(InMemoryAnalyticsStore(), AnalyticsStore)
