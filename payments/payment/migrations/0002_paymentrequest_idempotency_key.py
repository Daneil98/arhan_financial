from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentrequest',
            name='idempotency_key',
            field=models.CharField(blank=True, max_length=120, null=True, unique=True),
        ),
    ]
