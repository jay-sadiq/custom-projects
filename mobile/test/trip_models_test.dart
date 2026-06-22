import 'package:flutter_test/flutter_test.dart';
import 'package:trip_planner_app/features/trips/models/trip_models.dart';

void main() {
  group('Trip.fromJson', () {
    test('parses paginated trip fields', () {
      final trip = Trip.fromJson({
        'id': 1,
        'title': 'Lisbon Adventure',
        'destination': 'Lisbon',
        'start_date': '2026-08-01',
        'end_date': '2026-08-05',
        'duration_days': 5,
        'attendee_count': 2,
        'total_cost_local': '123.45',
      });

      expect(trip.id, 1);
      expect(trip.title, 'Lisbon Adventure');
      expect(trip.durationDays, 5);
      expect(trip.totalCostLocal, 123.45);
      expect(trip.startDate, DateTime(2026, 8, 1));
    });
  });

  group('StopBlock.fromJson', () {
    test('parses coordinates and meal fields', () {
      final stop = StopBlock.fromJson({
        'id': 10,
        'day_id': 3,
        'sequence_order': 1,
        'time_label': '9:00 AM',
        'title': 'Museum',
        'description': 'Visit',
        'latitude': '38.71',
        'longitude': '-9.13',
        'meal_name': 'Pastéis',
        'color_hex': '#8B1A1A',
      });

      expect(stop.hasCoordinates, isTrue);
      expect(stop.latitude, 38.71);
      expect(stop.mealName, 'Pastéis');
    });
  });

  group('TripCreationJob.fromJson', () {
    test('detects terminal states', () {
      final completed = TripCreationJob.fromJson({
        'id': 5,
        'status': 'completed',
        'trip_id': 12,
      });
      final failed = TripCreationJob.fromJson({
        'id': 6,
        'status': 'failed',
        'error_message': 'LLM error',
      });

      expect(completed.isTerminal, isTrue);
      expect(completed.tripId, 12);
      expect(failed.isFailed, isTrue);
      expect(failed.errorMessage, 'LLM error');
    });
  });
}
