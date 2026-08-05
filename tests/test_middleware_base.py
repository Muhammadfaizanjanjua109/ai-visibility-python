"""Tests for ai_visibility.middleware.base."""

from __future__ import annotations

from ai_visibility.middleware.base import AIVisibilityCore, MiddlewareConfig, is_html_content_type


class TestIsHtmlContentType:
    def test_true_for_html_with_charset(self) -> None:
        assert is_html_content_type("text/html; charset=utf-8") is True

    def test_false_for_json(self) -> None:
        assert is_html_content_type("application/json") is False

    def test_false_for_none(self) -> None:
        assert is_html_content_type(None) is False

    def test_false_for_empty_string(self) -> None:
        assert is_html_content_type("") is False


class TestAIVisibilityCoreHandleRequest:
    def test_returns_none_for_non_crawler(self) -> None:
        core = AIVisibilityCore()
        assert core.handle_request("Mozilla/5.0 Chrome/120", "/") is None

    def test_returns_crawler_info(self) -> None:
        core = AIVisibilityCore()
        crawler = core.handle_request("GPTBot/1.0", "/a")
        assert crawler is not None
        assert crawler.name == "GPTBot"

    def test_logs_visit_by_default(self) -> None:
        core = AIVisibilityCore()
        core.handle_request("GPTBot/1.0", "/a")
        assert len(core.analytics.get_visits()) == 1

    def test_log_visits_false_skips_logging(self) -> None:
        core = AIVisibilityCore(config=MiddlewareConfig(log_visits=False))
        core.handle_request("GPTBot/1.0", "/a")
        assert len(core.analytics.get_visits()) == 0

    def test_on_detect_callback_invoked_only_for_crawlers(self) -> None:
        seen = []
        core = AIVisibilityCore(
            config=MiddlewareConfig(on_detect=lambda c, p: seen.append((c.name, p)))
        )
        core.handle_request("Mozilla/5.0 Chrome/120", "/skip")
        core.handle_request("ClaudeBot/1.0", "/x")
        assert seen == [("ClaudeBot", "/x")]


class TestAIVisibilityCoreProcessHtml:
    def test_optimizes_by_default(self) -> None:
        core = AIVisibilityCore()
        result = core.process_html("<script>x</script><p>hi</p>")
        assert "<script>" not in result
        assert "hi" in result

    def test_noop_when_optimize_false(self) -> None:
        core = AIVisibilityCore(config=MiddlewareConfig(optimize=False))
        result = core.process_html("<script>x</script>")
        assert "<script>x</script>" in result

    def test_injects_schemas_without_optimize(self) -> None:
        core = AIVisibilityCore(
            config=MiddlewareConfig(
                optimize=False, inject_schemas=True, schemas=[{"@type": "Thing"}]
            )
        )
        result = core.process_html("<html><head></head><body>hi</body></html>")
        assert "application/ld+json" in result

    def test_injects_schemas_with_optimize(self) -> None:
        core = AIVisibilityCore(
            config=MiddlewareConfig(
                optimize=True, inject_schemas=True, schemas=[{"@type": "Thing"}]
            )
        )
        result = core.process_html("<html><head></head><body>hi</body></html>")
        assert "application/ld+json" in result
        assert "<html" in result
