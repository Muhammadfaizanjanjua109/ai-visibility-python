"""Django middleware for AI crawler detection and optimization.

Usage::

    # settings.py
    MIDDLEWARE = [
        "ai_visibility.middleware.django.AIVisibilityMiddleware",
        ...
    ]

    AI_VISIBILITY = {
        "optimize": True,
        "inject_schemas": True,
        "schemas": [...],
        "analytics": True,
        "log_visits": True,
    }

Requires the ``ai-visibility[django]`` extra.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ai_visibility.analytics import CrawlerAnalytics
from ai_visibility.middleware.base import AIVisibilityCore, MiddlewareConfig, is_html_content_type

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

GetResponse = Callable[["HttpRequest"], "HttpResponse"]


def _build_config(raw: dict[str, Any]) -> tuple[MiddlewareConfig, bool]:
    analytics_enabled = bool(raw.get("analytics", True))
    config = MiddlewareConfig(
        optimize=bool(raw.get("optimize", True)),
        inject_schemas=bool(raw.get("inject_schemas", False)),
        schemas=list(raw.get("schemas", [])),
        log_visits=bool(raw.get("log_visits", True)) and analytics_enabled,
        on_detect=raw.get("on_detect"),
        optimize_options=raw.get("optimize_options"),
    )
    return config, analytics_enabled


class AIVisibilityMiddleware:
    """Django middleware that optimizes responses served to AI crawlers.

    Reads its configuration from the ``AI_VISIBILITY`` dict in Django
    settings. Non-crawler requests pass through untouched.
    """

    def __init__(self, get_response: GetResponse) -> None:
        """Wire up the middleware using Django's ``AI_VISIBILITY`` setting.

        Args:
            get_response: The next middleware/view callable in the chain,
                supplied by Django.
        """
        self.get_response = get_response

        from django.conf import settings

        raw_config: dict[str, Any] = getattr(settings, "AI_VISIBILITY", {})
        config, _ = _build_config(raw_config)
        self.core = AIVisibilityCore(config=config, analytics=CrawlerAnalytics())

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process a request/response pair, optimizing HTML for crawlers.

        Args:
            request: The incoming Django request.

        Returns:
            The (possibly optimized) Django response.
        """
        response = self.get_response(request)

        user_agent = request.META.get("HTTP_USER_AGENT", "")
        crawler = self.core.handle_request(user_agent, request.path)
        if crawler is None:
            return response

        content_type = response.get("Content-Type", "")
        if not is_html_content_type(content_type) or not hasattr(response, "content"):
            return response

        charset = getattr(response, "charset", None) or "utf-8"
        html = response.content.decode(charset)
        processed = self.core.process_html(html)
        response.content = processed.encode(charset)
        if response.has_header("Content-Length"):
            response["Content-Length"] = str(len(response.content))

        return response
