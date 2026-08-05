# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-06

### Added

- Initial release of the Python port of [`ai-visibility`](https://www.npmjs.com/package/ai-visibility).
- `ai_visibility.detector`: AI crawler detection via User-Agent matching (`detect_crawler`, `is_ai_crawler`).
- `ai_visibility.crawlers`: shared crawler registry loader (`get_all_crawlers`, `get_crawler_by_name`, `get_crawlers_by_category`), backed by the same `crawlers.json` source of truth as the npm package.
- `ai_visibility.optimizer`: stdlib-only HTML optimizer (`optimize_html`, `inject_schemas`) that strips scripts/styles/tracking while preserving JSON-LD, meta tags, and semantic structure.
- `ai_visibility.schema`: JSON-LD structured data builders for Article, Product, FAQ, HowTo, Organization, LocalBusiness, Breadcrumb, Video, Event, and WebSite, plus `render_jsonld`.
- `ai_visibility.generators`: `generate_llms_txt`, `generate_llms_full_txt`, `generate_ai_txt`, `generate_robots_txt` (with per-crawler-category blocking).
- `ai_visibility.scoring`: multi-dimensional GEO/AI-visibility scoring (`score_page`) across structured data, semantic HTML, meta tags, heading hierarchy, accessibility, and llms.txt/ai.txt presence.
- `ai_visibility.analyzer`: human-readable AI-readability report (`analyze_content`) built on top of scoring.
- `ai_visibility.analytics`: crawler visit logging and aggregation (`CrawlerAnalytics`, `InMemoryAnalyticsStore`, pluggable `AnalyticsStore` protocol).
- `ai_visibility.middleware`: framework adapters for Django, Flask, and FastAPI/Starlette, sharing detection/optimization/analytics logic via `AIVisibilityCore`.
- `ai_visibility.cli`: `ai-visibility audit <url>`, `ai-visibility crawlers`, `ai-visibility generate llms-txt`, `ai-visibility generate robots-txt`.
- Zero required dependencies for the core library; optional extras for `django`, `flask`, `fastapi`, and `cli`.
- Full type annotations, `py.typed` marker, and 100% test coverage on all core modules.
