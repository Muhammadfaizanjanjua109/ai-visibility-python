"""Tests for ai_visibility.middleware.flask."""

from __future__ import annotations

from typing import Any

from flask import Flask

from ai_visibility.middleware.flask import AIVisibility


def _make_app(html: str, **kwargs: Any) -> Flask:
    app = Flask(__name__)
    AIVisibility(app, **kwargs)

    @app.route("/")
    def index() -> str:
        return html

    @app.route("/api")
    def api() -> dict:
        return {"a": 1}

    return app


class TestAIVisibilityFlask:
    def test_passthrough_for_regular_browser(self) -> None:
        app = _make_app("<html><head><script>x</script></head><body>hi</body></html>")
        client = app.test_client()
        resp = client.get("/", headers={"User-Agent": "Mozilla/5.0 Chrome/120"})
        assert "<script>x</script>" in resp.get_data(as_text=True)

    def test_optimizes_html_for_crawler(self) -> None:
        app = _make_app("<html><head><script>x</script></head><body>hi</body></html>")
        client = app.test_client()
        resp = client.get("/", headers={"User-Agent": "GPTBot/1.0"})
        body = resp.get_data(as_text=True)
        assert "<script>x</script>" not in body
        assert "hi" in body

    def test_logs_visit_for_crawler(self) -> None:
        app = _make_app("<html><body>hi</body></html>")
        client = app.test_client()
        client.get("/", headers={"User-Agent": "ClaudeBot/1.0"})
        extension = app.extensions["ai_visibility"]
        visits = extension.core.analytics.get_visits()
        assert len(visits) == 1
        assert visits[0].path == "/"

    def test_non_html_response_untouched(self) -> None:
        app = _make_app("ignored")
        client = app.test_client()
        resp = client.get("/api", headers={"User-Agent": "GPTBot/1.0"})
        assert resp.get_json() == {"a": 1}

    def test_optimize_disabled(self) -> None:
        app = _make_app(
            "<html><head><script>x</script></head><body>hi</body></html>", optimize=False
        )
        client = app.test_client()
        resp = client.get("/", headers={"User-Agent": "GPTBot/1.0"})
        assert "<script>x</script>" in resp.get_data(as_text=True)
