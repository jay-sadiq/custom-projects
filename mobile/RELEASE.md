# Mobile release guide (Phase 13)

Internal testing builds for TestFlight and Google Play Internal Testing.

## Prerequisites

| Requirement | iOS | Android |
|-------------|-----|---------|
| Developer account | [Apple Developer Program](https://developer.apple.com/programs/) ($99/yr) | [Google Play Console](https://play.google.com/console) ($25 one-time) |
| Machine | macOS with Xcode 15+ | Any OS for bundle; macOS optional |
| Backend | Deployed API (see root `README.md` Fly.io section) | Same |

## Flavors

| Flavor | App name (Android) | Application ID suffix | Default API |
|--------|-------------------|----------------------|-------------|
| `dev` | Trip Planner DEV | `.dev` | `http://127.0.0.1:8000` |
| `staging` | Trip Planner STG | `.staging` | `https://trip-planner-app-staging.fly.dev` |
| `prod` | Trip Planner | (none) | `https://trip-planner-app.fly.dev` |

Config files: `mobile/config/{dev,staging,prod}.json`

### Run locally

```bash
cd mobile
flutter pub get

# Android emulator (dev)
flutter run --flavor dev --dart-define-from-file=config/dev.json

# Override API (e.g. Android emulator → host machine)
flutter run --flavor dev \
  --dart-define-from-file=config/dev.json \
  --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Production API
flutter run --flavor prod --dart-define-from-file=config/prod.json
```

iOS uses schemes `dev`, `staging`, `prod` (matching `--flavor`). Android installs dev/staging/prod side-by-side via distinct application IDs.

## Regenerate icons & splash

After changing `assets/icon/app_icon.png`:

```bash
cd mobile
dart run flutter_launcher_icons
dart run flutter_native_splash:create
```

## Android — Play Internal Testing

### 1. Signing (first time)

Create a release keystore (keep backups and passwords secure):

```bash
keytool -genkey -v -keystore ~/trip-planner-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias trip-planner
```

Create `mobile/android/key.properties` (do **not** commit):

```properties
storePassword=YOUR_STORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=trip-planner
storeFile=/Users/you/trip-planner-release.jks
```

Wire signing in `android/app/build.gradle.kts` before store upload (currently uses debug signing for local `flutter run --release` only).

### 2. Build app bundle

```bash
./scripts/build_android.sh prod
# → build/app/outputs/bundle/prodRelease/app-prod-release.aab
```

### 3. Upload to Play Console

1. Create app in Play Console → **Internal testing** track
2. Upload the `.aab`
3. Add testers by email list
4. Complete store listing: title, short description (`store/metadata/app_description.txt`), privacy policy URL (`store/metadata/PRIVACY.md` hosted or GitHub raw link)
5. Upload screenshots per `store/metadata/SCREENSHOTS.md`

## iOS — TestFlight

### 1. Xcode signing

1. Open `mobile/ios/Runner.xcworkspace` in Xcode
2. Select **Runner** target → **Signing & Capabilities**
3. Set your Team and enable **Automatically manage signing**
4. Bundle ID: `com.tripplanner.tripPlannerApp` (prod)

### 2. Build IPA

```bash
./scripts/build_ios.sh prod
```

Or archive in Xcode: **Product → Archive** with scheme `prod`.

### 3. Upload to App Store Connect

1. Create app in [App Store Connect](https://appstoreconnect.apple.com)
2. Upload IPA via Xcode Organizer or `xcrun altool`
3. Add **Internal Testing** group in TestFlight
4. Fill App Privacy questionnaire (data linked to user account: trip content, photos)
5. Privacy policy URL → link to `PRIVACY.md` (GitHub or hosted page)
6. Screenshots per `SCREENSHOTS.md`

## CI

`.github/workflows/mobile.yml` runs on every mobile PR:

- `flutter analyze`
- `flutter test`
- `flutter build apk --debug --flavor dev`

On push to `main`, also builds `appbundle` for `prod` (unsigned with debug keys until release keystore is configured in CI secrets).

## Smoke test checklist (2 testers)

- [ ] Install from TestFlight / Play Internal
- [ ] Register or login against staging/prod API
- [ ] Trip list loads
- [ ] Open trip → map + timeline visible
- [ ] Toggle checklist item → verify on web
- [ ] Upload photo on stop → verify on web
- [ ] Kill app → reopen → still authenticated

## Version bumps

Update `version:` in `mobile/pubspec.yaml` (`1.0.0+1` → `1.0.1+2`). The number after `+` is the build number required by both stores.
