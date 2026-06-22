import logging
import threading

from django.conf import settings
from django.db import connections
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from itinerary.models import (
    Booking,
    ChecklistItem,
    DayItinerary,
    StopBlock,
    StopPhoto,
    Trip,
    TripCreationJob,
)
from itinerary.querysets import trip_detail_queryset, trips_for_dashboard
from itinerary.ratelimits import enforce_ai_rate_limit, ratelimit_response
from itinerary.services.llm import LLMService, LLMUnavailableError
from itinerary.services.mutations import MutationError, apply_stop_mutations
from itinerary.services.reviews import get_stop_reviews_data
from itinerary.services.trip_creation import run_trip_creation_job
from itinerary.services.weather import get_weather_for_day
from itinerary.services.booking_import import parse_booking_datetime
from itinerary.validators import UploadValidationError, validate_image_upload

from .serializers import (
    BookingImportSerializer,
    BookingSerializer,
    ChatEditSerializer,
    ChecklistItemSerializer,
    DayItinerarySerializer,
    RegisterSerializer,
    ReorderStopsSerializer,
    StopBlockSerializer,
    StopMapSerializer,
    StopPhotoSerializer,
    TripCreateSerializer,
    TripCreationJobSerializer,
    TripSerializer,
)

logger = logging.getLogger(__name__)


def _limited(request):
    return not enforce_ai_rate_limit(request)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"id": user.id, "username": user.username},
            status=status.HTTP_201_CREATED,
        )


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if self.action == "list":
            return trips_for_dashboard(self.request.user)
        return trip_detail_queryset(Trip.objects.filter(user=self.request.user))

    def get_serializer_class(self):
        if self.action == "create":
            return TripCreateSerializer
        return TripSerializer

    def create(self, request, *args, **kwargs):
        if _limited(request):
            return ratelimit_response(request, as_json=True)
        serializer = TripCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        attendees = data.get("attendees") or []
        if not attendees:
            display = request.user.get_full_name().strip() or request.user.username
            attendees = [{"name": display, "role": "Lead traveler"}]

        job = TripCreationJob.objects.create(
            user=request.user,
            destination=data["destination"],
            days_count=data["days_count"],
            start_date=data["start_date"],
            details=data.get("details", ""),
            attendees_json=attendees,
        )
        if settings.TRIP_CREATION_SYNC:
            run_trip_creation_job(job.id)
            job.refresh_from_db()
        else:
            def run() -> None:
                connections.close_all()
                try:
                    run_trip_creation_job(job.id)
                finally:
                    connections.close_all()

            threading.Thread(target=run, daemon=True).start()

        return Response(
            TripCreationJobSerializer(job).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"])
    def days(self, request, pk=None):
        trip = self.get_object()
        days = trip.days.all()
        return Response(DayItinerarySerializer(days, many=True).data)

    @action(detail=True, methods=["get"])
    def checklist(self, request, pk=None):
        trip = self.get_object()
        items = trip.checklist_items.all()
        return Response(ChecklistItemSerializer(items, many=True).data)

    @action(detail=True, methods=["get"])
    def bookings(self, request, pk=None):
        trip = self.get_object()
        bookings = trip.bookings.all()
        return Response(BookingSerializer(bookings, many=True).data)

    @action(detail=True, methods=["post"], url_path="bookings/import")
    def import_booking(self, request, pk=None):
        if _limited(request):
            return ratelimit_response(request, as_json=True)
        trip = self.get_object()
        serializer = BookingImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data["text"].strip()
        if not text:
            return Response({"detail": "No booking details provided."}, status=400)
        try:
            parsed_data = LLMService.parse_booking(text)
            booking = Booking.objects.create(
                trip=trip,
                booking_type=parsed_data.get("booking_type", "Activity"),
                title=parsed_data.get("title", "Booking confirmation"),
                confirmation_number=parsed_data.get("confirmation_number", ""),
                details=parsed_data.get("details", ""),
                start_time=parse_booking_datetime(parsed_data.get("start_time")),
                end_time=parse_booking_datetime(parsed_data.get("end_time")),
                cost=parsed_data.get("cost"),
            )
            return Response(
                BookingSerializer(booking).data,
                status=status.HTTP_201_CREATED,
            )
        except LLMUnavailableError as exc:
            return Response({"detail": str(exc)}, status=503)
        except Exception as exc:
            logger.error("API booking import failed: %s", exc)
            return Response({"detail": f"Failed to parse booking: {exc}"}, status=500)


class TripCreationJobViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TripCreationJobSerializer

    def get_queryset(self):
        return TripCreationJob.objects.filter(user=self.request.user)


class DayViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DayItinerarySerializer

    def get_queryset(self):
        return DayItinerary.objects.filter(trip__user=self.request.user).select_related(
            "trip"
        )

    @action(detail=True, methods=["get"])
    def stops(self, request, pk=None):
        day = self.get_object()
        stops = day.stops.all().order_by("sequence_order")
        if request.query_params.get("map") == "1":
            return Response(StopMapSerializer(stops, many=True).data)
        return Response(StopBlockSerializer(stops, many=True).data)

    @action(detail=True, methods=["get"])
    def weather(self, request, pk=None):
        day = self.get_object()
        return Response(get_weather_for_day(day))

    @action(detail=True, methods=["post"], url_path="chat-edit")
    def chat_edit(self, request, pk=None):
        if _limited(request):
            return ratelimit_response(request, as_json=True)
        day = self.get_object()
        serializer = ChatEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"].strip()
        if not message:
            return Response({"detail": "Message is required."}, status=400)

        current_stops = []
        for stop in day.stops.all().order_by("sequence_order"):
            current_stops.append(
                {
                    "id": stop.id,
                    "sequence_order": stop.sequence_order,
                    "time_label": stop.time_label,
                    "title": stop.title,
                    "description": stop.description,
                    "latitude": float(stop.latitude),
                    "longitude": float(stop.longitude),
                    "cost_local": float(stop.cost_local),
                    "cost_usd": float(stop.cost_usd),
                    "meal_type": stop.meal_type,
                    "meal_name": stop.meal_name,
                    "meal_desc": stop.meal_desc,
                    "tags": stop.tags,
                    "color_hex": stop.color_hex,
                }
            )

        try:
            mutations = LLMService.edit_agenda(current_stops, message)
            apply_stop_mutations(day, mutations)
            return Response(
                {
                    "status": "success",
                    "message": message,
                    "summary": "Agenda updated successfully.",
                    "mutations_applied": len(mutations),
                }
            )
        except MutationError as exc:
            return Response({"detail": str(exc)}, status=400)
        except LLMUnavailableError as exc:
            return Response({"detail": str(exc)}, status=503)

    @action(detail=True, methods=["post"], url_path="reorder-stops")
    def reorder_stops(self, request, pk=None):
        day = self.get_object()
        serializer = ReorderStopsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stop_ids = serializer.validated_data["stop_ids"]
        for index, stop_id in enumerate(stop_ids):
            StopBlock.objects.filter(id=stop_id, day=day).update(sequence_order=index + 1)
        return Response({"status": "success", "stop_ids": stop_ids})


class StopViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StopBlockSerializer

    def get_queryset(self):
        return StopBlock.objects.filter(day__trip__user=self.request.user).select_related(
            "day__trip"
        )

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        stop = self.get_object()
        return Response(get_stop_reviews_data(stop, request=request))

    @action(detail=True, methods=["get", "post"])
    def photos(self, request, pk=None):
        stop = self.get_object()
        if request.method == "GET":
            photos = stop.user_photos.all()
            return Response(
                StopPhotoSerializer(
                    photos, many=True, context={"request": request}
                ).data
            )
        photo_file = request.FILES.get("photo")
        if not photo_file:
            return Response({"detail": "No photo file provided."}, status=400)
        try:
            validate_image_upload(photo_file)
            photo = StopPhoto.objects.create(stop=stop, image=photo_file)
            return Response(
                StopPhotoSerializer(photo, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except UploadValidationError as exc:
            return Response({"detail": str(exc)}, status=400)


class ChecklistItemViewSet(
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ChecklistItemSerializer

    def get_queryset(self):
        return ChecklistItem.objects.filter(trip__user=self.request.user)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        item = self.get_object()
        item.is_completed = not item.is_completed
        item.save(update_fields=["is_completed"])
        return Response(ChecklistItemSerializer(item).data)


class StopPhotoViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = StopPhotoSerializer

    def get_queryset(self):
        return StopPhoto.objects.filter(stop__day__trip__user=self.request.user)
