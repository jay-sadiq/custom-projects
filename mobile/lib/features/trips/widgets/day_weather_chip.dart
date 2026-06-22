import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../trips_providers.dart';

class DayWeatherChip extends ConsumerWidget {
  const DayWeatherChip({super.key, required this.dayId});

  final int dayId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final weather = ref.watch(dayWeatherProvider(dayId));

    return weather.when(
      data: (data) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.crimson.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.crimson.withValues(alpha: 0.2)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(data.emoji, style: const TextStyle(fontSize: 16)),
              const SizedBox(width: 6),
              Text(
                '${data.temperatureC.toStringAsFixed(0)}°C · ${data.condition}',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              if (data.isDemoData) ...[
                const SizedBox(width: 6),
                Text(
                  '· ${data.label}',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ],
          ),
        );
      },
      loading: () => const SizedBox(
        width: 18,
        height: 18,
        child: CircularProgressIndicator(strokeWidth: 2),
      ),
      error: (error, stackTrace) => const SizedBox.shrink(),
    );
  }
}
