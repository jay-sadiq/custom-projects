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
  config/env.dart
  core/api/                 # Dio + JWT refresh
  core/cache/               # Hive offline read cache
  core/network/             # Connectivity status
  features/auth/
  features/trips/           # List, create, detail, map, timeline, photos
  routing/
```

## Phase 11 — Core companion screens

Trip list, AI create-trip, day map, stops, debounced notes, checklist toggle, and chat edit.

## Phase 12 — Offline, photos, parity widgets

- **Offline cache** — Hive stores last-viewed trips/days/stops/checklist; orange banner when offline; edits disabled
- **Camera upload** — `image_picker` → `POST /stops/{id}/photos/` with gallery on stop detail
- **Weather chip** — `GET /days/{id}/weather/` in day header
- **Reviews sheet** — `GET /stops/{id}/reviews/` from stop detail
- **Timeline** — read-only vertical schedule sorted by `start_time_of_day`
- **Booking import** — paste confirmation text → `POST /trips/{id}/bookings/import/`

Store builds and flavors land in **Phase 13**.
