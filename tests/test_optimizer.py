"""Tests for ai_visibility.optimizer."""

from __future__ import annotations

from ai_visibility.optimizer import optimize_html
from ai_visibility.types import OptimizeOptions


class TestOptimizeHtmlDefaults:
    def test_strips_script(self) -> None:
        html = "<html><head><script>alert(1)</script></head><body>hi</body></html>"
        result = optimize_html(html)
        assert "<script>" not in result
        assert "alert(1)" not in result

    def test_preserves_ld_json_script(self) -> None:
        html = (
            '<html><head><script type="application/ld+json">'
            '{"@type": "Article"}</script></head><body>hi</body></html>'
        )
        result = optimize_html(html)
        assert "application/ld+json" in result
        assert '"@type": "Article"' in result

    def test_strips_style_tag(self) -> None:
        html = "<html><head><style>body{color:red}</style></head><body>hi</body></html>"
        result = optimize_html(html)
        assert "<style>" not in result
        assert "color:red" not in result

    def test_strips_noscript(self) -> None:
        html = "<body><noscript>enable js</noscript><p>text</p></body>"
        result = optimize_html(html)
        assert "noscript" not in result
        assert "enable js" not in result
        assert "<p>text</p>" in result

    def test_strips_inline_event_handlers(self) -> None:
        html = '<button onclick="doThing()">Click</button>'
        result = optimize_html(html)
        assert "onclick" not in result
        assert "<button>Click</button>" in result

    def test_strips_style_attribute(self) -> None:
        html = '<div style="color:red">hi</div>'
        result = optimize_html(html)
        assert "style=" not in result

    def test_strips_tracking_pixel_img(self) -> None:
        html = '<img src="https://example.com/pixel.gif" width="1" height="1">'
        result = optimize_html(html)
        assert "<img" not in result

    def test_strips_ad_container(self) -> None:
        html = '<div class="ad-container"><p>Buy now</p></div><p>Real content</p>'
        result = optimize_html(html)
        assert "Buy now" not in result
        assert "Real content" in result

    def test_preserves_meta_tags(self) -> None:
        html = '<head><meta name="description" content="A page"></head>'
        result = optimize_html(html)
        assert 'name="description"' in result
        assert 'content="A page"' in result

    def test_preserves_og_tags(self) -> None:
        html = '<head><meta property="og:title" content="Hello"></head>'
        result = optimize_html(html)
        assert 'property="og:title"' in result

    def test_preserves_headings_and_landmarks(self) -> None:
        html = "<main><article><h1>Title</h1><h2>Sub</h2></article></main>"
        result = optimize_html(html)
        assert "<h1>Title</h1>" in result
        assert "<h2>Sub</h2>" in result
        assert "<main>" in result
        assert "<article>" in result

    def test_full_sample_html_smoke(self, sample_html: str) -> None:
        result = optimize_html(sample_html)
        assert "console.log" not in result
        assert "color: red" not in result
        assert "Enable JS" not in result
        assert "onclick" not in result
        assert "tracker.gif" not in result
        assert "application/ld+json" in result
        assert "<h1>Welcome</h1>" in result
        assert "Some content here." in result


class TestOptimizeHtmlOptionsOff:
    def test_keep_scripts_when_disabled(self) -> None:
        html = "<script>alert(1)</script>"
        result = optimize_html(html, OptimizeOptions(strip_scripts=False))
        assert "alert(1)" in result

    def test_keep_styles_when_disabled(self) -> None:
        html = "<style>body{color:red}</style>"
        result = optimize_html(html, OptimizeOptions(strip_styles=False))
        assert "color:red" in result

    def test_keep_event_handlers_when_disabled(self) -> None:
        html = '<button onclick="doThing()">Click</button>'
        result = optimize_html(html, OptimizeOptions(strip_event_handlers=False))
        assert "onclick" in result


class TestInjectSchemas:
    def test_injects_before_head_close(self) -> None:
        html = "<html><head><title>T</title></head><body>hi</body></html>"
        schema = {"@context": "https://schema.org", "@type": "Organization", "name": "Acme"}
        result = optimize_html(html, OptimizeOptions(inject_schemas=[schema]))
        assert result.index('"name": "Acme"') < result.index("</head>")

    def test_appends_when_no_head(self) -> None:
        html = "<body>hi</body>"
        schema = {"@context": "https://schema.org", "@type": "Organization"}
        result = optimize_html(html, OptimizeOptions(inject_schemas=[schema]))
        assert "application/ld+json" in result


class TestEdgeCases:
    def test_empty_string(self) -> None:
        assert optimize_html("") == ""

    def test_void_elements_do_not_corrupt_stack(self) -> None:
        html = "<div><img src='a.png'><br><p>after</p></div>"
        result = optimize_html(html)
        assert "<p>after</p>" in result
        assert "</div>" in result

    def test_nested_ad_div_with_children(self) -> None:
        html = '<div class="advertisement"><div><span>ad text</span></div></div><p>keep</p>'
        result = optimize_html(html)
        assert "ad text" not in result
        assert "<p>keep</p>" in result

    def test_boolean_attribute_preserved(self) -> None:
        html = "<input disabled>"
        result = optimize_html(html)
        assert "disabled" in result

    def test_xhtml_self_closed_tag(self) -> None:
        html = "<p>hi</p><customtag/><p>after</p>"
        result = optimize_html(html)
        assert "<customtag" in result
        assert "<p>after</p>" in result

    def test_unmatched_end_tag_ignored(self) -> None:
        html = "</div><p>text</p>"
        result = optimize_html(html)
        assert "<p>text</p>" in result

    def test_comment_preserved(self) -> None:
        html = "<!-- a comment --><p>text</p>"
        result = optimize_html(html)
        assert "<!-- a comment -->" in result

    def test_doctype_preserved(self) -> None:
        html = "<!DOCTYPE html><html><body>hi</body></html>"
        result = optimize_html(html)
        assert result.startswith("<!DOCTYPE html>")

    def test_processing_instruction_preserved(self) -> None:
        html = "<?xml-stylesheet href='a.xsl'?><p>text</p>"
        result = optimize_html(html)
        assert "xml-stylesheet" in result

    def test_comment_decl_and_pi_suppressed_inside_skipped_element(self) -> None:
        html = (
            '<div class="advertisement"><!-- ad comment --><!DOCTYPE x><?pi data?></div><p>keep</p>'
        )
        result = optimize_html(html)
        assert "ad comment" not in result
        assert "DOCTYPE" not in result
        assert "pi data" not in result
        assert "<p>keep</p>" in result
