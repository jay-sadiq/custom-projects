import logging
from datetime import timedelta

from django.db import transaction

from itinerary.models import (
    ChecklistItem,
    DayItinerary,
    StopBlock,
    Trip,
    TripCreationJob,
)
from itinerary.services.attendees import create_trip_attendees
from itinerary.services.llm import LLMService

logger = logging.getLogger(__name__)


def _create_checklist_defaults(trip: Trip) -> None:
    ChecklistItem.objects.create(
        trip=trip, category="Preparation", item_text="Check passport expiration dates"
    )
    ChecklistItem.objects.create(
        trip=trip, category="Preparation", item_text="Purchase travel insurance"
    )
    ChecklistItem.objects.create(
        trip=trip, category="Packing List", item_text="Comfortable walking shoes"
    )
    ChecklistItem.objects.create(
        trip=trip, category="Packing List", item_text="Power adapters & chargers"
    )


@transaction.atomic
def build_trip_from_itinerary(
    user, destination, days_count, start_date, details, itinerary_data, attendees=None
) -> Trip:
    trip = Trip.objects.create(
        user=user,
        title=itinerary_data.get("title", f"Adventure in {destination}"),
        destination=destination,
        start_date=start_date,
        end_date=start_date + timedelta(days=days_count - 1),
        currency=itinerary_data.get("currency", "USD"),
        conversion_rate=itinerary_data.get("conversion_rate", 1.0),
    )

    if not attendees:
        display_name = user.get_full_name().strip() or user.username
        attendees = [{"name": display_name, "role": "Lead traveler"}]
    create_trip_attendees(trip, attendees)

    for day_data in itinerary_data.get("days", []):
        day_num = day_data.get("day_number")
        day_date = start_date + timedelta(days=day_num - 1)
        day_itinerary = DayItinerary.objects.create(
            trip=trip,
            day_number=day_num,
            date=day_date,
            theme=day_data.get("theme", ""),
            early_start_banner=day_data.get("early_start_banner", ""),
        )

        for idx, stop_data in enumerate(day_data.get("stops", [])):
            StopBlock.objects.create(
                day=day_itinerary,
                sequence_order=stop_data.get("sequence_order", idx + 1),
                time_label=stop_data.get("time_label", ""),
                title=stop_data.get("title", ""),
                description=stop_data.get("description", ""),
                latitude=stop_data.get("latitude", 0.0),
                longitude=stop_data.get("longitude", 0.0),
                zoom_level=stop_data.get("zoom_level", 15),
                cost_local=stop_data.get("cost_local", 0.0),
                cost_usd=stop_data.get("cost_usd", 0.0),
                meal_type=stop_data.get("meal_type", ""),
                meal_name=stop_data.get("meal_name", ""),
                meal_desc=stop_data.get("meal_desc", ""),
                meal_price_label=stop_data.get("meal_price_label", ""),
                meal_recommendation=stop_data.get("meal_recommendation", ""),
                tags=stop_data.get("tags", []),
                color_hex=stop_data.get("color_hex", "#E67E22"),
            )

    _create_checklist_defaults(trip)
    return trip


def run_trip_creation_job(job_id: int) -> None:
    job = TripCreationJob.objects.select_related("user").get(id=job_id)
    if job.status != TripCreationJob.STATUS_PENDING:
        return

    job.status = TripCreationJob.STATUS_RUNNING
    job.save(update_fields=["status", "updated_at"])

    try:
        itinerary_data = LLMService.generate_itinerary(
            job.destination,
            job.days_count,
            job.start_date.isoformat(),
            job.details,
        )
        trip = build_trip_from_itinerary(
            job.user,
            job.destination,
            job.days_count,
            job.start_date,
            job.details,
            itinerary_data,
            attendees=job.attendees_json,
        )
        job.trip = trip
        job.status = TripCreationJob.STATUS_COMPLETED
        job.error_message = ""
        job.save(update_fields=["trip", "status", "error_message", "updated_at"])
    except Exception as exc:
        logger.exception("Trip creation job %s failed", job_id)
        job.status = TripCreationJob.STATUS_FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
