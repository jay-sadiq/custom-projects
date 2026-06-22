import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../models/trip_models.dart';
import '../trips_providers.dart';

class StopReviewsSheet extends ConsumerWidget {
  const StopReviewsSheet({super.key, required this.stopId});

  final int stopId;

  static Future<void> show(BuildContext context, int stopId) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => StopReviewsSheet(stopId: stopId),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final reviews = ref.watch(stopReviewsProvider(stopId));

    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        0,
        20,
        20 + MediaQuery.viewPaddingOf(context).bottom,
      ),
      child: reviews.when(
        data: (data) {
          return Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Reviews',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              if (data.rating > 0) ...[
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.star, color: Colors.amber, size: 20),
                    const SizedBox(width: 4),
                    Text(
                      data.rating.toStringAsFixed(1),
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    if (data.isDemoData)
                      const Padding(
                        padding: EdgeInsets.only(left: 8),
                        child: Text(
                          'Demo data',
                          style: TextStyle(color: AppColors.textSecondary),
                        ),
                      ),
                  ],
                ),
              ],
              if (data.photoUrls.isNotEmpty) ...[
                const SizedBox(height: 12),
                SizedBox(
                  height: 88,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: data.photoUrls.length,
                    separatorBuilder: (context, index) => const SizedBox(width: 8),
                    itemBuilder: (context, index) {
                      return ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          data.photoUrls[index],
                          width: 88,
                          height: 88,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) => Container(
                            width: 88,
                            height: 88,
                            color: Colors.grey.shade200,
                            child: const Icon(Icons.broken_image),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
              const SizedBox(height: 12),
              if (data.reviews.isEmpty)
                const Text(
                  'No reviews available.',
                  style: TextStyle(color: AppColors.textSecondary),
                )
              else
                ConstrainedBox(
                  constraints: BoxConstraints(
                    maxHeight: MediaQuery.sizeOf(context).height * 0.45,
                  ),
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: data.reviews.length,
                    separatorBuilder: (context, index) =>
                        const Divider(height: 20),
                    itemBuilder: (context, index) {
                      final review = data.reviews[index];
                      return _ReviewTile(review: review);
                    },
                  ),
                ),
            ],
          );
        },
        loading: () => const SizedBox(
          height: 120,
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (error, stackTrace) => const Text('Could not load reviews'),
      ),
    );
  }
}

class _ReviewTile extends StatelessWidget {
  const _ReviewTile({required this.review});

  final StopReview review;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              review.author,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const Spacer(),
            if (review.rating > 0)
              Text('${review.rating.toStringAsFixed(1)} ★'),
          ],
        ),
        if (review.text.isNotEmpty) ...[
          const SizedBox(height: 6),
          Text(review.text),
        ],
      ],
    );
  }
}
