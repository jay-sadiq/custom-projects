import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme/app_theme.dart';
import 'features/auth/auth_providers.dart';
import 'routing/app_router.dart';

class TripPlannerApp extends ConsumerStatefulWidget {
  const TripPlannerApp({super.key});

  @override
  ConsumerState<TripPlannerApp> createState() => _TripPlannerAppState();
}

class _TripPlannerAppState extends ConsumerState<TripPlannerApp> {
  @override
  void initState() {
    super.initState();
    Future.microtask(
      () => ref.read(authControllerProvider.notifier).bootstrap(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'Trip Planner',
      theme: AppTheme.light(),
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
