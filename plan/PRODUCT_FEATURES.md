# Annex C — Product Features (Market Competitive)

**Parent:** [MASTER_PLAN.md](./MASTER_PLAN.md) · Phases 14–18 · Milestones M3–M5

These phases close the gap vs Wanderlog, TripIt, MonkeyTravel, and TripProf. They assume **Annex A Phase 1** (auth) and **Annex B Phase 9** (API) are complete.

---

## Phase 14 — Booking email import

**Duration:** 1 week  
**Milestone:** M4 v1.5 (can start at M2 Beta)  
**User journey:** Organize → import confirmations without manual entry

### Goal 14.1 — Inbound email parser

- **S:** Unique forwarding address per user (`trips+{token}@yourdomain.com`) or Gmail OAuth; parse flight/hotel/activity confirmations into `Booking` rows.
- **M:** Forward sample TripIt-style email → booking appears on correct trip within 60s; ≥90% accuracy on test corpus of 10 emails.
- **A:** `mail-parser` + `LLMService.parse_booking` fallback for ambiguous formats.
- **R:** TripIt/Wanderlog table stakes.
- **T:** Days 1–4.

### Goal 14.2 — Trip matching & review UI

- **S:** Web + mobile UI to confirm imported booking, assign to trip/day, merge duplicates.
- **M:** User can reject/correct import before save.
- **A:** HTMX + API endpoint `POST /api/v1/bookings/import/confirm/`.
- **R:** Prevents bad auto-imports.
- **T:** Days 5–7.

**Exit criteria:** Email import works for flight + hotel; documented in README.

---

## Phase 15 — Group collaboration & voting

**Duration:** 2 weeks  
**Milestone:** M3 v1.0 (differentiator)  
**User journey:** Plan → invite group → vote on activities

### Goal 15.1 — Trip membership model

- **S:** `TripMember` model: `trip`, `user` (nullable for link guests), `role` (owner/editor/voter/viewer), `invite_token`, `joined_at`.
- **M:** Owner invites by email/link; viewer cannot edit stops; editor can.
- **A:** Migration + permissions extend `get_trip_for_user` to members.
- **R:** MonkeyTravel / Wanderlog collab.
- **T:** Days 1–3.

### Goal 15.2 — Real-time sync

- **S:** Django Channels or SSE for trip updates; mobile/web refresh on member edit.
- **M:** Edit on web visible on mobile within 3s on same trip.
- **A:** Start with SSE + HTMX trigger; upgrade to WebSockets if needed.
- **R:** "Google Docs for trips" expectation.
- **T:** Days 4–6.

### Goal 15.3 — Activity voting

- **S:** `StopVote` model: stop, member, choice (love/flexible/concerns/no); consensus score on stop card.
- **M:** 4-level vote matches MonkeyTravel; organizer sees participation %.
- **A:** API + web partial + Flutter bottom sheet.
- **R:** Group decision wedge vs Wanderlog.
- **T:** Days 7–10.

### Goal 15.4 — Proposals

- **S:** Member proposes new stop (pending); group votes; organizer approves → CREATE stop.
- **M:** Proposal flow e2e test on web + mobile.
- **A:** Extends chat-edit or separate proposal API.
- **R:** Reduces organizer bottleneck.
- **T:** Days 10–14.

**Exit criteria:** 2+ users on same trip with roles; voting changes visible everywhere.

---

## Phase 16 — Expenses, split & export

**Duration:** 1.5 weeks  
**Milestone:** M4 v1.5  
**User journey:** Organize budget → on-trip logging → settle up

### Goal 16.1 — Expense ledger

- **S:** `Expense` model: trip, payer, amount, currency, category, split_among members, receipt image optional.
- **M:** Add expense on mobile; totals match trip budget view.
- **A:** Link to existing `Trip.conversion_rate`.
- **R:** Lambus/Stippl parity.
- **T:** Days 1–4.

### Goal 16.2 — Split & settle

- **S:** "Who owes whom" settlement view; mark settled.
- **M:** 3-person split matches manual calculation on test scenario.
- **A:** Standard split algorithm; no payment processing v1.
- **R:** Replaces Splitwise sidecar.
- **T:** Days 5–7.

### Goal 16.3 — PDF & share export

- **S:** Export itinerary + bookings to PDF; public read-only share link (expiring).
- **M:** PDF renders day-by-day plan with map thumbnail; share link works without login.
- **A:** `weasyprint` or headless browser; tokenized share URLs.
- **R:** MonkeyTravel/Layla export expectation.
- **T:** Days 8–10.

**Exit criteria:** Group trip expense split demo; PDF export for 5-day trip.

---

## Phase 17 — Offline, documents & push

**Duration:** 2 weeks  
**Milestone:** M4 v1.5 complete  
**User journey:** Pre-trip download → on-trip without signal

### Goal 17.1 — Offline trip pack (mobile)

- **S:** `GET /api/v1/trips/{id}/offline-pack/` returns JSON blob + cached image URLs; Flutter stores in Hive.
- **M:** Airplane mode: today view + map tiles + checklist readable.
- **A:** Extend Annex B Phase 12 cache; server bundles trip graph.
- **R:** Wanderlog Pro / TripProf free offline.
- **T:** Days 1–5.

### Goal 17.2 — Document vault

- **S:** `TripDocument` model + upload UI for passport, visa, insurance, PDFs; encrypted at rest in prod.
- **M:** Upload PDF; second trip member can view (role-gated).
- **A:** Reuse `Booking.attachment` patterns; generalize.
- **R:** Lambus/TripProf document storage.
- **T:** Days 6–9.

### Goal 17.3 — Smart checklists

- **S:** AI-generated packing list from destination, dates, attendees, activities; assign items to members.
- **M:** Baku summer family trip → list includes sunscreen, kid items; editable.
- **A:** LLM prompt + `ChecklistItem` categories.
- **R:** Stippl/TripProf smart packing.
- **T:** Days 9–12.

### Goal 17.4 — Push notifications

- **S:** FCM/APNs; reminders: trip starts in 7 days, checklist incomplete, vote needed.
- **M:** Test push received on iOS + Android for one trigger.
- **A:** `firebase_messaging` in Flutter; Django cron + send API.
- **R:** TripIt Pro flight alerts lite.
- **T:** Days 12–14.

**Exit criteria:** Offline pack on device; document upload; one push type live.

---

## Phase 18 — Routes, guides & monetization

**Duration:** 2 weeks  
**Milestone:** M5 v2.0  
**User journey:** Polish + revenue

### Goal 18.1 — Route optimization

- **S:** Integrate OSRM or Google Directions between day stops; show travel time on map.
- **M:** Reorder suggestion reduces total day travel time on 6-stop test day.
- **A:** Server-side route API; optional "optimize day" button.
- **R:** Wanderlog road-trip strength.
- **T:** Days 1–5.

### Goal 18.2 — Destination guide sections

- **S:** AI-generated guide blocks per trip: transport, safety, food, culture, kid tips (5–10 sections).
- **M:** Guide differs for family vs solo same destination.
- **A:** Cached in `Trip.guide_json`; LLM with structured schema.
- **R:** TripProf 60-section depth (start smaller).
- **T:** Days 5–9.

### Goal 18.3 — Verified places pipeline

- **S:** Replace mock reviews when API missing; Google Places + cache TTL; flag stale data in UI.
- **M:** Zero mock data when `GOOGLE_PLACES_API_KEY` set; "Demo data" badge when not.
- **A:** Completes audit item on honest mocks.
- **R:** MonkeyTravel "real hours, real ratings" trust.
- **T:** Days 7–10.

### Goal 18.4 — Pro subscription

- **S:** Stripe Checkout; enforce limits on free tier (see MASTER_PLAN §7).
- **M:** Upgrade flow works; Pro unlocks offline + email import in feature flags.
- **A:** `django-stripe` or Stripe API; `Trip`/`User` plan field.
- **R:** Sustainable vs free-only MonkeyTravel.
- **T:** Days 10–14.

**Exit criteria:** Route times on map; guide tab on trip; Stripe test mode subscription works.

---

## Phase 14–18 summary

| Phase | Duration | Competitive target |
|-------|----------|-------------------|
| 14 | 1 week | TripIt email import |
| 15 | 2 weeks | MonkeyTravel voting + Wanderlog collab |
| 16 | 1.5 weeks | Lambus expenses + PDF export |
| 17 | 2 weeks | TripProf offline + docs + push |
| 18 | 2 weeks | Wanderlog routes + TripProf guides + revenue |

**Total:** ~8.5 weeks part-time after M3 v1.0.
