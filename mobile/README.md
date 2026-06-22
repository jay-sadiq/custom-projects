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
  config/env.dart          # API_BASE_URL dart-define
  core/api/api_client.dart # Dio + JWT refresh interceptor
  core/storage/            # Secure token storage
  features/auth/           # Login, register, Riverpod auth state
  features/home/           # Shell home + API health card
  features/trips/          # Trip/day navigation shell (Phase 11 fills data)
  routing/app_router.dart  # go_router + auth guard
```

## Phase 10 scope

- Authenticated shell with login/register
- JWT persisted in secure storage (survives app restart)
- API health check on home screen
- Routes: `/login`, `/register`, `/`, `/trips/:id/day/:n`

Trip list, map, and create-trip UI land in **Phase 11**.
