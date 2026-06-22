import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/cache/trip_cache.dart';
import '../../core/network/connectivity_service.dart';
import 'models/trip_models.dart';

class TripsRepository {
  TripsRepository({
    required ApiClient apiClient,
    TripCacheService? cache,
    OnlineStatusNotifier? onlineStatus,
  })  : _dio = apiClient.dio,
        _cache = cache ?? TripCacheService.instance,
        _onlineStatus = onlineStatus;

  final Dio _dio;
  final TripCacheService _cache;
  final OnlineStatusNotifier? _onlineStatus;

  Future<List<Trip>> fetchTrips() async {
    return _withCache<List<Trip>>(
      fetch: () async {
        final response = await _dio.get<dynamic>('/trips/');
        final data = response.data;
        final list = data is Map<String, dynamic>
            ? data['results'] as List<dynamic>? ?? []
            : data as List<dynamic>? ?? [];
        final maps = list.cast<Map<String, dynamic>>();
        await _cache.saveTripsList(maps);
        return maps.map(Trip.fromJson).toList();
      },
      readCache: () {
        final cached = _cache.getTripsList();
        if (cached == null) return null;
        return cached.map(Trip.fromJson).toList();
      },
    );
  }

  Future<Trip> fetchTrip(int tripId) async {
    return _withCache<Trip>(
      fetch: () async {
        final response = await _dio.get<Map<String, dynamic>>('/trips/$tripId/');
        final data = response.data ?? {};
        await _cache.saveTrip(tripId, data);
        return Trip.fromJson(data);
      },
      readCache: () {
        final cached = _cache.getTrip(tripId);
        if (cached == null) return null;
        return Trip.fromJson(cached);
      },
    );
  }

  Future<List<DayItinerary>> fetchDays(int tripId) async {
    return _withCache<List<DayItinerary>>(
      fetch: () async {
        final response =
            await _dio.get<List<dynamic>>('/trips/$tripId/days/');
        final maps = (response.data ?? []).cast<Map<String, dynamic>>();
        await _cache.saveDays(tripId, maps);
        return maps.map(DayItinerary.fromJson).toList();
      },
      readCache: () {
        final cached = _cache.getDays(tripId);
        if (cached == null) return null;
        return cached.map(DayItinerary.fromJson).toList();
      },
    );
  }

  Future<List<StopBlock>> fetchStops(int dayId, {bool mapOnly = false}) async {
    if (mapOnly) {
      final response = await _dio.get<List<dynamic>>(
        '/days/$dayId/stops/',
        queryParameters: {'map': '1'},
      );
      return (response.data ?? [])
          .cast<Map<String, dynamic>>()
          .map(StopBlock.fromJson)
          .toList();
    }

    return _withCache<List<StopBlock>>(
      fetch: () async {
        final response = await _dio.get<List<dynamic>>('/days/$dayId/stops/');
        final maps = (response.data ?? []).cast<Map<String, dynamic>>();
        await _cache.saveStops(dayId, maps);
        return maps.map(StopBlock.fromJson).toList();
      },
      readCache: () {
        final cached = _cache.getStops(dayId);
        if (cached == null) return null;
        return cached.map(StopBlock.fromJson).toList();
      },
    );
  }

  Future<DayItinerary> updateDayNotes(int dayId, String notes) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/days/$dayId/',
      data: {'notes': notes},
    );
    final day = DayItinerary.fromJson(response.data ?? {});
    final days = _cache.getDays(day.tripId);
    if (days != null) {
      final updated = days
          .map((item) => item['id'] == dayId ? response.data! : item)
          .cast<Map<String, dynamic>>()
          .toList();
      await _cache.saveDays(day.tripId, updated);
    }
    return day;
  }

  Future<List<ChecklistItem>> fetchChecklist(int tripId) async {
    return _withCache<List<ChecklistItem>>(
      fetch: () async {
        final response =
            await _dio.get<List<dynamic>>('/trips/$tripId/checklist/');
        final maps = (response.data ?? []).cast<Map<String, dynamic>>();
        await _cache.saveChecklist(tripId, maps);
        return maps.map(ChecklistItem.fromJson).toList();
      },
      readCache: () {
        final cached = _cache.getChecklist(tripId);
        if (cached == null) return null;
        return cached.map(ChecklistItem.fromJson).toList();
      },
    );
  }

  Future<ChecklistItem> toggleChecklistItem(int itemId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/checklist-items/$itemId/toggle/',
    );
    return ChecklistItem.fromJson(response.data ?? {});
  }

  Future<DayWeather> fetchDayWeather(int dayId) async {
    final response =
        await _dio.get<Map<String, dynamic>>('/days/$dayId/weather/');
    return DayWeather.fromJson(response.data ?? {});
  }

  Future<StopReviewsData> fetchStopReviews(int stopId) async {
    final response =
        await _dio.get<Map<String, dynamic>>('/stops/$stopId/reviews/');
    return StopReviewsData.fromJson(response.data ?? {});
  }

  Future<List<StopPhoto>> fetchStopPhotos(int stopId) async {
    final response =
        await _dio.get<List<dynamic>>('/stops/$stopId/photos/');
    return (response.data ?? [])
        .cast<Map<String, dynamic>>()
        .map(StopPhoto.fromJson)
        .toList();
  }

  Future<StopPhoto> uploadStopPhoto(int stopId, String filePath) async {
    final formData = FormData.fromMap({
      'photo': await MultipartFile.fromFile(filePath),
    });
    final response = await _dio.post<Map<String, dynamic>>(
      '/stops/$stopId/photos/',
      data: formData,
    );
    return StopPhoto.fromJson(response.data ?? {});
  }

  Future<void> deleteStopPhoto(int photoId) async {
    await _dio.delete('/photos/$photoId/');
  }

  Future<Booking> importBooking(int tripId, String text) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/trips/$tripId/bookings/import/',
      data: {'text': text},
    );
    return Booking.fromJson(response.data ?? {});
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

  Future<T> _withCache<T>({
    required Future<T> Function() fetch,
    required T? Function() readCache,
  }) async {
    try {
      final value = await fetch();
      _onlineStatus?.markOnline();
      return value;
    } on DioException catch (error) {
      if (_isNetworkError(error)) {
        _onlineStatus?.markOffline();
        final cached = readCache();
        if (cached != null) {
          return cached;
        }
      }
      rethrow;
    }
  }

  bool _isNetworkError(DioException error) {
    return error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout;
  }

  String _formatDate(DateTime date) {
    final year = date.year.toString().padLeft(4, '0');
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '$year-$month-$day';
  }
}
