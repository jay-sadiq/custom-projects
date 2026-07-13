from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from itinerary.models import (
    Booking,
    DayItinerary,
    PlaceDetail,
    StopBlock,
    Trip,
    TripAttendee,
    TripCreationJob,
)
from itinerary.querysets import trips_for_dashboard
from itinerary.services.places import place_detail_is_stale, refresh_place_detail


MOCK_ITINERARY = {
    "title": "Tokyo Adventure",
    "currency": "JPY",
    "conversion_rate": 150.0,
    "days": [
        {
            "day_number": 1,
            "theme": "Arrival",
            "early_start_banner": "",
            "stops": [
                {
                    "sequence_order": 1,
                    "time_label": "10:00 AM",
                    "title": "Shibuya Crossing",
                    "description": "Iconic intersection",
                    "latitude": 35.6595,
                    "longitude": 139.7005,
                    "zoom_level": 15,
                    "cost_local": 25.0,
                    "cost_usd": 0.17,
                    "tags": ["Landmark"],
                    "color_hex": "#E74C3C",
                }
            ],
        }
    ],
}


class QueryOptimizationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="perfuser", password="complexpass123")
        self.client.force_login(self.user)
        self.trip = Trip.objects.create(
            user=self.user,
            title="Perf Trip",
            destination="Lisbon",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 3),
        )
        for day_num in range(1, 4):
            day = DayItinerary.objects.create(
                trip=self.trip,
                day_number=day_num,
                date=date(2026, 7, day_num),
                theme=f"Day {day_num}",
            )
            for stop_idx in range(1, 4):
                StopBlock.objects.create(
                    day=day,
                    sequence_order=stop_idx,
                    time_label=f"{8 + stop_idx}:00 AM",
                    title=f"Stop {day_num}-{stop_idx}",
                    description="Test stop",
                    latitude=38.71,
                    longitude=-9.13,
                    cost_local=10.0 * stop_idx,
                )
        TripAttendee.objects.create(trip=self.trip, name="Alice", role="Traveler")
        TripAttendee.objects.create(trip=self.trip, name="Bob", role="Traveler")

    def test_trip_detail_uses_bounded_query_count(self):
        with self.assertNumQueries(8):
            response = self.client.get(reverse("trip_detail", args=[self.trip.id]))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_uses_annotated_cost_and_attendee_count(self):
        Booking.objects.create(
            trip=self.trip,
            booking_type="Flight",
            title="Inbound",
            cost=Decimal("50.00"),
        )
        trips = list(trips_for_dashboard(self.user))
        self.assertEqual(len(trips), 1)
        trip = trips[0]
        self.assertEqual(trip.attendee_count, 2)
        # 3 days × (10 + 20 + 30) stops + 50 booking = 230
        self.assertEqual(trip.total_cost_local, Decimal("230.00"))

        with self.assertNumQueries(1):
            list(trips_for_dashboard(self.user))

    def test_dashboard_view_avoids_n_plus_one(self):
        for idx in range(4):
            trip = Trip.objects.create(
                user=self.user,
                title=f"Trip {idx}",
                destination="City",
                start_date=date(2026, 8, 1),
                end_date=date(2026, 8, 2),
            )
            TripAttendee.objects.create(trip=trip, name="Solo", role="Lead")
            day = DayItinerary.objects.create(
                trip=trip,
                day_number=1,
                date=date(2026, 8, 1),
                theme="Explore",
            )
            StopBlock.objects.create(
                day=day,
                sequence_order=1,
                time_label="9:00 AM",
                title="Stop",
                description="",
                latitude=0,
                longitude=0,
                cost_local=5.0,
            )

        with self.assertNumQueries(9):
            response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)


class AsyncTripCreationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="asyncuser", password="complexpass123")
        self.client.force_login(self.user)

    @override_settings(TRIP_CREATION_SYNC=True)
    @patch(
        "itinerary.services.trip_creation.LLMService.generate_itinerary",
        return_value=MOCK_ITINERARY,
    )
    def test_sync_mode_still_redirects_when_enabled(self, _mock_llm):
        response = self.client.post(
            reverse("create_trip"),
            {
                "destination": "Tokyo",
                "days_count": 1,
                "start_date": "2026-10-01",
                "details": "Solo",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Redirect", response.headers)
        self.assertTrue(Trip.objects.filter(destination="Tokyo", user=self.user).exists())

    @patch("itinerary.views._start_trip_creation_thread")
    @patch("itinerary.services.trip_creation.LLMService.generate_itinerary", return_value=MOCK_ITINERARY)
    def test_async_create_returns_status_partial_immediately(self, _mock_llm, _mock_thread):
        response = self.client.post(
            reverse("create_trip"),
            {
                "destination": "Tokyo",
                "days_count": 1,
                "start_date": "2026-10-01",
                "details": "Solo",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Generating your itinerary")
        self.assertNotIn("HX-Redirect", response.headers)
        job = TripCreationJob.objects.get(destination="Tokyo", user=self.user)
        self.assertIn(job.status, (TripCreationJob.STATUS_PENDING, TripCreationJob.STATUS_RUNNING, TripCreationJob.STATUS_COMPLETED))

    @patch("itinerary.services.trip_creation.LLMService.generate_itinerary", return_value=MOCK_ITINERARY)
    def test_trip_creation_status_redirects_when_complete(self, _mock_llm):
        job = TripCreationJob.objects.create(
            user=self.user,
            destination="Tokyo",
            days_count=1,
            start_date=date(2026, 10, 1),
            details="Solo",
            status=TripCreationJob.STATUS_COMPLETED,
        )
        trip = Trip.objects.create(
            user=self.user,
            title="Tokyo Adventure",
            destination="Tokyo",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 1),
        )
        job.trip = trip
        job.save()

        response = self.client.get(reverse("trip_creation_status", args=[job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Redirect", response.headers)
        self.assertEqual(response.headers["HX-Redirect"], f"/trip/{trip.id}/")


class PlaceDetailCacheTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cacheuser", password="complexpass123")
        self.trip = Trip.objects.create(
            user=self.user,
            title="Cache Trip",
            destination="Baku",
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 1),
        )
        self.day = DayItinerary.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(2026, 6, 1),
            theme="Explore",
        )
        self.stop = StopBlock.objects.create(
            day=self.day,
            sequence_order=1,
            time_label="10:00 AM",
            title="Old Town",
            description="Historic quarter",
            latitude=40.36,
            longitude=49.83,
        )

    def test_place_detail_is_stale_after_backdated_updated_at(self):
        place_detail = PlaceDetail.objects.create(
            stop=self.stop,
            reviews_json=[{"author": "Cached", "rating": 5, "text": "Great"}],
            photos_json=[],
        )
        PlaceDetail.objects.filter(pk=place_detail.pk).update(
            updated_at=timezone.now() - timedelta(days=8)
        )
        place_detail.refresh_from_db()
        self.assertTrue(place_detail_is_stale(place_detail))

    @patch("itinerary.services.reviews.refresh_place_detail", return_value=False)
    def test_get_stop_reviews_refreshes_stale_cache(self, mock_refresh):
        place_detail = PlaceDetail.objects.create(
            stop=self.stop,
            reviews_json=[{"author": "Cached", "rating": 5, "text": "Great"}],
            photos_json=[],
        )
        PlaceDetail.objects.filter(pk=place_detail.pk).update(
            updated_at=timezone.now() - timedelta(days=8)
        )

        client = Client()
        client.force_login(self.user)
        response = client.get(reverse("get_stop_reviews", args=[self.stop.id]))
        self.assertEqual(response.status_code, 200)
        mock_refresh.assert_called_once()

    def test_fresh_place_detail_skips_refresh(self):
        place_detail = PlaceDetail.objects.create(
            stop=self.stop,
            reviews_json=[{"author": "Fresh", "rating": 5, "text": "Nice"}],
            photos_json=[],
        )
        self.assertFalse(place_detail_is_stale(place_detail))

        with patch("itinerary.services.places.refresh_place_detail") as mock_refresh:
            client = Client()
            client.force_login(self.user)
            response = client.get(reverse("get_stop_reviews", args=[self.stop.id]))
            self.assertEqual(response.status_code, 200)
            mock_refresh.assert_not_called()

    @patch("itinerary.services.places.requests.get")
    def test_refresh_place_detail_updates_reviews(self, mock_get):
        place_detail = PlaceDetail.objects.create(stop=self.stop)
        mock_get.side_effect = [
            type("Resp", (), {"json": lambda self: {"results": [{"place_id": "abc", "rating": 4.8}]}})(),
            type(
                "Resp",
                (),
                {
                    "json": lambda self: {
                        "result": {
                            "reviews": [
                                {"author_name": "New", "rating": 5, "text": "Updated review"}
                            ],
                            "photos": [],
                        }
                    }
                },
            )(),
        ]

        with override_settings(GOOGLE_PLACES_API_KEY="test-key"):
            refresh_place_detail(place_detail, self.stop)

        place_detail.refresh_from_db()
        self.assertEqual(place_detail.reviews_json[0]["author"], "New")
