"""JSON-LD structured data builders for schema.org types."""

from __future__ import annotations

import json
from typing import Any, Optional, Union

_SCHEMA_CONTEXT = "https://schema.org"

StrOrList = Union[str, list[str]]


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is None, keeping everything else as-is."""
    return {key: value for key, value in data.items() if value is not None}


def article_schema(
    *,
    headline: str,
    description: Optional[str] = None,
    author_name: Optional[str] = None,
    author_url: Optional[str] = None,
    date_published: Optional[str] = None,
    date_modified: Optional[str] = None,
    image: Optional[StrOrList] = None,
    publisher_name: Optional[str] = None,
    publisher_logo_url: Optional[str] = None,
    url: Optional[str] = None,
    article_type: str = "Article",
) -> dict[str, Any]:
    """Build an ``Article`` (or subtype) JSON-LD schema.

    Args:
        headline: The article's headline.
        description: Short summary of the article.
        author_name: Name of the author.
        author_url: URL of the author's profile/page.
        date_published: ISO 8601 publish date.
        date_modified: ISO 8601 last-modified date.
        image: One or more image URLs.
        publisher_name: Name of the publishing organization.
        publisher_logo_url: URL of the publisher's logo image.
        url: Canonical URL of the article.
        article_type: Schema.org type to use, e.g. ``"NewsArticle"``.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    author = (
        _clean({"@type": "Person", "name": author_name, "url": author_url}) if author_name else None
    )
    publisher = (
        _clean(
            {
                "@type": "Organization",
                "name": publisher_name,
                "logo": _clean({"@type": "ImageObject", "url": publisher_logo_url})
                if publisher_logo_url
                else None,
            }
        )
        if publisher_name
        else None
    )
    return _clean(
        {
            "@context": _SCHEMA_CONTEXT,
            "@type": article_type,
            "headline": headline,
            "description": description,
            "image": image,
            "author": author,
            "publisher": publisher,
            "datePublished": date_published,
            "dateModified": date_modified,
            "mainEntityOfPage": _clean({"@type": "WebPage", "@id": url}) if url else None,
        }
    )


def product_schema(
    *,
    name: str,
    description: Optional[str] = None,
    image: Optional[StrOrList] = None,
    sku: Optional[str] = None,
    brand: Optional[str] = None,
    price: Optional[Union[str, float]] = None,
    price_currency: Optional[str] = None,
    availability: Optional[str] = None,
    url: Optional[str] = None,
    rating_value: Optional[float] = None,
    review_count: Optional[int] = None,
) -> dict[str, Any]:
    """Build a ``Product`` JSON-LD schema, with optional offer and rating.

    Args:
        name: Product name.
        description: Product description.
        image: One or more image URLs.
        sku: Stock-keeping unit identifier.
        brand: Brand name.
        price: Numeric or string price; combined with ``price_currency``
            and ``availability`` into an ``Offer``.
        price_currency: ISO 4217 currency code, e.g. ``"USD"``.
        availability: Schema.org availability URL/token, e.g. ``"InStock"``.
        url: Canonical product URL.
        rating_value: Average rating; combined with ``review_count`` into
            an ``AggregateRating``.
        review_count: Number of reviews backing ``rating_value``.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    offers = None
    if price is not None:
        offers = _clean(
            {
                "@type": "Offer",
                "price": str(price),
                "priceCurrency": price_currency,
                "availability": f"https://schema.org/{availability}"
                if availability and not availability.startswith("http")
                else availability,
                "url": url,
            }
        )

    aggregate_rating = None
    if rating_value is not None:
        aggregate_rating = _clean(
            {
                "@type": "AggregateRating",
                "ratingValue": rating_value,
                "reviewCount": review_count,
            }
        )

    return _clean(
        {
            "@context": _SCHEMA_CONTEXT,
            "@type": "Product",
            "name": name,
            "description": description,
            "image": image,
            "sku": sku,
            "brand": _clean({"@type": "Brand", "name": brand}) if brand else None,
            "offers": offers,
            "aggregateRating": aggregate_rating,
            "url": url,
        }
    )


def faq_schema(questions: list[dict[str, str]]) -> dict[str, Any]:
    """Build an ``FAQPage`` JSON-LD schema.

    Args:
        questions: A list of ``{"question": ..., "answer": ...}`` dicts.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    main_entity = [
        {
            "@type": "Question",
            "name": q["question"],
            "acceptedAnswer": {"@type": "Answer", "text": q["answer"]},
        }
        for q in questions
    ]
    return {
        "@context": _SCHEMA_CONTEXT,
        "@type": "FAQPage",
        "mainEntity": main_entity,
    }


def howto_schema(
    *,
    name: str,
    description: Optional[str] = None,
    steps: Optional[list[dict[str, str]]] = None,
    total_time: Optional[str] = None,
    image: Optional[StrOrList] = None,
    estimated_cost: Optional[str] = None,
) -> dict[str, Any]:
    """Build a ``HowTo`` JSON-LD schema.

    Args:
        name: Title of the how-to guide.
        description: Short summary of the guide.
        steps: A list of ``{"name": ..., "text": ...}`` dicts, in order.
        total_time: ISO 8601 duration, e.g. ``"PT30M"``.
        image: One or more image URLs.
        estimated_cost: Estimated cost as free text, e.g. ``"$20"``.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    step_entries = (
        [{"@type": "HowToStep", "name": step["name"], "text": step["text"]} for step in steps]
        if steps
        else None
    )
    return _clean(
        {
            "@context": _SCHEMA_CONTEXT,
            "@type": "HowTo",
            "name": name,
            "description": description,
            "image": image,
            "totalTime": total_time,
            "estimatedCost": estimated_cost,
            "step": step_entries,
        }
    )


def organization_schema(
    *,
    name: str,
    url: Optional[str] = None,
    logo: Optional[str] = None,
    description: Optional[str] = None,
    same_as: Optional[list[str]] = None,
    contact_telephone: Optional[str] = None,
    contact_type: Optional[str] = None,
    contact_email: Optional[str] = None,
) -> dict[str, Any]:
    """Build an ``Organization`` JSON-LD schema.

    Args:
        name: Organization name.
        url: Organization's website URL.
        logo: URL of the organization's logo image.
        description: Short description of the organization.
        same_as: URLs of official social media / reference profiles.
        contact_telephone: Contact phone number.
        contact_type: Schema.org contact type, e.g. ``"customer support"``.
        contact_email: Contact email address.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    contact_point = None
    if contact_telephone or contact_email:
        contact_point = _clean(
            {
                "@type": "ContactPoint",
                "telephone": contact_telephone,
                "contactType": contact_type,
                "email": contact_email,
            }
        )
    return _clean(
        {
            "@context": _SCHEMA_CONTEXT,
            "@type": "Organization",
            "name": name,
            "url": url,
            "logo": logo,
            "description": description,
            "sameAs": same_as,
            "contactPoint": contact_point,
        }
    )


def local_business_schema(
    *,
    name: str,
    business_type: str = "LocalBusiness",
    url: Optional[str] = None,
    image: Optional[StrOrList] = None,
    telephone: Optional[str] = None,
    street_address: Optional[str] = None,
    address_locality: Optional[str] = None,
    address_region: Optional[str] = None,
    postal_code: Optional[str] = None,
    address_country: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    opening_hours: Optional[list[str]] = None,
    price_range: Optional[str] = None,
) -> dict[str, Any]:
    """Build a ``LocalBusiness`` (or subtype) JSON-LD schema.

    Args:
        name: Business name.
        business_type: Schema.org type, e.g. ``"Restaurant"``.
        url: Business website URL.
        image: One or more image URLs.
        telephone: Contact phone number.
        street_address: Street address line.
        address_locality: City/locality.
        address_region: State/region.
        postal_code: Postal/ZIP code.
        address_country: Country name or ISO code.
        latitude: Geographic latitude.
        longitude: Geographic longitude.
        opening_hours: Opening hours specifications, e.g. ``["Mo-Fr 09:00-17:00"]``.
        price_range: Free-text price range, e.g. ``"$$"``.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    address = None
    if any((street_address, address_locality, address_region, postal_code, address_country)):
        address = _clean(
            {
                "@type": "PostalAddress",
                "streetAddress": street_address,
                "addressLocality": address_locality,
                "addressRegion": address_region,
                "postalCode": postal_code,
                "addressCountry": address_country,
            }
        )
    geo = None
    if latitude is not None and longitude is not None:
        geo = {"@type": "GeoCoordinates", "latitude": latitude, "longitude": longitude}
    return _clean(
        {
            "@context": _SCHEMA_CONTEXT,
            "@type": business_type,
            "name": name,
            "url": url,
            "image": image,
            "telephone": telephone,
            "address": address,
            "geo": geo,
            "openingHours": opening_hours,
            "priceRange": price_range,
        }
    )


def breadcrumb_schema(items: list[dict[str, str]]) -> dict[str, Any]:
    """Build a ``BreadcrumbList`` JSON-LD schema.

    Args:
        items: A list of ``{"name": ..., "url": ...}`` dicts, in order
            from the root page to the current page.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    element_list = [
        {
            "@type": "ListItem",
            "position": index,
            "name": item["name"],
            "item": item["url"],
        }
        for index, item in enumerate(items, start=1)
    ]
    return {
        "@context": _SCHEMA_CONTEXT,
        "@type": "BreadcrumbList",
        "itemListElement": element_list,
    }


def video_schema(
    *,
    name: str,
    description: Optional[str] = None,
    thumbnail_url: Optional[StrOrList] = None,
    upload_date: Optional[str] = None,
    duration: Optional[str] = None,
    content_url: Optional[str] = None,
    embed_url: Optional[str] = None,
) -> dict[str, Any]:
    """Build a ``VideoObject`` JSON-LD schema.

    Args:
        name: Video title.
        description: Video description.
        thumbnail_url: One or more thumbnail image URLs.
        upload_date: ISO 8601 upload date.
        duration: ISO 8601 duration, e.g. ``"PT1M33S"``.
        content_url: Direct URL to the video file.
        embed_url: URL of an embeddable player for the video.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    return _clean(
        {
            "@context": _SCHEMA_CONTEXT,
            "@type": "VideoObject",
            "name": name,
            "description": description,
            "thumbnailUrl": thumbnail_url,
            "uploadDate": upload_date,
            "duration": duration,
            "contentUrl": content_url,
            "embedUrl": embed_url,
        }
    )


def event_schema(
    *,
    name: str,
    start_date: str,
    end_date: Optional[str] = None,
    location_name: Optional[str] = None,
    location_address: Optional[str] = None,
    description: Optional[str] = None,
    image: Optional[StrOrList] = None,
    event_status: Optional[str] = None,
    event_attendance_mode: Optional[str] = None,
    organizer_name: Optional[str] = None,
    organizer_url: Optional[str] = None,
) -> dict[str, Any]:
    """Build an ``Event`` JSON-LD schema.

    Args:
        name: Event name.
        start_date: ISO 8601 start date/time.
        end_date: ISO 8601 end date/time.
        location_name: Venue name.
        location_address: Venue street address.
        description: Event description.
        image: One or more image URLs.
        event_status: Schema.org event status, e.g. ``"EventScheduled"``.
        event_attendance_mode: Schema.org attendance mode, e.g.
            ``"OfflineEventAttendanceMode"``.
        organizer_name: Name of the organizing person/entity.
        organizer_url: URL of the organizer.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    location = (
        _clean(
            {
                "@type": "Place",
                "name": location_name,
                "address": location_address,
            }
        )
        if location_name or location_address
        else None
    )
    organizer = (
        _clean({"@type": "Organization", "name": organizer_name, "url": organizer_url})
        if organizer_name
        else None
    )
    return _clean(
        {
            "@context": _SCHEMA_CONTEXT,
            "@type": "Event",
            "name": name,
            "startDate": start_date,
            "endDate": end_date,
            "description": description,
            "image": image,
            "location": location,
            "eventStatus": f"https://schema.org/{event_status}"
            if event_status and not event_status.startswith("http")
            else event_status,
            "eventAttendanceMode": f"https://schema.org/{event_attendance_mode}"
            if event_attendance_mode and not event_attendance_mode.startswith("http")
            else event_attendance_mode,
            "organizer": organizer,
        }
    )


def website_schema(
    *,
    name: str,
    url: str,
    description: Optional[str] = None,
    search_url_template: Optional[str] = None,
) -> dict[str, Any]:
    """Build a ``WebSite`` JSON-LD schema, with an optional sitelinks search box.

    Args:
        name: Site name.
        url: Site's canonical/home URL.
        description: Site description.
        search_url_template: A URL containing ``{search_term_string}`` used
            to build a ``SearchAction`` for a sitelinks search box.

    Returns:
        A JSON-serializable ``dict`` with ``@context``/``@type`` set.
    """
    potential_action = None
    if search_url_template:
        potential_action = {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": search_url_template,
            },
            "query-input": "required name=search_term_string",
        }
    return _clean(
        {
            "@context": _SCHEMA_CONTEXT,
            "@type": "WebSite",
            "name": name,
            "url": url,
            "description": description,
            "potentialAction": potential_action,
        }
    )


def render_jsonld(schema: dict[str, Any]) -> str:
    """Render a schema dict as an HTML ``<script type="application/ld+json">`` tag.

    Args:
        schema: A JSON-LD schema dict, typically from one of the
            ``*_schema`` builder functions.

    Returns:
        The full HTML script tag as a string.
    """
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'
