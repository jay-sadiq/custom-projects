from django.utils import timezone
from django.utils.dateparse import parse_datetime


def parse_booking_datetime(value):
    if not value:
        return None
    if hasattr(value, "isoformat"):
        parsed = value
    else:
        parsed = parse_datetime(str(value))
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed
