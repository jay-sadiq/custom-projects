from datetime import date, time

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from itinerary.models import (
    ChecklistItem,
    DayItinerary,
    StopBlock,
    StopPhoto,
    Trip,
)


class TripOwnershipTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="other", password="pass12345")

        self.trip = Trip.objects.create(
            user=self.owner,
            title="Owner Trip",
            destination="Lisbon",
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 3),
        )
        self.day = DayItinerary.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(2026, 7, 1),
            theme="Arrival",
        )
        self.stop = StopBlock.objects.create(
            day=self.day,
            sequence_order=1,
            time_label="10:00 AM",
            title="City Center",
            description="Walk around",
            latitude=38.7223,
            longitude=-9.1393,
            start_time_of_day=time(10, 0),
            end_time_of_day=time(11, 0),
        )
        self.checklist_item = ChecklistItem.objects.create(
            trip=self.trip,
            item_text="Passport",
        )
        self.photo = StopPhoto.objects.create(
            stop=self.stop,
            image="stops/photos/test.jpg",
        )

    def login_as(self, user):
        self.assertTrue(self.client.login(username=user.username, password="pass12345"))

    def test_dashboard_lists_only_own_trips(self):
        Trip.objects.create(
            user=self.other,
            title="Other Trip",
            destination="Paris",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 2),
        )
        self.login_as(self.owner)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner Trip")
        self.assertNotContains(response, "Other Trip")

    def test_owner_can_view_trip_detail(self):
        self.login_as(self.owner)
        response = self.client.get(reverse("trip_detail", args=[self.trip.id]))
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_view_trip_detail(self):
        self.login_as(self.other)
        response = self.client.get(reverse("trip_detail", args=[self.trip.id]))
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_view_day_detail(self):
        self.login_as(self.other)
        response = self.client.get(
            reverse("day_detail", args=[self.trip.id, self.day.day_number])
        )
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_save_notes(self):
        self.login_as(self.other)
        response = self.client.post(
            reverse("save_notes", args=[self.day.id]),
            {"notes": "Hacked"},
        )
        self.assertEqual(response.status_code, 404)
        self.day.refresh_from_db()
        self.assertEqual(self.day.notes, "")

    def test_other_user_cannot_toggle_checklist(self):
        self.login_as(self.other)
        response = self.client.post(
            reverse("toggle_checklist_item", args=[self.checklist_item.id])
        )
        self.assertEqual(response.status_code, 404)
        self.checklist_item.refresh_from_db()
        self.assertFalse(self.checklist_item.is_completed)

    def test_other_user_cannot_edit_stop(self):
        self.login_as(self.other)
        response = self.client.get(reverse("edit_stop", args=[self.stop.id]))
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_delete_stop(self):
        self.login_as(self.other)
        response = self.client.post(reverse("delete_stop", args=[self.stop.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(StopBlock.objects.filter(id=self.stop.id).exists())

    def test_other_user_cannot_get_stops_json(self):
        self.login_as(self.other)
        response = self.client.get(
            reverse("get_stops_json", args=[self.trip.id, self.day.day_number])
        )
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_chat_edit(self):
        self.login_as(self.other)
        response = self.client.post(
            reverse("chat_edit", args=[self.trip.id, self.day.day_number]),
            {"message": "Add museum"},
        )
        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_delete_photo(self):
        self.login_as(self.other)
        response = self.client.post(reverse("delete_stop_photo", args=[self.photo.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(StopPhoto.objects.filter(id=self.photo.id).exists())

    def test_unauthenticated_user_redirected_from_dashboard(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
