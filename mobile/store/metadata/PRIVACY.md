# Privacy Policy — Trip Planner Mobile

**Last updated:** June 2026

Trip Planner is a companion app for the Trip Planner web service. This policy describes what the mobile app collects and how it is used.

## Data we collect

- **Account credentials** — username and password at registration/login. Passwords are sent over HTTPS to our API and are not stored in plain text on the device.
- **Authentication tokens** — JWT access and refresh tokens are stored in the device secure keychain (iOS Keychain / Android EncryptedSharedPreferences via `flutter_secure_storage`).
- **Trip content** — itineraries, stops, notes, checklist items, and photos you create or upload are stored on our servers and cached locally (Hive) for offline reading.
- **Photos** — images you attach to stops are uploaded to our backend and stored with your trip data.

## Data we do not collect

- We do not sell personal data.
- We do not use third-party advertising SDKs.
- Location is used only when you view maps (OpenStreetMap tiles); we do not continuously track GPS in the background.

## Third-party services

- **OpenStreetMap** — map tiles when viewing trip maps.
- **Weather API** — forecast data proxied through our Django backend (your device does not call weather providers directly).
- **Google Places** (when configured on the server) — reviews and place photos proxied through our API.

## Data retention

Trip data is retained while your account exists. You may delete trips via the web app. Uninstalling the mobile app removes local cache and secure tokens but not server-side data.

## Contact

For privacy requests, open an issue on the project repository or contact the app maintainer listed in the store listing.

## Changes

We may update this policy. Material changes will be reflected in the store listing privacy URL.
