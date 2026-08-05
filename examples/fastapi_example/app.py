"""Minimal FastAPI app using ai-visibility.

Run:
    pip install ai-visibility[fastapi]
    uvicorn app:app --reload

Then compare a regular visitor with a detected crawler:
    curl http://localhost:8000/
    curl -A "ClaudeBot/1.0" http://localhost:8000/
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from ai_visibility.middleware.fastapi import AIVisibilityMiddleware
from ai_visibility.schema import organization_schema

app = FastAPI()
app.add_middleware(
    AIVisibilityMiddleware,
    optimize=True,
    inject_schemas=True,
    schemas=[organization_schema(name="Acme Inc.", url="https://acme.example")],
)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<html>
<head><title>Acme Inc.</title></head>
<body>
<script>console.log('tracking pixel etc.');</script>
<main><h1>Welcome to Acme</h1><p>We make widgets.</p></main>
</body>
</html>"""
