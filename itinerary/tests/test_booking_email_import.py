from datetime import date
from email.message import EmailMessage
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from itinerary.models import Booking, BookingImportDraft, Trip, UserProfile
from itinerary.services.booking_import import (
    confirm_import_draft,
    create_import_draft,
    extract_text_from_email,
    extract_token_from_recipient,
    reject_import_draft,
    suggest_trip_for_user,
)


class EmailParseHelpersTestCase(TestCase):
    def test_extract_token_from_recipient(self):
        self.assertEqual(
            extract_token_from_recipient("trips+abc_TOKEN-1@bookings.example.com"),
            "abc_TOKEN-1",
        )
        self.assertIsNone(extract_token_from_recipient("someone@example.com"))

    def test_extract_text_from_plain_email(self):
        msg = EmailMessage()
        msg["Subject"] = "Your BA123 flight"
        msg["From"] = "airline@example.com"
        msg["To"] = "trips+tok@bookings.example.com"
        msg.set_content("Confirmation ABC123 for BA123 to Lisbon on 2026-08-02.")
        extracted = extract_text_from_email(msg.as_bytes())
        self.assertEqual(extracted["subject"], "Your BA123 flight")
        self.assertIn("ABC123", extracted["body"])
        self.assertIn("Your BA123 flight", extracted["text"])


class TripMatchingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="traveler", password="complexpass123")
        self.trip = Trip.objects.create(
            user=self.user,
            title="Lisbon",
            destination="Lisbon",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 5),
        )
        Trip.objects.create(
            user=self.user,
            title="Tokyo",
            destination="Tokyo",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 10),
        )

    def test_suggest_trip_by_start_time_overlap(self):
        parsed = {"start_time": "2026-08-02T10:00:00"}
        suggested = suggest_trip_for_user(self.user, parsed)
        self.assertEqual(suggested.id, self.trip.id)


class BookingImportDraftFlowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="traveler", password="complexpass123")
        self.trip = Trip.objects.create(
            user=self.user,
            title="Lisbon",
            destination="Lisbon",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 5),
        )

    @patch(
        "itinerary.services.booking_import.LLMService.parse_booking",
        return_value={
            "booking_type": "Flight",
            "title": "BA123 to Lisbon",
            "confirmation_number": "ABC123",
            "details": "Window seat",
            "start_time": "2026-08-02T09:00:00",
            "end_time": None,
            "cost": None,
        },
    )
    def test_create_and_confirm_draft(self, _mock_parse):
        draft = create_import_draft(
            user=self.user,
            raw_text="Flight BA123 confirmation ABC123",
            source="paste",
        )
        self.assertEqual(draft.status, BookingImportDraft.STATUS_PENDING)
        self.assertEqual(draft.suggested_trip_id, self.trip.id)

        booking = confirm_import_draft(draft, trip=self.trip)
        draft.refresh_from_db()
        self.assertEqual(draft.status, BookingImportDraft.STATUS_CONFIRMED)
        self.assertEqual(booking.title, "BA123 to Lisbon")
        self.assertEqual(Booking.objects.filter(trip=self.trip).count(), 1)

    @patch(
        "itinerary.services.booking_import.LLMService.parse_booking",
        return_value={
            "booking_type": "Hotel",
            "title": "Hotel Rossio",
            "confirmation_number": "H999",
            "details": "",
            "start_time": None,
            "end_time": None,
            "cost": None,
        },
    )
    def test_confirm_merges_duplicate_confirmation(self, _mock_parse):
        existing = Booking.objects.create(
            trip=self.trip,
            booking_type="Hotel",
            title="Old title",
            confirmation_number="H999",
            details="old",
        )
        draft = create_import_draft(user=self.user, raw_text="Hotel H999", source="paste")
        booking = confirm_import_draft(
            draft,
            trip=self.trip,
            overrides={"title": "Hotel Rossio", "details": "updated"},
        )
        self.assertEqual(booking.id, existing.id)
        self.assertEqual(Booking.objects.filter(trip=self.trip).count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.title, "Hotel Rossio")
        self.assertEqual(existing.details, "updated")

    def test_reject_draft(self):
        draft = BookingImportDraft.objects.create(
            user=self.user,
            raw_text="x",
            parsed_json={},
            status=BookingImportDraft.STATUS_PENDING,
        )
        reject_import_draft(draft)
        draft.refresh_from_db()
        self.assertEqual(draft.status, BookingImportDraft.STATUS_REJECTED)


@override_settings(
    BOOKING_IMPORT_EMAIL_DOMAIN="bookings.test",
    INBOUND_EMAIL_WEBHOOK_SECRET="secret-test",
)
class InboundEmailAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="traveler", password="complexpass123")
        self.profile = UserProfile.objects.create(user=self.user, email_import_token="tok123")
        Trip.objects.create(
            user=self.user,
            title="Lisbon",
            destination="Lisbon",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 5),
        )

    def test_forwarding_address_endpoint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("booking-import-address"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["forwarding_address"],
            "trips+tok123@bookings.test",
        )

    @patch(
        "itinerary.services.booking_import.LLMService.parse_booking",
        return_value={
            "booking_type": "Flight",
            "title": "TAP to LIS",
            "confirmation_number": "T1",
            "details": "",
            "start_time": "2026-08-03T12:00:00",
            "end_time": None,
            "cost": None,
        },
    )
    def test_inbound_webhook_creates_draft(self, _mock_parse):
        msg = EmailMessage()
        msg["Subject"] = "Flight confirmation"
        msg["From"] = "airline@example.com"
        msg["To"] = "trips+tok123@bookings.test"
        msg.set_content("Your flight TAP confirmation T1")
        response = self.client.post(
            reverse("inbound-email-webhook"),
            data={"raw": msg.as_string()},
            format="json",
            HTTP_X_WEBHOOK_SECRET="secret-test",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "pending")
        self.assertEqual(BookingImportDraft.objects.filter(user=self.user).count(), 1)

    def test_inbound_webhook_rejects_bad_secret(self):
        response = self.client.post(
            reverse("inbound-email-webhook"),
            data={"text": "hello", "to": "trips+tok123@bookings.test"},
            format="json",
            HTTP_X_WEBHOOK_SECRET="wrong",
        )
        self.assertEqual(response.status_code, 403)

    @patch(
        "itinerary.services.booking_import.LLMService.parse_booking",
        return_value={
            "booking_type": "Hotel",
            "title": "Hotel",
            "confirmation_number": "H1",
            "details": "",
            "start_time": None,
            "end_time": None,
            "cost": None,
        },
    )
    def test_preview_confirm_api(self, _mock_parse):
        self.client.force_authenticate(user=self.user)
        trip = Trip.objects.get(user=self.user)
        preview = self.client.post(
            reverse("booking-import-draft-preview"),
            {"text": "Hotel confirmation H1"},
            format="json",
        )
        self.assertEqual(preview.status_code, 201)
        draft_id = preview.json()["id"]
        confirm = self.client.post(
            reverse("booking-import-draft-confirm"),
            {"draft_id": draft_id, "trip_id": trip.id},
            format="json",
        )
        self.assertEqual(confirm.status_code, 200)
        self.assertEqual(confirm.json()["booking"]["confirmation_number"], "H1")


class BookingImportWebTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="traveler", password="complexpass123")
        self.client.login(username="traveler", password="complexpass123")
        self.trip = Trip.objects.create(
            user=self.user,
            title="Lisbon",
            destination="Lisbon",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 5),
        )

    def test_inbox_page_loads(self):
        response = self.client.get(reverse("booking_imports_inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Booking import inbox")
        self.assertContains(response, "trips+")

    @patch(
        "itinerary.services.booking_import.LLMService.parse_booking",
        return_value={
            "booking_type": "Flight",
            "title": "BA123",
            "confirmation_number": "Z9",
            "details": "",
            "start_time": None,
            "end_time": None,
            "cost": None,
        },
    )
    def test_web_preview_and_confirm(self, _mock_parse):
        preview = self.client.post(
            reverse("booking_import_preview"),
            {"paste_text": "Flight Z9", "trip_id": self.trip.id},
        )
        self.assertEqual(preview.status_code, 200)
        draft = BookingImportDraft.objects.get(user=self.user)
        confirm = self.client.post(
            reverse("booking_import_confirm", args=[draft.id]),
            {"trip_id": self.trip.id},
        )
        self.assertEqual(confirm.status_code, 200)
        self.assertTrue(Booking.objects.filter(trip=self.trip, confirmation_number="Z9").exists())
