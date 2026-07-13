# Trip Planner — Flutter companion

Companion app for the Django trip planner API (`/api/v1/`).

## Prerequisites

- Flutter stable SDK
- Running Django backend for dev (`uv run python manage.py runserver`)

## Run (flavors)

```bash
cd mobile
flutter pub get

# Dev — local API (iOS simulator / desktop)
flutter run --flavor dev --dart-define-from-file=config/dev.json

# Android emulator → host machine Django
flutter run --flavor dev \
  --dart-define-from-file=config/dev.json \
  --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Production API
flutter run --flavor prod --dart-define-from-file=config/prod.json
```

| Flavor | Android app name | Can install side-by-side |
|--------|------------------|------------------------|
| `dev` | Trip Planner DEV | Yes (`.dev` suffix) |
| `staging` | Trip Planner STG | Yes (`.staging` suffix) |
| `prod` | Trip Planner | Production ID |

## Test & analyze

```bash
flutter analyze
flutter test
```

## Release builds

See **[RELEASE.md](./RELEASE.md)** for TestFlight, Play Internal Testing, signing, and screenshot capture.

```bash
./scripts/build_android.sh prod   # Google Play .aab
./scripts/build_ios.sh prod       # TestFlight .ipa (macOS)
```

## Project structure

```
lib/config/          # env.dart, flavor.dart
config/              # dev.json, staging.json, prod.json
assets/icon/         # launcher + splash source
store/metadata/      # privacy policy, store copy, screenshot guide
scripts/             # build_android.sh, build_ios.sh
```

## Feature phases

- **Phase 11** — Trip list, create, map, checklist, notes, chat edit
- **Phase 12** — Offline cache, photos, weather, reviews, timeline, booking import
- **Phase 13** — Flavors, icons/splash, CI build, store release docs

Product competitiveness features (push, collab) are in Annex C Phases 14–18.
