"""Booking import helpers: datetime parsing, email extraction, trip matching, drafts."""

from __future__ import annotations

import email
import logging
import re
from email import policy

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from itinerary.models import Booking, BookingImportDraft, Trip, UserProfile
from itinerary.services.llm import LLMService, LLMUnavailableError

logger = logging.getLogger(__name__)

TOKEN_ADDRESS_RE = re.compile(
    r"(?:trips\+|booking\+)([A-Za-z0-9_\-]+)@",
    re.IGNORECASE,
)


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


def get_or_create_profile(user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def forwarding_address_for(user: User) -> str:
    profile = get_or_create_profile(user)
    domain = getattr(settings, "BOOKING_IMPORT_EMAIL_DOMAIN", "bookings.example.com")
    return f"trips+{profile.email_import_token}@{domain}"


def extract_token_from_recipient(recipient: str) -> str | None:
    if not recipient:
        return None
    match = TOKEN_ADDRESS_RE.search(recipient)
    return match.group(1) if match else None


def resolve_user_from_recipient(recipient: str) -> User | None:
    token = extract_token_from_recipient(recipient)
    if not token:
        return None
    try:
        profile = UserProfile.objects.select_related("user").get(email_import_token=token)
    except UserProfile.DoesNotExist:
        return None
    return profile.user


def extract_text_from_email(raw_bytes: bytes | str) -> dict:
    """Parse MIME email into subject, from, and plain text body."""
    if isinstance(raw_bytes, str):
        raw_bytes = raw_bytes.encode("utf-8", errors="replace")

    message = email.message_from_bytes(raw_bytes, policy=policy.default)
    subject = str(message.get("Subject") or "")
    from_addr = str(message.get("From") or "")
    to_addrs = str(message.get("To") or "")
    delivered_to = str(message.get("Delivered-To") or "")
    envelope_to = str(message.get("X-Original-To") or message.get("Envelope-To") or "")

    plain_parts: list[str] = []
    html_parts: list[str] = []

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")
            if "attachment" in disposition.lower():
                continue
            try:
                payload = part.get_content()
            except Exception:
                continue
            if not isinstance(payload, str):
                continue
            if content_type == "text/plain":
                plain_parts.append(payload)
            elif content_type == "text/html":
                html_parts.append(payload)
    else:
        try:
            payload = message.get_content()
        except Exception:
            payload = ""
        if isinstance(payload, str):
            if message.get_content_type() == "text/html":
                html_parts.append(payload)
            else:
                plain_parts.append(payload)

    body = "\n".join(plain_parts).strip()
    if not body and html_parts:
        soup = BeautifulSoup("\n".join(html_parts), "html.parser")
        body = soup.get_text("\n", strip=True)

    recipients = " ".join(filter(None, [to_addrs, delivered_to, envelope_to]))
    return {
        "subject": subject,
        "from_addr": from_addr,
        "recipients": recipients,
        "body": body,
        "text": f"{subject}\n\n{body}".strip(),
    }


def suggest_trip_for_user(user: User, parsed: dict) -> Trip | None:
    """Pick the best overlapping trip for a parsed booking start time."""
    trips = Trip.objects.filter(user=user).order_by("-start_date")
    if not trips.exists():
        return None

    start = parse_booking_datetime(parsed.get("start_time"))
    if start is None:
        return trips.first()

    booking_date = timezone.localtime(start).date() if timezone.is_aware(start) else start.date()
    overlapping = trips.filter(start_date__lte=booking_date, end_date__gte=booking_date)
    return overlapping.first() or trips.first()


def find_duplicate_booking(trip: Trip, parsed: dict) -> Booking | None:
    confirmation = (parsed.get("confirmation_number") or "").strip()
    title = (parsed.get("title") or "").strip()
    if confirmation:
        match = trip.bookings.filter(confirmation_number__iexact=confirmation).first()
        if match:
            return match
    if title:
        return trip.bookings.filter(title__iexact=title).first()
    return None


def create_booking_from_parsed(trip: Trip, parsed: dict) -> Booking:
    return Booking.objects.create(
        trip=trip,
        booking_type=parsed.get("booking_type") or "Activity",
        title=parsed.get("title") or "Booking confirmation",
        confirmation_number=parsed.get("confirmation_number") or "",
        details=parsed.get("details") or "",
        start_time=parse_booking_datetime(parsed.get("start_time")),
        end_time=parse_booking_datetime(parsed.get("end_time")),
        cost=parsed.get("cost"),
    )


def create_import_draft(
    *,
    user: User,
    raw_text: str,
    source: str = "paste",
    source_subject: str = "",
    source_from: str = "",
    trip: Trip | None = None,
    parse: bool = True,
) -> BookingImportDraft:
    parsed: dict = {}
    error_message = ""
    if parse and raw_text.strip():
        try:
            parsed = LLMService.parse_booking(raw_text)
        except LLMUnavailableError as exc:
            error_message = str(exc)
        except Exception as exc:
            logger.exception("Booking parse failed")
            error_message = f"Failed to parse booking: {exc}"

    suggested = trip or (suggest_trip_for_user(user, parsed) if parsed else None)
    return BookingImportDraft.objects.create(
        user=user,
        suggested_trip=suggested,
        status=BookingImportDraft.STATUS_PENDING,
        source=source,
        source_subject=source_subject[:255],
        source_from=source_from[:255],
        raw_text=raw_text,
        parsed_json=parsed or {},
        error_message=error_message,
    )


def confirm_import_draft(
    draft: BookingImportDraft,
    *,
    trip: Trip,
    overrides: dict | None = None,
) -> Booking:
    if draft.status != BookingImportDraft.STATUS_PENDING:
        raise ValueError("Draft is not pending review.")
    if trip.user_id != draft.user_id:
        raise PermissionError("Trip does not belong to draft owner.")

    parsed = dict(draft.parsed_json or {})
    if overrides:
        for key in (
            "booking_type",
            "title",
            "confirmation_number",
            "details",
            "start_time",
            "end_time",
            "cost",
        ):
            if key in overrides and overrides[key] is not None:
                parsed[key] = overrides[key]

    duplicate = find_duplicate_booking(trip, parsed)
    if duplicate:
        # Merge: update existing booking with newer parsed fields.
        duplicate.booking_type = parsed.get("booking_type") or duplicate.booking_type
        duplicate.title = parsed.get("title") or duplicate.title
        duplicate.confirmation_number = (
            parsed.get("confirmation_number") or duplicate.confirmation_number
        )
        if parsed.get("details"):
            duplicate.details = parsed["details"]
        if parsed.get("start_time"):
            duplicate.start_time = parse_booking_datetime(parsed.get("start_time"))
        if parsed.get("end_time"):
            duplicate.end_time = parse_booking_datetime(parsed.get("end_time"))
        if parsed.get("cost") is not None:
            duplicate.cost = parsed.get("cost")
        duplicate.save()
        booking = duplicate
    else:
        booking = create_booking_from_parsed(trip, parsed)

    draft.status = BookingImportDraft.STATUS_CONFIRMED
    draft.confirmed_trip = trip
    draft.booking = booking
    draft.parsed_json = parsed
    draft.save(
        update_fields=[
            "status",
            "confirmed_trip",
            "booking",
            "parsed_json",
            "updated_at",
        ]
    )
    return booking


def reject_import_draft(draft: BookingImportDraft) -> BookingImportDraft:
    if draft.status != BookingImportDraft.STATUS_PENDING:
        raise ValueError("Draft is not pending review.")
    draft.status = BookingImportDraft.STATUS_REJECTED
    draft.save(update_fields=["status", "updated_at"])
    return draft


def process_inbound_email(
    *,
    raw_email: bytes | str,
    recipient_override: str = "",
) -> BookingImportDraft:
    extracted = extract_text_from_email(raw_email)
    recipient = recipient_override or extracted["recipients"]
    user = resolve_user_from_recipient(recipient)
    if user is None:
        raise LookupError("No user matched the inbound recipient address.")

    text = extracted["text"]
    if not text.strip():
        raise ValueError("Email contained no extractable text.")

    return create_import_draft(
        user=user,
        raw_text=text,
        source="email",
        source_subject=extracted["subject"],
        source_from=extracted["from_addr"],
    )
