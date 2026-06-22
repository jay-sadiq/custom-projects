import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../network/connectivity_service.dart';

class OfflineBanner extends ConsumerWidget {
  const OfflineBanner({super.key, this.child});

  final Widget? child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOnline = ref.watch(isOnlineProvider);

    return Column(
      children: [
        if (!isOnline)
          MaterialBanner(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            content: const Text(
              'Offline — showing cached data. Edits are disabled.',
            ),
            leading: const Icon(Icons.wifi_off, color: Colors.orange),
            actions: const [SizedBox.shrink()],
          ),
        if (child != null) Expanded(child: child!),
      ],
    );
  }
}

class OfflineAwareScaffold extends ConsumerWidget {
  const OfflineAwareScaffold({
    super.key,
    this.appBar,
    this.floatingActionButton,
    required this.body,
  });

  final PreferredSizeWidget? appBar;
  final Widget? floatingActionButton;
  final Widget body;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOnline = ref.watch(isOnlineProvider);

    return Scaffold(
      appBar: appBar,
      floatingActionButton: floatingActionButton,
      body: Column(
        children: [
          if (!isOnline)
            Container(
              width: double.infinity,
              color: Colors.orange.shade100,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: const Row(
                children: [
                  Icon(Icons.wifi_off, size: 18, color: Colors.orange),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Offline — cached data only. Edits disabled.',
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
          Expanded(child: body),
        ],
      ),
    );
  }
}

void showOfflineSnackBar(BuildContext context) {
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(
      content: Text('You are offline. Connect to make changes.'),
    ),
  );
}
