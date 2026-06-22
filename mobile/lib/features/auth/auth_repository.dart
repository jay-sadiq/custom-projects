import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../core/storage/token_storage.dart';

class AuthRepository {
  AuthRepository({
    required ApiClient apiClient,
    required TokenStorage tokenStorage,
  })  : _apiClient = apiClient,
        _tokenStorage = tokenStorage;

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  Future<void> register({
    required String username,
    required String password,
    String email = '',
  }) async {
    await _apiClient.dio.post(
      '/auth/register/',
      data: {
        'username': username,
        'password': password,
        if (email.isNotEmpty) 'email': email,
      },
    );
  }

  Future<void> login({
    required String username,
    required String password,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/auth/login/',
      data: {
        'username': username,
        'password': password,
      },
    );
    final data = response.data ?? {};
    final access = data['access'] as String?;
    final refresh = data['refresh'] as String?;
    if (access == null || refresh == null) {
      throw DioException(
        requestOptions: response.requestOptions,
        message: 'Login response missing tokens.',
      );
    }
    await _tokenStorage.saveTokens(accessToken: access, refreshToken: refresh);
  }

  Future<void> logout() => _tokenStorage.clear();

  Future<bool> hasStoredSession() async {
    final access = await _tokenStorage.readAccessToken();
    return access != null && access.isNotEmpty;
  }
}
