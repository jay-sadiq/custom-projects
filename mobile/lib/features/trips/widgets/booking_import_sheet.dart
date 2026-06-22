import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/connectivity_service.dart';
import '../../../core/widgets/offline_banner.dart';
import '../trips_repository.dart';

class BookingImportSheet extends ConsumerStatefulWidget {
  const BookingImportSheet({
    super.key,
    required this.tripId,
    required this.repository,
  });

  final int tripId;
  final TripsRepository repository;

  static Future<void> show(
    BuildContext context, {
    required int tripId,
    required TripsRepository repository,
  }) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.viewInsetsOf(context).bottom,
        ),
        child: BookingImportSheet(tripId: tripId, repository: repository),
      ),
    );
  }

  @override
  ConsumerState<BookingImportSheet> createState() => _BookingImportSheetState();
}

class _BookingImportSheetState extends ConsumerState<BookingImportSheet> {
  final _controller = TextEditingController();
  bool _submitting = false;
  String? _error;
  String? _success;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!ref.read(isOnlineProvider)) {
      showOfflineSnackBar(context);
      return;
    }

    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _submitting = true;
      _error = null;
      _success = null;
    });

    try {
      final booking = await widget.repository.importBooking(widget.tripId, text);
      if (mounted) {
        setState(() {
          _success = 'Added booking: ${booking.title}';
          _controller.clear();
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not import booking. Check text and try again.');
      }
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Import booking',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Paste confirmation email or ticket text. AI will extract the booking details.',
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            maxLines: 6,
            decoration: const InputDecoration(
              hintText: 'Paste booking confirmation…',
              border: OutlineInputBorder(),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_success != null) ...[
            const SizedBox(height: 8),
            Text(_success!, style: const TextStyle(color: Colors.green)),
          ],
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _submitting ? null : _submit,
            icon: _submitting
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.flight_takeoff),
            label: const Text('Import booking'),
          ),
        ],
      ),
    );
  }
}
