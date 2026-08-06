"""Flask extension for AI crawler detection and optimization.

Usage::

    from flask import Flask
    from ai_visibility.middleware.flask import AIVisibility

    app = Flask(__name__)
    ai_vis = AIVisibility(app, optimize=True, inject_schemas=True)

Requires the ``ai-visibility[flask]`` extra.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ai_visibility.analytics import CrawlerAnalytics
from ai_visibility.middleware.base import (
    AIVisibilityCore,
    MiddlewareConfig,
    OnDetectCallback,
    is_html_content_type,
)
from ai_visibility.types import OptimizeOptions

if TYPE_CHECKING:
    from flask import Flask, Response


class AIVisibility:
    """Flask extension that optimizes responses served to AI crawlers.

    Can be constructed with an app directly (``AIVisibility(app)``) or
    initialized later via :meth:`init_app`, following Flask's standard
    extension pattern.
    """

    def __init__(
        self,
        app: Flask | None = None,
        *,
        optimize: bool = True,
        inject_schemas: bool = False,
        schemas: list[dict[str, Any]] | None = None,
        log_visits: bool = True,
        on_detect: OnDetectCallback | None = None,
        optimize_options: OptimizeOptions | None = None,
        analytics: CrawlerAnalytics | None = None,
    ) -> None:
        """Create the extension.

        Args:
            app: A Flask app to attach to immediately, or ``None`` to call
                :meth:`init_app` later.
            optimize: Serve an optimized HTML snapshot to detected crawlers.
            inject_schemas: Inject ``schemas`` as JSON-LD for crawlers.
            schemas: JSON-LD schema dicts to inject.
            log_visits: Log detected crawler visits.
            on_detect: Callback invoked with ``(crawler, path)`` on detection.
            optimize_options: Fine-grained optimizer options.
            analytics: Analytics tracker to log visits to. Defaults to a
                fresh in-memory tracker.
        """
        self.core = AIVisibilityCore(
            config=MiddlewareConfig(
                optimize=optimize,
                inject_schemas=inject_schemas,
                schemas=schemas or [],
                log_visits=log_visits,
                on_detect=on_detect,
                optimize_options=optimize_options,
            ),
            analytics=analytics or CrawlerAnalytics(),
        )
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Attach this extension's ``after_request`` hook to a Flask app.

        Args:
            app: The Flask application instance.
        """
        app.extensions = getattr(app, "extensions", {})
        app.extensions["ai_visibility"] = self
        app.after_request(self._after_request)

    def _after_request(self, response: Response) -> Response:
        from flask import request

        crawler = self.core.handle_request(request.headers.get("User-Agent", ""), request.path)
        if crawler is None:
            return response

        if not is_html_content_type(response.content_type):
            return response

        html = response.get_data(as_text=True)
        processed = self.core.process_html(html)
        response.set_data(processed)
        return response
