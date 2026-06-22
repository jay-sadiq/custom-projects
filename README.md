# Trip Planner App

AI-powered family trip planner (Django web app). Flutter mobile companion planned.

## Quick start (development)

```bash
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run python manage.py runserver
```

Open http://127.0.0.1:8000 — register a user and create a trip.

## Settings modules

| Module | Use |
|--------|-----|
| `core.settings.dev` | Local development (`manage.py` default) |
| `core.settings.prod` | Production (`wsgi.py` / `asgi.py` default) |

```bash
# Development
uv run python manage.py runserver

# Production checks (set env vars first)
export SECRET_KEY='your-secret'
export ALLOWED_HOSTS='example.com'
export CSRF_TRUSTED_ORIGINS='https://example.com'
DJANGO_SETTINGS_MODULE=core.settings.prod uv run python manage.py check --deploy
```

## Environment variables

See [`.env.example`](.env.example). Required in **production**:

- `SECRET_KEY`
- `ALLOWED_HOSTS` (comma-separated)
- `CSRF_TRUSTED_ORIGINS` (comma-separated HTTPS origins)

Optional integrations: `GEMINI_API_KEY`, `GOOGLE_PLACES_API_KEY`, `WEATHER_API_KEY`, `OLLAMA_URL`.

## Tests

```bash
uv run python manage.py test itinerary.tests
```

## Planning docs

See [`plan/README.md`](plan/README.md) for the full product and engineering roadmap.

## Seed data (optional)

```bash
uv run python seed_baku.py
```

Assigns the sample Baku itinerary to the first admin user.
