import os
from datetime import date
from decimal import Decimal
from importlib import reload
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from itinerary.models import DayItinerary, PlaceDetail, StopBlock, Trip
from itinerary.services.places import normalize_photo_entries


class ProdSettingsTestCase(TestCase):
    def test_prod_requires_secret_key(self):
        env = {
            "SECRET_KEY": "",
            "ALLOWED_HOSTS": "example.com",
            "CSRF_TRUSTED_ORIGINS": "https://example.com",
        }
        with patch.dict(os.environ, env, clear=False):
            import core.settings.prod as prod_settings

            with self.assertRaises(ImproperlyConfigured):
                reload(prod_settings)

    def test_prod_requires_allowed_hosts(self):
        env = {
            "SECRET_KEY": "test-secret-key-for-prod-settings-check",
            "ALLOWED_HOSTS": "",
            "CSRF_TRUSTED_ORIGINS": "https://example.com",
        }
        with patch.dict(os.environ, env, clear=False):
            import core.settings.prod as prod_settings

            with self.assertRaises(ImproperlyConfigured):
                reload(prod_settings)

    def test_prod_loads_with_required_env(self):
        env = {
            "SECRET_KEY": "test-secret-key-for-prod-settings-check",
            "ALLOWED_HOSTS": "example.com",
            "CSRF_TRUSTED_ORIGINS": "https://example.com",
        }
        with patch.dict(os.environ, env, clear=False):
            import core.settings.prod as prod_settings

            reloaded = reload(prod_settings)
            self.assertFalse(reloaded.DEBUG)
            self.assertTrue(reloaded.SESSION_COOKIE_SECURE)
            self.assertTrue(reloaded.CSRF_COOKIE_SECURE)
            self.assertIn("example.com", reloaded.ALLOWED_HOSTS)
            self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", reloaded.MIDDLEWARE)

    def test_prod_uses_database_url_when_set(self):
        env = {
            "SECRET_KEY": "test-secret-key-for-prod-settings-check",
            "ALLOWED_HOSTS": "example.com",
            "CSRF_TRUSTED_ORIGINS": "https://example.com",
            "DATABASE_URL": "postgres://user:pass@localhost:5432/tripplanner",
            "DATABASE_SSL_REQUIRE": "False",
        }
        with patch.dict(os.environ, env, clear=False):
            import core.settings.prod as prod_settings

            reloaded = reload(prod_settings)
            self.assertEqual(reloaded.DATABASES["default"]["ENGINE"], "django.db.backends.postgresql")


class PlacesPhotoProxyTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="owner", password="pass12345")
        self.other = User.objects.create_user(username="other", password="pass12345")
        self.trip = Trip.objects.create(
            user=self.owner,
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
        PlaceDetail.objects.create(
            stop=self.stop,
            rating=Decimal("4.5"),
            reviews_json=[{"author": "A", "rating": 5, "text": "Nice"}],
            photos_json=[{"type": "google_ref", "ref": "test-photo-ref"}],
        )

    def test_normalize_legacy_google_url_strips_key(self):
        legacy = [
            "https://maps.googleapis.com/maps/api/place/photo?maxwidth=400"
            "&photo_reference=abc123&key=SECRET_KEY_VALUE"
        ]
        normalized = normalize_photo_entries(legacy)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["type"], "google_ref")
        self.assertEqual(normalized[0]["ref"], "abc123")

    def test_reviews_html_uses_proxy_not_api_key(self):
        self.client.login(username="owner", password="pass12345")
        response = self.client.get(reverse("get_stop_reviews", args=[self.stop.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("proxy_place_photo", args=[self.stop.id, 0]))
        self.assertNotContains(response, "SECRET_KEY_VALUE")
        self.assertNotContains(response, "maps.googleapis.com/maps/api/place/photo")

    @override_settings(GOOGLE_PLACES_API_KEY="server-only-key")
    def test_proxy_requires_authentication(self):
        response = self.client.get(
            reverse("proxy_place_photo", args=[self.stop.id, 0])
        )
        self.assertEqual(response.status_code, 302)

    @override_settings(GOOGLE_PLACES_API_KEY="server-only-key")
    @patch("itinerary.views.fetch_google_place_photo")
    def test_proxy_serves_image_without_leaking_key(self, mock_fetch):
        mock_fetch.return_value = (b"fake-image-bytes", "image/jpeg")
        self.client.login(username="owner", password="pass12345")
        response = self.client.get(
            reverse("proxy_place_photo", args=[self.stop.id, 0])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"fake-image-bytes")
        self.assertNotIn(b"server-only-key", response.content)
        self.assertNotIn(b"key=", response.content)

    @override_settings(GOOGLE_PLACES_API_KEY="server-only-key")
    def test_other_user_cannot_proxy_photo(self):
        self.client.login(username="other", password="pass12345")
        response = self.client.get(
            reverse("proxy_place_photo", args=[self.stop.id, 0])
        )
        self.assertEqual(response.status_code, 404)


class WeatherHttpsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="owner", password="pass12345")
        self.client.login(username="owner", password="pass12345")
        trip = Trip.objects.create(
            user=self.user,
            title="Trip",
            destination="Lisbon",
            start_date="2026-07-01",
            end_date="2026-07-02",
        )
        self.day = DayItinerary.objects.create(
            trip=trip,
            day_number=1,
            date="2026-07-01",
        )

    @override_settings(WEATHER_API_KEY="weather-test-key")
    @patch("itinerary.services.weather.requests.get")
    def test_weather_api_uses_https(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: {
                "forecast": {
                    "forecastday": [
                        {
                            "day": {
                                "avgtemp_c": 22.0,
                                "condition": {"text": "Sunny"},
                            }
                        }
                    ]
                }
            }
        )
        response = self.client.get(reverse("get_weather", args=[self.day.id]))
        self.assertEqual(response.status_code, 200)
        called_url = mock_get.call_args[0][0]
        self.assertTrue(called_url.startswith("https://api.weatherapi.com/"))
        self.assertNotIn("http://api.weatherapi.com", called_url)
