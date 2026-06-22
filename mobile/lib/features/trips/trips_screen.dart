import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/network/connectivity_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/offline_banner.dart';
import '../auth/auth_providers.dart';
import 'trips_providers.dart';

class TripsScreen extends ConsumerWidget {
  const TripsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final trips = ref.watch(tripsListProvider);
    final health = ref.watch(apiHealthProvider);
    final isOnline = ref.watch(isOnlineProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Trips'),
        actions: [
          health.when(
            data: (payload) {
              final connected = payload['status'] == 'ok';
              return Padding(
                padding: const EdgeInsets.only(right: 4),
                child: Icon(
                  connected ? Icons.cloud_done : Icons.cloud_off,
                  color: connected ? Colors.green.shade700 : Colors.red.shade400,
                  size: 20,
                ),
              );
            },
            loading: () => const SizedBox.shrink(),
            error: (error, stackTrace) => Icon(
              Icons.cloud_off,
              color: Colors.red.shade400,
              size: 20,
            ),
          ),
          IconButton(
            tooltip: 'Log out',
            onPressed: () async {
              await ref.read(authControllerProvider.notifier).logout();
              if (context.mounted) {
                context.go('/login');
              }
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: isOnline
            ? () => context.push('/trips/create')
            : () => showOfflineSnackBar(context),
        icon: const Icon(Icons.add),
        label: const Text('New trip'),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(tripsListProvider.future),
        child: trips.when(
          data: (items) {
            if (items.isEmpty) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 80),
                  Icon(Icons.flight_takeoff, size: 64, color: AppColors.crimson.withValues(alpha: 0.6)),
                  const SizedBox(height: 16),
                  Text(
                    'No trips yet',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Create your first AI-planned itinerary to get started.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 24),
                  Center(
                    child: FilledButton.icon(
                      onPressed: () => context.push('/trips/create'),
                      icon: const Icon(Icons.auto_awesome),
                      label: const Text('Plan a trip'),
                    ),
                  ),
                ],
              );
            }

            return ListView.separated(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 88),
              itemCount: items.length,
              separatorBuilder: (context, index) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final trip = items[index];
                final dateLabel = _formatTripDates(trip.startDate, trip.endDate);
                return Card(
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 8,
                    ),
                    leading: CircleAvatar(
                      backgroundColor: AppColors.crimson.withValues(alpha: 0.12),
                      child: const Icon(Icons.map, color: AppColors.crimson),
                    ),
                    title: Text(
                      trip.title.isNotEmpty ? trip.title : trip.destination,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    subtitle: Text(
                      [
                        trip.destination,
                        if (dateLabel.isNotEmpty) dateLabel,
                        if (trip.durationDays > 0) '${trip.durationDays} days',
                      ].join(' · '),
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => context.go('/trips/${trip.id}/day/1'),
                  ),
                );
              },
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(24),
            children: [
              const SizedBox(height: 80),
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              const Text(
                'Could not load trips',
                textAlign: TextAlign.center,
                style: TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              const Text(
                'Check your API connection and pull to refresh.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.textSecondary),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTripDates(DateTime? start, DateTime? end) {
    if (start == null) return '';
    final formatter = DateFormat.MMMd();
    if (end == null) return formatter.format(start);
    return '${formatter.format(start)} – ${formatter.format(end)}';
  }
}
