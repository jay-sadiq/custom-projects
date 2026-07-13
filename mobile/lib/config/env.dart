import 'flavor.dart';

/// Runtime configuration via `--dart-define` or `--dart-define-from-file`.
///
/// Flavor files live in `mobile/config/*.json`.
class Env {
  const Env._();

  static const _flavorName = String.fromEnvironment('FLAVOR', defaultValue: 'dev');
  static const _apiBaseUrlOverride = String.fromEnvironment('API_BASE_URL');

  static AppFlavor get flavor => AppFlavor.parse(_flavorName);

  static String get apiBaseUrl {
    if (_apiBaseUrlOverride.isNotEmpty) {
      return _apiBaseUrlOverride;
    }
    return flavor.defaultApiBaseUrl;
  }

  static const apiPrefix = '/api/v1';

  static String get appName => flavor.displayName;

  static String get privacyPolicyUrl => flavor.privacyPolicyUrl;

  static bool get isProduction => flavor == AppFlavor.prod;
}
