"""Tests for ai_visibility.middleware.django."""

from __future__ import annotations

from django.conf import settings

if not settings.configured:
    settings.configure(
        AI_VISIBILITY={"optimize": True, "inject_schemas": False, "log_visits": True},
        ALLOWED_HOSTS=["testserver"],
        USE_TZ=True,
    )

from django.http import HttpResponse  # noqa: E402
from django.test import RequestFactory  # noqa: E402

from ai_visibility.middleware.django import AIVisibilityMiddleware  # noqa: E402


def _make_get_response(body: str, content_type: str = "text/html"):
    def get_response(request):
        return HttpResponse(body, content_type=content_type)

    return get_response


class TestAIVisibilityMiddlewareDjango:
    def test_passthrough_for_regular_browser(self) -> None:
        html = "<html><head><script>x</script></head><body>hi</body></html>"
        middleware = AIVisibilityMiddleware(_make_get_response(html))
        request = RequestFactory().get("/", HTTP_USER_AGENT="Mozilla/5.0 Chrome/120")
        response = middleware(request)
        assert "<script>x</script>" in response.content.decode()

    def test_optimizes_html_for_crawler(self) -> None:
        html = "<html><head><script>x</script></head><body>hi</body></html>"
        middleware = AIVisibilityMiddleware(_make_get_response(html))
        request = RequestFactory().get("/", HTTP_USER_AGENT="GPTBot/1.0")
        response = middleware(request)
        body = response.content.decode()
        assert "<script>x</script>" not in body
        assert "hi" in body

    def test_logs_visit_for_crawler(self) -> None:
        middleware = AIVisibilityMiddleware(_make_get_response("<html><body>hi</body></html>"))
        request = RequestFactory().get("/some-path", HTTP_USER_AGENT="ClaudeBot/1.0")
        middleware(request)
        visits = middleware.core.analytics.get_visits()
        assert len(visits) == 1
        assert visits[0].path == "/some-path"
        assert visits[0].crawler_name == "ClaudeBot"

    def test_non_html_response_untouched(self) -> None:
        middleware = AIVisibilityMiddleware(
            _make_get_response('{"a": 1}', content_type="application/json")
        )
        request = RequestFactory().get("/api", HTTP_USER_AGENT="GPTBot/1.0")
        response = middleware(request)
        assert response.content.decode() == '{"a": 1}'
