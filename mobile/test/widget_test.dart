import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:trip_planner_app/app.dart';
import 'package:trip_planner_app/core/api/api_client.dart';
import 'package:trip_planner_app/core/storage/token_storage.dart';
import 'package:trip_planner_app/core/theme/app_theme.dart';
import 'package:trip_planner_app/features/auth/auth_providers.dart';
import 'package:trip_planner_app/features/auth/auth_repository.dart';

class _FakeAuthRepository extends AuthRepository {
  _FakeAuthRepository()
      : super(
          apiClient: ApiClient(tokenStorage: TokenStorage()),
          tokenStorage: TokenStorage(),
        );

  @override
  Future<bool> hasStoredSession() async => false;
}

void main() {
  testWidgets('App renders login when unauthenticated', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authRepositoryProvider.overrideWith((ref) => _FakeAuthRepository()),
        ],
        child: const TripPlannerApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Trip Planner'), findsWidgets);
    expect(find.text('Sign in'), findsOneWidget);
  });

  test('AppTheme uses crimson primary color', () {
    final theme = AppTheme.light();
    expect(theme.colorScheme.primary, AppColors.crimson);
  });
}
