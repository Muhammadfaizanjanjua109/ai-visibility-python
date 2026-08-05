"""Tests for ai_visibility.cli."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
from click.testing import CliRunner

from ai_visibility.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCrawlersCommand:
    def test_lists_known_crawlers(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["crawlers"])
        assert result.exit_code == 0
        assert "GPTBot" in result.output
        assert "OpenAI" in result.output


class TestGenerateLlmsTxt:
    def test_basic(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["generate", "llms-txt", "--title", "Acme"])
        assert result.exit_code == 0
        assert result.output.startswith("# Acme")

    def test_with_description_and_url(self, runner: CliRunner) -> None:
        result = runner.invoke(
            main,
            [
                "generate",
                "llms-txt",
                "--title",
                "Acme",
                "--description",
                "Acme makes widgets.",
                "--url",
                "https://acme.com",
            ],
        )
        assert result.exit_code == 0
        assert "> Acme makes widgets." in result.output
        assert "https://acme.com" in result.output

    def test_requires_title(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["generate", "llms-txt"])
        assert result.exit_code != 0


class TestGenerateRobotsTxt:
    def test_basic(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["generate", "robots-txt"])
        assert result.exit_code == 0
        assert "User-agent: *" in result.output


_GOOD_HTML = (
    "<html><head><title>Great Page About Widgets and More</title>"
    '<meta name="description" content="A great great great great great great great '
    'great great great page about widgets and how they work.">'
    '<meta property="og:title" content="Great Page">'
    '<meta property="og:description" content="A great page.">'
    '<meta property="og:image" content="https://acme.com/img.png">'
    '<script type="application/ld+json">'
    '{"@context": "https://schema.org", "@type": "Article", "headline": "x"}</script>'
    "</head><body><main><article><h1>Great Page</h1><h2>Section</h2>"
    "<p>" + ("Lots of great widget content here. " * 30) + "</p>"
    "</article></main></body></html>"
)


class TestAuditCommand:
    def test_audits_url_successfully(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_get(url, timeout=None, follow_redirects=None, headers=None):
            response = MagicMock()
            if url.endswith("/llms.txt") or url.endswith("/ai.txt"):
                response.status_code = 404
                return response
            response.status_code = 200
            response.text = _GOOD_HTML
            return response

        monkeypatch.setattr(httpx, "get", fake_get)

        result = runner.invoke(main, ["audit", "https://acme.com"])
        assert "AI-Visibility Report" in result.output
        assert "Overall score" in result.output

    def test_audit_fetch_failure_exits_nonzero(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_get(*args, **kwargs):
            raise httpx.ConnectError("boom")

        monkeypatch.setattr(httpx, "get", fake_get)
        result = runner.invoke(main, ["audit", "https://doesnotexist.invalid"])
        assert result.exit_code != 0

    def test_audit_critical_findings_exit_nonzero(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_get(url, timeout=None, follow_redirects=None, headers=None):
            response = MagicMock()
            if url.endswith("/llms.txt") or url.endswith("/ai.txt"):
                response.status_code = 404
                return response
            response.status_code = 200
            response.text = "<html><body><div>bare page</div></body></html>"
            return response

        monkeypatch.setattr(httpx, "get", fake_get)
        result = runner.invoke(main, ["audit", "https://acme.com"])
        assert result.exit_code == 1
        assert "CRITICAL" in result.output
