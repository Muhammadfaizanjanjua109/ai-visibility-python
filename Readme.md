# ai-visibility (Python)

**Make your website optimally visible to AI crawlers, LLM search engines, and generative AI.**

The Python port of [`ai-visibility`](https://www.npmjs.com/package/ai-visibility) for Django, Flask, and FastAPI — GEO (Generative Engine Optimization) and AEO (Answer Engine Optimization) tooling from [CrawlPod](https://crawlpod.com), with **zero required dependencies**.

[![PyPI version](https://img.shields.io/pypi/v/ai-visibility.svg)](https://pypi.org/project/ai-visibility/)
[![Downloads](https://img.shields.io/pypi/dm/ai-visibility.svg)](https://pypi.org/project/ai-visibility/)
[![Python versions](https://img.shields.io/pypi/pyversions/ai-visibility.svg)](https://pypi.org/project/ai-visibility/)
[![License: MIT](https://img.shields.io/pypi/l/ai-visibility.svg)](https://github.com/Muhammadfaizanjanjua109/ai-visibility-python/blob/main/LICENSE)

---

## Why

AI crawlers (GPTBot, ClaudeBot, PerplexityBot, and more) and LLM-powered search engines increasingly decide whether your content gets cited, summarized, or recommended. `ai-visibility` detects those crawlers, serves them clean and structured content, and scores your pages against the signals that matter for AI visibility — all from a single, dependency-free Python package.

## What's included

| Capability | Module |
| --- | --- |
| AI crawler detection (User-Agent matching) | `ai_visibility.detector` |
| Verified crawler registry (shared with the npm package) | `ai_visibility.crawlers` |
| HTML optimization (strip scripts/styles/tracking, keep JSON-LD & semantics) | `ai_visibility.optimizer` |
| JSON-LD structured data builders (Article, Product, FAQ, HowTo, Organization, LocalBusiness, Breadcrumb, Video, Event, WebSite) | `ai_visibility.schema` |
| `llms.txt` / `llms-full.txt` / `ai.txt` / AI-aware `robots.txt` generators | `ai_visibility.generators` |
| Multi-dimensional GEO/AI-visibility scoring | `ai_visibility.scoring` |
| Human-readable content analysis & fix suggestions | `ai_visibility.analyzer` |
| AI crawler visit analytics (pluggable storage) | `ai_visibility.analytics` |
| Django / Flask / FastAPI middleware | `ai_visibility.middleware` |
| CLI (`ai-visibility audit`, `crawlers`, `generate`) | `ai_visibility.cli` |

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

Every middleware detects crawlers first and is a no-op for regular visitors — zero overhead on normal traffic.

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

crawler = detect_crawler(request.headers.get("User-Agent"))
if crawler:
    print(f"{crawler.name} ({crawler.company}) is visiting — category: {crawler.category.value}")

clean_html = optimize_html(page_html)

schema = article_schema(headline="How AI Crawlers Work", author_name="Jane Doe")
jsonld_tag = render_jsonld(schema)

llms_txt = generate_llms_txt(LlmsTxtConfig(title="Acme", summary="Acme makes widgets."))

result = score_page(page_html, has_llms_txt=True)
print(result.overall_score, result.dimension_scores)
```

## CLI

```bash
pip install ai-visibility[cli]

ai-visibility audit https://example.com
ai-visibility crawlers
ai-visibility generate llms-txt --title "Acme" --description "Acme makes widgets." --url "https://acme.com"
ai-visibility generate robots-txt
```

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

## Links

- npm package (Node.js/Next.js): <https://www.npmjs.com/package/ai-visibility>
- CrawlPod: <https://crawlpod.com>
- Documentation: <https://crawlpod.com/docs/python>
- Source: <https://github.com/Muhammadfaizanjanjua109/ai-visibility-python>

## License

MIT © Muhammad Faizan
