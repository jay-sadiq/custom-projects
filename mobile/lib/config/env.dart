/// Runtime configuration via `--dart-define`.
///
/// Example:
/// `flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000`
class Env {
  const Env._();

  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  static const apiPrefix = '/api/v1';
}
