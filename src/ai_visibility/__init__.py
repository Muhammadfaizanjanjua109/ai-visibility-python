"""ai_visibility: make your website optimally visible to AI crawlers and LLM search engines.

Covers GEO (Generative Engine Optimization) and AEO (Answer Engine
Optimization): AI crawler detection, HTML optimization, JSON-LD structured
data, llms.txt/ai.txt/robots.txt generation, GEO scoring, content analysis,
and crawler analytics — with zero required dependencies.

Framework middleware (Django, Flask, FastAPI) lives under
``ai_visibility.middleware`` and is not re-exported here, since each
requires an optional extra.
"""

from ai_visibility.analytics import CrawlerAnalytics, InMemoryAnalyticsStore
from ai_visibility.analyzer import analyze_content
from ai_visibility.crawlers import (
    get_all_crawlers,
    get_crawler_by_name,
    get_crawlers_by_category,
)
from ai_visibility.detector import detect_crawler, is_ai_crawler
from ai_visibility.generators import (
    generate_ai_txt,
    generate_llms_full_txt,
    generate_llms_txt,
    generate_robots_txt,
)
from ai_visibility.optimizer import inject_schemas, optimize_html
from ai_visibility.schema import (
    article_schema,
    breadcrumb_schema,
    event_schema,
    faq_schema,
    howto_schema,
    local_business_schema,
    organization_schema,
    product_schema,
    render_jsonld,
    video_schema,
    website_schema,
)
from ai_visibility.scoring import score_page
from ai_visibility.types import (
    AiTxtConfig,
    AnalysisResult,
    AnalyticsStore,
    AnalyticsSummary,
    CrawlerCategory,
    CrawlerInfo,
    CrawlerVisit,
    Finding,
    LlmsFullTxtConfig,
    LlmsFullTxtPage,
    LlmsTxtConfig,
    LlmsTxtLink,
    LlmsTxtSection,
    OptimizeOptions,
    RobotsRule,
    RobotsTxtConfig,
    ScoreResult,
    ScoringConfig,
    Severity,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # detector
    "detect_crawler",
    "is_ai_crawler",
    # crawlers
    "get_all_crawlers",
    "get_crawler_by_name",
    "get_crawlers_by_category",
    # optimizer
    "optimize_html",
    "inject_schemas",
    # schema
    "article_schema",
    "product_schema",
    "faq_schema",
    "howto_schema",
    "organization_schema",
    "local_business_schema",
    "breadcrumb_schema",
    "video_schema",
    "event_schema",
    "website_schema",
    "render_jsonld",
    # generators
    "generate_llms_txt",
    "generate_llms_full_txt",
    "generate_ai_txt",
    "generate_robots_txt",
    # scoring / analysis
    "score_page",
    "analyze_content",
    # analytics
    "CrawlerAnalytics",
    "InMemoryAnalyticsStore",
    # types
    "CrawlerCategory",
    "Severity",
    "CrawlerInfo",
    "OptimizeOptions",
    "LlmsTxtConfig",
    "LlmsTxtSection",
    "LlmsTxtLink",
    "LlmsFullTxtConfig",
    "LlmsFullTxtPage",
    "AiTxtConfig",
    "RobotsRule",
    "RobotsTxtConfig",
    "Finding",
    "ScoringConfig",
    "ScoreResult",
    "AnalysisResult",
    "CrawlerVisit",
    "AnalyticsSummary",
    "AnalyticsStore",
]
