"""Shared pytest fixtures for ai_visibility tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Sample Page</title>
    <meta name="description" content="A sample page for testing.">
    <meta property="og:title" content="Sample Page">
    <script>console.log('tracking');</script>
    <style>body { color: red; }</style>
    <script type="application/ld+json">{"@context": "https://schema.org", "@type": "Article"}</script>
</head>
<body>
    <nav><a href="/">Home</a></nav>
    <header><h1>Welcome</h1></header>
    <main>
        <article>
            <h2>Section</h2>
            <p onclick="track()">Some content here.</p>
            <img src="tracker.gif" width="1" height="1">
        </article>
    </main>
    <noscript>Enable JS</noscript>
    <footer>Copyright</footer>
</body>
</html>"""
