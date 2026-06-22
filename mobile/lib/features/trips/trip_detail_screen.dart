import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/network/connectivity_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/offline_banner.dart';
import 'models/trip_models.dart';
import 'trips_providers.dart';
import 'widgets/booking_import_sheet.dart';
import 'widgets/chat_edit_sheet.dart';
import 'widgets/checklist_section.dart';
import 'widgets/day_notes_field.dart';
import 'widgets/day_weather_chip.dart';
import 'widgets/stop_detail_sheet.dart';
import 'widgets/stop_timeline.dart';
import 'widgets/trip_map.dart';

class TripDetailScreen extends ConsumerWidget {
  const TripDetailScreen({
    super.key,
    required this.tripId,
    this.dayNumber = 1,
  });

  final String tripId;
  final int dayNumber;

  int get _tripIdInt => int.tryParse(tripId) ?? 0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tripAsync = ref.watch(tripDetailProvider(_tripIdInt));
    final daysAsync = ref.watch(tripDaysProvider(_tripIdInt));
    final repository = ref.watch(tripsRepositoryProvider);
    final isOnline = ref.watch(isOnlineProvider);

    return OfflineAwareScaffold(
      appBar: AppBar(
        title: tripAsync.when(
          data: (trip) => Text(
            trip.title.isNotEmpty ? trip.title : trip.destination,
            overflow: TextOverflow.ellipsis,
          ),
          loading: () => const Text('Trip'),
          error: (error, stackTrace) => const Text('Trip'),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/'),
        ),
        actions: [
          IconButton(
            tooltip: 'Import booking',
            onPressed: isOnline
                ? () => BookingImportSheet.show(
                      context,
                      tripId: _tripIdInt,
                      repository: repository,
                    )
                : () => showOfflineSnackBar(context),
            icon: const Icon(Icons.flight_takeoff),
          ),
        ],
      ),
      floatingActionButton: daysAsync.maybeWhen(
        data: (days) {
          final day = _findDay(days);
          if (day == null || !isOnline) return null;
          return FloatingActionButton.extended(
            onPressed: () => ChatEditSheet.show(
              context,
              dayId: day.id,
              tripId: _tripIdInt,
              repository: repository,
            ),
            icon: const Icon(Icons.auto_awesome),
            label: const Text('AI edit'),
          );
        },
        orElse: () => null,
      ),
      body: daysAsync.when(
        data: (days) {
          if (days.isEmpty) {
            return const Center(child: Text('No days found for this trip.'));
          }
          final day = _findDay(days) ?? days.first;
          final stopsAsync = ref.watch(dayStopsProvider(day.id));

          return RefreshIndicator(
            onRefresh: () async {
              if (!isOnline) return;
              ref.invalidate(tripDetailProvider(_tripIdInt));
              ref.invalidate(tripDaysProvider(_tripIdInt));
              ref.invalidate(dayStopsProvider(day.id));
              ref.invalidate(tripChecklistProvider(_tripIdInt));
              ref.invalidate(dayWeatherProvider(day.id));
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              children: [
                _DayChipBar(
                  tripId: tripId,
                  days: days,
                  selectedDayNumber: day.dayNumber,
                ),
                const SizedBox(height: 16),
                _DayHeader(day: day),
                const SizedBox(height: 12),
                DayWeatherChip(dayId: day.id),
                const SizedBox(height: 16),
                SizedBox(
                  height: 240,
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: stopsAsync.when(
                      data: (stops) => TripMap(
                        stops: stops,
                        onStopTap: (stop) => StopDetailSheet.show(
                          context,
                          stop: stop,
                          repository: repository,
                        ),
                      ),
                      loading: () =>
                          const Center(child: CircularProgressIndicator()),
                      error: (error, stackTrace) => Container(
                        color: Colors.grey.shade100,
                        alignment: Alignment.center,
                        child: const Text('Could not load map'),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                stopsAsync.when(
                  data: (stops) => StopTimeline(
                    stops: stops,
                    onStopTap: (stop) => StopDetailSheet.show(
                      context,
                      stop: stop,
                      repository: repository,
                    ),
                  ),
                  loading: () => const Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                  ),
                  error: (error, stackTrace) => const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('Could not load stops'),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                stopsAsync.when(
                  data: (stops) => _StopsList(
                    stops: stops,
                    onStopTap: (stop) => StopDetailSheet.show(
                      context,
                      stop: stop,
                      repository: repository,
                    ),
                  ),
                  loading: () => const SizedBox.shrink(),
                  error: (error, stackTrace) => const SizedBox.shrink(),
                ),
                const SizedBox(height: 16),
                DayNotesField(day: day, repository: repository),
                const SizedBox(height: 16),
                ChecklistSection(tripId: _tripIdInt, repository: repository),
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) =>
            const Center(child: Text('Could not load trip days')),
      ),
    );
  }

  DayItinerary? _findDay(List<DayItinerary> days) {
    for (final day in days) {
      if (day.dayNumber == dayNumber) return day;
    }
    return null;
  }
}

class _DayChipBar extends StatelessWidget {
  const _DayChipBar({
    required this.tripId,
    required this.days,
    required this.selectedDayNumber,
  });

  final String tripId;
  final List<DayItinerary> days;
  final int selectedDayNumber;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (final day in days)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text('Day ${day.dayNumber}'),
                selected: day.dayNumber == selectedDayNumber,
                onSelected: (_) =>
                    context.go('/trips/$tripId/day/${day.dayNumber}'),
                selectedColor: AppColors.crimson.withValues(alpha: 0.15),
                labelStyle: TextStyle(
                  color: day.dayNumber == selectedDayNumber
                      ? AppColors.crimson
                      : AppColors.textPrimary,
                  fontWeight: day.dayNumber == selectedDayNumber
                      ? FontWeight.w700
                      : FontWeight.w500,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _DayHeader extends StatelessWidget {
  const _DayHeader({required this.day});

  final DayItinerary day;

  @override
  Widget build(BuildContext context) {
    final dateLabel =
        day.date != null ? DateFormat.yMMMEd().format(day.date!) : '';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (day.theme.isNotEmpty)
              Text(
                day.theme,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
            if (dateLabel.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                dateLabel,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
            ],
            if (day.earlyStartBanner.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.wb_sunny, color: Colors.amber.shade800, size: 20),
                    const SizedBox(width: 8),
                    Expanded(child: Text(day.earlyStartBanner)),
                  ],
                ),
              ),
            ],
            if (day.dayCostLocal != null && day.dayCostLocal! > 0) ...[
              const SizedBox(height: 12),
              Text(
                'Day cost: ${day.dayCostLocal!.toStringAsFixed(2)}',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StopsList extends StatelessWidget {
  const _StopsList({
    required this.stops,
    required this.onStopTap,
  });

  final List<StopBlock> stops;
  final ValueChanged<StopBlock> onStopTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
              child: Text(
                'All stops',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ),
            if (stops.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text(
                  'No stops scheduled for this day.',
                  style: TextStyle(color: AppColors.textSecondary),
                ),
              )
            else
              for (final stop in stops)
                ListTile(
                  leading: CircleAvatar(
                    backgroundColor:
                        parseStopColor(stop.colorHex).withValues(alpha: 0.15),
                    child: Text(
                      '${stop.sequenceOrder}',
                      style: TextStyle(
                        color: parseStopColor(stop.colorHex),
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  title: Text(stop.title),
                  subtitle: Text(
                    [
                      if (stop.timeLabel.isNotEmpty) stop.timeLabel,
                      if (stop.description.isNotEmpty) stop.description,
                    ].join(' · '),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => onStopTap(stop),
                ),
          ],
        ),
      ),
    );
  }
}
