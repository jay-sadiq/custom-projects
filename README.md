# Trip Planner App

[![CI](https://github.com/jay-sadiq/custom-projects/actions/workflows/ci.yml/badge.svg)](https://github.com/jay-sadiq/custom-projects/actions/workflows/ci.yml)

AI-powered family trip planner (Django web app + JSON API + Flutter companion in `mobile/`).

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
| `core.settings.prod` | Production (`wsgi.py` / `asgi.py` / Docker) |

```bash
# Development
uv run python manage.py runserver

# Production checks (set env vars first)
export SECRET_KEY='your-secret'
export ALLOWED_HOSTS='example.com'
export CSRF_TRUSTED_ORIGINS='https://example.com'
DJANGO_SETTINGS_MODULE=core.settings.prod uv run python manage.py check --deploy
```

## REST API (`/api/v1/`)

JWT authentication for mobile and integrations. Web HTMX UI continues to use session cookies.

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health/` | Health check (public) |
| `POST /api/v1/auth/register/` | Create account |
| `POST /api/v1/auth/login/` | Obtain access + refresh tokens |
| `POST /api/v1/auth/token/refresh/` | Refresh access token |
| `GET /api/v1/trips/` | List user's trips |
| `POST /api/v1/trips/` | Start async AI trip creation (returns job) |
| `GET /api/v1/trip-jobs/{id}/` | Poll trip creation job status |
| `GET /api/v1/trips/{id}/days/` | Trip days |
| `GET /api/v1/days/{id}/stops/` | Day stops (`?format=map` for map JSON) |
| `GET /api/v1/days/{id}/weather/` | Weather JSON |
| `POST /api/v1/days/{id}/chat-edit/` | AI agenda edit |
| `GET /api/v1/stops/{id}/reviews/` | Place reviews JSON |
| `GET /api/v1/bookings/import/address/` | Unique `trips+{token}@…` forwarding address |
| `POST /api/v1/bookings/import/drafts/preview/` | Parse text → pending draft (review before save) |
| `GET /api/v1/bookings/import/drafts/` | List import drafts (`?status=pending`) |
| `POST /api/v1/bookings/import/drafts/confirm/` | Confirm draft onto a trip |
| `POST /api/v1/bookings/import/drafts/{id}/reject/` | Reject draft |
| `POST /api/v1/webhooks/inbound-email/` | Inbound MIME/text webhook (secret required in prod) |

Example:

```bash
curl http://127.0.0.1:8000/api/v1/health/
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"you","password":"your-password"}'
```

## Deploy to Fly.io (staging/production)

**Platform:** [Fly.io](https://fly.io) — Docker-based, HTTPS, Postgres add-on, health checks.

### 1. Prerequisites

- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) installed and logged in
- Fly app name (edit `app` in `fly.toml` if needed)

### 2. Create Postgres

```bash
fly postgres create --name trip-planner-db
fly postgres attach trip-planner-db
```

This sets `DATABASE_URL` on the Fly app.

### 3. Set secrets

```bash
fly secrets set \
  SECRET_KEY='generate-a-long-random-secret' \
  ALLOWED_HOSTS='your-app.fly.dev' \
  CSRF_TRUSTED_ORIGINS='https://your-app.fly.dev' \
  GEMINI_API_KEY='your-key'
```

Optional S3 media storage:

```bash
fly secrets set USE_S3_STORAGE=True \
  AWS_ACCESS_KEY_ID=... \
  AWS_SECRET_ACCESS_KEY=... \
  AWS_STORAGE_BUCKET_NAME=... \
  AWS_S3_REGION_NAME=us-east-1
```

### 4. Deploy

```bash
fly deploy
```

Fly runs migrations and `collectstatic` via `docker-entrypoint.sh`, then starts Gunicorn. Health check: `GET /api/v1/health/`.

### 5. Verify

```bash
fly open /api/v1/health/
fly logs
```

## Environment variables

See [`.env.example`](.env.example). Required in **production**:

- `SECRET_KEY`
- `ALLOWED_HOSTS` (comma-separated)
- `CSRF_TRUSTED_ORIGINS` (comma-separated HTTPS origins)
- `DATABASE_URL` (PostgreSQL on Fly/Railway/Render)

Optional: `GEMINI_API_KEY`, `GOOGLE_PLACES_API_KEY`, `WEATHER_API_KEY`, `USE_S3_STORAGE`, `AI_RATE_LIMIT`.

## Tests

```bash
uv sync --dev
uv run python manage.py test itinerary.tests
uv run coverage run --source=itinerary manage.py test itinerary.tests
uv run coverage report --include='itinerary/views.py'
```

## Mobile app (Phase 10–13)

Trip list, offline cache, photos, and store-ready flavors are in the Flutter companion. See [`mobile/RELEASE.md`](mobile/RELEASE.md) for TestFlight and Play Console steps.

```bash
cd mobile
flutter pub get
flutter run --flavor dev --dart-define-from-file=config/dev.json
```

Android emulator: add `--dart-define=API_BASE_URL=http://10.0.2.2:8000`.

See [`mobile/README.md`](mobile/README.md) for flavors, structure, and CI.

## Booking email import (Phase 14)

Each user gets a unique forwarding address shown on the dashboard and at
`GET /api/v1/bookings/import/address/` — format `trips+{token}@{BOOKING_IMPORT_EMAIL_DOMAIN}`.

1. Point your inbound email provider (Mailgun/SendGrid/Postmark inbound parse) at
   `POST /api/v1/webhooks/inbound-email/` with header `X-Webhook-Secret`.
2. Body: raw MIME in `raw`/`email`, or JSON `{ "text": "...", "to": "trips+token@…" }`.
3. Review pending drafts at `/bookings/imports/` (web) or via
   `POST /api/v1/bookings/import/drafts/confirm/`.
4. Confirm assigns the booking to a trip (auto-suggested by date overlap) or reject it.
   Duplicate confirmation numbers merge into the existing booking.

Paste-to-import without email still works from the trip detail page and
`POST /api/v1/trips/{id}/bookings/import/` (saves immediately). Use the draft
preview endpoints when you want review-before-save.

## Planning docs

See [`plan/README.md`](plan/README.md) for the full product and engineering roadmap.

## Seed data (dev only)

```bash
uv run python manage.py seed_baku --user yourusername
```

Legacy wrapper: `uv run python seed_baku.py yourusername`
