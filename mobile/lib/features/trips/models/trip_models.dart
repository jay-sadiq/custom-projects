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
    this.startTimeOfDay,
    this.endTimeOfDay,
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
  final String? startTimeOfDay;
  final String? endTimeOfDay;

  bool get hasCoordinates => latitude != 0 || longitude != 0;

  String get timelineLabel {
    if (startTimeOfDay != null && startTimeOfDay!.isNotEmpty) {
      return formatTimeOfDay(startTimeOfDay!);
    }
    return timeLabel;
  }

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
      startTimeOfDay: json['start_time_of_day'] as String?,
      endTimeOfDay: json['end_time_of_day'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'day_id': dayId,
        'sequence_order': sequenceOrder,
        'time_label': timeLabel,
        'title': title,
        'description': description,
        'latitude': latitude,
        'longitude': longitude,
        'zoom_level': zoomLevel,
        'cost_local': costLocal,
        'cost_usd': costUsd,
        'meal_type': mealType,
        'meal_name': mealName,
        'meal_desc': mealDesc,
        'color_hex': colorHex,
        'start_time_of_day': startTimeOfDay,
        'end_time_of_day': endTimeOfDay,
      };
}

String formatTimeOfDay(String value) {
  final parts = value.split(':');
  if (parts.length < 2) return value;
  final hour = int.tryParse(parts[0]) ?? 0;
  final minute = int.tryParse(parts[1]) ?? 0;
  final period = hour >= 12 ? 'PM' : 'AM';
  final hour12 = hour % 12 == 0 ? 12 : hour % 12;
  return '$hour12:${minute.toString().padLeft(2, '0')} $period';
}

List<StopBlock> sortStopsForTimeline(List<StopBlock> stops) {
  final copy = List<StopBlock>.from(stops);
  copy.sort((a, b) {
    final aTime = a.startTimeOfDay ?? '';
    final bTime = b.startTimeOfDay ?? '';
    if (aTime.isNotEmpty && bTime.isNotEmpty) {
      return aTime.compareTo(bTime);
    }
    if (aTime.isNotEmpty) return -1;
    if (bTime.isNotEmpty) return 1;
    return a.sequenceOrder.compareTo(b.sequenceOrder);
  });
  return copy;
}

class DayWeather {
  const DayWeather({
    required this.label,
    required this.emoji,
    required this.temperatureC,
    required this.condition,
    this.isDemoData = false,
  });

  final String label;
  final String emoji;
  final double temperatureC;
  final String condition;
  final bool isDemoData;

  factory DayWeather.fromJson(Map<String, dynamic> json) {
    return DayWeather(
      label: json['label'] as String? ?? '',
      emoji: json['emoji'] as String? ?? '',
      temperatureC: parseApiDouble(json['temperature_c']) ?? 0,
      condition: json['condition'] as String? ?? '',
      isDemoData: json['is_demo_data'] as bool? ?? false,
    );
  }
}

class StopPhoto {
  const StopPhoto({
    required this.id,
    required this.stopId,
    required this.imageUrl,
  });

  final int id;
  final int stopId;
  final String imageUrl;

  factory StopPhoto.fromJson(Map<String, dynamic> json) {
    return StopPhoto(
      id: parseApiInt(json['id']),
      stopId: parseApiInt(json['stop_id']),
      imageUrl: json['image_url'] as String? ?? '',
    );
  }
}

class StopReview {
  const StopReview({
    required this.author,
    required this.rating,
    required this.text,
  });

  final String author;
  final double rating;
  final String text;

  factory StopReview.fromJson(Map<String, dynamic> json) {
    return StopReview(
      author: json['author'] as String? ?? json['author_name'] as String? ?? 'Guest',
      rating: parseApiDouble(json['rating']) ?? 0,
      text: json['text'] as String? ?? '',
    );
  }
}

class StopReviewsData {
  const StopReviewsData({
    required this.stopId,
    required this.rating,
    required this.reviews,
    required this.photoUrls,
    this.isDemoData = false,
  });

  final int stopId;
  final double rating;
  final List<StopReview> reviews;
  final List<String> photoUrls;
  final bool isDemoData;

  factory StopReviewsData.fromJson(Map<String, dynamic> json) {
    final reviews = (json['reviews'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>()
        .map(StopReview.fromJson)
        .toList();
    final photoUrls = (json['photo_urls'] as List<dynamic>? ?? [])
        .map((item) => item.toString())
        .toList();
    return StopReviewsData(
      stopId: parseApiInt(json['stop_id']),
      rating: parseApiDouble(json['rating']) ?? 0,
      reviews: reviews,
      photoUrls: photoUrls,
      isDemoData: json['is_demo_data'] as bool? ?? false,
    );
  }
}

class Booking {
  const Booking({
    required this.id,
    required this.tripId,
    required this.title,
    this.bookingType = '',
    this.confirmationNumber = '',
    this.details = '',
  });

  final int id;
  final int tripId;
  final String title;
  final String bookingType;
  final String confirmationNumber;
  final String details;

  factory Booking.fromJson(Map<String, dynamic> json) {
    return Booking(
      id: parseApiInt(json['id']),
      tripId: parseApiInt(json['trip_id']),
      title: json['title'] as String? ?? '',
      bookingType: json['booking_type'] as String? ?? '',
      confirmationNumber: json['confirmation_number'] as String? ?? '',
      details: json['details'] as String? ?? '',
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
