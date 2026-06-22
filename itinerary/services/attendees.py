from itinerary.models import Trip, TripAttendee


def parse_attendees_from_request(post, user) -> list[dict]:
    names = post.getlist("attendee_name")
    roles = post.getlist("attendee_role")
    attendees = []
    for name, role in zip(names, roles):
        name = (name or "").strip()
        role = (role or "").strip()
        if name:
            attendees.append({"name": name, "role": role or "Traveler"})
    if not attendees:
        display_name = user.get_full_name().strip() or user.username
        attendees.append({"name": display_name, "role": "Lead traveler"})
    return attendees


def create_trip_attendees(trip: Trip, attendees: list[dict]) -> None:
    for entry in attendees:
        TripAttendee.objects.create(
            trip=trip,
            name=entry["name"],
            role=entry.get("role") or "Traveler",
        )
