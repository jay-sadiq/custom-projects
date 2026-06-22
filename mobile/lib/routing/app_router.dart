import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/auth_providers.dart';
import '../../features/auth/login_screen.dart';
import '../../features/auth/register_screen.dart';
import '../../features/trips/create_trip_screen.dart';
import '../../features/trips/trip_detail_screen.dart';
import '../../features/trips/trips_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authControllerProvider);

  return GoRouter(
    initialLocation: '/',
    refreshListenable: _RouterRefresh(ref),
    redirect: (context, state) {
      if (auth.isLoading) {
        return state.matchedLocation == '/boot' ? null : '/boot';
      }
      final isAuthenticated = auth.isAuthenticated;
      final isAuthRoute =
          state.matchedLocation == '/login' || state.matchedLocation == '/register';

      if (!isAuthenticated && !isAuthRoute) {
        return '/login';
      }
      if (isAuthenticated && isAuthRoute) {
        return '/';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/boot',
        builder: (context, state) => const Scaffold(
          body: Center(child: Text('Loading…')),
        ),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/',
        builder: (context, state) => const TripsScreen(),
      ),
      GoRoute(
        path: '/trips/create',
        builder: (context, state) => const CreateTripScreen(),
      ),
      GoRoute(
        path: '/trips/:tripId',
        builder: (context, state) {
          final tripId = state.pathParameters['tripId']!;
          return TripDetailScreen(tripId: tripId);
        },
        routes: [
          GoRoute(
            path: 'day/:dayNumber',
            builder: (context, state) {
              final tripId = state.pathParameters['tripId']!;
              final dayNumber =
                  int.tryParse(state.pathParameters['dayNumber'] ?? '1') ?? 1;
              return TripDetailScreen(tripId: tripId, dayNumber: dayNumber);
            },
          ),
        ],
      ),
    ],
  );
});

class _RouterRefresh extends ChangeNotifier {
  _RouterRefresh(this.ref) {
    ref.listen<AuthState>(authControllerProvider, (previous, next) {
      notifyListeners();
    });
  }

  final Ref ref;
}
