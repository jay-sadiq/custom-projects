import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/cache/trip_cache.dart';
import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await TripCacheService.init();
  runApp(const ProviderScope(child: TripPlannerApp()));
}
