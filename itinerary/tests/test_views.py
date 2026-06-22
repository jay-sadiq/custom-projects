from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from itinerary.models import DayItinerary, StopBlock, Trip


MOCK_ITINERARY = {
    "title": "Lisbon Adventure",
    "currency": "EUR",
    "conversion_rate": 1.0,
    "days": [
        {
            "day_number": 1,
            "theme": "Arrival Day",
            "early_start_banner": "",
            "stops": [
                {
                    "sequence_order": 1,
                    "time_label": "10:00 AM — City center",
                    "title": "Praça do Comércio",
                    "description": "Waterfront square",
                    "latitude": 38.7078,
                    "longitude": -9.1366,
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


class AuthFlowTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {"username": "newuser", "password1": "complexpass123", "password2": "complexpass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertEqual(response.url, reverse("dashboard"))

    def test_login_with_valid_credentials(self):
        User.objects.create_user(username="alice", password="complexpass123")
        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "complexpass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))

    def test_login_with_invalid_credentials_shows_form(self):
        User.objects.create_user(username="alice", password="complexpass123")
        response = self.client.post(
            reverse("login"),
            {"username": "alice", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects_to_login(self):
        User.objects.create_user(username="alice", password="complexpass123")
        self.client.login(username="alice", password="complexpass123")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))


class TripViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="traveler", password="complexpass123")
        self.client.login(username="traveler", password="complexpass123")
        self.trip = Trip.objects.create(
            user=self.user,
            title="My Trip",
            destination="Lisbon",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 3),
        )
        self.day = DayItinerary.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(2026, 8, 1),
            theme="Explore",
        )
        self.stop_one = StopBlock.objects.create(
            day=self.day,
            sequence_order=1,
            time_label="9:00 AM",
            title="Stop A",
            description="First",
            latitude=38.71,
            longitude=-9.13,
        )
        self.stop_two = StopBlock.objects.create(
            day=self.day,
            sequence_order=2,
            time_label="11:00 AM",
            title="Stop B",
            description="Second",
            latitude=38.72,
            longitude=-9.14,
        )

    @patch("itinerary.views.LLMService.generate_itinerary", return_value=MOCK_ITINERARY)
    def test_create_trip_persists_itinerary(self, _mock_llm):
        response = self.client.post(
            reverse("create_trip"),
            {
                "destination": "Lisbon",
                "days_count": 1,
                "start_date": "2026-09-01",
                "details": "Solo trip",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Redirect", response.headers)
        trip = Trip.objects.get(destination="Lisbon", user=self.user, title="Lisbon Adventure")
        self.assertEqual(trip.days.count(), 1)
        self.assertEqual(trip.days.first().stops.count(), 1)

    def test_create_trip_requires_destination_and_date(self):
        response = self.client.post(
            reverse("create_trip"),
            {"destination": "", "start_date": ""},
        )
        self.assertEqual(response.status_code, 400)

    def test_trip_detail_renders_for_owner(self):
        response = self.client.get(reverse("trip_detail", args=[self.trip.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Trip")

    def test_day_detail_renders_partial(self):
        response = self.client.get(
            reverse("day_detail", args=[self.trip.id, self.day.day_number])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stop A")

    def test_save_notes_persists_text(self):
        response = self.client.post(
            reverse("save_notes", args=[self.day.id]),
            {"notes": "Remember museum tickets"},
        )
        self.assertEqual(response.status_code, 200)
        self.day.refresh_from_db()
        self.assertEqual(self.day.notes, "Remember museum tickets")

    def test_reorder_stops_updates_sequence(self):
        response = self.client.post(
            reverse("reorder_stops", args=[self.trip.id, self.day.day_number]),
            {"stop_ids": f"[{self.stop_two.id}, {self.stop_one.id}]"},
        )
        self.assertEqual(response.status_code, 200)
        self.stop_one.refresh_from_db()
        self.stop_two.refresh_from_db()
        self.assertEqual(self.stop_two.sequence_order, 1)
        self.assertEqual(self.stop_one.sequence_order, 2)

    def test_get_stops_json_returns_map_data(self):
        response = self.client.get(
            reverse("get_stops_json", args=[self.trip.id, self.day.day_number])
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["title"], "Stop A")

    @patch("itinerary.views.LLMService.parse_booking")
    def test_parse_booking_import_creates_booking(self, mock_parse):
        mock_parse.return_value = {
            "booking_type": "Flight",
            "title": "LIS → OPO",
            "confirmation_number": "ABC123",
            "details": "Morning flight",
            "cost": 120.0,
        }
        response = self.client.post(
            reverse("parse_booking_pdf", args=[self.trip.id]),
            {"paste_text": "Flight confirmation ABC123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ABC123")
        self.assertEqual(self.trip.bookings.count(), 1)

    def test_edit_stop_get_renders_form(self):
        response = self.client.get(
            reverse("edit_stop", args=[self.stop_one.id]),
            {"index": 0},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stop A")

    def test_edit_stop_post_updates_fields(self):
        response = self.client.post(
            reverse("edit_stop", args=[self.stop_one.id]),
            {
                "index": 0,
                "title": "Renamed Stop",
                "time_label": "9:30 AM",
                "description": "Updated",
                "latitude": "38.71",
                "longitude": "-9.13",
                "zoom_level": "15",
                "cost_local": "5.00",
                "cost_usd": "3.00",
                "meal_type": "",
                "meal_name": "",
                "meal_desc": "",
                "meal_price_label": "",
                "meal_recommendation": "",
                "tags_raw": "Tag1",
                "color_hex": "#E67E22",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.stop_one.refresh_from_db()
        self.assertEqual(self.stop_one.title, "Renamed Stop")

    def test_delete_stop_removes_and_reorders(self):
        response = self.client.post(reverse("delete_stop", args=[self.stop_two.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StopBlock.objects.filter(id=self.stop_two.id).exists())
        self.stop_one.refresh_from_db()
        self.assertEqual(self.stop_one.sequence_order, 1)

    def test_edit_day_updates_theme(self):
        response = self.client.post(
            reverse("edit_day", args=[self.day.id]),
            {"theme": "New Theme", "early_start_banner": "Early!"},
        )
        self.assertEqual(response.status_code, 200)
        self.day.refresh_from_db()
        self.assertEqual(self.day.theme, "New Theme")

    def test_update_stop_times_returns_json(self):
        response = self.client.post(
            reverse("update_stop_times", args=[self.stop_one.id]),
            {"start_time": "09:00", "end_time": "10:30"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.stop_one.refresh_from_db()
        self.assertEqual(str(self.stop_one.start_time_of_day), "09:00:00")

    def test_view_stop_renders_card(self):
        response = self.client.get(
            reverse("view_stop", args=[self.stop_one.id]),
            {"index": 0},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stop A")
