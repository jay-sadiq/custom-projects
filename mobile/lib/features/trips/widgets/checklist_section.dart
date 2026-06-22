import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../models/trip_models.dart';
import '../trips_providers.dart';
import '../trips_repository.dart';

class ChecklistSection extends ConsumerWidget {
  const ChecklistSection({
    super.key,
    required this.tripId,
    required this.repository,
  });

  final int tripId;
  final TripsRepository repository;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final checklist = ref.watch(tripChecklistProvider(tripId));

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Checklist',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 8),
            checklist.when(
              data: (items) {
                if (items.isEmpty) {
                  return const Text(
                    'No checklist items yet.',
                    style: TextStyle(color: AppColors.textSecondary),
                  );
                }
                final grouped = <String, List<ChecklistItem>>{};
                for (final item in items) {
                  grouped.putIfAbsent(item.category, () => []).add(item);
                }
                return Column(
                  children: [
                    for (final entry in grouped.entries) ...[
                      if (entry.key.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 8, bottom: 4),
                          child: Text(
                            entry.key,
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              color: AppColors.crimson,
                            ),
                          ),
                        ),
                      for (final item in entry.value)
                        CheckboxListTile(
                          contentPadding: EdgeInsets.zero,
                          value: item.isCompleted,
                          onChanged: (_) async {
                            await repository.toggleChecklistItem(item.id);
                            ref.invalidate(tripChecklistProvider(tripId));
                          },
                          title: Text(
                            item.itemText,
                            style: TextStyle(
                              decoration: item.isCompleted
                                  ? TextDecoration.lineThrough
                                  : null,
                              color: item.isCompleted
                                  ? AppColors.textSecondary
                                  : AppColors.textPrimary,
                            ),
                          ),
                          controlAffinity: ListTileControlAffinity.leading,
                        ),
                    ],
                  ],
                );
              },
              loading: () => const Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, stackTrace) => const Text(
                'Could not load checklist',
                style: TextStyle(color: Colors.red),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
