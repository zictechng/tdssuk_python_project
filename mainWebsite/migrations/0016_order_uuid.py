import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainWebsite', '0015_order_order_destination_country_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='uuid',
            field=models.UUIDField(null=True, default=uuid.uuid4, editable=False),
        ),
    ]