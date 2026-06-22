from django.core.management.base import BaseCommand, CommandError

from itinerary.dev_seed.baku import resolve_seed_user, seed_baku_itinerary


class Command(BaseCommand):
    help = "Seed the demo Baku family itinerary for a specific user (dev only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            required=True,
            help="Username that should own the seeded trip.",
        )

    def handle(self, *args, **options):
        try:
            user = resolve_seed_user(options["user"])
        except Exception as exc:
            raise CommandError(f"Could not resolve user '{options['user']}': {exc}") from exc

        trip = seed_baku_itinerary(user)
        self.stdout.write(self.style.SUCCESS(f"Seeded trip {trip.id} for user {user.username}."))
