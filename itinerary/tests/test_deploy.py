from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from itinerary.models import DayItinerary, Trip


class RateLimitTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(username="limited", password="complexpass123")
        self.client.force_login(self.user)
        self.trip = Trip.objects.create(
            user=self.user,
            title="Trip",
            destination="Lisbon",
            start_date="2026-08-01",
            end_date="2026-08-03",
        )
        self.day = DayItinerary.objects.create(
            trip=self.trip,
            day_number=1,
            date="2026-08-01",
            theme="Explore",
        )

    @override_settings(AI_RATE_LIMIT="2/h")
    @patch("itinerary.views.run_trip_creation_job")
    def test_create_trip_rate_limited_after_threshold(self, _mock_job):
        payload = {
            "destination": "Lisbon",
            "days_count": 1,
            "start_date": "2026-09-01",
            "details": "",
        }
        for _ in range(2):
            response = self.client.post(reverse("create_trip"), payload)
            self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse("create_trip"), payload)
        self.assertEqual(response.status_code, 429)

    @override_settings(AI_RATE_LIMIT="2/h")
    @patch("itinerary.views.LLMService.edit_agenda", return_value=[])
    def test_chat_edit_rate_limited_after_threshold(self, _mock_edit):
        url = reverse("chat_edit", args=[self.trip.id, self.day.day_number])
        for _ in range(2):
            response = self.client.post(url, {"message": "Add park"})
            self.assertEqual(response.status_code, 200)
        response = self.client.post(url, {"message": "Add park again"})
        self.assertEqual(response.status_code, 429)
