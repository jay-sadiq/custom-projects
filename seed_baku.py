#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
    import django

    django.setup()
    from django.core.management import call_command

    print("Deprecated: use `python manage.py seed_baku --user <username>` instead.")
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    call_command("seed_baku", user=username)
