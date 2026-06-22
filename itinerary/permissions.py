from django.shortcuts import get_object_or_404

from .models import Trip, DayItinerary, StopBlock, ChecklistItem, StopPhoto
from .querysets import trip_detail_queryset, trips_for_dashboard


def user_trips_queryset(user):
    return Trip.objects.filter(user=user)


def get_trip_for_user(user, trip_id):
    return get_object_or_404(Trip, id=trip_id, user=user)


def get_trip_detail_for_user(user, trip_id):
    qs = trip_detail_queryset(user_trips_queryset(user))
    return get_object_or_404(qs, id=trip_id)


def dashboard_trips_for_user(user):
    return trips_for_dashboard(user)


def get_day_for_user(user, day_id):
    day = get_object_or_404(DayItinerary.objects.select_related("trip"), id=day_id)
    get_trip_for_user(user, day.trip_id)
    return day


def get_day_for_user_trip(user, trip_id, day_number):
    trip = get_trip_for_user(user, trip_id)
    return get_object_or_404(DayItinerary, trip=trip, day_number=day_number)


def get_stop_for_user(user, stop_id):
    stop = get_object_or_404(
        StopBlock.objects.select_related("day__trip"),
        id=stop_id,
    )
    get_trip_for_user(user, stop.day.trip_id)
    return stop


def get_checklist_item_for_user(user, item_id):
    item = get_object_or_404(ChecklistItem.objects.select_related("trip"), id=item_id)
    get_trip_for_user(user, item.trip_id)
    return item


def get_photo_for_user(user, photo_id):
    photo = get_object_or_404(
        StopPhoto.objects.select_related("stop__day__trip"),
        id=photo_id,
    )
    get_trip_for_user(user, photo.stop.day.trip_id)
    return photo
