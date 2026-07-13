import json
import logging
import threading
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import connections

from .models import (
    DayItinerary,
    StopBlock,
    Booking,
    ChecklistItem,
    PlaceDetail,
    StopPhoto,
    TripCreationJob,
)
from .permissions import (
    dashboard_trips_for_user,
    get_checklist_item_for_user,
    get_day_for_user,
    get_day_for_user_trip,
    get_photo_for_user,
    get_stop_for_user,
    get_trip_detail_for_user,
    get_trip_for_user,
)
from .services.booking_import import parse_booking_datetime
from .services.pdf import extract_text_from_pdf
from .services.llm import LLMService, LLMUnavailableError
from .validators import UploadValidationError, validate_image_upload, validate_pdf_upload
from .services.mutations import MutationError, apply_stop_mutations
from .services.places import fetch_google_place_photo, normalize_photo_entries
from .services.reviews import get_stop_reviews_data
from .services.weather import get_weather_for_day
from .services.trip_creation import run_trip_creation_job
from .services.attendees import parse_attendees_from_request
from .ratelimits import enforce_ai_rate_limit, ratelimit_response

logger = logging.getLogger(__name__)


def _start_trip_creation_thread(job_id: int) -> None:
    def run() -> None:
        connections.close_all()
        try:
            run_trip_creation_job(job_id)
        finally:
            connections.close_all()

    threading.Thread(target=run, daemon=True).start()


def _render_chat_messages(request, message, ai_message, trigger_refresh=False):
    response = render(
        request,
        "itinerary/partials/chat_messages.html",
        {"message": message, "ai_message": ai_message},
    )
    if trigger_refresh:
        response["HX-Trigger"] = "refresh-stops"
    return response

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    from itinerary.models import BookingImportDraft
    from itinerary.services.booking_import import forwarding_address_for, get_or_create_profile

    get_or_create_profile(request.user)
    trips = dashboard_trips_for_user(request.user)
    pending_imports = BookingImportDraft.objects.filter(
        user=request.user,
        status=BookingImportDraft.STATUS_PENDING,
    ).count()
    return render(
        request,
        "itinerary/dashboard.html",
        {
            "trips": trips,
            "forwarding_address": forwarding_address_for(request.user),
            "pending_import_count": pending_imports,
        },
    )


@login_required
def booking_imports_inbox(request):
    from itinerary.models import BookingImportDraft
    from itinerary.services.booking_import import forwarding_address_for, get_or_create_profile

    get_or_create_profile(request.user)
    drafts = (
        BookingImportDraft.objects.filter(user=request.user)
        .select_related("suggested_trip", "confirmed_trip", "booking")
        .order_by("-created_at")[:50]
    )
    trips = dashboard_trips_for_user(request.user)
    return render(
        request,
        "itinerary/booking_imports.html",
        {
            "drafts": drafts,
            "trips": trips,
            "forwarding_address": forwarding_address_for(request.user),
        },
    )


@login_required
@require_POST
def booking_import_preview(request):
    """Paste text → pending draft (review before save)."""
    from itinerary.services.booking_import import create_import_draft

    if not enforce_ai_rate_limit(request):
        return ratelimit_response(request)
    text = (request.POST.get("paste_text") or "").strip()
    if not text:
        return HttpResponse("Paste booking confirmation text first.", status=400)
    trip_id = request.POST.get("trip_id")
    trip = None
    if trip_id:
        trip = get_trip_for_user(request.user, trip_id)
    draft = create_import_draft(
        user=request.user,
        raw_text=text,
        source="paste",
        trip=trip,
    )
    return render(
        request,
        "itinerary/partials/booking_import_draft_card.html",
        {"draft": draft, "trips": dashboard_trips_for_user(request.user)},
    )


@login_required
@require_POST
def booking_import_confirm(request, draft_id):
    from itinerary.models import BookingImportDraft
    from itinerary.services.booking_import import confirm_import_draft

    draft = get_object_or_404(
        BookingImportDraft, id=draft_id, user=request.user
    )
    trip_id = request.POST.get("trip_id")
    if not trip_id:
        return HttpResponse("Select a trip before confirming.", status=400)
    trip = get_trip_for_user(request.user, trip_id)
    overrides = {
        "title": request.POST.get("title") or None,
        "booking_type": request.POST.get("booking_type") or None,
        "confirmation_number": request.POST.get("confirmation_number") or None,
        "details": request.POST.get("details") or None,
    }
    overrides = {k: v for k, v in overrides.items() if v}
    try:
        booking = confirm_import_draft(draft, trip=trip, overrides=overrides or None)
    except ValueError as exc:
        return HttpResponse(str(exc), status=400)
    return render(
        request,
        "itinerary/partials/booking_imported.html",
        {"booking": booking},
    )


@login_required
@require_POST
def booking_import_reject(request, draft_id):
    from itinerary.models import BookingImportDraft
    from itinerary.services.booking_import import reject_import_draft

    draft = get_object_or_404(
        BookingImportDraft, id=draft_id, user=request.user
    )
    try:
        reject_import_draft(draft)
    except ValueError as exc:
        return HttpResponse(str(exc), status=400)
    return HttpResponse(
        '<div class="cost-row" style="opacity:0.7;">Rejected import draft.</div>'
    )


@login_required
@require_POST
def create_trip(request):
    if not enforce_ai_rate_limit(request):
        return ratelimit_response(request)
    destination = request.POST.get('destination')
    days_count = int(request.POST.get('days_count', 3))
    start_date_str = request.POST.get('start_date')
    details = request.POST.get('details', '')

    if not destination or not start_date_str:
        return HttpResponse("Please provide destination and start date.", status=400)

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)

    job = TripCreationJob.objects.create(
        user=request.user,
        destination=destination,
        days_count=days_count,
        start_date=start_date,
        details=details,
        attendees_json=parse_attendees_from_request(request.POST, request.user),
    )

    if settings.TRIP_CREATION_SYNC:
        run_trip_creation_job(job.id)
        job.refresh_from_db()
        if job.status == TripCreationJob.STATUS_FAILED:
            return HttpResponse(f"AI generation failed: {job.error_message}", status=500)
        response = HttpResponse()
        response['HX-Redirect'] = f'/trip/{job.trip_id}/'
        return response

    _start_trip_creation_thread(job.id)
    return render(
        request,
        "itinerary/partials/trip_creation_status.html",
        {"job": job},
    )


@login_required
def trip_creation_status(request, job_id):
    job = get_object_or_404(TripCreationJob, id=job_id, user=request.user)
    if job.status == TripCreationJob.STATUS_COMPLETED and job.trip_id:
        response = render(
            request,
            "itinerary/partials/trip_creation_status.html",
            {"job": job},
        )
        response["HX-Redirect"] = f"/trip/{job.trip_id}/"
        return response
    return render(
        request,
        "itinerary/partials/trip_creation_status.html",
        {"job": job},
    )

@login_required
def trip_detail(request, trip_id):
    trip = get_trip_detail_for_user(request.user, trip_id)
    days = list(trip.days.all())

    day_num = int(request.GET.get('day', 1))
    current_day = next((day for day in days if day.day_number == day_num), None)
    if current_day is None and days:
        current_day = days[0]

    checklist_items = list(trip.checklist_items.all())
    categories = list(dict.fromkeys(item.category for item in checklist_items))
    
    hours_range = [
        "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
        "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM",
        "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"
    ]
    
    context = {
        'trip': trip,
        'days': days,
        'current_day': current_day,
        'checklist_items': checklist_items,
        'checklist_categories': categories,
        'hours_range': hours_range,
    }
    return render(request, 'itinerary/trip_detail.html', context)

@login_required
def day_detail(request, trip_id, day_number):
    trip = get_trip_detail_for_user(request.user, trip_id)
    days = list(trip.days.all())
    day = next((item for item in days if item.day_number == day_number), None)
    if day is None:
        day = get_object_or_404(DayItinerary, trip=trip, day_number=day_number)
    
    hours_range = [
        "06:00 AM", "07:00 AM", "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM",
        "12:00 PM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM",
        "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM", "10:00 PM", "11:00 PM"
    ]
    
    context = {
        'trip': trip,
        'current_day': day,
        'days': days,
        'hours_range': hours_range,
    }
    return render(request, 'itinerary/partials/day_panel.html', context)

@login_required
@require_POST
def save_notes(request, day_id):
    day = get_day_for_user(request.user, day_id)
    day.notes = request.POST.get('notes', '')
    day.save()
    
    # Return HTMX label
    return HttpResponse('<span class="notes-saved-ok">Saved ✓</span>')

@login_required
@require_POST
def toggle_checklist_item(request, item_id):
    item = get_checklist_item_for_user(request.user, item_id)
    item.is_completed = not item.is_completed
    item.save()

    return render(
        request,
        "itinerary/partials/checklist_item_row.html",
        {"item": item},
    )

@login_required
def get_stops_json(request, trip_id, day_number):
    day = get_day_for_user_trip(request.user, trip_id, day_number)
    
    stops_list = []
    for stop in day.stops.all().order_by('sequence_order'):
        stops_list.append({
            'id': stop.id,
            'sequence_order': stop.sequence_order,
            'time_label': stop.time_label,
            'title': stop.title,
            'latitude': float(stop.latitude),
            'longitude': float(stop.longitude),
            'zoom': stop.zoom_level,
            'color': stop.color_hex,
        })
    return JsonResponse(stops_list, safe=False)

@login_required
@require_POST
def chat_edit(request, trip_id, day_number):
    if not enforce_ai_rate_limit(request):
        return ratelimit_response(request)
    day = get_day_for_user_trip(request.user, trip_id, day_number)
    message = request.POST.get('message', '').strip()
    
    if not message:
        return HttpResponse("", status=400)
    
    # 1. Format current stops as JSON for LLM context
    current_stops = []
    for s in day.stops.all().order_by('sequence_order'):
        current_stops.append({
            'id': s.id,
            'sequence_order': s.sequence_order,
            'time_label': s.time_label,
            'title': s.title,
            'description': s.description,
            'latitude': float(s.latitude),
            'longitude': float(s.longitude),
            'cost_local': float(s.cost_local),
            'cost_usd': float(s.cost_usd),
            'meal_type': s.meal_type,
            'meal_name': s.meal_name,
            'meal_desc': s.meal_desc,
            'tags': s.tags,
            'color_hex': s.color_hex
        })
    
    # 2. Get mutations list from LLMService
    try:
        mutations = LLMService.edit_agenda(current_stops, message)
    except Exception as e:
        logger.error(f"Error parsing edit command: {e}")
        return _render_chat_messages(
            request,
            message,
            f"⚠️ AI editing failed: {e}",
        )

    try:
        apply_stop_mutations(day, mutations)
        return _render_chat_messages(
            request,
            message,
            "✓ Agenda updated! Reordered stops have been synchronized.",
            trigger_refresh=True,
        )
    except MutationError as e:
        logger.error(f"Error applying mutations: {e}")
        return _render_chat_messages(request, message, f"⚠️ Error applying edits: {e}")
    except LLMUnavailableError as e:
        return _render_chat_messages(request, message, f"⚠️ {e}")
    except Exception as e:
        logger.error(f"Error applying mutations: {e}")
        return _render_chat_messages(request, message, f"⚠️ Error applying edits: {e}")

@login_required
def get_stop_reviews(request, stop_id):
    stop = get_stop_for_user(request.user, stop_id)
    data = get_stop_reviews_data(stop, request=request)
    place_detail, _ = PlaceDetail.objects.get_or_create(stop=stop)
    return render(
        request,
        "itinerary/partials/stop_reviews.html",
        {
            "stop": stop,
            "place_detail": place_detail,
            "photos": data["photos"],
            "is_demo_data": data["is_demo_data"],
        },
    )


@login_required
def proxy_place_photo(request, stop_id, photo_index):
    stop = get_stop_for_user(request.user, stop_id)
    place_detail = get_object_or_404(PlaceDetail, stop=stop)
    photos = normalize_photo_entries(place_detail.photos_json)

    try:
        photo_index = int(photo_index)
    except (TypeError, ValueError):
        return HttpResponse(status=404)

    if photo_index < 0 or photo_index >= len(photos):
        return HttpResponse(status=404)

    photo = photos[photo_index]
    if photo.get("type") != "google_ref":
        return HttpResponse(status=404)

    try:
        content, content_type = fetch_google_place_photo(photo["ref"])
    except Exception as e:
        logger.error(f"Error proxying Google place photo: {e}")
        return HttpResponse(status=502)

    response = HttpResponse(content, content_type=content_type)
    response["Cache-Control"] = "private, max-age=86400"
    return response

@login_required
@require_POST
def parse_booking_pdf(request, trip_id):
    trip = get_trip_for_user(request.user, trip_id)
    uploaded_file = request.FILES.get('booking_file')
    paste_text = request.POST.get('paste_text', '').strip()
    
    text_to_parse = paste_text
    
    # Simple PDF text extractor if file uploaded
    if uploaded_file:
        try:
            validate_pdf_upload(uploaded_file)
            pdf_text = extract_text_from_pdf(uploaded_file)
            if pdf_text.strip():
                text_to_parse += f"\n{pdf_text}"
            else:
                text_to_parse += f"\nUploaded PDF ({uploaded_file.name}) contained no extractable text."
        except UploadValidationError as e:
            return HttpResponse(str(e), status=400)
        except Exception as e:
            return HttpResponse(f"Error reading PDF: {e}", status=400)
            
    if not text_to_parse:
        return HttpResponse("No booking details provided.", status=400)
        
    try:
        parsed_data = LLMService.parse_booking(text_to_parse)
        booking = Booking.objects.create(
            trip=trip,
            booking_type=parsed_data.get('booking_type', 'Activity'),
            title=parsed_data.get('title', 'Booking confirmation'),
            confirmation_number=parsed_data.get('confirmation_number', ''),
            details=parsed_data.get('details', ''),
            start_time=parse_booking_datetime(parsed_data.get('start_time')),
            end_time=parse_booking_datetime(parsed_data.get('end_time')),
            cost=parsed_data.get('cost')
        )

        return render(
            request,
            "itinerary/partials/booking_imported.html",
            {"booking": booking},
        )
    except LLMUnavailableError as e:
        return HttpResponse(str(e), status=503)
    except Exception as e:
        logger.error(f"Error parsing booking: {e}")
        return HttpResponse(f"Failed to parse booking: {e}", status=500)

@login_required
def edit_day(request, day_id):
    day = get_day_for_user(request.user, day_id)
    trip = day.trip
    if request.method == 'POST':
        day.theme = request.POST.get('theme', '')
        day.early_start_banner = request.POST.get('early_start_banner', '')
        day.save()
        return render(request, 'itinerary/partials/day_header_card.html', {
            'current_day': day,
            'trip': trip
        })
    return render(request, 'itinerary/partials/edit_day_form.html', {
        'day': day,
        'trip': trip
    })

@login_required
def view_day_header(request, day_id):
    day = get_day_for_user(request.user, day_id)
    return render(request, 'itinerary/partials/day_header_card.html', {
        'current_day': day,
        'trip': day.trip
    })

@login_required
def edit_stop(request, stop_id):
    stop = get_stop_for_user(request.user, stop_id)
    index = int(request.GET.get('index', 0))
    
    if request.method == 'POST':
        stop.time_label = request.POST.get('time_label', '')
        stop.title = request.POST.get('title', '')
        stop.description = request.POST.get('description', '')
        stop.latitude = float(request.POST.get('latitude', 0.0))
        stop.longitude = float(request.POST.get('longitude', 0.0))
        stop.zoom_level = int(request.POST.get('zoom_level', 15))
        
        cost_local = request.POST.get('cost_local', '0.00')
        stop.cost_local = float(cost_local) if cost_local else 0.00
        
        cost_usd = request.POST.get('cost_usd', '0.00')
        stop.cost_usd = float(cost_usd) if cost_usd else 0.00
        
        stop.meal_type = request.POST.get('meal_type', '')
        stop.meal_name = request.POST.get('meal_name', '')
        stop.meal_desc = request.POST.get('meal_desc', '')
        stop.meal_price_label = request.POST.get('meal_price_label', '')
        stop.meal_recommendation = request.POST.get('meal_recommendation', '')
        
        tags_raw = request.POST.get('tags_raw', '')
        stop.tags = [t.strip() for t in tags_raw.split(',') if t.strip()]
        
        stop.color_hex = request.POST.get('color_hex', '#E67E22')
        
        # Optional: Edit start/end time directly
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        if start_time_str:
            stop.start_time_of_day = datetime.strptime(start_time_str, "%H:%M").time()
        if end_time_str:
            stop.end_time_of_day = datetime.strptime(end_time_str, "%H:%M").time()
            
        stop.save()
        
        response = render(request, 'itinerary/partials/stop_block_card.html', {
            'stop': stop,
            'index': index
        })
        response['HX-Trigger'] = 'refresh-stops'
        return response

    tags_str = ", ".join(stop.tags) if stop.tags else ""
    return render(request, 'itinerary/partials/edit_stop_form.html', {
        'stop': stop,
        'index': index,
        'tags_str': tags_str
    })

@login_required
def view_stop(request, stop_id):
    stop = get_stop_for_user(request.user, stop_id)
    index = int(request.GET.get('index', 0))
    return render(request, 'itinerary/partials/stop_block_card.html', {
        'stop': stop,
        'index': index
    })

@login_required
@require_POST
def delete_stop(request, stop_id):
    stop = get_stop_for_user(request.user, stop_id)
    day = stop.day
    stop.delete()
    
    # Reorder remaining stops
    all_stops = list(day.stops.all().order_by('sequence_order'))
    for idx, s in enumerate(all_stops):
        if s.sequence_order != idx + 1:
            s.sequence_order = idx + 1
            s.save()
            
    response = HttpResponse("")
    response['HX-Trigger'] = 'refresh-stops'
    return response

@login_required
@require_POST
def reorder_stops(request, trip_id, day_number):
    day = get_day_for_user_trip(request.user, trip_id, day_number)
    
    stop_ids_raw = request.POST.get('stop_ids', '[]')
    try:
        stop_ids = json.loads(stop_ids_raw)
        
        for idx, stop_id in enumerate(stop_ids):
            StopBlock.objects.filter(id=stop_id, day=day).update(sequence_order=idx + 1)
            
        response = HttpResponse("Reordered successfully")
        response['HX-Trigger'] = 'refresh-stops'
        return response
    except Exception as e:
        logger.error(f"Error reordering stops: {e}")
        return HttpResponse(f"Error: {e}", status=400)

@login_required
def get_weather(request, day_id):
    day = get_day_for_user(request.user, day_id)
    weather = get_weather_for_day(day)
    return HttpResponse(
        f"<span>🌡️ {weather['label']}: {weather['emoji']} "
        f"{weather['temperature_c']}°C · {weather['condition']}</span>"
    )





@login_required
@require_POST
def update_stop_times(request, stop_id):
    stop = get_stop_for_user(request.user, stop_id)
    start_str = request.POST.get('start_time')  # e.g., "09:30"
    end_str = request.POST.get('end_time')      # e.g., "11:00"
    
    try:
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        
        stop.start_time_of_day = start_time
        stop.end_time_of_day = end_time
        
        # update time label
        desc_part = ""
        if "—" in stop.time_label:
            parts = stop.time_label.split("—", 1)
            if len(parts) > 1:
                desc_part = " —" + parts[1]
                
        start_fmt = start_time.strftime("%I:%M %p").lstrip('0')
        if desc_part:
            stop.time_label = f"{start_fmt}{desc_part}"
        else:
            end_fmt = end_time.strftime("%I:%M %p").lstrip('0')
            stop.time_label = f"{start_fmt} - {end_fmt}"
            
        stop.save()
        
        # Re-index chronologically
        day = stop.day
        stops = list(day.stops.all().order_by('start_time_of_day', 'sequence_order'))
        for idx, s in enumerate(stops):
            s.sequence_order = idx + 1
            s.save()
            
        return JsonResponse({
            'status': 'success',
            'time_label': stop.time_label,
            'start_time': start_str,
            'end_time': end_str,
            'sequence_order': stop.sequence_order
        })
    except Exception as e:
        logger.error(f"Error updating stop times: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def upload_stop_photo(request, stop_id):
    stop = get_stop_for_user(request.user, stop_id)
    photo_file = request.FILES.get('photo')
    if not photo_file:
        return JsonResponse({'status': 'error', 'message': 'No photo file provided'}, status=400)
    
    try:
        validate_image_upload(photo_file)
        photo = StopPhoto.objects.create(stop=stop, image=photo_file)
        return JsonResponse({
            'status': 'success',
            'photo_id': photo.id,
            'photo_url': photo.image.url
        })
    except UploadValidationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error uploading photo: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def delete_stop_photo(request, photo_id):
    photo = get_photo_for_user(request.user, photo_id)
    photo.delete()
    return JsonResponse({'status': 'success'})
