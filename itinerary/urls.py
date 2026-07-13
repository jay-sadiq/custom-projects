from django.urls import path
from . import views

urlpatterns = [
    # Auth Views
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('', views.dashboard, name='dashboard'),
    path('bookings/imports/', views.booking_imports_inbox, name='booking_imports_inbox'),
    path('bookings/imports/preview/', views.booking_import_preview, name='booking_import_preview'),
    path(
        'bookings/imports/<int:draft_id>/confirm/',
        views.booking_import_confirm,
        name='booking_import_confirm',
    ),
    path(
        'bookings/imports/<int:draft_id>/reject/',
        views.booking_import_reject,
        name='booking_import_reject',
    ),
    path('trip/create/', views.create_trip, name='create_trip'),
    path('trip/create/status/<int:job_id>/', views.trip_creation_status, name='trip_creation_status'),
    path('trip/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trip/<int:trip_id>/day/<int:day_number>/', views.day_detail, name='day_detail'),
    path('day/<int:day_id>/notes/', views.save_notes, name='save_notes'),
    path('day/<int:day_id>/weather/', views.get_weather, name='get_weather'),

    # Checklist & Booking Imports
    path('checklist/toggle/<int:item_id>/', views.toggle_checklist_item, name='toggle_checklist_item'),
    path('trip/<int:trip_id>/booking/import/', views.parse_booking_pdf, name='parse_booking_pdf'),
    
    # Day Header Editing
    path('day/<int:day_id>/edit/', views.edit_day, name='edit_day'),
    path('day/<int:day_id>/view-header/', views.view_day_header, name='view_day_header'),
    
    # Stop Card Editing & Deleting
    path('stop/<int:stop_id>/edit/', views.edit_stop, name='edit_stop'),
    path('stop/<int:stop_id>/view-card/', views.view_stop, name='view_stop'),
    path('stop/<int:stop_id>/delete/', views.delete_stop, name='delete_stop'),
    
    # Drag-Adjust Times & Photos
    path('stop/<int:stop_id>/update-times/', views.update_stop_times, name='update_stop_times'),
    path('stop/<int:stop_id>/upload-photo/', views.upload_stop_photo, name='upload_stop_photo'),
    path('photo/<int:photo_id>/delete/', views.delete_stop_photo, name='delete_stop_photo'),
    
    # LLM Dynamic Agendas & Reviews
    path('trip/<int:trip_id>/day/<int:day_number>/chat-edit/', views.chat_edit, name='chat_edit'),
    path('stop/<int:stop_id>/reviews/', views.get_stop_reviews, name='get_stop_reviews'),
    path(
        'stop/<int:stop_id>/place-photo/<int:photo_index>/',
        views.proxy_place_photo,
        name='proxy_place_photo',
    ),
    
    # Map Geodata API
    path('trip/<int:trip_id>/day/<int:day_number>/stops/json/', views.get_stops_json, name='get_stops_json'),
    path('trip/<int:trip_id>/day/<int:day_number>/reorder/', views.reorder_stops, name='reorder_stops'),
]

