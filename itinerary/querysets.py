from decimal import Decimal

from django.db.models import Count, DecimalField, OuterRef, Prefetch, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from .models import Booking, DayItinerary, StopBlock, Trip


def _annotate_trip_costs(queryset):
    stops_total = (
        StopBlock.objects.filter(day__trip_id=OuterRef("pk"))
        .values("day__trip_id")
        .annotate(total=Sum("cost_local"))
        .values("total")[:1]
    )
    bookings_total = (
        Booking.objects.filter(trip_id=OuterRef("pk"))
        .values("trip_id")
        .annotate(total=Sum("cost"))
        .values("total")[:1]
    )
    decimal_out = DecimalField(max_digits=12, decimal_places=2)
    return queryset.annotate(
        attendee_count=Count("attendees", distinct=True),
        stops_cost_total=Coalesce(
            Subquery(stops_total),
            Value(Decimal("0.00")),
            output_field=decimal_out,
        ),
        bookings_cost_total=Coalesce(
            Subquery(bookings_total),
            Value(Decimal("0.00")),
            output_field=decimal_out,
        ),
    )


def trips_for_dashboard(user):
    return _annotate_trip_costs(
        Trip.objects.filter(user=user).order_by("-created_at")
    )


def trip_detail_queryset(queryset=None):
    qs = queryset if queryset is not None else Trip.objects.all()
    stops_qs = StopBlock.objects.order_by("sequence_order").prefetch_related("user_photos")
    days_qs = DayItinerary.objects.order_by("day_number").prefetch_related(
        Prefetch("stops", queryset=stops_qs)
    )
    return qs.prefetch_related(
        Prefetch("days", queryset=days_qs),
        "checklist_items",
        "bookings",
    )
