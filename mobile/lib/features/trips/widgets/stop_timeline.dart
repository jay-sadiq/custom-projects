import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../models/trip_models.dart';
import 'stop_detail_sheet.dart';

class StopTimeline extends StatelessWidget {
  const StopTimeline({
    super.key,
    required this.stops,
    required this.onStopTap,
  });

  final List<StopBlock> stops;
  final ValueChanged<StopBlock> onStopTap;

  @override
  Widget build(BuildContext context) {
    final ordered = sortStopsForTimeline(stops);

    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
              child: Text(
                'Timeline',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ),
            if (ordered.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text(
                  'No scheduled stops yet.',
                  style: TextStyle(color: AppColors.textSecondary),
                ),
              )
            else
              for (var index = 0; index < ordered.length; index++)
                _TimelineRow(
                  stop: ordered[index],
                  isLast: index == ordered.length - 1,
                  onTap: () => onStopTap(ordered[index]),
                ),
          ],
        ),
      ),
    );
  }
}

class _TimelineRow extends StatelessWidget {
  const _TimelineRow({
    required this.stop,
    required this.isLast,
    required this.onTap,
  });

  final StopBlock stop;
  final bool isLast;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = parseStopColor(stop.colorHex);

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 0),
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                width: 72,
                child: Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text(
                    stop.timelineLabel,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      color: AppColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                ),
              ),
              SizedBox(
                width: 24,
                child: Column(
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: color,
                        shape: BoxShape.circle,
                      ),
                    ),
                    if (!isLast)
                      Expanded(
                        child: Container(
                          width: 2,
                          color: color.withValues(alpha: 0.25),
                        ),
                      ),
                  ],
                ),
              ),
              Expanded(
                child: Padding(
                  padding: EdgeInsets.only(bottom: isLast ? 0 : 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        stop.title,
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                      if (stop.description.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          stop.description,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(color: AppColors.textSecondary),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
