import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/storage/token_storage.dart';
import 'auth_repository.dart';

final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(tokenStorage: ref.watch(tokenStorageProvider));
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    apiClient: ref.watch(apiClientProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});

class AuthState {
  const AuthState({
    required this.isAuthenticated,
    this.isLoading = false,
    this.errorMessage,
  });

  final bool isAuthenticated;
  final bool isLoading;
  final String? errorMessage;

  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    String? errorMessage,
    bool clearError = false,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._authRepository)
      : super(const AuthState(isAuthenticated: false, isLoading: true));

  final AuthRepository _authRepository;

  Future<void> bootstrap() async {
    final hasSession = await _authRepository.hasStoredSession();
    state = AuthState(isAuthenticated: hasSession);
  }

  Future<bool> login(String username, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      await _authRepository.login(username: username, password: password);
      state = const AuthState(isAuthenticated: true);
      return true;
    } catch (error) {
      state = AuthState(
        isAuthenticated: false,
        errorMessage: 'Login failed. Check your credentials and API URL.',
      );
      return false;
    }
  }

  Future<bool> register(String username, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      await _authRepository.register(username: username, password: password);
      await _authRepository.login(username: username, password: password);
      state = const AuthState(isAuthenticated: true);
      return true;
    } catch (error) {
      state = AuthState(
        isAuthenticated: false,
        errorMessage: 'Registration failed. Username may already exist.',
      );
      return false;
    }
  }

  Future<void> logout() async {
    await _authRepository.logout();
    state = const AuthState(isAuthenticated: false);
  }
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref.watch(authRepositoryProvider));
});

final apiHealthProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final client = ref.watch(apiClientProvider);
  return client.health();
});
