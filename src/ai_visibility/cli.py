"""Command-line interface for ai_visibility (requires the ``cli`` extra)."""

from __future__ import annotations

import sys
from urllib.parse import urljoin

import click
import httpx

from ai_visibility.analyzer import analyze_content
from ai_visibility.crawlers import get_all_crawlers
from ai_visibility.generators import generate_llms_txt as _generate_llms_txt
from ai_visibility.generators import generate_robots_txt as _generate_robots_txt
from ai_visibility.types import (
    LlmsTxtConfig,
    LlmsTxtLink,
    LlmsTxtSection,
    RobotsTxtConfig,
    Severity,
)

_SEVERITY_COLORS = {
    Severity.CRITICAL: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}


@click.group()
@click.version_option(package_name="ai-visibility")
def main() -> None:
    """ai-visibility: make your site optimally visible to AI crawlers."""


def _check_url_exists(base_url: str, path: str, timeout: float) -> bool | None:
    try:
        response = httpx.get(urljoin(base_url, path), timeout=timeout, follow_redirects=True)
        return bool(response.status_code == 200)
    except httpx.HTTPError:
        return None


@main.command()
@click.argument("url")
@click.option("--timeout", default=10.0, show_default=True, help="HTTP request timeout in seconds.")
def audit(url: str, timeout: float) -> None:
    """Fetch URL, score it for AI-visibility, and print a report."""
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "ai-visibility-cli/0.1"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        click.secho(f"Failed to fetch {url}: {exc}", fg="red", err=True)
        sys.exit(1)

    has_llms_txt = _check_url_exists(url, "/llms.txt", timeout)
    has_ai_txt = _check_url_exists(url, "/ai.txt", timeout)

    result = analyze_content(
        response.text, url=url, has_llms_txt=has_llms_txt, has_ai_txt=has_ai_txt
    )

    click.secho(f"\nAI-Visibility Report for {url}\n", bold=True)
    click.echo(result.summary)
    click.echo()
    click.secho(f"Overall score: {result.score.overall_score}/100", bold=True)
    for dimension, score in result.score.dimension_scores.items():
        click.echo(f"  {dimension.replace('_', ' ').title():<20} {score}/100")

    if result.recommendations:
        click.echo()
        click.secho("Findings:", bold=True)
        for finding in result.recommendations:
            click.secho(
                f"  [{finding.severity.value.upper()}] {finding.message}",
                fg=_SEVERITY_COLORS[finding.severity],
            )
            if finding.fix:
                click.echo(f"      Fix: {finding.fix}")

    has_critical = any(finding.severity == Severity.CRITICAL for finding in result.recommendations)
    sys.exit(1 if has_critical else 0)


@main.command(name="crawlers")
def list_crawlers() -> None:
    """List all known AI crawlers in the registry."""
    for crawler in get_all_crawlers():
        verified = "verified" if crawler.verified else "unverified"
        click.echo(
            f"{crawler.name:<20} {crawler.company:<15} {crawler.category.value:<10} ({verified})"
        )


@main.group()
def generate() -> None:
    """Generate llms.txt / robots.txt content to stdout."""


@generate.command(name="llms-txt")
@click.option("--title", required=True, help="Site or project title (used as the H1).")
@click.option(
    "--description", "summary", default=None, help="One-line summary (used as the blockquote)."
)
@click.option("--url", "site_url", default=None, help="Homepage URL, added as a link entry.")
def generate_llms_txt_command(title: str, summary: str | None, site_url: str | None) -> None:
    """Generate llms.txt content."""
    config = LlmsTxtConfig(title=title, summary=summary)
    if site_url:
        config.sections.append(
            LlmsTxtSection(name="Links", links=[LlmsTxtLink(title=title, url=site_url)])
        )
    click.echo(_generate_llms_txt(config), nl=False)


@generate.command(name="robots-txt")
def generate_robots_txt_command() -> None:
    """Generate an AI-aware robots.txt."""
    click.echo(_generate_robots_txt(RobotsTxtConfig()), nl=False)


if __name__ == "__main__":
    main()
