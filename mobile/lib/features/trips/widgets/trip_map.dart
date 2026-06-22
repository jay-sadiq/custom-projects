import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../models/trip_models.dart';
import 'stop_detail_sheet.dart';

class TripMap extends StatelessWidget {
  const TripMap({
    super.key,
    required this.stops,
    this.selectedStopId,
    required this.onStopTap,
  });

  final List<StopBlock> stops;
  final int? selectedStopId;
  final ValueChanged<StopBlock> onStopTap;

  @override
  Widget build(BuildContext context) {
    final mappedStops = stops.where((stop) => stop.hasCoordinates).toList();
    if (mappedStops.isEmpty) {
      return Container(
        color: Colors.grey.shade100,
        alignment: Alignment.center,
        child: const Text('No map coordinates for this day'),
      );
    }

    final center = stopsCenter(mappedStops)!;
    final zoom = mappedStops.length == 1
        ? mappedStops.first.zoomLevel.toDouble()
        : 12.0;

    return FlutterMap(
      options: MapOptions(
        initialCenter: center,
        initialZoom: zoom,
        interactionOptions: const InteractionOptions(
          flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
        ),
      ),
      children: [
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'com.tripplanner.trip_planner_app',
        ),
        MarkerLayer(
          markers: [
            for (final stop in mappedStops)
              Marker(
                point: LatLng(stop.latitude, stop.longitude),
                width: 40,
                height: 40,
                child: GestureDetector(
                  onTap: () => onStopTap(stop),
                  child: Icon(
                    Icons.location_on,
                    size: selectedStopId == stop.id ? 40 : 34,
                    color: parseStopColor(stop.colorHex),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }
}
