/// Build-time flavor configuration via `--dart-define` / `--dart-define-from-file`.
///
/// Example:
/// `flutter run --flavor dev --dart-define-from-file=config/dev.json`
enum AppFlavor {
  dev,
  staging,
  prod;

  static AppFlavor parse(String value) {
    return switch (value.toLowerCase()) {
      'staging' => AppFlavor.staging,
      'prod' => AppFlavor.prod,
      _ => AppFlavor.dev,
    };
  }

  String get name => switch (this) {
        AppFlavor.dev => 'dev',
        AppFlavor.staging => 'staging',
        AppFlavor.prod => 'prod',
      };

  String get displayName => switch (this) {
        AppFlavor.dev => 'Trip Planner DEV',
        AppFlavor.staging => 'Trip Planner STG',
        AppFlavor.prod => 'Trip Planner',
      };

  /// Default API base when `API_BASE_URL` is not overridden.
  String get defaultApiBaseUrl => switch (this) {
        AppFlavor.dev => 'http://127.0.0.1:8000',
        AppFlavor.staging => 'https://trip-planner-app-staging.fly.dev',
        AppFlavor.prod => 'https://trip-planner-app.fly.dev',
      };

  String get privacyPolicyUrl => switch (this) {
        AppFlavor.dev => 'https://github.com/jay-sadiq/custom-projects/blob/main/mobile/store/metadata/PRIVACY.md',
        AppFlavor.staging => 'https://github.com/jay-sadiq/custom-projects/blob/main/mobile/store/metadata/PRIVACY.md',
        AppFlavor.prod => 'https://github.com/jay-sadiq/custom-projects/blob/main/mobile/store/metadata/PRIVACY.md',
      };
}
