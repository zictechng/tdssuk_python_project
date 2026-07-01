import uuid

from django.db import migrations


def populate_uuid(apps, schema_editor):
    Order = apps.get_model('mainWebsite', 'order')
    for order in Order.objects.all():
        order.uuid = uuid.uuid4()
        order.save(update_fields=['uuid'])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('mainWebsite', '0016_order_uuid'),
    ]

    operations = [
        migrations.RunPython(populate_uuid, reverse_noop),
    ]