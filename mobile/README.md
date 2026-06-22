# Trip Planner — Flutter companion

Companion app for the Django trip planner API (`/api/v1/`).

## Prerequisites

- Flutter stable SDK
- Running Django backend (`uv run python manage.py runserver`)

## Run

```bash
cd mobile
flutter pub get
flutter run \
  --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

**Android emulator:** use `http://10.0.2.2:8000` instead of `127.0.0.1`.

**iOS simulator:** `http://127.0.0.1:8000` works.

## Test & analyze

```bash
flutter analyze
flutter test
```

## Project structure

```
lib/
  config/env.dart              # API_BASE_URL dart-define
  core/api/api_client.dart     # Dio + JWT refresh interceptor
  core/storage/                # Secure token storage
  features/auth/               # Login, register, Riverpod auth state
  features/trips/              # Trip list, create, detail, map, checklist, chat
  routing/app_router.dart      # go_router + auth guard
```

## Phase 10 — Foundation

- Authenticated shell with login/register
- JWT persisted in secure storage (survives app restart)
- Routes: `/login`, `/register`, `/`, `/trips/create`, `/trips/:id/day/:n`

## Phase 11 — Core companion screens

- **Trip list** — pull-to-refresh dashboard at `/`
- **Create trip** — AI job polling via `POST /trips/` + `GET /trip-jobs/{id}/`
- **Trip detail** — day chips, theme/banner/costs, OSM map (`flutter_map`), stops list
- **Notes** — debounced `PATCH /days/{id}/`
- **Checklist** — toggle via `POST /checklist-items/{id}/toggle/`
- **AI chat edit** — bottom sheet calling `POST /days/{id}/chat-edit/`

Offline cache, camera upload, and weather widgets land in **Phase 12**.
