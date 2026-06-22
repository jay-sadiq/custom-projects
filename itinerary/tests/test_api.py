from datetime import date, datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from itinerary.models import (
    Booking,
    ChecklistItem,
    DayItinerary,
    StopBlock,
    Trip,
    TripCreationJob,
)


class APIHealthTestCase(APITestCase):
    def test_health_endpoint_is_public(self):
        response = self.client.get(reverse("api-health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class APIAuthTestCase(APITestCase):
    def test_register_creates_user(self):
        response = self.client.post(
            reverse("api-register"),
            {"username": "apiuser", "password": "complexpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="apiuser").exists())

    def test_login_returns_jwt_tokens(self):
        User.objects.create_user(username="apiuser", password="complexpass123")
        response = self.client.post(
            reverse("api-login"),
            {"username": "apiuser", "password": "complexpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_protected_endpoint_requires_auth(self):
        response = self.client.get(reverse("trip-list"))
        self.assertEqual(response.status_code, 401)


class APITripOwnershipTestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="complexpass123")
        self.other = User.objects.create_user(username="other", password="complexpass123")
        self.trip = Trip.objects.create(
            user=self.owner,
            title="Owner Trip",
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
        self.stop = StopBlock.objects.create(
            day=self.day,
            sequence_order=1,
            time_label="9:00 AM",
            title="Museum",
            description="Visit",
            latitude=38.71,
            longitude=-9.13,
        )
        self.checklist = ChecklistItem.objects.create(
            trip=self.trip,
            category="Packing",
            item_text="Passport",
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_owner_can_list_own_trips(self):
        self._auth(self.owner)
        response = self.client.get(reverse("trip-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_other_user_cannot_retrieve_trip(self):
        self._auth(self.other)
        response = self.client.get(reverse("trip-detail", args=[self.trip.id]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_list_trip_days(self):
        self._auth(self.owner)
        response = self.client.get(reverse("trip-days", args=[self.trip.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_owner_can_list_day_stops(self):
        self._auth(self.owner)
        response = self.client.get(reverse("day-stops", args=[self.day.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["title"], "Museum")

    def test_owner_can_get_map_stops_json(self):
        self._auth(self.owner)
        response = self.client.get(
            reverse("day-stops", args=[self.day.id]),
            {"map": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("latitude", response.json()[0])

    def test_owner_can_toggle_checklist_item(self):
        self._auth(self.owner)
        response = self.client.post(reverse("checklist-item-toggle", args=[self.checklist.id]))
        self.assertEqual(response.status_code, 200)
        self.checklist.refresh_from_db()
        self.assertTrue(self.checklist.is_completed)

    def test_other_user_cannot_toggle_checklist_item(self):
        self._auth(self.other)
        response = self.client.post(reverse("checklist-item-toggle", args=[self.checklist.id]))
        self.assertEqual(response.status_code, 404)

    @patch("itinerary.api.views.get_stop_reviews_data")
    def test_owner_can_get_stop_reviews(self, mock_reviews):
        mock_reviews.return_value = {
            "stop_id": self.stop.id,
            "rating": 4.5,
            "reviews": [],
            "photos": [],
            "photo_urls": [],
            "is_demo_data": True,
        }
        self._auth(self.owner)
        response = self.client.get(reverse("stop-reviews", args=[self.stop.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_demo_data"])

    def test_owner_can_get_day_weather_json(self):
        self._auth(self.owner)
        response = self.client.get(reverse("day-weather", args=[self.day.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("temperature_c", response.json())

    @override_settings(TRIP_CREATION_SYNC=True)
    @patch("itinerary.services.trip_creation.LLMService.generate_itinerary")
    def test_create_trip_returns_job(self, mock_llm):
        mock_llm.return_value = {
            "title": "API Trip",
            "currency": "EUR",
            "conversion_rate": 1.0,
            "days": [
                {
                    "day_number": 1,
                    "theme": "Day 1",
                    "early_start_banner": "",
                    "stops": [],
                }
            ],
        }
        self._auth(self.owner)
        response = self.client.post(
            reverse("trip-list"),
            {
                "destination": "Porto",
                "days_count": 1,
                "start_date": "2026-09-01",
                "details": "Food tour",
                "attendees": [{"name": "Alex", "role": "Traveler"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["status"], TripCreationJob.STATUS_COMPLETED)

    @patch("itinerary.api.views.LLMService.edit_agenda", return_value=[])
    def test_chat_edit_returns_json_summary(self, _mock_edit):
        self._auth(self.owner)
        response = self.client.post(
            reverse("day-chat-edit", args=[self.day.id]),
            {"message": "Add a coffee stop"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_reorder_stops_endpoint(self):
        stop_two = StopBlock.objects.create(
            day=self.day,
            sequence_order=2,
            time_label="11:00 AM",
            title="Cafe",
            description="Coffee",
            latitude=38.72,
            longitude=-9.14,
        )
        self._auth(self.owner)
        response = self.client.post(
            reverse("day-reorder-stops", args=[self.day.id]),
            {"stop_ids": [stop_two.id, self.stop.id]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.stop.refresh_from_db()
        stop_two.refresh_from_db()
        self.assertEqual(stop_two.sequence_order, 1)
        self.assertEqual(self.stop.sequence_order, 2)

    def test_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
        response = self.client.get(reverse("trip-list"))
        self.assertEqual(response.status_code, 401)

    def test_owner_can_list_stop_photos(self):
        from itinerary.models import StopPhoto

        StopPhoto.objects.create(
            stop=self.stop,
            image="stops/photos/test.jpg",
        )
        self._auth(self.owner)
        response = self.client.get(reverse("stop-photos", args=[self.stop.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    @patch("itinerary.api.views.LLMService.parse_booking")
    def test_owner_can_import_booking_from_text(self, mock_parse):
        mock_parse.return_value = {
            "booking_type": "Flight",
            "title": "BA123 to Lisbon",
            "confirmation_number": "ABC123",
            "details": "Window seat",
            "start_time": None,
            "end_time": None,
            "cost": None,
        }
        self._auth(self.owner)
        response = self.client.post(
            reverse("trip-import-booking", args=[self.trip.id]),
            {"text": "Flight BA123 confirmation ABC123"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["title"], "BA123 to Lisbon")
        self.assertTrue(Booking.objects.filter(trip=self.trip).exists())
