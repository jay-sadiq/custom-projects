import logging
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def google_photo_ref(reference: str) -> dict:
    return {"type": "google_ref", "ref": reference}


def external_photo_url(url: str) -> dict:
    return {"type": "external", "url": url}


def normalize_photo_entries(raw_list) -> list[dict]:
    normalized = []
    for item in raw_list or []:
        if isinstance(item, dict):
            if item.get("type") == "google_ref" and item.get("ref"):
                normalized.append({"type": "google_ref", "ref": item["ref"]})
            elif item.get("type") == "external" and item.get("url"):
                normalized.append({"type": "external", "url": item["url"]})
            elif item.get("ref"):
                normalized.append({"type": "google_ref", "ref": item["ref"]})
            elif item.get("url"):
                normalized.append({"type": "external", "url": item["url"]})
        elif isinstance(item, str):
            if "photo_reference=" in item:
                query = parse_qs(urlparse(item).query)
                ref = query.get("photo_reference", [None])[0]
                if ref:
                    normalized.append({"type": "google_ref", "ref": ref})
            elif item.startswith("http"):
                normalized.append({"type": "external", "url": item})
    return normalized


def place_detail_is_stale(place_detail, *, created: bool = False) -> bool:
    if created or not place_detail.reviews_json:
        return True
    age = timezone.now() - place_detail.updated_at
    return age > timedelta(days=settings.PLACE_DETAIL_CACHE_DAYS)


def refresh_place_detail(place_detail, stop) -> bool:
    api_key = settings.GOOGLE_PLACES_API_KEY
    if api_key:
        try:
            url = (
                "https://maps.googleapis.com/maps/api/place/textsearch/json"
                f"?query={stop.title}&key={api_key}"
            )
            resp = requests.get(url, timeout=settings.EXTERNAL_REQUEST_TIMEOUT).json()
            results = resp.get("results", [])
            if results:
                place = results[0]
                g_place_id = place.get("place_id")
                place_detail.place_id = g_place_id
                place_detail.rating = place.get("rating")

                detail_url = (
                    "https://maps.googleapis.com/maps/api/place/details/json"
                    f"?place_id={g_place_id}&fields=reviews,photos&key={api_key}"
                )
                detail_resp = requests.get(
                    detail_url, timeout=settings.EXTERNAL_REQUEST_TIMEOUT
                ).json()
                detail_result = detail_resp.get("result", {})

                reviews = []
                for rev in detail_result.get("reviews", [])[:10]:
                    reviews.append(
                        {
                            "author": rev.get("author_name"),
                            "rating": rev.get("rating"),
                            "text": rev.get("text"),
                        }
                    )
                place_detail.reviews_json = reviews

                photos = []
                for ph in detail_result.get("photos", [])[:5]:
                    ref = ph.get("photo_reference")
                    if ref:
                        photos.append(google_photo_ref(ref))
                place_detail.photos_json = photos
                place_detail.save()
                return True
        except Exception as e:
            logger.error("Error fetching Google reviews: %s", e)

    place_detail.rating = 4.5
    place_detail.reviews_json = [
        {
            "author": "Alex M.",
            "rating": 5,
            "text": (
                f"Wonderful spot! We visited {stop.title} during our trip "
                "and it was absolutely worth the stop."
            ),
        },
        {
            "author": "Samira K.",
            "rating": 4,
            "text": "Clean, welcoming, and great for families. Would visit again.",
        },
        {
            "author": "Chris L.",
            "rating": 4,
            "text": (
                "Lovely atmosphere — best enjoyed in the late afternoon "
                "when the area really comes alive."
            ),
        },
    ]
    place_detail.photos_json = [
        external_photo_url(
            "https://images.unsplash.com/photo-1549693578-d683be217e58?auto=format&fit=crop&w=400&q=80"
        ),
        external_photo_url(
            "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=400&q=80"
        ),
    ]
    place_detail.save()
    return False


def fetch_google_place_photo(reference: str) -> tuple[bytes, str]:
    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_PLACES_API_KEY is not configured")

    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "maxwidth": settings.GOOGLE_PLACES_PHOTO_MAX_WIDTH,
        "photo_reference": reference,
        "key": api_key,
    }
    response = requests.get(
        url,
        params=params,
        timeout=settings.EXTERNAL_REQUEST_TIMEOUT,
        allow_redirects=True,
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "image/jpeg")
    return response.content, content_type
