# Annex B — API & Flutter Mobile

**Parent plan:** [MASTER_PLAN.md](./MASTER_PLAN.md) — vision, user journey, competitive analysis, unified timeline.

| | |
|--|--|
| **Phases covered** | 9–13 |
| **Milestones** | M2 Beta (9) · M3 v1.0 (10–13) |
| **Prerequisites** | [Annex A](./ROADMAP.md) Phases 1–4 minimum; Phase 8 for store builds |
| **Related** | [Annex C: Product Features](./PRODUCT_FEATURES.md) Phase 15 overlaps collab |

Add a **Flutter hybrid companion app** (iOS + Android from one codebase) that shares the **same Django backend** as the existing web app. One repo, one API, one domain model — web keeps HTMX templates; mobile consumes JSON.

---

## Strategy

| Layer | Technology | Role |
|-------|------------|------|
| Web | Django + HTMX + Leaflet | Full planner UI |
| API | DRF `/api/v1/` | Shared contract for mobile |
| Mobile | Flutter `mobile/` | Companion on iOS/Android |
| Logic | `itinerary/services/` | Single source for web + API |

**Hybrid** = one Flutter codebase → iOS + Android. **Companion** = read + light edit on mobile; full calendar editing stays web-first until Annex B Phase 12.

Monorepo layout and prerequisites: [MASTER_PLAN.md](./MASTER_PLAN.md) §1 and Annex A Phases 1–4.

---

**Duration:** 1.5 weeks  
**Outcome:** Versioned JSON API alongside existing web views; no breaking change to HTMX UI.

### Goal 9.1 — DRF setup & URL namespace

- **S:** Add `djangorestframework` + `djangorestframework-simplejwt`; mount `api/v1/` in `core/urls.py`; create `itinerary/api/` package.
- **M:** `GET /api/v1/health/` returns `{"status": "ok"}`; OpenAPI schema generated (`drf-spectacular` optional).
- **A:** Standard DRF install; web URLs unchanged.
- **R:** Mobile needs a stable JSON contract.
- **T:** Days 1–2.

### Goal 9.2 — JWT authentication

- **S:** `POST /api/v1/auth/register/`, `login/` (returns access + refresh), `token/refresh/`; mobile uses Bearer tokens; web keeps session cookies.
- **M:** Flutter can login and call authenticated endpoint; invalid token returns 401.
- **A:** `simplejwt` defaults + custom register serializer.
- **R:** Stateless auth for mobile.
- **T:** Days 2–4.

### Goal 9.3 — Core resource endpoints

- **S:** Serializers + viewsets for: `Trip`, `DayItinerary`, `StopBlock`, `ChecklistItem`, `Booking`, `StopPhoto` (read/write where web already allows).
- **M:** Documented endpoints match this matrix:

| Resource | Endpoints | Notes |
|----------|-----------|-------|
| Trips | `GET/POST /trips/`, `GET/PATCH/DELETE /trips/{id}/` | POST triggers async AI job (Phase 5) or sync v1 |
| Days | `GET /trips/{id}/days/`, `GET/PATCH /days/{id}/` | Includes `notes`, `theme` |
| Stops | `GET /days/{id}/stops/`, `PATCH /stops/{id}/`, `POST` reorder | Stops JSON for map |
| Checklist | `GET /trips/{id}/checklist/`, `POST /checklist/{id}/toggle/` | |
| Chat edit | `POST /trips/{id}/days/{n}/chat-edit/` | Returns mutation summary, not HTML |
| Weather | `GET /days/{id}/weather/` | JSON, not HTML fragment |
| Reviews | `GET /stops/{id}/reviews/` | Proxied photos only |
| Photos | `POST /stops/{id}/photos/`, `DELETE /photos/{id}/` | Multipart upload |

- **A:** Reuse `get_trip_for_user` from Phase 1 in all API permissions.
- **R:** Parity with web features mobile needs.
- **T:** Days 4–8.

### Goal 9.4 — Extract shared service layer

- **S:** Move mutation logic from `chat_edit` view into `itinerary/services/mutations.py`; web view and API view both call it.
- **M:** One implementation; web + API tests pass for same edit command.
- **A:** Refactor, not rewrite.
- **R:** Single maintenance path (one repo goal).
- **T:** Days 8–9.

### Goal 9.5 — API tests

- **S:** `itinerary/tests/test_api.py` — auth, ownership, CRUD, chat-edit allowlist.
- **M:** ≥15 API tests; included in CI.
- **A:** `APIClient` + JWT.
- **R:** Contract lock before Flutter.
- **T:** Days 9–10.

**Phase 9 exit criteria:** API documented; all endpoints ownership-scoped; CI green; web UI still works.

---

## Phase 10 — Flutter project foundation

**Duration:** 1 week  
**Outcome:** Runnable app shell with auth and navigation.

### Goal 10.1 — Bootstrap `mobile/` app

- **S:** `flutter create .` inside `mobile/`; package name `com.tripplanner.app` (adjust to your domain); min SDK iOS 15+, Android API 24+.
- **M:** `flutter analyze` and `flutter test` pass; app launches on iOS sim + Android emulator.
- **A:** Official Flutter create; commit platform folders.
- **R:** Monorepo mobile root.
- **T:** Day 1.

### Goal 10.2 — Networking & config

- **S:** Add `dio` + `flutter_secure_storage`; `lib/config/env.dart` with `--dart-define=API_BASE_URL=...` for dev/staging/prod.
- **M:** App calls `/api/v1/health/` and shows connected/disconnected on debug screen.
- **A:** Single `ApiClient` class with JWT interceptor (attach token, refresh on 401).
- **R:** All screens share one HTTP layer.
- **T:** Days 2–3.

### Goal 10.3 — State management & routing

- **S:** `flutter_riverpod` (or `bloc`) + `go_router`; routes: `/login`, `/register`, `/`, `/trips/:id`, `/trips/:id/day/:n`.
- **M:** Auth guard redirects unauthenticated users to login; back stack correct on Android.
- **A:** Common Flutter patterns.
- **R:** Scalable structure for 10+ screens.
- **T:** Days 4–5.

### Goal 10.4 — Auth screens

- **S:** Login + register screens matching web fields; persist tokens in secure storage; logout clears state.
- **M:** User can register, login, kill app, reopen — still authenticated.
- **A:** Material 3 UI aligned with web crimson palette from `static/css/index.css`.
- **R:** First real feature.
- **T:** Days 6–7.

**Phase 10 exit criteria:** Authenticated shell; CI workflow `mobile.yml` runs analyze + test.

---

## Phase 11 — Core companion screens

**Duration:** 2 weeks  
**Outcome:** Day-to-day trip use works on phone without opening the browser.

### Goal 11.1 — Trip list (dashboard)

- **S:** `TripsScreen` — list user trips, pull-to-refresh, FAB or button → create trip form.
- **M:** Shows same trips as web dashboard for logged-in user; empty state CTA.
- **A:** `GET /api/v1/trips/`.
- **R:** Primary entry point.
- **T:** Days 1–3.

### Goal 11.2 — Create trip (AI)

- **S:** Form: destination, days, start date, details; calls `POST /trips/`; loading UI with progress (poll job status if Phase 5 async exists).
- **M:** New trip appears in list; navigates to trip detail on success.
- **A:** Reuse API from Phase 9.
- **R:** Core web feature on mobile.
- **T:** Days 3–5.

### Goal 11.3 — Trip detail & day selector

- **S:** Horizontal day chips; swap day content; show theme, banner, costs.
- **M:** Day N matches web data for same trip.
- **A:** `GET /trips/{id}/days/`.
- **R:** Navigation pattern from web topnav.
- **T:** Days 5–7.

### Goal 11.4 — Stops list & map

- **S:** `flutter_map` (Leaflet-compatible) or `google_maps_flutter`; markers from stops JSON; tap marker → stop detail bottom sheet.
- **M:** Map markers match web coordinates; route polyline optional v1.1.
- **A:** `flutter_map` + OSM tiles avoids extra API key on mobile.
- **R:** Map is core trip planner value.
- **T:** Days 7–10.

### Goal 11.5 — Notes & checklist

- **S:** Debounced notes field (`PATCH /days/{id}/`); checklist with toggle.
- **M:** Edit on mobile appears on web after refresh (same DB).
- **A:** Simple forms.
- **R:** High-value low-effort companion features.
- **T:** Days 10–12.

### Goal 11.6 — AI chat edit

- **S:** Chat bottom sheet on day view; `POST .../chat-edit/`; refresh stops on success.
- **M:** “Add lunch near old city” updates stops like web chat.
- **A:** JSON API from Phase 9.4.
- **R:** Differentiator feature.
- **T:** Days 12–14.

**Phase 11 exit criteria:** Manual test script: create trip → view map → toggle checklist → chat edit → verify on web.

---

## Phase 12 — Mobile polish, offline & parity gaps

**Duration:** 1.5 weeks  
**Outcome:** Feels like a real app, not a mobile web wrapper.

### Goal 12.1 — Offline read cache

- **S:** `hive` or `drift` — cache last-viewed trip/days/stops; show offline banner; read-only when no network.
- **M:** Airplane mode: last opened trip still visible; edits queue or show clear error.
- **A:** Cache-on-fetch; no full offline-first sync in v1.
- **R:** Travel use case (spotty connectivity).
- **T:** Days 1–4.

### Goal 12.2 — Camera photo upload

- **S:** `image_picker` → `POST /stops/{id}/photos/`; gallery on stop detail.
- **M:** Photo taken on phone appears on web stop card.
- **A:** Multipart Dio upload.
- **R:** Web supports drag-drop; mobile uses camera.
- **T:** Days 4–6.

### Goal 12.3 — Weather & reviews widgets

- **S:** Day header weather chip; stop reviews sheet from API.
- **M:** JSON weather/reviews; no WebView hacks.
- **A:** Consumer of Phase 9 endpoints.
- **R:** Parity with web widgets.
- **T:** Days 6–8.

### Goal 12.4 — Calendar timeline (simplified)

- **S:** Read-only vertical timeline of stops by `start_time_of_day` (no drag-resize in v1).
- **M:** Stop order and times match web; drag-resize remains web-only until v2.
- **A:** `ListView` + time labels; defer complex gesture code.
- **R:** Avoid rebuilding full Alpine calendar in Flutter v1.
- **T:** Days 8–10.

### Goal 12.5 — Booking import (optional v1)

- **S:** Share sheet / paste text → `POST /trips/{id}/bookings/import/` when PDF API ready (web Phase 7).
- **M:** Paste confirmation text → booking created.
- **A:** Defer PDF picker until `pypdf` backend exists.
- **R:** Nice-to-have companion feature.
- **T:** Days 10+ (optional).

**Phase 12 exit criteria:** Offline read works; camera upload works; app usable on a real trip without laptop.

---

## Phase 13 — Release, CI & store submission

**Duration:** 1 week  
**Outcome:** Internal testing builds on TestFlight and Play Console.

### Goal 13.1 — Mobile CI

- **S:** `.github/workflows/mobile.yml` — `flutter analyze`, `flutter test`, optional `flutter build apk --debug` on PR.
- **M:** Red PR if analyze fails; matrix: stable Flutter channel.
- **A:** `subosito/flutter-action`.
- **R:** Same quality bar as Django CI.
- **T:** Days 1–2.

### Goal 13.2 — Environment flavors

- **S:** `--flavor dev|staging|prod` with distinct app IDs / names (“Trip Planner DEV”).
- **M:** Dev app points at localhost/staging; prod at deployed URL.
- **A:** Flutter flavors + dart-define.
- **R:** Safe testing without prod data risk.
- **T:** Days 2–4.

### Goal 13.3 — App icons, splash, store metadata

- **S:** Launcher icons, splash screen, privacy policy URL, store screenshots.
- **M:** `flutter_launcher_icons` + `flutter_native_splash` configured; 5 screenshots per platform.
- **A:** Tooling + assets in `mobile/assets/`.
- **R:** Store requirements.
- **T:** Days 4–5.

### Goal 13.4 — TestFlight & Play Internal Testing

- **S:** iOS archive + upload; Android App Bundle to internal track.
- **M:** 2 testers install from stores; login → view trip end-to-end.
- **A:** Requires Apple Developer + Google Play accounts (~$99/yr + $25).
- **R:** Real device validation.
- **T:** Days 5–7.

**Phase 13 exit criteria:** Internal store builds available; README documents mobile release process.

---

## Next phases

| Phase | Document |
|-------|----------|
| 14–18 Product competitiveness | [Annex C: PRODUCT_FEATURES.md](./PRODUCT_FEATURES.md) |
| Unified timeline & metrics | [MASTER_PLAN.md](./MASTER_PLAN.md) |

## Deferred to Annex C or later

- Push notifications → [Phase 17](./PRODUCT_FEATURES.md#phase-17--offline-documents--push)
- Full group collab → [Phase 15](./PRODUCT_FEATURES.md#phase-15--group-collaboration--voting)
- Flutter web replacing Django templates
- Apple Watch / Android Wear

## Maintenance model (one repo)

| Change type | Touch |
|-------------|--------|
| New model field | Django migration → serializer → Flutter model + UI |
| New business rule | `itinerary/services/` only; web + API call it |
| AI prompt change | `llm.py` only |
| Web-only UX | `templates/` only |
| Mobile-only UX | `mobile/lib/` only |

**Rule:** No duplicate business logic in Flutter — validate on API, display in app.
