# Store screenshots

Capture **5 screenshots per platform** before submitting to App Store Connect or Google Play Console.

## Recommended scenes

1. **Login** — clean auth screen showing crimson branding
2. **Trip list** — dashboard with at least one trip
3. **Trip detail / map** — day view with map markers and day chips
4. **Timeline + weather** — scroll to timeline and weather chip
5. **Stop detail** — bottom sheet with photos or reviews

## How to capture

### iOS Simulator

```bash
cd mobile
flutter run --flavor dev --dart-define-from-file=config/dev.json
# Cmd+S in Simulator saves to Desktop
```

### Android Emulator

```bash
flutter run --flavor dev --dart-define-from-file=config/dev.json
# Use emulator screenshot button or: adb exec-out screencap -p > screenshot.png
```

## File naming

Save into this folder before upload:

```
store/screenshots/ios/
  01_login.png
  02_trips.png
  03_map.png
  04_timeline.png
  05_stop_detail.png

store/screenshots/android/
  01_login.png
  ...
```

Google Play requires phone + 7-inch tablet for production apps; start with phone-sized 1080×1920 or higher.

App Store Connect requires 6.7" and 6.5" iPhone sizes (use Xcode simulator devices).
