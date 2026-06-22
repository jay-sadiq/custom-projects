from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from itinerary.models import ChecklistItem, DayItinerary, PlaceDetail, StopBlock, Trip
from itinerary.services.mutations import MutationError, apply_stop_mutations, filter_stop_fields


class XSSProtectionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.client.login(username="owner", password="pass12345")

        self.trip = Trip.objects.create(
            user=self.user,
            title="Trip",
            destination="Lisbon",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 2),
        )
        self.day = DayItinerary.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(2026, 7, 1),
        )
        self.stop = StopBlock.objects.create(
            day=self.day,
            sequence_order=1,
            time_label="10:00 AM",
            title="Museum",
            description="Visit",
            latitude=38.72,
            longitude=-9.14,
        )

    def test_chat_edit_escapes_user_message(self):
        xss = '<script>alert(1)</script>'
        with patch("itinerary.views.LLMService.edit_agenda", return_value=[]):
            response = self.client.post(
                reverse("chat_edit", args=[self.trip.id, self.day.day_number]),
                {"message": xss},
            )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_checklist_toggle_escapes_item_text(self):
        item = ChecklistItem.objects.create(
            trip=self.trip,
            item_text='<img src=x onerror=alert(1)>',
        )
        response = self.client.post(reverse("toggle_checklist_item", args=[item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<img src=x onerror=alert(1)>")
        self.assertContains(response, "&lt;img src=x onerror=alert(1)&gt;")

    def test_stop_reviews_escape_review_text(self):
        PlaceDetail.objects.create(
            stop=self.stop,
            rating=Decimal("4.5"),
            reviews_json=[
                {
                    "author": "Tester",
                    "rating": 5,
                    "text": '<script>alert("xss")</script>',
                }
            ],
            photos_json=[],
        )
        response = self.client.get(reverse("get_stop_reviews", args=[self.stop.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<script>alert("xss")</script>')
        self.assertContains(response, "&lt;script&gt;")


class MutationSafetyTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.trip = Trip.objects.create(
            user=self.user,
            title="Trip",
            destination="Lisbon",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 2),
        )
        self.day = DayItinerary.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(2026, 7, 1),
        )
        self.stop = StopBlock.objects.create(
            day=self.day,
            sequence_order=1,
            time_label="10:00 AM",
            title="Original",
            description="Visit",
            latitude=38.72,
            longitude=-9.14,
        )

    def test_filter_stop_fields_removes_unknown_keys(self):
        raw = {"title": "New", "day": 999, "id": 1, "malicious": True}
        filtered = filter_stop_fields(raw)
        self.assertEqual(filtered, {"title": "New"})

    def test_update_ignores_disallowed_fields(self):
        apply_stop_mutations(
            self.day,
            [
                {
                    "action": "UPDATE",
                    "stop_id": self.stop.id,
                    "fields": {
                        "title": "Updated",
                        "day": 999,
                        "id": 42,
                    },
                }
            ],
        )
        self.stop.refresh_from_db()
        self.assertEqual(self.stop.title, "Updated")
        self.assertEqual(self.stop.day_id, self.day.id)

    def test_create_without_title_raises_and_does_not_persist(self):
        initial_count = self.day.stops.count()
        with self.assertRaises(MutationError):
            apply_stop_mutations(
                self.day,
                [
                    {
                        "action": "CREATE",
                        "fields": {"latitude": 40.0, "longitude": 49.0},
                    }
                ],
            )
        self.assertEqual(self.day.stops.count(), initial_count)

    def test_atomic_rollback_on_invalid_create_in_batch(self):
        mutations = [
            {
                "action": "CREATE",
                "fields": {
                    "title": "Valid Stop",
                    "latitude": 40.1,
                    "longitude": 49.1,
                },
            },
            {
                "action": "CREATE",
                "fields": {"latitude": 40.2, "longitude": 49.2},
            },
        ]
        initial_count = self.day.stops.count()
        with self.assertRaises(MutationError):
            apply_stop_mutations(self.day, mutations)
        self.assertEqual(self.day.stops.count(), initial_count)

    def test_create_with_required_fields_succeeds(self):
        apply_stop_mutations(
            self.day,
            [
                {
                    "action": "CREATE",
                    "fields": {
                        "title": "Cafe",
                        "latitude": 40.37,
                        "longitude": 49.83,
                        "description": "Coffee break",
                    },
                }
            ],
        )
        self.assertEqual(self.day.stops.count(), 2)
        new_stop = self.day.stops.get(title="Cafe")
        self.assertEqual(new_stop.sequence_order, 2)

    def test_chat_edit_surfaces_mutation_validation_error(self):
        client = Client()
        client.login(username="owner", password="pass12345")
        with patch(
            "itinerary.views.LLMService.edit_agenda",
            return_value=[
                {
                    "action": "CREATE",
                    "fields": {"latitude": 40.0, "longitude": 49.0},
                }
            ],
        ):
            response = client.post(
                reverse("chat_edit", args=[self.trip.id, self.day.day_number]),
                {"message": "Add a place"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Error applying edits")
        self.assertEqual(self.day.stops.count(), 1)
