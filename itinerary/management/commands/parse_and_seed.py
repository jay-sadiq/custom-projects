from django.core.management.base import BaseCommand, CommandError

from itinerary.dev_seed.baku import resolve_seed_user
from itinerary.dev_seed.html_seed import seed_from_html


class Command(BaseCommand):
    help = "Seed a trip from legacy day HTML files for a specific user (dev only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            required=True,
            help="Username that should own the seeded trip.",
        )
        parser.add_argument(
            "--source-dir",
            required=True,
            help="Directory containing day1.html … day11.html source files.",
        )

    def handle(self, *args, **options):
        try:
            user = resolve_seed_user(options["user"])
        except Exception as exc:
            raise CommandError(f"Could not resolve user '{options['user']}': {exc}") from exc

        try:
            trip = seed_from_html(user, options["source_dir"])
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(f"Seeded trip {trip.id} from HTML for user {user.username}.")
        )
