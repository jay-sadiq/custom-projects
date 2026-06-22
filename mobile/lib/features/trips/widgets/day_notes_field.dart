import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/connectivity_service.dart';
import '../../../core/widgets/offline_banner.dart';
import '../models/trip_models.dart';
import '../trips_providers.dart';
import '../trips_repository.dart';

class DayNotesField extends ConsumerStatefulWidget {
  const DayNotesField({
    super.key,
    required this.day,
    required this.repository,
  });

  final DayItinerary day;
  final TripsRepository repository;

  @override
  ConsumerState<DayNotesField> createState() => _DayNotesFieldState();
}

class _DayNotesFieldState extends ConsumerState<DayNotesField> {
  late final TextEditingController _controller;
  Timer? _debounce;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.day.notes);
  }

  @override
  void didUpdateWidget(covariant DayNotesField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.day.id != widget.day.id &&
        _controller.text != widget.day.notes) {
      _controller.text = widget.day.notes;
    }
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    if (!ref.read(isOnlineProvider)) {
      showOfflineSnackBar(context);
      return;
    }
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 600), () async {
      setState(() {
        _saving = true;
        _error = null;
      });
      try {
        await widget.repository.updateDayNotes(widget.day.id, value);
        ref.invalidate(tripDaysProvider(widget.day.tripId));
      } catch (_) {
        if (mounted) {
          setState(() => _error = 'Could not save notes');
        }
      } finally {
        if (mounted) {
          setState(() => _saving = false);
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  'Day notes',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                const Spacer(),
                if (_saving)
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _controller,
              onChanged: _onChanged,
              readOnly: !ref.watch(isOnlineProvider),
              maxLines: 4,
              decoration: const InputDecoration(
                hintText: 'Add notes for this day…',
                border: OutlineInputBorder(),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],
          ],
        ),
      ),
    );
  }
}
