import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final connectivityServiceProvider = Provider<ConnectivityService>((ref) {
  final service = ConnectivityService();
  ref.onDispose(service.dispose);
  return service;
});

final isOnlineProvider = StateNotifierProvider<OnlineStatusNotifier, bool>((ref) {
  return OnlineStatusNotifier(ref.watch(connectivityServiceProvider));
});

class ConnectivityService {
  ConnectivityService() : _connectivity = Connectivity();

  final Connectivity _connectivity;

  Future<bool> checkIsOnline() async {
    final results = await _connectivity.checkConnectivity();
    return _isOnline(results);
  }

  bool _isOnline(List<ConnectivityResult> results) {
    return results.any((result) => result != ConnectivityResult.none);
  }

  StreamSubscription<List<ConnectivityResult>> listen(
    void Function(bool isOnline) onChanged,
  ) {
    return _connectivity.onConnectivityChanged.listen((results) {
      onChanged(_isOnline(results));
    });
  }

  void dispose() {}
}

class OnlineStatusNotifier extends StateNotifier<bool> {
  OnlineStatusNotifier(this._connectivity) : super(true) {
    _subscription = _connectivity.listen((isOnline) {
      state = isOnline;
    });
    _connectivity.checkIsOnline().then((isOnline) {
      state = isOnline;
    });
  }

  final ConnectivityService _connectivity;
  late final StreamSubscription<List<ConnectivityResult>> _subscription;

  void markOnline() => state = true;
  void markOffline() => state = false;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
