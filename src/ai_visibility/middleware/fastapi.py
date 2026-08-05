"""FastAPI/Starlette middleware for AI crawler detection and optimization.

Usage::

    from fastapi import FastAPI
    from ai_visibility.middleware.fastapi import AIVisibilityMiddleware

    app = FastAPI()
    app.add_middleware(AIVisibilityMiddleware, optimize=True, inject_schemas=True)

Requires the ``ai-visibility[fastapi]`` extra.
"""

from __future__ import annotations

from typing import Any, Optional, cast

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from ai_visibility.analytics import CrawlerAnalytics
from ai_visibility.middleware.base import (
    AIVisibilityCore,
    MiddlewareConfig,
    OnDetectCallback,
    is_html_content_type,
)
from ai_visibility.types import OptimizeOptions


def _chunk_to_bytes(chunk: str | bytes | memoryview[int], charset: str) -> bytes:
    if isinstance(chunk, bytes):
        return chunk
    if isinstance(chunk, memoryview):
        return bytes(chunk)
    return chunk.encode(charset)


class AIVisibilityMiddleware(BaseHTTPMiddleware):
    """Starlette/FastAPI middleware that optimizes responses for AI crawlers."""

    def __init__(
        self,
        app: Starlette,
        *,
        optimize: bool = True,
        inject_schemas: bool = False,
        schemas: Optional[list[dict[str, Any]]] = None,
        log_visits: bool = True,
        on_detect: Optional[OnDetectCallback] = None,
        optimize_options: Optional[OptimizeOptions] = None,
        analytics: Optional[CrawlerAnalytics] = None,
    ) -> None:
        """Create the middleware.

        Args:
            app: The ASGI application, supplied by Starlette/FastAPI.
            optimize: Serve an optimized HTML snapshot to detected crawlers.
            inject_schemas: Inject ``schemas`` as JSON-LD for crawlers.
            schemas: JSON-LD schema dicts to inject.
            log_visits: Log detected crawler visits.
            on_detect: Callback invoked with ``(crawler, path)`` on detection.
            optimize_options: Fine-grained optimizer options.
            analytics: Analytics tracker to log visits to. Defaults to a
                fresh in-memory tracker.
        """
        super().__init__(app)
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

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Detect a crawler and optimize the HTML response if appropriate.

        Args:
            request: The incoming Starlette request.
            call_next: Calls the next handler in the ASGI chain.

        Returns:
            The (possibly optimized) response.
        """
        response = await call_next(request)

        user_agent = request.headers.get("user-agent", "")
        crawler = self.core.handle_request(user_agent, request.url.path)
        if crawler is None:
            return response

        content_type = response.headers.get("content-type", "")
        if not is_html_content_type(content_type):
            return response

        streaming_response = cast(StreamingResponse, response)
        charset = response.charset or "utf-8"
        body_chunks = [
            _chunk_to_bytes(chunk, charset) async for chunk in streaming_response.body_iterator
        ]
        body = b"".join(body_chunks)
        processed = self.core.process_html(body.decode(charset))
        new_body = processed.encode(charset)

        headers = dict(response.headers)
        headers["content-length"] = str(len(new_body))

        return Response(
            content=new_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )
