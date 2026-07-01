import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainWebsite', '0017_populate_order_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='uuid',
            field=models.UUIDField(unique=True, default=uuid.uuid4, editable=False),
        ),
    ]