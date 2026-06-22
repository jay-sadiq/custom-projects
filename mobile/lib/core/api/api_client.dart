import 'package:dio/dio.dart';

import '../../config/env.dart';
import '../storage/token_storage.dart';

class ApiClient {
  ApiClient({
    required TokenStorage tokenStorage,
    Dio? dio,
  })  : _tokenStorage = tokenStorage,
        dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: '${Env.apiBaseUrl}${Env.apiPrefix}',
                connectTimeout: const Duration(seconds: 10),
                receiveTimeout: const Duration(seconds: 20),
                headers: {'Content-Type': 'application/json'},
              ),
            ) {
    this.dio.interceptors.add(
          InterceptorsWrapper(
            onRequest: _onRequest,
            onError: _onError,
          ),
        );
  }

  final TokenStorage _tokenStorage;
  final Dio dio;

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final accessToken = await _tokenStorage.readAccessToken();
    if (accessToken != null && accessToken.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $accessToken';
    }
    handler.next(options);
  }

  Future<void> _onError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    if (error.response?.statusCode != 401) {
      handler.next(error);
      return;
    }

    final refreshed = await _tryRefreshToken();
    if (!refreshed) {
      await _tokenStorage.clear();
      handler.next(error);
      return;
    }

    final accessToken = await _tokenStorage.readAccessToken();
    final request = error.requestOptions;
    request.headers['Authorization'] = 'Bearer $accessToken';
    try {
      final response = await dio.fetch(request);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }

  Future<bool> _tryRefreshToken() async {
    final refreshToken = await _tokenStorage.readRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      return false;
    }

    try {
      final response = await Dio(
        BaseOptions(baseUrl: '${Env.apiBaseUrl}${Env.apiPrefix}'),
      ).post(
        '/auth/token/refresh/',
        data: {'refresh': refreshToken},
      );
      final access = response.data['access'] as String?;
      if (access == null) {
        return false;
      }
      await _tokenStorage.saveTokens(
        accessToken: access,
        refreshToken: refreshToken,
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, dynamic>> health() async {
    final response = await dio.get<Map<String, dynamic>>('/health/');
    return response.data ?? {};
  }
}
