from django.contrib.auth.models import User
from rest_framework import serializers

from itinerary.models import (
    Booking,
    ChecklistItem,
    DayItinerary,
    StopBlock,
    StopPhoto,
    Trip,
    TripAttendee,
    TripCreationJob,
)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "password", "email")
        extra_kwargs = {"email": {"required": False}}

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )


class TripAttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripAttendee
        fields = ("id", "name", "role")


class TripSerializer(serializers.ModelSerializer):
    duration_days = serializers.IntegerField(read_only=True)
    attendee_count = serializers.IntegerField(read_only=True, required=False)
    total_cost_local = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, required=False
    )

    class Meta:
        model = Trip
        fields = (
            "id",
            "title",
            "destination",
            "start_date",
            "end_date",
            "currency",
            "conversion_rate",
            "duration_days",
            "attendee_count",
            "total_cost_local",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class TripCreateSerializer(serializers.Serializer):
    destination = serializers.CharField(max_length=200)
    days_count = serializers.IntegerField(min_value=1, max_value=14)
    start_date = serializers.DateField()
    details = serializers.CharField(required=False, allow_blank=True, default="")
    attendees = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )


class TripCreationJobSerializer(serializers.ModelSerializer):
    trip_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = TripCreationJob
        fields = (
            "id",
            "status",
            "destination",
            "days_count",
            "start_date",
            "details",
            "trip_id",
            "error_message",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "trip_id",
            "error_message",
            "created_at",
            "updated_at",
        )


class DayItinerarySerializer(serializers.ModelSerializer):
    day_cost_local = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    day_cost_usd = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = DayItinerary
        fields = (
            "id",
            "trip_id",
            "day_number",
            "date",
            "theme",
            "early_start_banner",
            "notes",
            "day_cost_local",
            "day_cost_usd",
        )


class StopBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = StopBlock
        fields = (
            "id",
            "day_id",
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
        )


class StopMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = StopBlock
        fields = (
            "id",
            "sequence_order",
            "time_label",
            "title",
            "latitude",
            "longitude",
            "zoom_level",
            "color_hex",
        )


class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ("id", "trip_id", "category", "item_text", "is_completed", "created_at")
        read_only_fields = ("created_at",)


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = (
            "id",
            "trip_id",
            "booking_type",
            "title",
            "confirmation_number",
            "details",
            "start_time",
            "end_time",
            "cost",
        )


class StopPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = StopPhoto
        fields = ("id", "stop_id", "image_url", "uploaded_at")
        read_only_fields = ("uploaded_at",)

    def get_image_url(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class BookingImportSerializer(serializers.Serializer):
    text = serializers.CharField()


class ChatEditSerializer(serializers.Serializer):
    message = serializers.CharField()


class ReorderStopsSerializer(serializers.Serializer):
    stop_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
