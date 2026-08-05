"""Shared dataclasses, enums, and protocols used across ai_visibility modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Protocol, runtime_checkable


class CrawlerCategory(str, Enum):
    """Why a known bot visits a site."""

    TRAINING = "training"
    SEARCH = "search"
    INDEXING = "indexing"


class Severity(str, Enum):
    """Severity level for a scoring/analysis finding."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class CrawlerInfo:
    """A known AI/search crawler from the shared registry.

    Attributes:
        name: Canonical bot name, e.g. ``"GPTBot"``.
        company: The organization operating the bot.
        user_agent_pattern: Lowercase substring matched case-insensitively
            against a request's ``User-Agent`` header.
        category: Why the bot crawls (training, search, indexing).
        verified: Whether the pattern was confirmed against the vendor's
            own current documentation.
        source_url: Vendor documentation URL, if any.
        last_checked: ISO date string of when the entry was last verified.
    """

    name: str
    company: str
    user_agent_pattern: str
    category: CrawlerCategory
    verified: bool = False
    source_url: Optional[str] = None
    last_checked: Optional[str] = None


@dataclass
class OptimizeOptions:
    """Options controlling :func:`ai_visibility.optimizer.optimize_html`.

    Attributes:
        strip_scripts: Remove ``<script>`` elements (JSON-LD is preserved).
        strip_styles: Remove ``<style>`` elements and ``style`` attributes.
        strip_noscript: Remove ``<noscript>`` elements.
        strip_event_handlers: Remove inline ``on*`` event-handler attributes.
        strip_tracking: Remove common tracking pixels / ad elements.
        inject_schemas: Extra JSON-LD schema dicts to inject into ``<head>``.
    """

    strip_scripts: bool = True
    strip_styles: bool = True
    strip_noscript: bool = True
    strip_event_handlers: bool = True
    strip_tracking: bool = True
    inject_schemas: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class LlmsTxtLink:
    """A single link entry within an ``llms.txt`` section."""

    title: str
    url: str
    description: Optional[str] = None


@dataclass
class LlmsTxtSection:
    """A named group of links in an ``llms.txt`` file, e.g. ``"Docs"``."""

    name: str
    links: list[LlmsTxtLink] = field(default_factory=list)


@dataclass
class LlmsTxtConfig:
    """Configuration for :func:`ai_visibility.generators.generate_llms_txt`.

    Mirrors the https://llmstxt.org spec: an H1 title, an optional
    blockquote summary, optional free-form markdown details, then any
    number of H2 sections of links. A section named ``"Optional"`` marks
    secondary links a consumer may skip when trimming context.
    """

    title: str
    summary: Optional[str] = None
    details: Optional[str] = None
    sections: list[LlmsTxtSection] = field(default_factory=list)


@dataclass
class LlmsFullTxtPage:
    """A single page's full content, inlined into ``llms-full.txt``."""

    title: str
    url: str
    content: str


@dataclass
class LlmsFullTxtConfig:
    """Configuration for :func:`ai_visibility.generators.generate_llms_full_txt`."""

    title: str
    summary: Optional[str] = None
    pages: list[LlmsFullTxtPage] = field(default_factory=list)


@dataclass
class AiTxtConfig:
    """Configuration for :func:`ai_visibility.generators.generate_ai_txt`."""

    allow: list[str] = field(default_factory=list)
    disallow: list[str] = field(default_factory=list)
    contact: Optional[str] = None
    license: Optional[str] = None


@dataclass
class RobotsRule:
    """A single per-crawler allow/disallow rule block."""

    user_agent: str
    allow: list[str] = field(default_factory=list)
    disallow: list[str] = field(default_factory=list)


@dataclass
class RobotsTxtConfig:
    """Configuration for :func:`ai_visibility.generators.generate_robots_txt`."""

    default_allow: bool = True
    rules: list[RobotsRule] = field(default_factory=list)
    sitemap_urls: list[str] = field(default_factory=list)
    block_training_bots: bool = False
    block_categories: list[CrawlerCategory] = field(default_factory=list)


@dataclass
class Finding:
    """A single actionable issue surfaced by scoring or analysis."""

    severity: Severity
    message: str
    fix: Optional[str] = None
    dimension: Optional[str] = None


@dataclass
class ScoringConfig:
    """Weights (0-1, should sum to 1.0) for each scoring dimension."""

    structured_data_weight: float = 0.25
    semantic_html_weight: float = 0.15
    meta_tags_weight: float = 0.15
    heading_hierarchy_weight: float = 0.15
    accessibility_weight: float = 0.15
    llms_txt_weight: float = 0.15


@dataclass
class ScoreResult:
    """Result of :func:`ai_visibility.scoring.score_page`."""

    overall_score: int
    dimension_scores: dict[str, int]
    findings: list[Finding] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Result of :func:`ai_visibility.analyzer.analyze_content`."""

    score: ScoreResult
    summary: str
    recommendations: list[Finding] = field(default_factory=list)


@dataclass
class CrawlerVisit:
    """A single logged crawler visit."""

    crawler_name: str
    path: str
    timestamp: datetime
    category: Optional[CrawlerCategory] = None


@dataclass
class AnalyticsSummary:
    """Aggregate view over logged crawler visits."""

    total_visits: int
    visits_by_crawler: dict[str, int]
    visits_by_path: dict[str, int]
    first_visit: Optional[datetime] = None
    last_visit: Optional[datetime] = None


@runtime_checkable
class AnalyticsStore(Protocol):
    """Storage backend contract for :class:`ai_visibility.analytics.CrawlerAnalytics`.

    Implement this against SQLite, Redis, or any database to persist visits
    instead of using the default in-memory store.
    """

    def add(self, visit: CrawlerVisit) -> None:
        """Persist a single crawler visit."""
        ...

    def query(
        self,
        since: Optional[datetime] = None,
        crawler_name: Optional[str] = None,
    ) -> list[CrawlerVisit]:
        """Return logged visits matching the given filters."""
        ...
