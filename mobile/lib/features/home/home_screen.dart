import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../config/env.dart';
import '../../core/theme/app_theme.dart';
import '../auth/auth_providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(apiHealthProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Trip Planner'),
        actions: [
          IconButton(
            tooltip: 'Log out',
            onPressed: () async {
              await ref.read(authControllerProvider.notifier).logout();
              if (context.mounted) {
                context.go('/login');
              }
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'API connection',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${Env.apiBaseUrl}${Env.apiPrefix}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textSecondary,
                        ),
                  ),
                  const SizedBox(height: 12),
                  health.when(
                    data: (payload) {
                      final connected = payload['status'] == 'ok';
                      return Row(
                        children: [
                          Icon(
                            connected ? Icons.check_circle : Icons.error,
                            color: connected ? Colors.green : Colors.red,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            connected ? 'Connected' : 'Unexpected response',
                            style: TextStyle(
                              color: connected ? Colors.green : Colors.red,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      );
                    },
                    loading: () => const Row(
                      children: [
                        SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                        SizedBox(width: 8),
                        Text('Checking API…'),
                      ],
                    ),
                    error: (error, stackTrace) => const Row(
                      children: [
                        Icon(Icons.cloud_off, color: Colors.red),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Disconnected — start Django and check API_BASE_URL',
                            style: TextStyle(color: Colors.red),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    onPressed: () => ref.invalidate(apiHealthProvider),
                    child: const Text('Retry health check'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: ListTile(
              leading: const Icon(Icons.map, color: AppColors.crimson),
              title: const Text('Sample trip shell'),
              subtitle: const Text('Phase 11 will load your real trips here'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/trips/1/day/1'),
            ),
          ),
        ],
      ),
    );
  }
}
