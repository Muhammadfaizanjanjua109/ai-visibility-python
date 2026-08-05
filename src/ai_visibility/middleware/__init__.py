"""Framework middleware adapters for ai_visibility.

Only :mod:`ai_visibility.middleware.base` is imported here — the
framework-specific adapters (:mod:`.django`, :mod:`.flask`, :mod:`.fastapi`)
each depend on an optional extra and must be imported directly, e.g.::

    from ai_visibility.middleware.flask import AIVisibility

so that installing the core package never requires Django, Flask, or
FastAPI to be present.
"""

from ai_visibility.middleware.base import AIVisibilityCore, MiddlewareConfig, is_html_content_type

__all__ = ["AIVisibilityCore", "MiddlewareConfig", "is_html_content_type"]
