"""Framework-agnostic request/response types and shared middleware logic.

Each framework adapter (Django, Flask, FastAPI) is a thin wrapper around
:class:`AIVisibilityCore` — it translates that framework's native
request/response objects into calls here, so the detection, optimization,
and analytics logic is written and tested exactly once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ai_visibility.analytics import CrawlerAnalytics
from ai_visibility.detector import detect_crawler
from ai_visibility.optimizer import inject_schemas, optimize_html
from ai_visibility.types import CrawlerInfo, OptimizeOptions

OnDetectCallback = Callable[[CrawlerInfo, str], None]


def is_html_content_type(content_type: Optional[str]) -> bool:
    """Return whether a ``Content-Type`` header value denotes HTML.

    Args:
        content_type: The raw ``Content-Type`` header value, if any.

    Returns:
        ``True`` if the media type is ``text/html`` (ignoring parameters
        like charset).
    """
    if not content_type:
        return False
    return content_type.split(";", 1)[0].strip().lower() == "text/html"


@dataclass
class MiddlewareConfig:
    """Shared configuration for all framework middleware adapters.

    Attributes:
        optimize: Serve an optimized (script/style/tracking-stripped) HTML
            snapshot to detected crawlers.
        inject_schemas: Inject ``schemas`` as JSON-LD into responses served
            to detected crawlers.
        schemas: JSON-LD schema dicts to inject when ``inject_schemas`` is set.
        log_visits: Log detected visits to ``analytics``.
        on_detect: Optional callback invoked with ``(crawler, path)``
            whenever a known crawler is detected, for custom side effects.
        optimize_options: Fine-grained control passed through to
            :func:`ai_visibility.optimizer.optimize_html`.
    """

    optimize: bool = True
    inject_schemas: bool = False
    schemas: list[dict[str, Any]] = field(default_factory=list)
    log_visits: bool = True
    on_detect: Optional[OnDetectCallback] = None
    optimize_options: Optional[OptimizeOptions] = None


class AIVisibilityCore:
    """Detection, optimization, and analytics logic shared by all adapters.

    This class never touches a framework's request/response objects
    directly — adapters extract a user agent and request path, hand them
    to :meth:`handle_request`, and pass any HTML body through
    :meth:`process_html` before returning it to a detected crawler.
    """

    def __init__(
        self,
        config: Optional[MiddlewareConfig] = None,
        analytics: Optional[CrawlerAnalytics] = None,
    ) -> None:
        """Create the shared middleware core.

        Args:
            config: Behavior configuration. Defaults to
                :class:`MiddlewareConfig`'s defaults.
            analytics: Analytics tracker to log visits to. Defaults to a
                fresh :class:`~ai_visibility.analytics.CrawlerAnalytics`
                with an in-memory store.
        """
        self.config = config or MiddlewareConfig()
        self.analytics = analytics or CrawlerAnalytics()

    def handle_request(self, user_agent: Optional[str], path: str) -> Optional[CrawlerInfo]:
        """Detect a crawler and run visit-logging side effects for a request.

        Args:
            user_agent: The request's ``User-Agent`` header value.
            path: The request path being visited.

        Returns:
            The detected :class:`~ai_visibility.types.CrawlerInfo`, or
            ``None`` if this isn't a known AI crawler — in which case the
            caller should treat the request as a normal pass-through with
            zero added overhead.
        """
        crawler = detect_crawler(user_agent)
        if crawler is None:
            return None

        if self.config.log_visits:
            self.analytics.log_visit(crawler, path)
        if self.config.on_detect is not None:
            self.config.on_detect(crawler, path)

        return crawler

    def process_html(self, html: str) -> str:
        """Apply the configured optimization/schema-injection to an HTML body.

        Args:
            html: The original response body.

        Returns:
            The processed HTML, ready to serve to a detected crawler.
        """
        cfg = self.config
        if cfg.optimize:
            options = cfg.optimize_options or OptimizeOptions()
            if cfg.inject_schemas and cfg.schemas:
                options = OptimizeOptions(
                    strip_scripts=options.strip_scripts,
                    strip_styles=options.strip_styles,
                    strip_noscript=options.strip_noscript,
                    strip_event_handlers=options.strip_event_handlers,
                    strip_tracking=options.strip_tracking,
                    inject_schemas=[*options.inject_schemas, *cfg.schemas],
                )
            return optimize_html(html, options)

        if cfg.inject_schemas and cfg.schemas:
            return inject_schemas(html, cfg.schemas)

        return html
