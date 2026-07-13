import 'package:flutter_test/flutter_test.dart';
import 'package:trip_planner_app/config/env.dart';
import 'package:trip_planner_app/config/flavor.dart';

void main() {
  test('Env exposes API prefix and dev defaults', () {
    expect(Env.apiPrefix, '/api/v1');
    expect(Env.apiBaseUrl, isNotEmpty);
    expect(Env.flavor, AppFlavor.dev);
    expect(Env.appName, 'Trip Planner DEV');
  });

  group('AppFlavor', () {
    test('parse maps flavor names', () {
      expect(AppFlavor.parse('prod'), AppFlavor.prod);
      expect(AppFlavor.parse('staging'), AppFlavor.staging);
      expect(AppFlavor.parse('dev'), AppFlavor.dev);
    });

    test('prod default API uses fly.dev host', () {
      expect(
        AppFlavor.prod.defaultApiBaseUrl,
        'https://trip-planner-app.fly.dev',
      );
    });
  });
}
