"""Minimal Flask app using ai-visibility.

Run:
    pip install ai-visibility[flask]
    python app.py

Then compare a regular visitor with a detected crawler:
    curl http://localhost:5000/
    curl -A "GPTBot/1.0" http://localhost:5000/
"""

from flask import Flask

from ai_visibility.middleware.flask import AIVisibility
from ai_visibility.schema import organization_schema

app = Flask(__name__)
AIVisibility(
    app,
    optimize=True,
    inject_schemas=True,
    schemas=[organization_schema(name="Acme Inc.", url="https://acme.example")],
)


@app.route("/")
def index() -> str:
    return """<html>
<head><title>Acme Inc.</title></head>
<body>
<script>console.log('tracking pixel etc.');</script>
<main><h1>Welcome to Acme</h1><p>We make widgets.</p></main>
</body>
</html>"""


if __name__ == "__main__":
    app.run(debug=True)
