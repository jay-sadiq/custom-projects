import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import 'models/trip_models.dart';

class TripsRepository {
  TripsRepository({required ApiClient apiClient}) : _dio = apiClient.dio;

  final Dio _dio;

  Future<List<Trip>> fetchTrips() async {
    final response = await _dio.get<dynamic>('/trips/');
    final data = response.data;
    final list = data is Map<String, dynamic>
        ? data['results'] as List<dynamic>? ?? []
        : data as List<dynamic>? ?? [];
    return list
        .cast<Map<String, dynamic>>()
        .map(Trip.fromJson)
        .toList();
  }

  Future<Trip> fetchTrip(int tripId) async {
    final response = await _dio.get<Map<String, dynamic>>('/trips/$tripId/');
    return Trip.fromJson(response.data ?? {});
  }

  Future<List<DayItinerary>> fetchDays(int tripId) async {
    final response =
        await _dio.get<List<dynamic>>('/trips/$tripId/days/');
    return (response.data ?? [])
        .cast<Map<String, dynamic>>()
        .map(DayItinerary.fromJson)
        .toList();
  }

  Future<List<StopBlock>> fetchStops(int dayId, {bool mapOnly = false}) async {
    final response = await _dio.get<List<dynamic>>(
      '/days/$dayId/stops/',
      queryParameters: mapOnly ? {'map': '1'} : null,
    );
    return (response.data ?? [])
        .cast<Map<String, dynamic>>()
        .map(StopBlock.fromJson)
        .toList();
  }

  Future<DayItinerary> updateDayNotes(int dayId, String notes) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/days/$dayId/',
      data: {'notes': notes},
    );
    return DayItinerary.fromJson(response.data ?? {});
  }

  Future<List<ChecklistItem>> fetchChecklist(int tripId) async {
    final response =
        await _dio.get<List<dynamic>>('/trips/$tripId/checklist/');
    return (response.data ?? [])
        .cast<Map<String, dynamic>>()
        .map(ChecklistItem.fromJson)
        .toList();
  }

  Future<ChecklistItem> toggleChecklistItem(int itemId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/checklist-items/$itemId/toggle/',
    );
    return ChecklistItem.fromJson(response.data ?? {});
  }

  Future<TripCreationJob> createTrip({
    required String destination,
    required int daysCount,
    required DateTime startDate,
    String details = '',
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/trips/',
      data: {
        'destination': destination,
        'days_count': daysCount,
        'start_date': _formatDate(startDate),
        'details': details,
      },
    );
    return TripCreationJob.fromJson(response.data ?? {});
  }

  Future<TripCreationJob> fetchTripJob(int jobId) async {
    final response =
        await _dio.get<Map<String, dynamic>>('/trip-jobs/$jobId/');
    return TripCreationJob.fromJson(response.data ?? {});
  }

  Future<Map<String, dynamic>> chatEditDay(int dayId, String message) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/days/$dayId/chat-edit/',
      data: {'message': message},
    );
    return response.data ?? {};
  }

  String _formatDate(DateTime date) {
    final year = date.year.toString().padLeft(4, '0');
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '$year-$month-$day';
  }
}
