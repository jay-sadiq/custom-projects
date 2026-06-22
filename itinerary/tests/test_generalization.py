from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from itinerary.models import DayItinerary, StopBlock, Trip, TripAttendee, TripCreationJob
from itinerary.services.attendees import parse_attendees_from_request


MOCK_ITINERARY = {
    "title": "Barcelona Adventure",
    "currency": "EUR",
    "conversion_rate": 1.0,
    "days": [
        {
            "day_number": 1,
            "theme": "Arrival",
            "early_start_banner": "",
            "stops": [
                {
                    "sequence_order": 1,
                    "time_label": "10:00 AM",
                    "title": "Gothic Quarter",
                    "description": "Historic center",
                    "latitude": 41.38,
                    "longitude": 2.17,
                    "zoom_level": 15,
                    "cost_local": 0.0,
                    "cost_usd": 0.0,
                    "tags": ["Landmark"],
                    "color_hex": "#27AE60",
                }
            ],
        }
    ],
}


class AttendeeParsingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="planner", password="complexpass123")

    def test_parse_attendees_from_form_fields(self):
        class FakePost:
            def getlist(self, key):
                if key == "attendee_name":
                    return ["Alice", "Ben"]
                if key == "attendee_role":
                    return ["Parent", "Child (6yo)"]
                return []

        attendees = parse_attendees_from_request(FakePost(), self.user)
        self.assertEqual(
            attendees,
            [
                {"name": "Alice", "role": "Parent"},
                {"name": "Ben", "role": "Child (6yo)"},
            ],
        )

    def test_empty_attendees_defaults_to_user(self):
        class FakePost:
            def getlist(self, _key):
                return []

        attendees = parse_attendees_from_request(FakePost(), self.user)
        self.assertEqual(attendees, [{"name": "planner", "role": "Lead traveler"}])

    @override_settings(TRIP_CREATION_SYNC=True)
    @patch(
        "itinerary.services.trip_creation.LLMService.generate_itinerary",
        return_value=MOCK_ITINERARY,
    )
    def test_create_trip_uses_submitted_attendees_not_heuristic(self, _mock_llm):
        client = Client()
        client.force_login(self.user)
        response = client.post(
            reverse("create_trip"),
            {
                "destination": "Barcelona",
                "days_count": 1,
                "start_date": "2026-11-01",
                "details": "Family trip with toddler",
                "attendee_name": ["Morgan", "Jordan"],
                "attendee_role": ["Parent", "Toddler"],
            },
        )
        self.assertEqual(response.status_code, 200)
        trip = Trip.objects.get(destination="Barcelona", user=self.user)
        names = list(trip.attendees.order_by("id").values_list("name", flat=True))
        self.assertEqual(names, ["Morgan", "Jordan"])
        self.assertFalse(any("Abdul" in name for name in names))


class SeedCommandTestCase(TestCase):
    def test_seed_baku_assigns_trip_to_specified_user(self):
        owner = User.objects.create_user(username="jawad", password="complexpass123")
        other = User.objects.create_user(username="other", password="complexpass123")

        call_command("seed_baku", user="jawad")

        trip = Trip.objects.get(destination="Baku, Azerbaijan")
        self.assertEqual(trip.user, owner)
        self.assertFalse(Trip.objects.filter(user=other).exists())


class NeutralCopyTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="neutral",
            password="complexpass123",
            first_name="Sam",
        )
        self.client.force_login(self.user)
        self.trip = Trip.objects.create(
            user=self.user,
            title="Coastal Trip",
            destination="Lisbon, Portugal",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 3),
        )
        DayItinerary.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(2026, 9, 1),
            theme="Explore",
        )

    def test_trip_detail_uses_neutral_greeting(self):
        response = self.client.get(reverse("trip_detail", args=[self.trip.id]))
        self.assertContains(response, "Hi Sam!")
        self.assertNotContains(response, "Abdul Jawad")

    def test_dashboard_has_no_hardcoded_flag_prefix(self):
        response = self.client.get(reverse("dashboard"))
        self.assertNotContains(response, "🇦🇿")

    @patch("itinerary.views.get_stop_reviews_data")
    def test_stop_reviews_labels_demo_data(self, mock_data):
        day = self.trip.days.get(day_number=1)
        stop = StopBlock.objects.create(
            day=day,
            sequence_order=1,
            time_label="9:00 AM",
            title="Belém Tower",
            description="Landmark",
            latitude=38.69,
            longitude=-9.21,
        )
        mock_data.return_value = {
            "stop_id": stop.id,
            "rating": 4.5,
            "reviews": [],
            "photos": [],
            "photo_urls": [],
            "is_demo_data": True,
        }
        response = self.client.get(reverse("get_stop_reviews", args=[stop.id]))
        self.assertContains(response, "Demo data")
        self.assertContains(response, "Estimated Rating")
