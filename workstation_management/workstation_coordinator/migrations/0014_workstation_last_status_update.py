# Generated by Django 5.0.1 on 2024-05-23 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workstation_coordinator', '0013_alter_proxymapping_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='workstation',
            name='last_status_update',
            field=models.DateTimeField(auto_now=True),
        ),
    ]