"""Minimal single-file Django app using ai-visibility.

Run:
    pip install ai-visibility[django]
    python app.py runserver

Then compare a regular visitor with a detected crawler:
    curl http://localhost:8000/
    curl -A "GPTBot/1.0" http://localhost:8000/
"""

import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import HttpRequest, HttpResponse
from django.urls import path

from ai_visibility.schema import organization_schema

settings.configure(
    DEBUG=True,
    ALLOWED_HOSTS=["*"],
    ROOT_URLCONF=__name__,
    MIDDLEWARE=["ai_visibility.middleware.django.AIVisibilityMiddleware"],
    AI_VISIBILITY={
        "optimize": True,
        "inject_schemas": True,
        "schemas": [organization_schema(name="Acme Inc.", url="https://acme.example")],
        "log_visits": True,
    },
    SECRET_KEY="example-only-not-for-production",  # noqa: S106
)
django.setup()


def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse(
        """<html>
<head><title>Acme Inc.</title></head>
<body>
<script>console.log('tracking pixel etc.');</script>
<main><h1>Welcome to Acme</h1><p>We make widgets.</p></main>
</body>
</html>""",
        content_type="text/html",
    )


urlpatterns = [path("", index)]

if __name__ == "__main__":
    execute_from_command_line()
