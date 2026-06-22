import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';

class TripDetailScreen extends StatelessWidget {
  const TripDetailScreen({
    super.key,
    required this.tripId,
    this.dayNumber = 1,
  });

  final String tripId;
  final int dayNumber;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Trip $tripId'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/'),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              children: List.generate(3, (index) {
                final day = index + 1;
                final selected = day == dayNumber;
                return ChoiceChip(
                  label: Text('Day $day'),
                  selected: selected,
                  onSelected: (_) => context.go('/trips/$tripId/day/$day'),
                  selectedColor: AppColors.crimson.withValues(alpha: 0.15),
                  labelStyle: TextStyle(
                    color: selected ? AppColors.crimson : AppColors.textPrimary,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  ),
                );
              }),
            ),
            const SizedBox(height: 20),
            Text(
              'Day $dayNumber itinerary',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Trip list, map, and stops arrive in Phase 11. Navigation shell is ready.',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}
