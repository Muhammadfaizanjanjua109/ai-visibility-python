"""AI crawler visit logging and aggregation."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from ai_visibility.types import AnalyticsStore, AnalyticsSummary, CrawlerInfo, CrawlerVisit


class InMemoryAnalyticsStore:
    """Default, non-persistent :class:`~ai_visibility.types.AnalyticsStore`.

    Implement the same interface (``add``/``query``) against SQLite, Redis,
    or any database to persist visits across process restarts.
    """

    def __init__(self) -> None:
        self._visits: list[CrawlerVisit] = []

    def add(self, visit: CrawlerVisit) -> None:
        """Append a visit to the in-memory list."""
        self._visits.append(visit)

    def query(
        self,
        since: Optional[datetime] = None,
        crawler_name: Optional[str] = None,
    ) -> list[CrawlerVisit]:
        """Return stored visits matching the given filters."""
        results = self._visits
        if since is not None:
            results = [v for v in results if v.timestamp >= since]
        if crawler_name is not None:
            lowered = crawler_name.lower()
            results = [v for v in results if v.crawler_name.lower() == lowered]
        return list(results)


class CrawlerAnalytics:
    """Logs and summarizes AI crawler visits against a pluggable store."""

    def __init__(self, store: Optional[AnalyticsStore] = None) -> None:
        """Create an analytics tracker.

        Args:
            store: A storage backend implementing
                :class:`~ai_visibility.types.AnalyticsStore`. Defaults to
                a non-persistent :class:`InMemoryAnalyticsStore`.
        """
        self.store: AnalyticsStore = store or InMemoryAnalyticsStore()

    def log_visit(
        self,
        crawler: CrawlerInfo,
        path: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a single crawler visit.

        Args:
            crawler: The detected crawler, e.g. from
                :func:`ai_visibility.detector.detect_crawler`.
            path: The request path that was visited.
            timestamp: When the visit occurred. Defaults to the current
                UTC time.
        """
        visit = CrawlerVisit(
            crawler_name=crawler.name,
            path=path,
            timestamp=timestamp or datetime.now(timezone.utc),
            category=crawler.category,
        )
        self.store.add(visit)

    def get_visits(
        self,
        since: Optional[datetime] = None,
        crawler_name: Optional[str] = None,
    ) -> list[CrawlerVisit]:
        """Return logged visits, optionally filtered.

        Args:
            since: Only return visits at or after this time.
            crawler_name: Only return visits from this crawler (exact,
                case-insensitive match).

        Returns:
            Matching :class:`~ai_visibility.types.CrawlerVisit` records.
        """
        return self.store.query(since=since, crawler_name=crawler_name)

    def get_summary(self) -> AnalyticsSummary:
        """Aggregate all logged visits by crawler, by path, and over time.

        Returns:
            An :class:`~ai_visibility.types.AnalyticsSummary`.
        """
        visits = self.store.query()
        if not visits:
            return AnalyticsSummary(total_visits=0, visits_by_crawler={}, visits_by_path={})

        timestamps = [visit.timestamp for visit in visits]
        return AnalyticsSummary(
            total_visits=len(visits),
            visits_by_crawler=dict(Counter(visit.crawler_name for visit in visits)),
            visits_by_path=dict(Counter(visit.path for visit in visits)),
            first_visit=min(timestamps),
            last_visit=max(timestamps),
        )
