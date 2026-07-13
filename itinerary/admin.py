from django.contrib import admin

from .models import (
    Booking,
    BookingImportDraft,
    ChecklistItem,
    DayItinerary,
    PlaceDetail,
    StopBlock,
    StopPhoto,
    Trip,
    TripAttendee,
    TripCreationJob,
    UserProfile,
)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("title", "destination", "user", "start_date", "end_date", "created_at")
    list_filter = ("destination", "start_date", "created_at")
    search_fields = ("title", "destination", "user__username")
    raw_id_fields = ("user",)


@admin.register(DayItinerary)
class DayItineraryAdmin(admin.ModelAdmin):
    list_display = ("trip", "day_number", "date", "theme")
    list_filter = ("date",)
    search_fields = ("trip__title", "theme")
    raw_id_fields = ("trip",)


@admin.register(StopBlock)
class StopBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "day", "sequence_order", "time_label", "cost_local")
    list_filter = ("meal_type",)
    search_fields = ("title", "description")
    raw_id_fields = ("day",)


@admin.register(TripAttendee)
class TripAttendeeAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "trip")
    search_fields = ("name", "role", "trip__title")
    raw_id_fields = ("trip",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("title", "booking_type", "trip", "start_time", "end_time", "cost")
    list_filter = ("booking_type",)
    search_fields = ("title", "confirmation_number")
    raw_id_fields = ("trip",)


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("item_text", "category", "trip", "is_completed")
    list_filter = ("category", "is_completed")
    search_fields = ("item_text",)
    raw_id_fields = ("trip",)


@admin.register(PlaceDetail)
class PlaceDetailAdmin(admin.ModelAdmin):
    list_display = ("stop", "place_id", "rating", "updated_at")
    search_fields = ("stop__title", "place_id")
    raw_id_fields = ("stop",)


@admin.register(StopPhoto)
class StopPhotoAdmin(admin.ModelAdmin):
    list_display = ("stop", "uploaded_at")
    raw_id_fields = ("stop",)


@admin.register(TripCreationJob)
class TripCreationJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "destination", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("destination", "user__username")
    raw_id_fields = ("user", "trip")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email_import_token")
    search_fields = ("user__username", "email_import_token")
    raw_id_fields = ("user",)


@admin.register(BookingImportDraft)
class BookingImportDraftAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "source", "source_subject", "created_at")
    list_filter = ("status", "source", "created_at")
    search_fields = ("source_subject", "source_from", "user__username")
    raw_id_fields = ("user", "suggested_trip", "confirmed_trip", "booking")
