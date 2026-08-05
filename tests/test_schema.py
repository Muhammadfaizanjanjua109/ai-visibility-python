"""Tests for ai_visibility.schema."""

from __future__ import annotations

import json

from ai_visibility import schema


class TestArticleSchema:
    def test_minimal(self) -> None:
        result = schema.article_schema(headline="Hello World")
        assert result["@context"] == "https://schema.org"
        assert result["@type"] == "Article"
        assert result["headline"] == "Hello World"
        assert "author" not in result

    def test_full(self) -> None:
        result = schema.article_schema(
            headline="Hello",
            description="desc",
            author_name="Jane Doe",
            author_url="https://example.com/jane",
            date_published="2026-01-01",
            date_modified="2026-01-02",
            image="https://example.com/img.png",
            publisher_name="Acme",
            publisher_logo_url="https://example.com/logo.png",
            url="https://example.com/article",
            article_type="NewsArticle",
        )
        assert result["@type"] == "NewsArticle"
        assert result["author"] == {
            "@type": "Person",
            "name": "Jane Doe",
            "url": "https://example.com/jane",
        }
        assert result["publisher"]["logo"]["url"] == "https://example.com/logo.png"
        assert result["mainEntityOfPage"] == {
            "@type": "WebPage",
            "@id": "https://example.com/article",
        }


class TestProductSchema:
    def test_minimal(self) -> None:
        result = schema.product_schema(name="Widget")
        assert result["@type"] == "Product"
        assert "offers" not in result

    def test_with_price_and_rating(self) -> None:
        result = schema.product_schema(
            name="Widget",
            price=19.99,
            price_currency="USD",
            availability="InStock",
            rating_value=4.5,
            review_count=10,
        )
        assert result["offers"]["price"] == "19.99"
        assert result["offers"]["priceCurrency"] == "USD"
        assert result["offers"]["availability"] == "https://schema.org/InStock"
        assert result["aggregateRating"]["ratingValue"] == 4.5
        assert result["aggregateRating"]["reviewCount"] == 10


class TestFaqSchema:
    def test_builds_main_entity(self) -> None:
        result = schema.faq_schema(
            [
                {"question": "What is X?", "answer": "X is Y."},
                {"question": "Why?", "answer": "Because."},
            ]
        )
        assert result["@type"] == "FAQPage"
        assert len(result["mainEntity"]) == 2
        assert result["mainEntity"][0]["name"] == "What is X?"
        assert result["mainEntity"][0]["acceptedAnswer"]["text"] == "X is Y."


class TestHowtoSchema:
    def test_with_steps(self) -> None:
        result = schema.howto_schema(
            name="Make tea",
            steps=[
                {"name": "Boil water", "text": "Boil it."},
                {"name": "Steep", "text": "Steep it."},
            ],
            total_time="PT5M",
        )
        assert result["@type"] == "HowTo"
        assert len(result["step"]) == 2
        assert result["step"][0]["@type"] == "HowToStep"
        assert result["totalTime"] == "PT5M"


class TestOrganizationSchema:
    def test_with_contact_point(self) -> None:
        result = schema.organization_schema(
            name="Acme",
            url="https://acme.com",
            contact_telephone="+1-555-1234",
            contact_type="customer support",
        )
        assert result["contactPoint"]["telephone"] == "+1-555-1234"
        assert result["contactPoint"]["contactType"] == "customer support"


class TestLocalBusinessSchema:
    def test_with_address_and_geo(self) -> None:
        result = schema.local_business_schema(
            name="Joe's Diner",
            business_type="Restaurant",
            street_address="123 Main St",
            address_locality="Springfield",
            latitude=1.23,
            longitude=4.56,
        )
        assert result["@type"] == "Restaurant"
        assert result["address"]["streetAddress"] == "123 Main St"
        assert result["geo"]["latitude"] == 1.23

    def test_omits_empty_address(self) -> None:
        result = schema.local_business_schema(name="Joe's Diner")
        assert "address" not in result
        assert "geo" not in result


class TestBreadcrumbSchema:
    def test_positions_are_sequential(self) -> None:
        result = schema.breadcrumb_schema(
            [
                {"name": "Home", "url": "https://example.com/"},
                {"name": "Blog", "url": "https://example.com/blog"},
            ]
        )
        assert result["itemListElement"][0]["position"] == 1
        assert result["itemListElement"][1]["position"] == 2


class TestVideoSchema:
    def test_minimal(self) -> None:
        result = schema.video_schema(name="My Video", upload_date="2026-01-01")
        assert result["@type"] == "VideoObject"
        assert result["uploadDate"] == "2026-01-01"


class TestEventSchema:
    def test_with_location_and_organizer(self) -> None:
        result = schema.event_schema(
            name="Conf",
            start_date="2026-06-01T09:00:00",
            location_name="Venue Hall",
            event_status="EventScheduled",
            organizer_name="Acme",
        )
        assert result["location"]["name"] == "Venue Hall"
        assert result["eventStatus"] == "https://schema.org/EventScheduled"
        assert result["organizer"]["name"] == "Acme"


class TestWebsiteSchema:
    def test_with_search_action(self) -> None:
        result = schema.website_schema(
            name="Acme",
            url="https://acme.com",
            search_url_template="https://acme.com/search?q={search_term_string}",
        )
        assert result["potentialAction"]["@type"] == "SearchAction"
        assert "{search_term_string}" in result["potentialAction"]["target"]["urlTemplate"]

    def test_without_search_action(self) -> None:
        result = schema.website_schema(name="Acme", url="https://acme.com")
        assert "potentialAction" not in result


class TestRenderJsonld:
    def test_wraps_in_script_tag(self) -> None:
        data = {"@context": "https://schema.org", "@type": "Thing", "name": "X"}
        rendered = schema.render_jsonld(data)
        assert rendered.startswith('<script type="application/ld+json">')
        assert rendered.endswith("</script>")
        inner = rendered[len('<script type="application/ld+json">') : -len("</script>")]
        assert json.loads(inner) == data
