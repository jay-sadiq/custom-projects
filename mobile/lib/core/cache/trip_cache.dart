import 'dart:convert';

import 'package:hive_flutter/hive_flutter.dart';

class TripCacheService {
  TripCacheService._();

  static const _boxName = 'trip_planner_cache';
  static TripCacheService? _instance;

  static Future<TripCacheService> init() async {
    if (_instance != null) {
      return _instance!;
    }
    await Hive.initFlutter();
    await Hive.openBox<String>(_boxName);
    _instance = TripCacheService._();
    return _instance!;
  }

  static TripCacheService get instance {
    final cache = _instance;
    if (cache == null) {
      throw StateError('TripCacheService.init() must be called before use.');
    }
    return cache;
  }

  Box<String> get _box => Hive.box<String>(_boxName);

  Future<void> saveTripsList(List<Map<String, dynamic>> trips) async {
    await _box.put('trips_list', jsonEncode(trips));
  }

  List<Map<String, dynamic>>? getTripsList() {
    return _decodeList(_box.get('trips_list'));
  }

  Future<void> saveTrip(int tripId, Map<String, dynamic> trip) async {
    await _box.put('trip_$tripId', jsonEncode(trip));
  }

  Map<String, dynamic>? getTrip(int tripId) {
    return _decodeMap(_box.get('trip_$tripId'));
  }

  Future<void> saveDays(int tripId, List<Map<String, dynamic>> days) async {
    await _box.put('trip_${tripId}_days', jsonEncode(days));
  }

  List<Map<String, dynamic>>? getDays(int tripId) {
    return _decodeList(_box.get('trip_${tripId}_days'));
  }

  Future<void> saveStops(int dayId, List<Map<String, dynamic>> stops) async {
    await _box.put('day_${dayId}_stops', jsonEncode(stops));
  }

  List<Map<String, dynamic>>? getStops(int dayId) {
    return _decodeList(_box.get('day_${dayId}_stops'));
  }

  Future<void> saveChecklist(
    int tripId,
    List<Map<String, dynamic>> checklist,
  ) async {
    await _box.put('trip_${tripId}_checklist', jsonEncode(checklist));
  }

  List<Map<String, dynamic>>? getChecklist(int tripId) {
    return _decodeList(_box.get('trip_${tripId}_checklist'));
  }

  List<Map<String, dynamic>>? _decodeList(String? raw) {
    if (raw == null) return null;
    final decoded = jsonDecode(raw);
    if (decoded is! List) return null;
    return decoded.cast<Map<String, dynamic>>();
  }

  Map<String, dynamic>? _decodeMap(String? raw) {
    if (raw == null) return null;
    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, dynamic>) return null;
    return decoded;
  }
}
