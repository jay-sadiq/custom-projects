import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../trips_providers.dart';
import '../trips_repository.dart';

class ChatEditSheet extends ConsumerStatefulWidget {
  const ChatEditSheet({
    super.key,
    required this.dayId,
    required this.tripId,
    required this.repository,
  });

  final int dayId;
  final int tripId;
  final TripsRepository repository;

  static Future<void> show(
    BuildContext context, {
    required int dayId,
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
        child: ChatEditSheet(
          dayId: dayId,
          tripId: tripId,
          repository: repository,
        ),
      ),
    );
  }

  @override
  ConsumerState<ChatEditSheet> createState() => _ChatEditSheetState();
}

class _ChatEditSheetState extends ConsumerState<ChatEditSheet> {
  final _controller = TextEditingController();
  bool _sending = false;
  String? _error;
  String? _success;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final message = _controller.text.trim();
    if (message.isEmpty) return;

    setState(() {
      _sending = true;
      _error = null;
      _success = null;
    });

    try {
      final result = await widget.repository.chatEditDay(widget.dayId, message);
      ref.invalidate(dayStopsProvider(widget.dayId));
      ref.invalidate(tripDaysProvider(widget.tripId));
      if (mounted) {
        setState(() {
          _success = result['summary'] as String? ?? 'Agenda updated.';
          _controller.clear();
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Edit failed. Check API and try again.');
      }
    } finally {
      if (mounted) {
        setState(() => _sending = false);
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
            'AI agenda edit',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Try: “Add lunch near the old city” or “Move museum to afternoon”',
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            maxLines: 3,
            textInputAction: TextInputAction.send,
            onSubmitted: (_) => _sending ? null : _send(),
            decoration: const InputDecoration(
              hintText: 'Describe the change…',
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
            onPressed: _sending ? null : _send,
            icon: _sending
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.auto_awesome),
            label: const Text('Apply edit'),
          ),
        ],
      ),
    );
  }
}
