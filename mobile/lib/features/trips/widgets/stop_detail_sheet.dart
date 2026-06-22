import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';

import '../../../core/theme/app_theme.dart';
import '../models/trip_models.dart';
import 'trip_map.dart';

class StopDetailSheet extends StatelessWidget {
  const StopDetailSheet({super.key, required this.stop});

  final StopBlock stop;

  static Future<void> show(BuildContext context, StopBlock stop) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => StopDetailSheet(stop: stop),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        0,
        20,
        20 + MediaQuery.viewPaddingOf(context).bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            stop.title,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
          if (stop.timeLabel.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              stop.timeLabel,
              style: const TextStyle(color: AppColors.textSecondary),
            ),
          ],
          if (stop.description.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(stop.description),
          ],
          if (stop.mealName.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(
              stop.mealName,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            if (stop.mealDesc.isNotEmpty)
              Text(
                stop.mealDesc,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
          ],
          if (stop.costLocal != null && stop.costLocal! > 0) ...[
            const SizedBox(height: 12),
            Text('Cost: ${stop.costLocal!.toStringAsFixed(2)}'),
          ],
          if (stop.hasCoordinates) ...[
            const SizedBox(height: 16),
            SizedBox(
              height: 180,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: TripMap(
                  stops: [stop],
                  selectedStopId: stop.id,
                  onStopTap: (_) {},
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

Color parseStopColor(String hex) {
  final cleaned = hex.replaceAll('#', '');
  if (cleaned.length == 6) {
    final value = int.tryParse(cleaned, radix: 16);
    if (value != null) {
      return Color(0xFF000000 | value);
    }
  }
  return AppColors.crimson;
}

LatLng? stopsCenter(List<StopBlock> stops) {
  final withCoords = stops.where((stop) => stop.hasCoordinates).toList();
  if (withCoords.isEmpty) return null;
  final lat =
      withCoords.map((stop) => stop.latitude).reduce((a, b) => a + b) /
          withCoords.length;
  final lng =
      withCoords.map((stop) => stop.longitude).reduce((a, b) => a + b) /
          withCoords.length;
  return LatLng(lat, lng);
}
