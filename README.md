# ai-visibility (Python)

**Make your website optimally visible to AI crawlers, LLM search engines, and generative AI.**

The Python port of [`ai-visibility`](https://www.npmjs.com/package/ai-visibility) for Django, Flask, and FastAPI — GEO (Generative Engine Optimization) and AEO (Answer Engine Optimization) tooling from [CrawlPod](https://crawlpod.com), with **zero required dependencies**.

[![PyPI version](https://img.shields.io/pypi/v/ai-visibility.svg)](https://pypi.org/project/ai-visibility/)
[![Downloads](https://img.shields.io/pypi/dm/ai-visibility.svg)](https://pypi.org/project/ai-visibility/)
[![Python versions](https://img.shields.io/pypi/pyversions/ai-visibility.svg)](https://pypi.org/project/ai-visibility/)
[![License: MIT](https://img.shields.io/pypi/l/ai-visibility.svg)](https://github.com/Muhammadfaizanjanjua109/ai-visibility-python/blob/main/LICENSE)

---

## The problem

When someone asks ChatGPT, Perplexity, Google AI Overview, or Claude *"best shoes in Islamabad"* or *"top CRM tools for startups"*, the AI picks 2–3 sources to cite. Everyone else is invisible.

How does the AI decide? It crawls the web with bots like **GPTBot**, **ClaudeBot**, **PerplexityBot**, and **Google-Extended** — and the sites that serve clean, structured, AI-readable content get cited. Sites that block these crawlers, serve JavaScript-heavy pages, or lack structured data get skipped entirely.

**ai-visibility** solves this. One package. Zero dependencies. Your Django, Flask, or FastAPI app becomes fully optimized for AI crawlers — automatically.

## Why ai-visibility?

- **AI search is replacing traditional search.** Users are asking AI assistants instead of typing into Google. If your site isn't optimized for AI crawlers, you're losing traffic you'll never see in analytics.
- **SEO alone is not enough anymore.** GEO (Generative Engine Optimization) and AEO (Answer Engine Optimization) are the new disciplines. ai-visibility is purpose-built for them.
- **Zero config, zero overhead.** The middleware detects AI crawlers by User-Agent and only activates for them. Regular visitors get zero performance impact.
- **Framework support built in.** Django, Flask, FastAPI — pick your stack. Or use the core library framework-agnostic.
- **Shared crawler registry.** The same verified crawler database powers the [npm package](https://www.npmjs.com/package/ai-visibility), the [CrawlPod WordPress plugin](https://crawlpod.com), and this Python package — one source of truth across ecosystems.

## What's included

| Capability | Module | Description |
| --- | --- | --- |
| AI crawler detection | `ai_visibility.detector` | Identify GPTBot, ClaudeBot, PerplexityBot, Amazonbot, Google-Extended, and 15+ AI crawlers by User-Agent |
| Verified crawler registry | `ai_visibility.crawlers` | Shared with the npm package — names, companies, categories, verification URLs, last-checked dates |
| HTML optimization | `ai_visibility.optimizer` | Strip scripts, styles, tracking pixels, and ads — serve clean semantic HTML to AI crawlers while keeping JSON-LD and structured data intact |
| JSON-LD schema builders | `ai_visibility.schema` | Article, Product, FAQ, HowTo, Organization, LocalBusiness, Breadcrumb, Video, Event, WebSite — all Google/schema.org compliant |
| Content generators | `ai_visibility.generators` | Generate `llms.txt`, `llms-full.txt`, `ai.txt`, and AI-aware `robots.txt` files that tell crawlers exactly what to index |
| GEO scoring | `ai_visibility.scoring` | Multi-dimensional AI-visibility score across 7 dimensions: answer front-loading, E-E-A-T signals, heading structure, schema coverage, fact density, snippability, crawler accessibility |
| Content analyzer | `ai_visibility.analyzer` | Human-readable analysis with specific fix suggestions — "add FAQ schema", "front-load your answer", "missing author markup" |
| Crawler analytics | `ai_visibility.analytics` | Track which AI crawlers visit which pages, how often, and what they see — with pluggable storage backends |
| Framework middleware | `ai_visibility.middleware` | Drop-in middleware for Django, Flask, and FastAPI — one line to activate |
| CLI | `ai_visibility.cli` | `ai-visibility audit <url>`, `ai-visibility crawlers`, `ai-visibility generate` — audit any site from the command line |

## Installation

```bash
pip install ai-visibility               # core library, zero dependencies
pip install ai-visibility[django]       # + Django middleware
pip install ai-visibility[flask]        # + Flask extension
pip install ai-visibility[fastapi]      # + FastAPI/Starlette middleware
pip install ai-visibility[cli]          # + `ai-visibility` CLI
pip install ai-visibility[all]          # everything
```

## Quick start

### Django

```python
# settings.py
MIDDLEWARE = [
    "ai_visibility.middleware.django.AIVisibilityMiddleware",
    ...
]

AI_VISIBILITY = {
    "optimize": True,
    "inject_schemas": True,
    "schemas": [],
    "log_visits": True,
}
```

### Flask

```python
from flask import Flask
from ai_visibility.middleware.flask import AIVisibility

app = Flask(__name__)
ai_vis = AIVisibility(app, optimize=True, inject_schemas=True)
```

### FastAPI

```python
from fastapi import FastAPI
from ai_visibility.middleware.fastapi import AIVisibilityMiddleware

app = FastAPI()
app.add_middleware(AIVisibilityMiddleware, optimize=True, inject_schemas=True)
```

Every middleware detects AI crawlers first and is a no-op for regular visitors — zero overhead on normal traffic.

### Core library (framework-agnostic)

```python
from ai_visibility import (
    detect_crawler,
    optimize_html,
    article_schema,
    render_jsonld,
    generate_llms_txt,
    score_page,
    LlmsTxtConfig,
)

# Detect AI crawlers
crawler = detect_crawler(request.headers.get("User-Agent"))
if crawler:
    print(f"{crawler.name} ({crawler.company}) is visiting — category: {crawler.category.value}")

# Optimize HTML for AI consumption
clean_html = optimize_html(page_html)

# Build structured data
schema = article_schema(headline="How AI Crawlers Work", author_name="Jane Doe")
jsonld_tag = render_jsonld(schema)

# Generate llms.txt
llms_txt = generate_llms_txt(LlmsTxtConfig(title="Acme", summary="Acme makes widgets."))

# Score your page's AI visibility
result = score_page(page_html, has_llms_txt=True)
print(result.overall_score, result.dimension_scores)
```

## CLI

Audit any website's AI visibility from the command line:

```bash
pip install ai-visibility[cli]

# Audit a URL — get a full AI-visibility report with scores and fix suggestions
ai-visibility audit https://example.com

# List all known AI crawlers with their companies and categories
ai-visibility crawlers

# Generate llms.txt for your site
ai-visibility generate llms-txt --title "Acme" --description "Acme makes widgets." --url "https://acme.com"

# Generate AI-aware robots.txt
ai-visibility generate robots-txt
```

## AI crawlers supported

ai-visibility detects and optimizes for all major AI crawlers:

| Crawler | Company | Category |
| --- | --- | --- |
| GPTBot | OpenAI | AI Search / Training |
| OAI-SearchBot | OpenAI | AI Search |
| ChatGPT-User | OpenAI | AI Search |
| ClaudeBot | Anthropic | AI Training |
| Claude-SearchBot | Anthropic | AI Search |
| PerplexityBot | Perplexity | AI Search |
| Google-Extended | Google | AI Training |
| Googlebot (AI Overviews) | Google | Search + AI |
| Amazonbot | Amazon | AI Search |
| Amzn-SearchBot | Amazon | AI Search |
| Bytespider | ByteDance | AI Training |
| Meta-ExternalAgent | Meta | AI Training |
| Applebot-Extended | Apple | AI Features |
| Cohere-ai | Cohere | AI Training |
| ...and more | | |

The full registry is verified against each vendor's official documentation and updated with every release. See `ai-visibility crawlers` for the complete list.

## GEO scoring dimensions

The `score_page()` function evaluates your content across 7 weighted dimensions that determine how well AI systems can understand, extract, and cite your content:

| Dimension | Weight | What it measures |
| --- | --- | --- |
| Answer front-loading | 20% | Is the answer in the first paragraph? AI models prefer content that leads with the answer. |
| E-E-A-T signals | 20% | Author markup, organization schema, credentials — signals that build trust for AI citation. |
| Heading structure | 15% | Clean H1→H2→H3 hierarchy that AI can parse into a table of contents. |
| Schema coverage | 15% | JSON-LD structured data — Article, FAQ, HowTo, Product, etc. |
| Fact density | 10% | Numbers, dates, statistics, named entities — concrete facts AI can extract and cite. |
| Snippability | 10% | Short, quotable paragraphs that AI can directly use as answers. |
| Crawler accessibility | 10% | Can AI crawlers actually reach and parse your content? Blocks = score 0. |

## How it works

```
Regular visitor → Normal response (zero overhead)

AI crawler detected →
  1. Strip JavaScript, CSS, tracking, ads
  2. Keep semantic HTML, JSON-LD, structured data
  3. Inject any configured schemas
  4. Serve clean, AI-optimized response
  5. Log the visit for analytics
```

## Part of the CrawlPod ecosystem

**ai-visibility** is the Python package in the [CrawlPod](https://crawlpod.com) product family — a complete AI visibility toolkit spanning multiple platforms:

| Product | Platform | Status |
| --- | --- | --- |
| [ai-visibility (npm)](https://www.npmjs.com/package/ai-visibility) | Node.js / Next.js / React / Vue / Nuxt | ✅ Live on npm |
| **ai-visibility (Python)** | Django / Flask / FastAPI | ✅ Live on PyPI |
| [CrawlPod WordPress Plugin](https://crawlpod.com) | WordPress | ✅ Built — under review |
| CrawlPod Pro | WordPress (premium) | ✅ Built |
| CrawlPod Shopify App | Shopify | 🔜 Coming soon |
| [CrawlPod Scanner](https://crawlpod.com/scan) | Web (free) | ✅ Live |

All products share the same verified crawler registry and scoring weights — one source of truth, consistent behavior across every platform.

## Documentation

Full documentation, guides, and API reference:

- **Python docs:** [crawlpod.com/docs/python](https://crawlpod.com/docs/python)
- **Getting started guide:** [crawlpod.com/docs](https://crawlpod.com/docs)
- **Free AI-visibility scanner:** [crawlpod.com/scan](https://crawlpod.com/scan)
- **npm package docs:** [crawlpod.com/docs/npm](https://crawlpod.com/docs/npm)

## Vendored data

Two files are copied verbatim from the published npm package rather than
reimplemented, so this package doesn't silently drift from the JS/TypeScript
version's behavior:

| Vendored file | Source in the npm package | Consumed by |
| --- | --- | --- |
| `src/ai_visibility/crawlers.json` | `dist/crawlers.json` | `ai_visibility.crawlers` (crawler registry: names, categories, verification status) |
| `src/ai_visibility/scoring_weights.json` | `dist/scoring-weights.json` | `ai_visibility.scoring_weights` (the 7 GEO scoring dimensions and their default weights) |

Both were vendored from `ai-visibility@0.5.0` on npm (fetched via
`unpkg.com/ai-visibility@<version>/dist/...`, since the npm package ships
these as build artifacts rather than checking them into `src/`). The
`answer_front_loading` / `eeat_signals` / `heading_structure` /
`schema_coverage` / `fact_density` / `snippability` / `crawler_accessibility`
dimension keys, labels, and weights in `scoring_weights.json` are the exact
values published there — the Python code in `ai_visibility.scoring` that
*computes* each dimension's score from HTML is an original implementation
written to match each dimension's published description, since the npm
package's own docs state the rubric is a heuristic with no published exact
formulas.

### Re-verification checklist (run before each release)

- [ ] Check the current npm version: `npm view ai-visibility version`
- [ ] Fetch the latest registry: `https://unpkg.com/ai-visibility@<version>/dist/crawlers.json` and diff it against `src/ai_visibility/crawlers.json`
- [ ] Fetch the latest weights: `https://unpkg.com/ai-visibility@<version>/dist/scoring-weights.json` and diff it against `src/ai_visibility/scoring_weights.json`
- [ ] If either file changed, update the vendored copy (and `ai_visibility.crawlers` / `ai_visibility.scoring_weights` loader logic if the schema itself changed, e.g. new fields or renamed keys)
- [ ] Re-run the full test suite — `tests/test_detector.py` and `tests/test_scoring_weights.py` assert against the vendored data and will fail loudly on an unhandled schema change
- [ ] Note the synced npm version in `CHANGELOG.md`

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/Muhammadfaizanjanjua109/ai-visibility-python).

```bash
# Clone and set up dev environment
git clone https://github.com/Muhammadfaizanjanjua109/ai-visibility-python.git
cd ai-visibility-python
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/ai_visibility

# Linting
ruff check src/ tests/
```

## Links

- **CrawlPod (home):** [crawlpod.com](https://crawlpod.com)
- **Free scanner:** [crawlpod.com/scan](https://crawlpod.com/scan)
- **Documentation:** [crawlpod.com/docs/python](https://crawlpod.com/docs/python)
- **npm package (Node.js/Next.js):** [npmjs.com/package/ai-visibility](https://www.npmjs.com/package/ai-visibility)
- **Source:** [github.com/Muhammadfaizanjanjua109/ai-visibility-python](https://github.com/Muhammadfaizanjanjua109/ai-visibility-python)
- **Issues:** [github.com/Muhammadfaizanjanjua109/ai-visibility-python/issues](https://github.com/Muhammadfaizanjanjua109/ai-visibility-python/issues)

## License

MIT © Muhammad Faizan
