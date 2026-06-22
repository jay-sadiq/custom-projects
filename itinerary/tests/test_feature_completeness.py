from datetime import datetime
from io import BytesIO

from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from pypdf import PdfWriter

from itinerary.models import Booking, DayItinerary, StopBlock, Trip
from itinerary.services.booking_import import parse_booking_datetime
from itinerary.services.llm import LLMService, LLMUnavailableError
from itinerary.services.pdf import extract_text_from_pdf
from itinerary.validators import UploadValidationError, validate_image_upload, validate_pdf_upload


def _make_pdf(text: str) -> SimpleUploadedFile:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return SimpleUploadedFile("booking.pdf", buffer.getvalue(), content_type="application/pdf")


class PdfExtractionTestCase(TestCase):
    def test_rejects_non_pdf_extension(self):
        upload = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
        with self.assertRaises(UploadValidationError):
            validate_pdf_upload(upload)

    def test_rejects_invalid_pdf_header(self):
        upload = SimpleUploadedFile("fake.pdf", b"not-a-pdf", content_type="application/pdf")
        with self.assertRaises(UploadValidationError):
            validate_pdf_upload(upload)

    @override_settings(MAX_PDF_UPLOAD_BYTES=10)
    def test_rejects_oversized_pdf(self):
        upload = SimpleUploadedFile("big.pdf", b"%PDF-" + b"x" * 20, content_type="application/pdf")
        with self.assertRaises(UploadValidationError):
            validate_pdf_upload(upload)

    def test_extract_text_from_pdf_returns_empty_for_blank_page(self):
        text = extract_text_from_pdf(_make_pdf(""))
        self.assertEqual(text, "")


class BookingImportTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="booker", password="complexpass123")
        self.client.force_login(self.user)
        self.trip = Trip.objects.create(
            user=self.user,
            title="Trip",
            destination="Lisbon",
            start_date=datetime(2026, 8, 1).date(),
            end_date=datetime(2026, 8, 3).date(),
        )

    def test_parse_booking_datetime_parses_iso_string(self):
        parsed = parse_booking_datetime("2026-08-01T10:30:00")
        self.assertEqual(parsed.year, 2026)
        self.assertEqual(parsed.hour, 10)

    def test_parse_booking_import_persists_times(self):
        from unittest.mock import patch

        mock_data = {
            "booking_type": "Flight",
            "title": "LIS → OPO",
            "confirmation_number": "ABC123",
            "details": "Morning flight",
            "start_time": "2026-08-01T08:00:00",
            "end_time": "2026-08-01T09:15:00",
            "cost": 120.0,
        }
        with patch("itinerary.views.LLMService.parse_booking", return_value=mock_data):
            response = self.client.post(
                reverse("parse_booking_pdf", args=[self.trip.id]),
                {"paste_text": "Flight ABC123"},
            )
        self.assertEqual(response.status_code, 200)
        booking = Booking.objects.get(trip=self.trip)
        self.assertIsNotNone(booking.start_time)
        self.assertIsNotNone(booking.end_time)
        self.assertContains(response, "Starts:")


class UploadValidationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="uploader", password="complexpass123")
        self.client.force_login(self.user)
        self.trip = Trip.objects.create(
            user=self.user,
            title="Trip",
            destination="Lisbon",
            start_date=datetime(2026, 8, 1).date(),
            end_date=datetime(2026, 8, 3).date(),
        )
        self.day = DayItinerary.objects.create(
            trip=self.trip,
            day_number=1,
            date=datetime(2026, 8, 1).date(),
            theme="Explore",
        )
        self.stop = StopBlock.objects.create(
            day=self.day,
            sequence_order=1,
            time_label="9:00 AM",
            title="Stop",
            description="",
            latitude=0,
            longitude=0,
        )

    @override_settings(MAX_IMAGE_UPLOAD_BYTES=32)
    def test_rejects_oversized_image_upload(self):
        upload = SimpleUploadedFile(
            "photo.jpg",
            b"\xff\xd8\xff" + b"x" * 64,
            content_type="image/jpeg",
        )
        with self.assertRaises(UploadValidationError):
            validate_image_upload(upload)

    def test_rejects_invalid_image_bytes(self):
        upload = SimpleUploadedFile(
            "photo.jpg",
            b"not-an-image",
            content_type="image/jpeg",
        )
        response = self.client.post(
            reverse("upload_stop_photo", args=[self.stop.id]),
            {"photo": upload},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")


class LLMDegradationTestCase(TestCase):
    @override_settings(GEMINI_API_KEY="")
    @patch.object(LLMService, "_query_ollama", return_value=None)
    def test_query_raises_clear_error_when_no_providers(self, _mock_ollama):
        with self.assertRaises(LLMUnavailableError) as ctx:
            LLMService.query("system", "user")
        self.assertIn("AI is unavailable", str(ctx.exception))


class AdminRegistrationTestCase(TestCase):
    def test_trip_and_booking_registered_in_admin(self):
        from django.contrib import admin

        self.assertIn(Trip, admin.site._registry)
        self.assertIn(Booking, admin.site._registry)
