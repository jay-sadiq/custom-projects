double? parseApiDouble(dynamic value) {
  if (value == null) return null;
  if (value is num) return value.toDouble();
  if (value is String) return double.tryParse(value);
  return null;
}

int parseApiInt(dynamic value, {int fallback = 0}) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  if (value is String) return int.tryParse(value) ?? fallback;
  return fallback;
}

DateTime? parseApiDate(dynamic value) {
  if (value == null || value is! String || value.isEmpty) return null;
  return DateTime.tryParse(value);
}

class Trip {
  const Trip({
    required this.id,
    required this.title,
    required this.destination,
    this.startDate,
    this.endDate,
    this.currency = 'USD',
    this.durationDays = 0,
    this.attendeeCount = 0,
    this.totalCostLocal,
  });

  final int id;
  final String title;
  final String destination;
  final DateTime? startDate;
  final DateTime? endDate;
  final String currency;
  final int durationDays;
  final int attendeeCount;
  final double? totalCostLocal;

  factory Trip.fromJson(Map<String, dynamic> json) {
    return Trip(
      id: parseApiInt(json['id']),
      title: json['title'] as String? ?? '',
      destination: json['destination'] as String? ?? '',
      startDate: parseApiDate(json['start_date']),
      endDate: parseApiDate(json['end_date']),
      currency: json['currency'] as String? ?? 'USD',
      durationDays: parseApiInt(json['duration_days']),
      attendeeCount: parseApiInt(json['attendee_count']),
      totalCostLocal: parseApiDouble(json['total_cost_local']),
    );
  }
}

class DayItinerary {
  const DayItinerary({
    required this.id,
    required this.tripId,
    required this.dayNumber,
    this.date,
    this.theme = '',
    this.earlyStartBanner = '',
    this.notes = '',
    this.dayCostLocal,
    this.dayCostUsd,
  });

  final int id;
  final int tripId;
  final int dayNumber;
  final DateTime? date;
  final String theme;
  final String earlyStartBanner;
  final String notes;
  final double? dayCostLocal;
  final double? dayCostUsd;

  factory DayItinerary.fromJson(Map<String, dynamic> json) {
    return DayItinerary(
      id: parseApiInt(json['id']),
      tripId: parseApiInt(json['trip_id']),
      dayNumber: parseApiInt(json['day_number'], fallback: 1),
      date: parseApiDate(json['date']),
      theme: json['theme'] as String? ?? '',
      earlyStartBanner: json['early_start_banner'] as String? ?? '',
      notes: json['notes'] as String? ?? '',
      dayCostLocal: parseApiDouble(json['day_cost_local']),
      dayCostUsd: parseApiDouble(json['day_cost_usd']),
    );
  }
}

class StopBlock {
  const StopBlock({
    required this.id,
    required this.dayId,
    required this.sequenceOrder,
    required this.title,
    this.timeLabel = '',
    this.description = '',
    this.latitude = 0,
    this.longitude = 0,
    this.zoomLevel = 14,
    this.costLocal,
    this.costUsd,
    this.mealType = '',
    this.mealName = '',
    this.mealDesc = '',
    this.colorHex = '#8B1A1A',
  });

  final int id;
  final int dayId;
  final int sequenceOrder;
  final String timeLabel;
  final String title;
  final String description;
  final double latitude;
  final double longitude;
  final int zoomLevel;
  final double? costLocal;
  final double? costUsd;
  final String mealType;
  final String mealName;
  final String mealDesc;
  final String colorHex;

  bool get hasCoordinates => latitude != 0 || longitude != 0;

  factory StopBlock.fromJson(Map<String, dynamic> json) {
    return StopBlock(
      id: parseApiInt(json['id']),
      dayId: parseApiInt(json['day_id']),
      sequenceOrder: parseApiInt(json['sequence_order']),
      timeLabel: json['time_label'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      latitude: parseApiDouble(json['latitude']) ?? 0,
      longitude: parseApiDouble(json['longitude']) ?? 0,
      zoomLevel: parseApiInt(json['zoom_level'], fallback: 14),
      costLocal: parseApiDouble(json['cost_local']),
      costUsd: parseApiDouble(json['cost_usd']),
      mealType: json['meal_type'] as String? ?? '',
      mealName: json['meal_name'] as String? ?? '',
      mealDesc: json['meal_desc'] as String? ?? '',
      colorHex: json['color_hex'] as String? ?? '#8B1A1A',
    );
  }
}

class ChecklistItem {
  const ChecklistItem({
    required this.id,
    required this.tripId,
    required this.category,
    required this.itemText,
    this.isCompleted = false,
  });

  final int id;
  final int tripId;
  final String category;
  final String itemText;
  final bool isCompleted;

  ChecklistItem copyWith({bool? isCompleted}) {
    return ChecklistItem(
      id: id,
      tripId: tripId,
      category: category,
      itemText: itemText,
      isCompleted: isCompleted ?? this.isCompleted,
    );
  }

  factory ChecklistItem.fromJson(Map<String, dynamic> json) {
    return ChecklistItem(
      id: parseApiInt(json['id']),
      tripId: parseApiInt(json['trip_id']),
      category: json['category'] as String? ?? '',
      itemText: json['item_text'] as String? ?? '',
      isCompleted: json['is_completed'] as bool? ?? false,
    );
  }
}

class TripCreationJob {
  const TripCreationJob({
    required this.id,
    required this.status,
    this.tripId,
    this.destination = '',
    this.errorMessage = '',
  });

  final int id;
  final String status;
  final int? tripId;
  final String destination;
  final String errorMessage;

  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';
  bool get isTerminal => isCompleted || isFailed;

  factory TripCreationJob.fromJson(Map<String, dynamic> json) {
    return TripCreationJob(
      id: parseApiInt(json['id']),
      status: json['status'] as String? ?? 'pending',
      tripId: json['trip_id'] == null ? null : parseApiInt(json['trip_id']),
      destination: json['destination'] as String? ?? '',
      errorMessage: json['error_message'] as String? ?? '',
    );
  }
}
