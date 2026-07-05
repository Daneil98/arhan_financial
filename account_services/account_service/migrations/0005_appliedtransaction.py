from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account_service', '0004_rename_savings_account_card_bank_account_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppliedTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=120, unique=True)),
                ('operation', models.CharField(max_length=10)),
                ('account_number', models.CharField(max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
