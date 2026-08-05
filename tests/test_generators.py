"""Tests for ai_visibility.generators."""

from __future__ import annotations

from ai_visibility.generators import (
    generate_ai_txt,
    generate_llms_full_txt,
    generate_llms_txt,
    generate_robots_txt,
)
from ai_visibility.types import (
    AiTxtConfig,
    CrawlerCategory,
    LlmsFullTxtConfig,
    LlmsFullTxtPage,
    LlmsTxtConfig,
    LlmsTxtLink,
    LlmsTxtSection,
    RobotsRule,
    RobotsTxtConfig,
)


class TestGenerateLlmsTxt:
    def test_title_only(self) -> None:
        result = generate_llms_txt(LlmsTxtConfig(title="Acme"))
        assert result.startswith("# Acme\n")

    def test_with_summary_and_sections(self) -> None:
        config = LlmsTxtConfig(
            title="Acme",
            summary="Acme makes widgets.",
            sections=[
                LlmsTxtSection(
                    name="Docs",
                    links=[
                        LlmsTxtLink(title="Getting Started", url="https://acme.com/start"),
                        LlmsTxtLink(
                            title="API",
                            url="https://acme.com/api",
                            description="Full API reference",
                        ),
                    ],
                ),
                LlmsTxtSection(
                    name="Optional", links=[LlmsTxtLink(title="Blog", url="https://acme.com/blog")]
                ),
            ],
        )
        result = generate_llms_txt(config)
        assert "> Acme makes widgets." in result
        assert "## Docs" in result
        assert "- [Getting Started](https://acme.com/start)" in result
        assert "- [API](https://acme.com/api): Full API reference" in result
        assert "## Optional" in result
        assert result.index("## Docs") < result.index("## Optional")

    def test_ends_with_single_newline(self) -> None:
        result = generate_llms_txt(LlmsTxtConfig(title="Acme"))
        assert result.endswith("\n")
        assert not result.endswith("\n\n")

    def test_with_details(self) -> None:
        result = generate_llms_txt(
            LlmsTxtConfig(title="Acme", details="Some extra free-form markdown.")
        )
        assert "Some extra free-form markdown." in result


class TestGenerateLlmsFullTxt:
    def test_inlines_page_content(self) -> None:
        config = LlmsFullTxtConfig(
            title="Acme",
            summary="Full docs",
            pages=[
                LlmsFullTxtPage(
                    title="Intro", url="https://acme.com/intro", content="Welcome to Acme."
                ),
                LlmsFullTxtPage(
                    title="API", url="https://acme.com/api", content="The API has one endpoint."
                ),
            ],
        )
        result = generate_llms_full_txt(config)
        assert "## Intro" in result
        assert "URL: https://acme.com/intro" in result
        assert "Welcome to Acme." in result
        assert "---" in result
        assert result.index("## Intro") < result.index("## API")

    def test_no_separator_for_single_page(self) -> None:
        config = LlmsFullTxtConfig(
            title="Acme",
            pages=[LlmsFullTxtPage(title="Intro", url="https://acme.com", content="Hi")],
        )
        result = generate_llms_full_txt(config)
        assert "---" not in result


class TestGenerateAiTxt:
    def test_allow_disallow(self) -> None:
        config = AiTxtConfig(allow=["/blog/"], disallow=["/private/"])
        result = generate_ai_txt(config)
        assert "User-agent: *" in result
        assert "Allow: /blog/" in result
        assert "Disallow: /private/" in result

    def test_contact_and_license(self) -> None:
        config = AiTxtConfig(contact="mailto:hi@acme.com", license="https://acme.com/license")
        result = generate_ai_txt(config)
        assert "Contact: mailto:hi@acme.com" in result
        assert "License: https://acme.com/license" in result


class TestGenerateRobotsTxt:
    def test_default_permissive(self) -> None:
        result = generate_robots_txt()
        assert "User-agent: *" in result
        assert "Allow: /" in result

    def test_default_deny(self) -> None:
        result = generate_robots_txt(RobotsTxtConfig(default_allow=False))
        assert "User-agent: *\nDisallow: /" in result

    def test_explicit_rule(self) -> None:
        config = RobotsTxtConfig(rules=[RobotsRule(user_agent="GPTBot", disallow=["/private/"])])
        result = generate_robots_txt(config)
        assert "User-agent: GPTBot" in result
        assert "Disallow: /private/" in result

    def test_block_training_bots(self) -> None:
        config = RobotsTxtConfig(block_training_bots=True)
        result = generate_robots_txt(config)
        assert "User-agent: GPTBot\nDisallow: /" in result
        assert "User-agent: ClaudeBot\nDisallow: /" in result
        # search-category bots should not be swept up
        assert "User-agent: PerplexityBot\nDisallow: /" not in result

    def test_block_categories(self) -> None:
        config = RobotsTxtConfig(block_categories=[CrawlerCategory.SEARCH])
        result = generate_robots_txt(config)
        assert "User-agent: PerplexityBot\nDisallow: /" in result

    def test_explicit_rule_not_duplicated_by_category_block(self) -> None:
        config = RobotsTxtConfig(
            rules=[RobotsRule(user_agent="GPTBot", allow=["/"])],
            block_training_bots=True,
        )
        result = generate_robots_txt(config)
        assert result.count("User-agent: GPTBot") == 1

    def test_sitemap_appended(self) -> None:
        config = RobotsTxtConfig(sitemap_urls=["https://acme.com/sitemap.xml"])
        result = generate_robots_txt(config)
        assert result.strip().endswith("Sitemap: https://acme.com/sitemap.xml")
