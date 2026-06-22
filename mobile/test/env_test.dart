import 'package:flutter_test/flutter_test.dart';
import 'package:trip_planner_app/config/env.dart';

void main() {
  test('Env exposes API prefix', () {
    expect(Env.apiPrefix, '/api/v1');
    expect(Env.apiBaseUrl, isNotEmpty);
  });
}
