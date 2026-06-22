# Generated manually for Phase 1 authorization

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def delete_orphan_trips(apps, schema_editor):
    Trip = apps.get_model("itinerary", "Trip")
    Trip.objects.filter(user__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("itinerary", "0002_stopblock_end_time_of_day_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(delete_orphan_trips, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="trip",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="trips",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
