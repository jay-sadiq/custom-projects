#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
    import django

    django.setup()
    from django.core.management import call_command

    print("Deprecated: use `python manage.py parse_and_seed --user <username> --source-dir <path>` instead.")
    if len(sys.argv) < 3:
        print("Usage: parse_and_seed.py <username> <source-dir>")
        sys.exit(1)
    call_command("parse_and_seed", user=sys.argv[1], source_dir=sys.argv[2])
