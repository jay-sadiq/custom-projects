import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import 'trips_providers.dart';

class CreateTripScreen extends ConsumerStatefulWidget {
  const CreateTripScreen({super.key});

  @override
  ConsumerState<CreateTripScreen> createState() => _CreateTripScreenState();
}

class _CreateTripScreenState extends ConsumerState<CreateTripScreen> {
  final _formKey = GlobalKey<FormState>();
  final _destinationController = TextEditingController();
  final _detailsController = TextEditingController();
  int _daysCount = 3;
  DateTime _startDate = DateTime.now().add(const Duration(days: 30));

  @override
  void dispose() {
    _destinationController.dispose();
    _detailsController.dispose();
    super.dispose();
  }

  Future<void> _pickStartDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _startDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365 * 2)),
    );
    if (picked != null) {
      setState(() => _startDate = picked);
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final tripId = await ref.read(createTripControllerProvider.notifier).submit(
          destination: _destinationController.text.trim(),
          daysCount: _daysCount,
          startDate: _startDate,
          details: _detailsController.text.trim(),
        );

    if (!mounted) return;

    if (tripId != null) {
      ref.invalidate(tripsListProvider);
      context.go('/trips/$tripId/day/1');
    }
  }

  @override
  Widget build(BuildContext context) {
    final createState = ref.watch(createTripControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Plan a trip'),
      ),
      body: AbsorbPointer(
        absorbing: createState.isSubmitting,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text(
              'AI will build your itinerary',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Same flow as the web app — destination, length, and travel details.',
              style: TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 24),
            Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  TextFormField(
                    controller: _destinationController,
                    decoration: const InputDecoration(
                      labelText: 'Destination',
                      hintText: 'e.g. Lisbon, Portugal',
                    ),
                    textInputAction: TextInputAction.next,
                    validator: (value) =>
                        value == null || value.trim().isEmpty
                            ? 'Destination is required'
                            : null,
                  ),
                  const SizedBox(height: 20),
                  Text('Trip length: $_daysCount days'),
                  Slider(
                    value: _daysCount.toDouble(),
                    min: 1,
                    max: 14,
                    divisions: 13,
                    label: '$_daysCount days',
                    onChanged: (value) =>
                        setState(() => _daysCount = value.round()),
                  ),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: _pickStartDate,
                    icon: const Icon(Icons.calendar_today),
                    label: Text(
                      'Start date: ${_startDate.year}-${_startDate.month.toString().padLeft(2, '0')}-${_startDate.day.toString().padLeft(2, '0')}',
                    ),
                  ),
                  const SizedBox(height: 20),
                  TextFormField(
                    controller: _detailsController,
                    decoration: const InputDecoration(
                      labelText: 'Trip details (optional)',
                      hintText: 'Family with kids, food preferences, pace…',
                      alignLabelWithHint: true,
                    ),
                    maxLines: 4,
                  ),
                ],
              ),
            ),
            if (createState.errorMessage != null) ...[
              const SizedBox(height: 16),
              Text(
                createState.errorMessage!,
                style: const TextStyle(color: Colors.red),
              ),
            ],
            if (createState.isSubmitting) ...[
              const SizedBox(height: 24),
              const Center(child: CircularProgressIndicator()),
              const SizedBox(height: 12),
              Text(
                createState.statusMessage,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textSecondary),
              ),
            ],
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: createState.isSubmitting ? null : _submit,
              icon: const Icon(Icons.auto_awesome),
              label: const Text('Create trip with AI'),
            ),
          ],
        ),
      ),
    );
  }
}
