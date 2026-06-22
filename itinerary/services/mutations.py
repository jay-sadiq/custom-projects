import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction

from itinerary.models import StopBlock

logger = logging.getLogger(__name__)

ALLOWED_STOP_FIELDS = frozenset({
    "sequence_order",
    "time_label",
    "title",
    "description",
    "latitude",
    "longitude",
    "zoom_level",
    "start_time_of_day",
    "end_time_of_day",
    "cost_local",
    "cost_usd",
    "meal_type",
    "meal_name",
    "meal_desc",
    "meal_price_label",
    "meal_recommendation",
    "tags",
    "color_hex",
})

REQUIRED_CREATE_FIELDS = frozenset({"title", "latitude", "longitude"})


class MutationError(Exception):
    """Raised when LLM mutations cannot be applied safely."""


def filter_stop_fields(fields: dict) -> dict:
    if not isinstance(fields, dict):
        return {}
    return {key: value for key, value in fields.items() if key in ALLOWED_STOP_FIELDS}


def _parse_time(value):
    if value is None or value == "":
        return None
    if hasattr(value, "hour"):
        return value
    if isinstance(value, str):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
    raise MutationError(f"Invalid time value: {value!r}")


def coerce_stop_fields(fields: dict) -> dict:
    coerced = dict(fields)

    int_fields = ("sequence_order", "zoom_level")
    for name in int_fields:
        if name in coerced and coerced[name] is not None:
            coerced[name] = int(coerced[name])

    decimal_fields = ("latitude", "longitude", "cost_local", "cost_usd")
    for name in decimal_fields:
        if name in coerced and coerced[name] is not None:
            try:
                coerced[name] = Decimal(str(coerced[name]))
            except (InvalidOperation, ValueError) as exc:
                raise MutationError(f"Invalid {name}: {coerced[name]!r}") from exc

    for name in ("start_time_of_day", "end_time_of_day"):
        if name in coerced:
            coerced[name] = _parse_time(coerced[name])

    if "tags" in coerced and coerced["tags"] is not None:
        tags = coerced["tags"]
        if not isinstance(tags, list):
            raise MutationError("tags must be a list")
        coerced["tags"] = [str(tag) for tag in tags]

    return coerced


def validate_create_fields(fields: dict) -> None:
    missing = [name for name in REQUIRED_CREATE_FIELDS if not fields.get(name)]
    if missing:
        raise MutationError(
            f"CREATE missing required fields: {', '.join(sorted(missing))}"
        )


def _reindex_stops(day) -> None:
    all_stops = list(day.stops.all().order_by("sequence_order"))
    for order_idx, stop in enumerate(all_stops):
        if stop.sequence_order != order_idx + 1:
            stop.sequence_order = order_idx + 1
            stop.save(update_fields=["sequence_order"])


def apply_stop_mutations(day, mutations) -> None:
    if not isinstance(mutations, list):
        raise MutationError("AI response must be a list of mutations")

    with transaction.atomic():
        for mut in mutations:
            if not isinstance(mut, dict):
                raise MutationError("Each mutation must be an object")

            action = mut.get("action")
            stop_id = mut.get("stop_id")
            fields = filter_stop_fields(mut.get("fields", {}))

            if action == "DELETE":
                if not stop_id:
                    continue
                StopBlock.objects.filter(id=stop_id, day=day).delete()
            elif action == "UPDATE":
                if not stop_id or not fields:
                    continue
                fields = coerce_stop_fields(fields)
                StopBlock.objects.filter(id=stop_id, day=day).update(**fields)
            elif action == "CREATE":
                if "sequence_order" not in fields:
                    fields["sequence_order"] = day.stops.count() + 1
                fields = coerce_stop_fields(fields)
                validate_create_fields(fields)
                if "description" not in fields:
                    fields["description"] = ""
                if "time_label" not in fields:
                    fields["time_label"] = fields["title"]
                StopBlock.objects.create(day=day, **fields)
            else:
                logger.warning("Ignoring unknown mutation action: %s", action)

        _reindex_stops(day)
