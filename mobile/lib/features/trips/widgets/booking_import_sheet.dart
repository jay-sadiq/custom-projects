import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
  String? _forwardingAddress;
  Map<String, dynamic>? _draft;

  @override
  void initState() {
    super.initState();
    widget.repository.fetchBookingForwardingAddress().then((address) {
      if (mounted) {
        setState(() => _forwardingAddress = address);
      }
    }).catchError((_) {});
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _preview() async {
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
      _draft = null;
    });

    try {
      final draft = await widget.repository.previewBookingImport(
        text: text,
        tripId: widget.tripId,
      );
      if (mounted) {
        setState(() => _draft = draft);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not parse booking. Check text and try again.');
      }
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  Future<void> _confirm() async {
    final draft = _draft;
    if (draft == null) return;
    if (!ref.read(isOnlineProvider)) {
      showOfflineSnackBar(context);
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final result = await widget.repository.confirmBookingImport(
        draftId: draft['id'] as int,
        tripId: widget.tripId,
      );
      final booking = result['booking'] as Map<String, dynamic>? ?? {};
      if (mounted) {
        setState(() {
          _success = 'Added booking: ${booking['title'] ?? 'OK'}';
          _draft = null;
          _controller.clear();
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not confirm booking.');
      }
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final parsed = _draft?['parsed'] as Map<String, dynamic>?;

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
            'Paste confirmation text to preview, then confirm onto this trip.',
          ),
          if (_forwardingAddress != null && _forwardingAddress!.isNotEmpty) ...[
            const SizedBox(height: 12),
            InkWell(
              onTap: () {
                Clipboard.setData(ClipboardData(text: _forwardingAddress!));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Forwarding address copied')),
                );
              },
              child: Text(
                'Email forward: $_forwardingAddress',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ],
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            maxLines: 5,
            decoration: const InputDecoration(
              hintText: 'Paste booking confirmation…',
              border: OutlineInputBorder(),
            ),
          ),
          if (_draft != null && parsed != null) ...[
            const SizedBox(height: 12),
            Card(
              child: ListTile(
                title: Text(parsed['title']?.toString() ?? 'Parsed booking'),
                subtitle: Text(
                  [
                    if (parsed['booking_type'] != null) parsed['booking_type'],
                    if (parsed['confirmation_number'] != null)
                      'Ref ${parsed['confirmation_number']}',
                  ].join(' · '),
                ),
              ),
            ),
          ],
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          if (_success != null) ...[
            const SizedBox(height: 8),
            Text(_success!, style: const TextStyle(color: Colors.green)),
          ],
          const SizedBox(height: 12),
          if (_draft == null)
            FilledButton.icon(
              onPressed: _submitting ? null : _preview,
              icon: _submitting
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.preview),
              label: const Text('Parse for review'),
            )
          else
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _submitting
                        ? null
                        : () => setState(() => _draft = null),
                    child: const Text('Edit'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _submitting ? null : _confirm,
                    icon: const Icon(Icons.check),
                    label: const Text('Confirm'),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}
