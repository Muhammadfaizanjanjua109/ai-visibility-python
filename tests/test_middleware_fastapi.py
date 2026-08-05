"""Tests for ai_visibility.middleware.fastapi."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.testclient import TestClient

from ai_visibility.middleware.fastapi import AIVisibilityMiddleware


def _make_app(html: str, **kwargs: Any) -> FastAPI:
    app = FastAPI()
    app.add_middleware(AIVisibilityMiddleware, **kwargs)

    @app.get("/")
    def index() -> HTMLResponse:
        return HTMLResponse(html)

    @app.get("/api")
    def api() -> JSONResponse:
        return JSONResponse({"a": 1})

    return app


class TestAIVisibilityFastAPI:
    def test_passthrough_for_regular_browser(self) -> None:
        app = _make_app("<html><head><script>x</script></head><body>hi</body></html>")
        client = TestClient(app)
        resp = client.get("/", headers={"User-Agent": "Mozilla/5.0 Chrome/120"})
        assert "<script>x</script>" in resp.text

    def test_optimizes_html_for_crawler(self) -> None:
        app = _make_app("<html><head><script>x</script></head><body>hi</body></html>")
        client = TestClient(app)
        resp = client.get("/", headers={"User-Agent": "GPTBot/1.0"})
        assert "<script>x</script>" not in resp.text
        assert "hi" in resp.text

    def test_non_html_response_untouched(self) -> None:
        app = _make_app("ignored")
        client = TestClient(app)
        resp = client.get("/api", headers={"User-Agent": "GPTBot/1.0"})
        assert resp.json() == {"a": 1}

    def test_optimize_disabled(self) -> None:
        app = _make_app(
            "<html><head><script>x</script></head><body>hi</body></html>", optimize=False
        )
        client = TestClient(app)
        resp = client.get("/", headers={"User-Agent": "GPTBot/1.0"})
        assert "<script>x</script>" in resp.text
