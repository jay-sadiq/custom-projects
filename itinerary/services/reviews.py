from django.urls import reverse

from itinerary.models import PlaceDetail
from itinerary.services.places import (
    normalize_photo_entries,
    place_detail_is_stale,
    refresh_place_detail,
)


def get_stop_reviews_data(stop, *, request=None) -> dict:
    place_detail, created = PlaceDetail.objects.get_or_create(stop=stop)
    if place_detail_is_stale(place_detail, created=created):
        used_live_api = refresh_place_detail(place_detail, stop)
    else:
        used_live_api = bool(place_detail.place_id)

    photos = normalize_photo_entries(place_detail.photos_json)
    photo_urls = []
    for index, photo in enumerate(photos):
        if photo.get("type") == "google_ref" and request is not None:
            photo_urls.append(
                request.build_absolute_uri(
                    reverse("proxy_place_photo", args=[stop.id, index])
                )
            )
        elif photo.get("type") == "external":
            photo_urls.append(photo.get("url"))

    return {
        "stop_id": stop.id,
        "rating": place_detail.rating,
        "reviews": place_detail.reviews_json,
        "photos": photos,
        "photo_urls": photo_urls,
        "is_demo_data": not used_live_api,
    }
