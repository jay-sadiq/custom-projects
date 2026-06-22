import logging
from urllib.parse import parse_qs, urlparse

import requests
from django.conf import settings

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
