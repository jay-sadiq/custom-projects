import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/network/connectivity_service.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/offline_banner.dart';
import '../trips_providers.dart';
import '../trips_repository.dart';

class StopPhotosSection extends ConsumerStatefulWidget {
  const StopPhotosSection({
    super.key,
    required this.stopId,
    required this.repository,
  });

  final int stopId;
  final TripsRepository repository;

  @override
  ConsumerState<StopPhotosSection> createState() => _StopPhotosSectionState();
}

class _StopPhotosSectionState extends ConsumerState<StopPhotosSection> {
  bool _uploading = false;

  Future<void> _pickPhoto(ImageSource source) async {
    if (!ref.read(isOnlineProvider)) {
      if (mounted) showOfflineSnackBar(context);
      return;
    }

    final picker = ImagePicker();
    final image = await picker.pickImage(source: source, imageQuality: 85);
    if (image == null) return;

    setState(() => _uploading = true);
    try {
      await widget.repository.uploadStopPhoto(widget.stopId, image.path);
      ref.invalidate(stopPhotosProvider(widget.stopId));
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Photo upload failed')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _uploading = false);
      }
    }
  }

  void _showSourcePicker() {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Wrap(
            children: [
              ListTile(
                leading: const Icon(Icons.photo_camera),
                title: const Text('Take photo'),
                onTap: () {
                  Navigator.pop(context);
                  _pickPhoto(ImageSource.camera);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library),
                title: const Text('Choose from gallery'),
                onTap: () {
                  Navigator.pop(context);
                  _pickPhoto(ImageSource.gallery);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final photos = ref.watch(stopPhotosProvider(widget.stopId));
    final isOnline = ref.watch(isOnlineProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              'Your photos',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const Spacer(),
            if (_uploading)
              const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            else
              TextButton.icon(
                onPressed: isOnline ? _showSourcePicker : () => showOfflineSnackBar(context),
                icon: const Icon(Icons.add_a_photo, size: 18),
                label: const Text('Add'),
              ),
          ],
        ),
        const SizedBox(height: 8),
        photos.when(
          data: (items) {
            if (items.isEmpty) {
              return const Text(
                'No photos yet. Add one from your camera or gallery.',
                style: TextStyle(color: AppColors.textSecondary),
              );
            }
            return SizedBox(
              height: 92,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: items.length,
                separatorBuilder: (context, index) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final photo = items[index];
                  return ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.network(
                      photo.imageUrl,
                      width: 92,
                      height: 92,
                      fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) => Container(
                        width: 92,
                        height: 92,
                        color: Colors.grey.shade200,
                        child: const Icon(Icons.broken_image),
                      ),
                    ),
                  );
                },
              ),
            );
          },
          loading: () => const SizedBox(
            height: 40,
            child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
          ),
          error: (error, stackTrace) => const Text(
            'Could not load photos',
            style: TextStyle(color: AppColors.textSecondary),
          ),
        ),
      ],
    );
  }
}
