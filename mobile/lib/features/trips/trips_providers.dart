import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_providers.dart';
import 'models/trip_models.dart';
import 'trips_repository.dart';

final tripsRepositoryProvider = Provider<TripsRepository>((ref) {
  return TripsRepository(apiClient: ref.watch(apiClientProvider));
});

final tripsListProvider = FutureProvider.autoDispose<List<Trip>>((ref) async {
  return ref.watch(tripsRepositoryProvider).fetchTrips();
});

final tripDetailProvider =
    FutureProvider.autoDispose.family<Trip, int>((ref, tripId) async {
  return ref.watch(tripsRepositoryProvider).fetchTrip(tripId);
});

final tripDaysProvider =
    FutureProvider.autoDispose.family<List<DayItinerary>, int>((ref, tripId) async {
  return ref.watch(tripsRepositoryProvider).fetchDays(tripId);
});

final dayStopsProvider =
    FutureProvider.autoDispose.family<List<StopBlock>, int>((ref, dayId) async {
  return ref.watch(tripsRepositoryProvider).fetchStops(dayId);
});

final tripChecklistProvider =
    FutureProvider.autoDispose.family<List<ChecklistItem>, int>((ref, tripId) async {
  return ref.watch(tripsRepositoryProvider).fetchChecklist(tripId);
});

class CreateTripState {
  const CreateTripState({
    this.isSubmitting = false,
    this.statusMessage = '',
    this.errorMessage,
  });

  final bool isSubmitting;
  final String statusMessage;
  final String? errorMessage;
}

class CreateTripController extends StateNotifier<CreateTripState> {
  CreateTripController(this._repository) : super(const CreateTripState());

  final TripsRepository _repository;

  Future<int?> submit({
    required String destination,
    required int daysCount,
    required DateTime startDate,
    String details = '',
  }) async {
    state = const CreateTripState(
      isSubmitting: true,
      statusMessage: 'Starting AI trip planner…',
    );

    try {
      final job = await _repository.createTrip(
        destination: destination,
        daysCount: daysCount,
        startDate: startDate,
        details: details,
      );

      var current = job;
      while (!current.isTerminal) {
        state = CreateTripState(
          isSubmitting: true,
          statusMessage: _jobStatusLabel(current.status),
        );
        await Future<void>.delayed(const Duration(seconds: 2));
        current = await _repository.fetchTripJob(job.id);
      }

      if (current.isFailed) {
        state = CreateTripState(
          errorMessage: current.errorMessage.isNotEmpty
              ? current.errorMessage
              : 'Trip creation failed.',
        );
        return null;
      }

      state = const CreateTripState();
      return current.tripId;
    } catch (error) {
      state = CreateTripState(
        errorMessage: 'Could not create trip. Check API connection and try again.',
      );
      return null;
    }
  }

  void reset() {
    state = const CreateTripState();
  }

  String _jobStatusLabel(String status) {
    return switch (status) {
      'running' => 'AI is building your itinerary…',
      'pending' => 'Waiting to start…',
      'completed' => 'Done!',
      _ => 'Creating your trip…',
    };
  }
}

final createTripControllerProvider =
    StateNotifierProvider.autoDispose<CreateTripController, CreateTripState>((ref) {
  return CreateTripController(ref.watch(tripsRepositoryProvider));
});
